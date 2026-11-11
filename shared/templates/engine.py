"""版式模板渲染器：按「风格文件 + 镜头模板 + 片段模板」把口播原片和素材合成一段视频。

模板只定结构（每块放哪、什么形状、怎么进场），颜色、字体、字号这类皮肤从风格文件读。
同一个模板放进不同风格，出来的颜色和字体跟着风格变。

用法：
  python engine.py render <job.json> <out.mp4>          渲染一段（通常是开头）
  python engine.py still  <job.json> <秒> <out.jpg>     只出一帧，先看效果
  python engine.py wire   <模板id> <out.jpg> [风格id]    出一张模板线框图（不需要素材）
  python engine.py list                                   列出所有模板
  python engine.py plan   <job.json> [out.json]           只算时间轴不出画面：每个镜头的起止、切点、用哪段素材、文字、拍点。
                                                          审片台读这个画轨道，所有模板任务（口播开头、vlog 卡点）都是同一个格式

job.json 见 templates/README.md「任务文件」一节。
配乐卡点（维度 14）：job 里给 music（配乐 + 节拍表），片段模板里的镜头就能按「几拍」排、按拍换素材，
节拍表用 shared/music/beatgen.py 生成，或用 shared/music/beats.py 从现成的歌里测。
"""
import json, os, sys, math, subprocess, glob
try:
    import numpy as np, cv2
except ImportError:
    raise SystemExit("缺 numpy / opencv：运行技能目录里的 install.sh（Windows：install.ps1）装好再用版式模板。")
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
# 插件里的复制品在 <here>/library；仓库里的正本在仓库根目录
LIB_DIRS = [os.path.join(HERE, "library"), os.path.normpath(os.path.join(HERE, "..", ".."))]
FPS = 30
MODELS = {  # 人像分割和人脸位置（Google MediaPipe，Apache-2.0），第一次用时自动下载到 models 目录
    "selfie_multiclass_256x256.tflite": "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
    "blaze_face_short_range.tflite": "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite",
}


def model(models_dir, name):
    p = os.path.join(models_dir, name)
    if not os.path.exists(p):
        import urllib.request
        os.makedirs(models_dir, exist_ok=True)
        print("下载模型", name, "…", flush=True)
        urllib.request.urlretrieve(MODELS[name], p + ".part")
        os.replace(p + ".part", p)
    return p


# ---------------------------------------------------------------- 读库
def _find(kind, name):
    sub = {"shot": "templates/shots", "sequence": "templates/sequences", "style": "styles"}[kind]
    for d in LIB_DIRS:
        p = os.path.join(d, sub, name + ".json")
        if os.path.exists(p):
            return p
    raise SystemExit(f"找不到{kind}：{name}")


def load(kind, name):
    with open(_find(kind, name), encoding="utf-8") as f:
        return json.load(f)


def style_dir(name):
    return os.path.dirname(_find("style", name))


def hexrgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


class Style:
    def __init__(self, name):
        self.d = load("style", name)
        self.W, self.H = self.d["canvas"]
        self.tok = self.d["tokens"]
        self.base = style_dir(name)
        self._fonts = {}

    def color(self, v):
        if v is None:
            return None
        v = self.tok.get(v, v)
        return hexrgb(v) if isinstance(v, str) else tuple(v)

    def font_path(self, role):
        for cand in self.d["fonts"][role]:
            p, _, idx = cand.partition("#")
            p = os.path.expanduser(p)
            if not os.path.isabs(p):
                # 相对路径按风格对应技能的 fonts/ 找，仓库里在 plugins/*/skills/*/fonts
                hits = [os.path.join(self.base, "..", p)] + glob.glob(os.path.join(self.base, "..", "plugins", "*", "skills", "*", p))
                hits += [os.path.join(HERE, "..", "..", p)]
                p = next((h for h in hits if os.path.exists(h)), p)
            if os.path.exists(p):
                return p, int(idx or 0)
        raise SystemExit(f"风格 {self.d['id']} 的字体 {role} 一个都找不到：{self.d['fonts'][role]}")

    def font(self, role, px):
        k = (role, px)
        if k not in self._fonts:
            p, i = self.font_path(role)
            self._fonts[k] = ImageFont.truetype(p, px, index=i)
        return self._fonts[k]

    def text_style(self, name):
        return self.d["text"][name]


# ---------------------------------------------------------------- 素材
_SEG = {}


def segmenter(models):
    """人像分割（MediaPipe），口播原片抠像和「字在人后」共用一个。"""
    if "seg" not in _SEG:
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        _SEG["mp"] = mp
        _SEG["seg"] = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=model(models, "selfie_multiclass_256x256.tflite")),
            output_confidence_masks=True))
    return _SEG["seg"], _SEG["mp"]


def person_mask(img, models):
    seg, mp = segmenter(models)
    r = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img)))
    a = 1.0 - r.confidence_masks[0].numpy_view()
    a = a[..., 0] if a.ndim == 3 else a
    return np.clip((a - 0.35) / 0.4, 0, 1).astype(np.float32)


class Beats:
    """节拍表：beatgen.py / beats.py 的输出。时间都换算成从开头片段第 0 秒起。"""

    def __init__(self, spec, base):
        p = spec.get("beats") or os.path.splitext(spec["src"])[0] + ".beats.json"
        p = os.path.join(base, os.path.expanduser(p))
        with open(p, encoding="utf-8") as f:
            self.d = json.load(f)
        self.bpm = self.d["bpm"]
        self.len = 60.0 / self.bpm
        self.raw = np.array(self.d["beats"], np.float64)
        self.first = 0.0   # 片段第 0 拍是歌里的第几拍（可以是负数：歌在片段开始之后才进来）
        self.offset = 0.0  # 片段第 0 秒在歌里的秒数

    def song(self, i):
        """歌里第 i 拍的秒数，i 可以是小数或超出节拍表（按 BPM 往两头推）。"""
        n = len(self.raw)
        if i < 0:
            return self.raw[0] + i * self.len
        if i > n - 1:
            return self.raw[-1] + (i - n + 1) * self.len
        return float(np.interp(i, np.arange(n), self.raw))

    def align_beat(self, i):
        self.first = i
        self.offset = self.song(i)

    def align_time(self, t):
        i = int(np.searchsorted(self.raw, t - 0.02))
        self.align_beat(i)

    def at(self, k):
        """片段里第 k 拍的秒数。"""
        return self.song(self.first + k) - self.offset

    def index_of(self, t):
        return int(np.argmin(np.abs(self.raw - t)))


class Portrait:
    """口播原片：按时间取帧；需要时做人像分割和人脸位置。"""

    def __init__(self, src, start, models):
        self.cap = cv2.VideoCapture(os.path.expanduser(src))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.start = start
        self.cache, self.mcache = {}, {}
        self.models = models
        self._seg = None
        self._last = -1
        self._frame = None
        self.face = None  # (cx, cy, w) 源画面坐标

    def idx(self, t):
        return int((self.start + t) * self.fps + 1e-6)

    def frame(self, t):
        i = self.idx(t)
        if i in self.cache:
            return self.cache[i]
        if i != self._last + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = self.cap.read()
        if not ok:
            f = self._frame
        self._last, self._frame = i, f
        f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        if len(self.cache) > 90:
            self.cache.clear()
        self.cache[i] = f
        return f

    def mask(self, t):
        """人像蒙版 0..1，和相邻帧做一点时间平滑，边缘不闪。"""
        i = self.idx(t)
        if i in self.mcache:
            return self.mcache[i]
        a = person_mask(self.frame(t), self.models)
        prev = self.mcache.get(i - 1)
        if prev is not None:
            a = a * 0.7 + prev * 0.3
        if len(self.mcache) > 90:
            self.mcache.clear()
        self.mcache[i] = a
        return a

    def detect_face(self, ts):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        fd = vision.FaceDetector.create_from_options(vision.FaceDetectorOptions(
            base_options=BaseOptions(model_asset_path=model(self.models, "blaze_face_short_range.tflite"))))
        boxes = []
        for t in ts:
            f = self.frame(t)
            d = fd.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)))
            if d.detections:
                b = d.detections[0].bounding_box
                boxes.append((b.origin_x + b.width / 2, b.origin_y + b.height / 2, b.width))
        fd.close()
        if boxes:
            self.face = tuple(np.median(np.array(boxes), axis=0))
        else:
            f = self.frame(ts[0])
            self.face = (f.shape[1] / 2, f.shape[0] * 0.35, f.shape[1] * 0.45)


class Content:
    """素材：图片（缓推）或视频。"""

    def __init__(self, spec, base):
        self.src = os.path.join(base, os.path.expanduser(spec["src"]))
        self.push = spec.get("push", 1.06)
        self.focus = spec.get("focus")  # 铺满时取景中心（素材宽高的比例），默认正中
        self.start = spec.get("start", 0)
        self.crop = spec.get("crop")  # [x, y, 宽, 高]，源画面比例，裁掉不要的部分（比如烧进去的字幕）
        ext = os.path.splitext(self.src)[1].lower()
        self.is_img = ext in (".png", ".jpg", ".jpeg", ".webp")
        if self.is_img:
            self.img = np.array(Image.open(self.src).convert("RGB"))
        else:
            self.cap = cv2.VideoCapture(self.src)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
            self._last, self._f = -1, None

    def frame(self, t, dur):
        if self.is_img:
            return self._crop(self.img), 1 + (self.push - 1) * min(1, max(0, t / max(dur, 0.1)))
        i = min(int((self.start + t) * self.fps), self.n - 1)  # 素材比镜头短就停在最后一帧
        if i != self._last or self._f is None:
            if i != self._last + 1:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = self.cap.read()
            if not ok and self._f is None:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, self.n - 2))
                ok, f = self.cap.read()
            if ok:
                self._f = self._crop(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            self._last = i
        return self._f, 1.0

    def _crop(self, f):
        if not self.crop or f is None:
            return f
        h, w = f.shape[:2]
        x, y, cw, ch = self.crop
        return f[int(y * h):int((y + ch) * h), int(x * w):int((x + cw) * w)]


# ---------------------------------------------------------------- 画图小工具
def fit_crop(src, bw, bh, focus=None, face_w=None, face_frac=None, zoom=1.0, face_y=0.42):
    """把源画面裁成 bw×bh：默认铺满；给了人脸和 face_frac 就让脸占框宽的这个比例。"""
    sh, sw = src.shape[:2]
    s = max(bw / sw, bh / sh)
    if face_frac and face_w:
        s = max(s, bw * face_frac / face_w)
    s *= zoom
    cx, cy = focus if focus else (sw / 2, sh / 2)
    cw, ch = bw / s, bh / s
    x0 = min(max(cx - cw / 2, 0), max(sw - cw, 0))
    y0 = min(max(cy - ch * 0.42, 0), max(sh - ch, 0))
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    return cv2.warpAffine(src, M, (int(bw), int(bh)), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def shape_mask(w, h, shape, radius):
    ss = 2
    m = np.zeros((h * ss, w * ss), np.uint8)
    if shape == "circle":
        r = min(w, h) * ss // 2
        cv2.circle(m, (w * ss // 2, h * ss // 2), r, 255, -1, cv2.LINE_AA)
    else:
        r = int(min(radius, min(w, h) / 2) * ss)
        if r <= 0:
            m[:] = 255
        else:
            cv2.rectangle(m, (r, 0), (w * ss - 1 - r, h * ss - 1), 255, -1)
            cv2.rectangle(m, (0, r), (w * ss - 1, h * ss - 1 - r), 255, -1)
            for cx, cy in [(r, r), (w * ss - 1 - r, r), (r, h * ss - 1 - r), (w * ss - 1 - r, h * ss - 1 - r)]:
                cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    m = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
    return m.astype(np.float32) / 255


def blend(dst, src, x, y, a, alpha=1.0):
    """把 src(h,w,3) 按蒙版 a(h,w) 贴到 dst 的 (x,y)，自动裁掉画外部分。"""
    H, W = dst.shape[:2]
    h, w = a.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    sa = a[y0 - y:y1 - y, x0 - x:x1 - x][..., None] * alpha
    ss = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    d = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (ss * sa + d * (1 - sa)).astype(np.uint8)


def solid(h, w, rgb):
    o = np.empty((h, w, 3), np.uint8)
    o[:] = rgb
    return o


def soft_shadow(dst, mask, x, y, strength=0.28, blur=26, dy=14):
    pad = blur * 2
    m = cv2.copyMakeBorder(mask, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    m = cv2.GaussianBlur(m, (0, 0), blur) * strength
    blend(dst, solid(*m.shape, (20, 18, 16)), x - pad, y - pad + dy, m)


def ring(dst, x, y, w, h, shape, radius, color, width, alpha):
    outer = shape_mask(w + 2 * width, h + 2 * width, shape, radius + width if shape != "circle" else 0)
    inner = np.zeros_like(outer)
    inner[width:width + h, width:width + w] = shape_mask(w, h, shape, radius)
    blend(dst, solid(*outer.shape, color), x - width, y - width, np.clip(outer - inner, 0, 1), alpha)


def paper(W, H, rgb, seed=7):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    n = cv2.resize(cv2.GaussianBlur(n, (0, 0), 1.2), (W, H))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    g = n * 5 + fine * 3
    o = np.clip(np.array(rgb, np.float32)[None, None] + g[..., None], 0, 255)
    return o.astype(np.uint8)


def dashed_outline(dst, mask, x, y, color, width, dash, alpha):
    m = (mask > 0.5).astype(np.uint8)
    k = max(1, width)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, 2 * k + 1)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    layer = np.zeros(m.shape, np.uint8)
    for c in cs:
        if len(c) < 50:
            continue
        pts = c[:, 0, :]
        seg = np.cumsum(np.r_[0, np.linalg.norm(np.diff(pts, axis=0), axis=1)])
        on = (seg // dash).astype(int) % 2 == 0
        for i in range(len(pts) - 1):
            if on[i]:
                cv2.line(layer, tuple(map(int, pts[i])), tuple(map(int, pts[i + 1])), 255, width, cv2.LINE_AA)
    blend(dst, solid(*layer.shape, color), x, y, layer.astype(np.float32) / 255, alpha)


# ---------------------------------------------------------------- 文字
class TextCache:
    def __init__(self, style):
        self.st = style
        self.c = {}

    def render(self, text, sname, max_w=None):
        k = (text, sname, max_w)
        if k in self.c:
            return self.c[k]
        st, S = self.st.text_style(sname), self.st
        px = int(st["size"] * S.H)
        f = S.font(st["font"], px)
        lines = text.split("\n")
        sw = int(st.get("stroke", 0) * S.H)
        lh = int(px * st.get("line_height", 1.15))
        track = st.get("track", 0) * px
        widths = []
        for ln in lines:
            widths.append(sum(f.getlength(ch) for ch in ln) + track * max(len(ln) - 1, 0))
        pad = sw + int(px * 0.3)
        bw, bh = int(max(widths)) + 2 * pad, lh * len(lines) + 2 * pad
        im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        fills = st.get("fills") or [st["fill"]]
        box = st.get("box")
        if box:
            bpx = int(box.get("pad", 0.4) * px)
            im = Image.new("RGBA", (bw + 2 * bpx, bh + bpx), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            col = S.color(box["fill"]) + (int(255 * box.get("alpha", 1)),)
            d.rounded_rectangle((pad, pad - bpx // 3, bw + 2 * bpx - pad, bh + bpx - pad + bpx // 3), int(px * 0.18), fill=col)
            ox, oy = bpx, bpx // 2
        else:
            ox, oy = 0, 0
        align = st.get("align", "center")
        for li, ln in enumerate(lines):
            x = pad + ox + {"center": (max(widths) - widths[li]) / 2, "left": 0, "right": max(widths) - widths[li]}[align]
            y = pad + oy + li * lh
            fill = S.color(fills[min(li, len(fills) - 1)])
            for ch in ln:
                d.text((x, y), ch, font=f, fill=fill, stroke_width=sw, stroke_fill=S.color(st.get("stroke_color", "ink")))
                x += f.getlength(ch) + track
        if st.get("shadow"):
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
            sh.putalpha(im.split()[3].point(lambda a: a * 0.45).filter(ImageFilter.GaussianBlur(max(2, px // 18))))
            out = Image.new("RGBA", im.size, (0, 0, 0, 0))
            out.alpha_composite(sh, (0, max(2, px // 16)))
            out.alpha_composite(im)
            im = out
        if max_w and im.width > max_w:
            im = im.resize((max_w, int(im.height * max_w / im.width)), Image.LANCZOS)
        a = np.array(im)
        self.c[k] = a
        return a


def put_text(dst, rgba, ax, ay, align, alpha=1.0, scale=1.0, reveal=1.0):
    if scale != 1.0:
        h, w = rgba.shape[:2]
        rgba = cv2.resize(rgba, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_LINEAR)
    h, w = rgba.shape[:2]
    if reveal < 1.0:
        rgba = rgba.copy()
        rgba[:, int(w * reveal):, 3] = 0
    x = {"center": ax - w // 2, "left": ax, "right": ax - w}[align]
    y = ay - h // 2
    blend(dst, rgba[..., :3], int(x), int(y), rgba[..., 3].astype(np.float32) / 255, alpha)


# ---------------------------------------------------------------- 渲染一帧
GEOM = ("rect", "roundrect", "circle")


def px_box(S, box):
    x, y, w, h = box
    W, H = S.W, S.H
    if h is None:  # 圆：高按宽算成正圆
        h = w * W / H
    return int(x * W), int(y * H), int(w * W), int(h * H)


def lerp(a, b, e):
    return a + (b - a) * e


class Renderer:
    def __init__(self, job, base):
        self.job = job
        self.base = base
        self.S = Style(job.get("style", "koubo"))
        self.txt = TextCache(self.S)
        self.models = os.path.expanduser(job.get("models", "~/.cache/edit-skills/models"))
        p = job.get("portrait")  # vlog 开头可以没有口播
        self.P = Portrait(p["src"], p.get("start", 0), self.models) if p else None
        self.contents = [Content(c, base) for c in job.get("content", [])]
        self.cues = job.get("cues", [])
        self.titles = job.get("titles", {})
        self.music = job.get("music")
        self.beats = Beats(self.music, base) if self.music else None
        self.paper = paper(self.S.W, self.S.H, self.S.color("paper" if "paper" in self.S.tok else "white"))
        self.look = dict(self.S.d.get("look", {}), **job.get("look", {}))
        self._grain = None
        self.shots = self.plan()
        dur = self.shots[-1]["t1"]
        if self.P:
            self.P.detect_face([dur * k / 6 for k in range(6)])

    # 片段模板 + 字幕时间 → 每个镜头的起止时间
    def plan(self):
        job = self.job
        if "shots" in job:
            spec = {"shots": job["shots"], "transition": job.get("transition", {})}
        else:
            spec = load("sequence", job["sequence"])
        self.trans = spec.get("transition", {"type": "morph", "duration": 0.4})
        shots, ci = [], 0
        cues = self.cues
        B = self.beats
        if B:  # 配乐对齐：标了 on_drop 的镜头正好从落点开始；没有就从歌的 music.start 开始
            pre = 0
            for s in spec["shots"]:
                if s.get("on_drop"):
                    break
                pre += s.get("beats", 0)
            else:
                pre = None
            if pre is not None and self.music.get("start", "auto") == "auto":
                B.align_beat(B.index_of(B.d.get("drop", 0)) - pre)
            else:
                st = self.music.get("start", 0)
                B.align_time(0 if st == "auto" else st)
        end_all = job.get("duration") or (cues[-1][1] if cues else (B.at(sum(s.get("beats", 0) for s in spec["shots"])) if B else 8))
        bi = 0      # 当前在第几拍
        cyc = None  # 按拍换素材时，素材轮到第几段（跨镜头接着往下轮）
        for k, s in enumerate(spec["shots"]):
            t0 = shots[-1]["t1"] if shots else 0
            n = s.get("cues", 1)
            if job.get("split"):  # 任务里可以按这一集的句子长短，改每个镜头占几句
                n = job["split"][k] if k < len(job["split"]) else n
            if "beats" in s and B:
                bi0 = bi
                bi += s["beats"]
                t1 = B.at(bi)
            elif n == "rest" or k == len(spec["shots"]) - 1:
                t1 = end_all
                ci = len(cues)
            elif "seconds" in s:
                t1 = t0 + s["seconds"]
            else:
                ci = min(ci + n, len(cues))
                t1 = cues[ci][0] if ci < len(cues) else end_all
            tpl = load("shot", s["template"])
            sh = dict(s, t0=t0, t1=t1, tpl=tpl, bg=s.get("background", tpl.get("background", {"type": "paper"})))
            # 按拍换素材：cut_every 是几拍换一次（0.5 = 半拍）。切点就是节拍表上的拍点
            ce = s.get("cut_every")
            if ce and B and "beats" in s:
                if cyc is None or isinstance(s.get("content"), int):
                    cyc = s.get("content", 0)
                pts, j = [], 0
                while j * ce < s["beats"] - 1e-6:
                    pts.append((B.at(bi0 + j * ce), cyc))
                    cyc += 1
                    j += 1
                sh["cuts"] = pts
                self._cyc0 = getattr(self, "_cyc0", None)
                if self._cyc0 is None:
                    self._cyc0 = pts[0][1]
            elif isinstance(s.get("content"), int):
                cyc = s["content"] + 1
            shots.append(sh)
        return shots

    def timeline(self):
        """时间轴（给审片台）：镜头 / 切点 / 文字 / 拍点，时间都是成片里的秒数。"""
        N = len(self.contents)
        out = {"job_version": 1, "style": self.S.d["id"], "sequence": self.job.get("sequence"),
               "duration": round(self.shots[-1]["t1"], 3), "canvas": [self.S.W, self.S.H], "shots": []}
        for k, sh in enumerate(self.shots):
            segs = []
            if sh.get("cuts"):
                for j, (a, _) in enumerate(sh["cuts"]):
                    b = sh["cuts"][j + 1][0] if j + 1 < len(sh["cuts"]) else sh["t1"]
                    c = self.cut_at(sh, a + 1e-4)[0]
                    segs.append({"t0": round(a, 3), "t1": round(b, 3), "content": self.job["content"][self.contents.index(c)]["src"]})
            elif N and (sh["tpl"].get("background", {}).get("type") == "content" or any(L["slot"] == "content" for L in sh["tpl"]["layers"])):
                c = self.content_of(sh)
                segs.append({"t0": round(sh["t0"], 3), "t1": round(sh["t1"], 3), "content": self.job["content"][self.contents.index(c)]["src"]})
            texts = {}
            for L in sh["tpl"]["layers"]:
                if L["slot"] == "title":
                    tx = self.title_text(sh, L)
                    if tx:
                        texts[L.get("key") or sh.get("title") or "title"] = tx
            out["shots"].append({"index": k, "template": sh["template"], "t0": round(sh["t0"], 3), "t1": round(sh["t1"], 3),
                                 "beats": sh.get("beats"), "cut_every": sh.get("cut_every"), "segments": segs, "texts": texts,
                                 **{k: sh[k] for k in ("role", "why", "chapter") if k in sh}})
        if self.beats:
            d = out["duration"]
            bs, k = [], 0
            while self.beats.at(k) <= d + 1e-6:
                if self.beats.at(k) >= -1e-6:
                    bs.append(round(self.beats.at(k), 3))
                k += 1
            out["music"] = {"src": self.music["src"], "bpm": self.beats.bpm, "offset": round(self.beats.offset, 3),
                            "beats": bs, "drop": round(self.beats.d.get("drop", 0) - self.beats.offset, 3)}
        if self.cues:
            out["cues"] = self.cues
        return out

    def beat_len(self):
        return self.beats.len if self.beats else 0.5

    def content_of(self, shot):
        if not self.contents:
            return None
        return self.contents[min(shot.get("content", 0), len(self.contents) - 1)]

    def cut_at(self, shot, t):
        """按拍换素材的镜头：现在轮到哪段素材、这段从哪一秒开始放 → (素材, 段内时间, 段长)"""
        cuts = shot.get("cuts")
        if not cuts or not self.contents:
            return self.content_of(shot), t - shot["t0"], shot["t1"] - shot["t0"]
        j = max(i for i, (a, _) in enumerate(cuts) if a <= t + 1e-6) if t >= cuts[0][0] else 0
        a, ci = cuts[j]
        b = cuts[j + 1][0] if j + 1 < len(cuts) else shot["t1"]
        N = len(self.contents)
        c0 = min(getattr(self, "_cyc0", 0) or 0, N - 1)
        # 快切只在「快切素材」里轮：跳过镜头里点名用的那几段（钩子、收尾、字在人后），不够就循环
        fixed = {sh["content"] % N for sh in self.shots if isinstance(sh.get("content"), int) and not sh.get("cuts")}
        pool = [i for i in range(c0, N) if i not in fixed] or list(range(N))
        return self.contents[pool[(ci - c0) % len(pool)]], t - a, b - a

    def title_text(self, shot, L=None):
        k = (L or {}).get("key") or shot.get("title")
        if not k:
            return None
        return shot.get("texts", {}).get(k) or self.titles.get(k) or (None if (L or {}).get("key") else k)

    def cue_at(self, t):
        for a, b, x in self.cues:
            if a <= t < b + 0.05:
                return x
        return None

    # 一个镜头的画面（不含转场），layers 可被转场改写几何
    def draw(self, canvas, shot, t, layers=None, alphas=None, bg=True):
        S, P = self.S, self.P
        tpl = shot["tpl"]
        lt = t - shot["t0"]
        dur = shot["t1"] - shot["t0"]
        content, clt, cdur = self.cut_at(shot, t)
        if bg:
            self.background(canvas, shot["bg"], t, shot, content, clt, cdur)
        self._clt = (clt, cdur)
        for li, L in enumerate(layers or tpl["layers"]):
            al = (alphas or {}).get(li, 1.0)
            if al <= 0.001:
                continue
            self.layer(canvas, L, t, lt, dur, shot, content, al)

    def bust(self, shape):
        """半身像修形：原片里人往往顶到画框两侧和底边，抠出来会有一刀直边。
        用一个以脸为中心的椭圆把肩膀收圆，像一张半身贴纸。"""
        if getattr(self, "_bust", None) is not None and self._bust.shape == shape[:2]:
            return self._bust
        sh, sw = shape[:2]
        fx, fy, fw = self.P.face
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
        rx = min(1.45 * fw, 0.47 * sw)
        ry = 2.1 * fw
        cy = fy + 0.9 * fw
        d = ((xx - fx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        m = np.clip((1.0 - d) / 0.12 + 0.5, 0, 1)
        m[yy < cy] = np.maximum(m[yy < cy], ((np.abs(xx - fx) < rx * 0.98) & (yy < cy))[yy < cy].astype(np.float32))
        self._bust = cv2.GaussianBlur(m, (0, 0), 3)
        return self._bust

    def background(self, canvas, B, t, shot, content, lt, dur, alpha=1.0):
        S = self.S
        typ = B.get("type", "paper")
        if typ == "paper":
            img = self.paper
        elif typ == "color":
            img = solid(S.H, S.W, S.color(B["color"]))
        elif typ == "content" and content:
            f, z = content.frame(lt, dur)
            fc = (content.focus[0] * f.shape[1], content.focus[1] * f.shape[0]) if content.focus else None
            img = fit_crop(f, S.W, S.H, focus=fc, zoom=z, face_y=0.5)
        elif self.P:  # portrait_blur：口播画面放大、虚化、压暗
            f = self.P.frame(t)
            img = fit_crop(f, S.W, S.H)
        else:
            img = self.paper
        if B.get("blur"):
            k = B["blur"] * S.W
            small = cv2.resize(img, (S.W // 4, S.H // 4))
            img = cv2.resize(cv2.GaussianBlur(small, (0, 0), k / 4), (S.W, S.H))
        if B.get("dim"):
            img = (img.astype(np.float32) * (1 - B["dim"])).astype(np.uint8)
        if B.get("lower_dim"):  # 下半部分压暗（宽银幕框）
            y = int(B["lower_dim"][0] * S.H)
            img = img.copy()
            img[y:] = (img[y:].astype(np.float32) * (1 - B["lower_dim"][1])).astype(np.uint8)
        self._bg_img = img
        if alpha >= 0.999:
            canvas[:] = img
        else:
            canvas[:] = (img.astype(np.float32) * alpha + canvas.astype(np.float32) * (1 - alpha)).astype(np.uint8)

    def enter(self, L, lt):
        """进场动画 → (alpha, scale, reveal, dy)"""
        e = L.get("enter")
        d = L.get("enter_dur", 0.3)
        u = min(1, max(0, lt / d)) if e else 1
        ease = 1 - (1 - u) ** 3
        if e == "pop":
            back = 1 + 0.12 * math.sin(math.pi * u) if u < 1 else 1
            return min(1, u * 2), (0.6 + 0.4 * ease) * back, 1, 0
        if e == "fade":
            return ease, 1, 1, 0
        if e == "rise":
            return ease, 1, 1, (1 - ease) * 0.03
        if e == "wipe":
            return 1, 1, ease, 0
        if e == "slide_left":
            return 1, 1, 1, ("x", (1 - ease) * -0.6)
        return 1, 1, 1, 0

    def layer(self, canvas, L, t, lt, dur, shot, content, alpha):
        S, P = self.S, self.P
        slot, shape = L["slot"], L.get("shape")
        if slot == "portrait" and P is None:
            return
        if L.get("at_beat") is not None:  # 卡点出现：镜头开始后第几拍才出来，进场动画从那一拍算
            lt -= L["at_beat"] * self.beat_len()
            if lt < 0:
                return
        if L.get("until_beat") is not None and lt >= L["until_beat"] * self.beat_len():
            return
        if L.get("out_beat") is not None:  # 从镜头里第几拍开始淡出（半拍淡完），比如城市名压过第二个镜头再走
            u = (t - shot["t0"] - L["out_beat"] * self.beat_len()) / (0.5 * self.beat_len())
            alpha *= float(np.clip(1 - u, 0, 1))
            if alpha <= 0:
                return
        if isinstance(L.get("content"), int) and self.contents:
            content = self.contents[L["content"] % len(self.contents)]
        a, sc, rev, dy = self.enter(L, lt)
        alpha *= a
        dx = 0
        if isinstance(dy, tuple):
            dx, dy = dy[1], 0
        if slot in ("content", "portrait") and shape in GEOM:
            x, y, w, h = px_box(S, L["box"])
            if sc != 1:
                cx, cy = x + w / 2, y + h / 2
                w, h = int(w * sc), int(h * sc)
                x, y = int(cx - w / 2), int(cy - h / 2)
            x += int(dx * S.W)
            y += int(dy * S.H)
            if w < 4 or h < 4:
                return
            if slot == "content":
                if not content:
                    return
                f, z = content.frame(*(self._clt if shot.get("cuts") and not isinstance(L.get("content"), int) else (lt, dur)))
                img = fit_crop(f, w, h, zoom=z * L.get("zoom", 1.0))
            else:
                f = P.frame(t)
                fx, fy, fw = P.face
                img = fit_crop(f, w, h, focus=(fx, fy), face_w=fw, face_frac=L.get("face_width"), zoom=L.get("zoom", 1.0), face_y=L.get("face_y", 0.42))
            r = L.get("radius", 0) * S.W
            m = shape_mask(w, h, shape, r)
            if L.get("shadow"):
                soft_shadow(canvas, m * alpha, x, y)
            blend(canvas, img, x, y, m, alpha)
            if L.get("ring"):
                R = L["ring"]
                ring(canvas, x, y, w, h, shape, r, S.color(R.get("color", "white")), max(1, int(R.get("width", 0.005) * S.W)), alpha)
        elif slot == "portrait" and shape == "cutout":
            x, y, w, h = px_box(S, L["box"])
            f = P.frame(t)
            m = P.mask(t)
            sh_, sw_ = f.shape[:2]
            s = h / sh_ * sc
            tw, th = int(sw_ * s), int(sh_ * s)
            if L.get("bust"):
                m = m * self.bust(f.shape)
            img = cv2.resize(f, (tw, th), interpolation=cv2.INTER_LINEAR)
            mm = cv2.resize(m, (tw, th), interpolation=cv2.INTER_LINEAR)
            al = L.get("align", "center")
            ox = {"left": x, "right": x + w - tw, "center": x + (w - tw) // 2}[al] + int(dx * S.W)
            oy = y + h - th + int(dy * S.H)
            st = L.get("stroke")
            if st:
                wpx = max(2, int(st.get("width", 0.01) * S.W))
                col = S.color(st.get("color", "white"))
                if st.get("style") == "dashed":
                    dashed_outline(canvas, mm, ox, oy, col, max(2, wpx // 2), int(st.get("dash", 0.02) * S.W), alpha)
                else:
                    big = cv2.dilate((mm > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * wpx + 1, 2 * wpx + 1)))
                    big = cv2.GaussianBlur(big.astype(np.float32), (0, 0), 1.2)
                    if L.get("shadow"):
                        soft_shadow(canvas, big * alpha, ox, oy, 0.35, 18, 10)
                    blend(canvas, solid(th, tw, col), ox, oy, big, alpha)
            blend(canvas, img, ox, oy, mm, alpha)
        elif slot == "panel":
            pts = np.array([[p[0] * S.W, p[1] * S.H] for p in L["points"]], np.int32)
            m = np.zeros((S.H, S.W), np.uint8)
            cv2.fillPoly(m, [pts], 255, cv2.LINE_AA)
            blend(canvas, solid(S.H, S.W, S.color(L.get("fill", "ink"))), 0, 0, m.astype(np.float32) / 255, alpha * L.get("opacity", 1))
        elif slot in ("content", "portrait") and shape == "polygon":
            pts = np.array([[p[0] * S.W, p[1] * S.H] for p in L["points"]], np.float32)
            x0, y0 = pts.min(0).astype(int)
            x1, y1 = pts.max(0).astype(int)
            w, h = x1 - x0, y1 - y0
            if slot == "content":
                if not content:
                    return
                f, z = content.frame(lt, dur)
                img = fit_crop(f, w, h, zoom=z)
            else:
                fx, fy, fw = P.face
                img = fit_crop(P.frame(t), w, h, focus=(fx, fy), face_w=fw, face_frac=L.get("face_width"), face_y=L.get("face_y", 0.42))
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [(pts - [x0, y0]).astype(np.int32)], 255, cv2.LINE_AA)
            m = m.astype(np.float32) / 255
            # 斜切进场：从上往下扫进来
            if L.get("enter") == "slide_down":
                u = min(1, lt / L.get("enter_dur", 0.35))
                y0 = int(y0 - (1 - (1 - (1 - u) ** 3)) * h)
            blend(canvas, img, x0, y0, m, alpha)
            if L.get("edge"):
                E = L["edge"]
                for a_, b_ in zip(L["points"], L["points"][1:] + L["points"][:1]):
                    if [a_, b_] in E["segments"] or [b_, a_] in E["segments"]:
                        cv2.line(canvas, (int(a_[0] * S.W), int(a_[1] * S.H) + (y0 - int(pts.min(0)[1]))),
                                 (int(b_[0] * S.W), int(b_[1] * S.H) + (y0 - int(pts.min(0)[1]))),
                                 S.color(E.get("color", "white")), max(1, int(E.get("width", 0.004) * S.W)), cv2.LINE_AA)
        elif slot == "lines":
            col = S.color(L.get("color", "white"))
            wpx = max(1, int(L.get("width", 0.003) * S.H))
            u = min(1, lt / L.get("enter_dur", 0.4)) if L.get("enter") == "draw" else 1
            for yy in L["ys"]:
                yp = int(yy * S.H)
                xe = int(S.W * (1 - (1 - u) ** 3))
                ov = canvas.copy()
                cv2.line(ov, (0, yp), (xe, yp), col, wpx, cv2.LINE_AA)
                canvas[:] = (ov.astype(np.float32) * alpha + canvas.astype(np.float32) * (1 - alpha)).astype(np.uint8)
        elif slot == "title":
            text = self.title_text(shot, L)
            if not text:
                return
            rgba = self.txt.render(text, L.get("text_style", "title"), int(L.get("max_w", 0.9) * S.W))
            put_text(canvas, rgba, int((L["anchor"][0] + dx) * S.W), int((L["anchor"][1] + (dy or 0)) * S.H), L.get("align", "center"), alpha, sc, rev)
            if L.get("behind_subject") and getattr(self, "_bg_img", None) is not None:
                # 字在人后：把背景画面里的人抠出来，再盖回字上面
                m = person_mask(self._bg_img, self.models)
                m = cv2.GaussianBlur(m, (0, 0), 1.5)
                blend(canvas, self._bg_img, 0, 0, m)
        elif slot == "subtitle":
            text = self.cue_at(t)
            if not text:
                return
            if L.get("enter") == "type":  # 逐字打出：按这一句已经过去的比例
                for a_, b_, x_ in self.cues:
                    if x_ == text and a_ <= t:
                        rev = min(1, (t - a_) / min(0.6, max(0.2, b_ - a_)))
            rgba = self.txt.render(text, L.get("text_style", "subtitle"), int(L.get("max_w", 0.9) * S.W))
            put_text(canvas, rgba, int(L["anchor"][0] * S.W), int(L["anchor"][1] * S.H), L.get("align", "center"), alpha, 1, rev)

    def frame(self, t):
        return self.grade(self._frame(t), t)

    def grade(self, im, t):
        """风格的调色（look）：暖一点、黑位提一点、饱和度、暗角、胶片颗粒。只在风格或任务里写了才做。"""
        L = self.look
        if not L:
            return im
        x = im.astype(np.float32) / 255
        if L.get("lift"):
            x = L["lift"] + x * (1 - L["lift"])
        if L.get("warm"):
            w = L["warm"]
            x[..., 0] *= 1 + w
            x[..., 2] *= 1 - w
        if L.get("sat") is not None:
            g = x.mean(2, keepdims=True)
            x = g + (x - g) * L["sat"]
        if L.get("vignette"):
            if getattr(self, "_vig", None) is None:
                H, W = x.shape[:2]
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                d = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2) / 0.5
                self._vig = (1 - L["vignette"] * d)[..., None]
            x *= self._vig
        if L.get("grain"):
            H, W = x.shape[:2]
            rng = np.random.default_rng(int(t * FPS + 0.5))
            n = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
            n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)
            x += n[..., None] * L["grain"]
        return (np.clip(x, 0, 1) * 255).astype(np.uint8)

    # 转场：同名同类的块插值位置和大小（形变），其余块淡入淡出
    def _frame(self, t):
        S = self.S
        k = next((i for i, s in enumerate(self.shots) if t < s["t1"]), len(self.shots) - 1)
        shot = self.shots[k]
        canvas = np.zeros((S.H, S.W, 3), np.uint8)
        T = self.trans.get("duration", 0.4)
        typ = shot.get("transition", self.trans.get("type", "morph"))
        lt = t - shot["t0"]
        if k == 0 or lt >= T or typ == "cut":
            self.draw(canvas, shot, t)
            return canvas
        prev = self.shots[k - 1]
        u = lt / T
        e = u * u * (3 - 2 * u)
        A, B = prev["tpl"]["layers"], shot["tpl"]["layers"]
        if typ == "fade":
            a = np.zeros_like(canvas)
            self.draw(a, prev, t)
            self.draw(canvas, shot, t)
            return (a.astype(np.float32) * (1 - e) + canvas.astype(np.float32) * e).astype(np.uint8)
        # morph
        cont_prev = self.content_of(prev)
        cont = self.content_of(shot)
        self.background(canvas, prev["bg"], t, prev, cont_prev, t - prev["t0"], prev["t1"] - prev["t0"])
        self.background(canvas, shot["bg"], t, shot, cont, lt, shot["t1"] - shot["t0"], alpha=e)
        used = set()
        merged = []
        for L in B:
            m = None
            if L.get("shape") in GEOM:
                for j, P_ in enumerate(A):
                    if j not in used and P_["slot"] == L["slot"] and P_.get("shape") in GEOM:
                        m = j
                        break
            if m is not None:
                used.add(m)
                P_ = A[m]
                pb = list(px_box(S, P_["box"]))
                nb = list(px_box(S, L["box"]))
                bx = [lerp(pb[i], nb[i], e) for i in range(4)]
                pr = min(pb[2], pb[3]) / 2 / S.W if P_["shape"] == "circle" else P_.get("radius", 0)
                nr = min(nb[2], nb[3]) / 2 / S.W if L["shape"] == "circle" else L.get("radius", 0)
                NL = dict(L, shape="roundrect", radius=lerp(pr, nr, e), enter=None,
                          box=[bx[0] / S.W, bx[1] / S.H, bx[2] / S.W, bx[3] / S.H],
                          face_width=lerp(P_.get("face_width") or 0.28, L.get("face_width") or 0.28, e),
                          ring=L.get("ring") or P_.get("ring"))
                merged.append((NL, 1.0))
            else:
                merged.append((dict(L, enter=None) if L["slot"] not in ("title",) else L, e))
        olds = [(dict(P_, enter=None), 1 - e) for j, P_ in enumerate(A) if j not in used and P_["slot"] not in ("subtitle",)]
        for L, al in olds:
            self.layer(canvas, L, t, t - prev["t0"], prev["t1"] - prev["t0"], prev, cont_prev, al)
        for L, al in merged:
            self.layer(canvas, L, t, lt, shot["t1"] - shot["t0"], shot, cont, al)
        return canvas

    def render(self, out):
        S = self.S
        dur = self.shots[-1]["t1"]
        tmp = out + ".v.mp4"
        enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{S.W}x{S.H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                                "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        n = int(round(dur * FPS))
        for i in range(n):
            enc.stdin.write(self.frame(i / FPS).tobytes())
        enc.stdin.close()
        enc.wait()
        p = self.job.get("portrait")
        M = self.music
        cmd = ["ffmpeg", "-loglevel", "error", "-y", "-i", tmp]
        if M:
            # 配乐：从节拍表对齐的位置开始取；有口播时人声一响配乐自动让开（侧链压缩）；统一到 -14 LUFS
            msrc = os.path.join(self.base, os.path.expanduser(M["src"]))
            cmd += ["-ss", f"{max(0.0, self.beats.offset):.3f}", "-t", f"{dur + 0.5:.3f}", "-i", msrc]
            lead = max(0.0, -self.beats.offset)  # 歌比片段晚开始（落点前的拍子不够）就在前面垫静音
            g = M.get("gain_db", 0)
            fo = max(0.0, dur - M.get("fade_out", 0.6))
            mus = f"[1:a]adelay={int(lead * 1000)}:all=1,volume={g}dB,afade=t=out:st={fo:.3f}:d={M.get('fade_out', 0.6)},atrim=0:{dur:.3f}"
            if p and M.get("voice", True):
                cmd += ["-ss", str(p.get("start", 0)), "-t", f"{dur:.3f}", "-i", os.path.expanduser(p["src"])]
                fc = (f"{mus}[m];[2:a]asplit[v][sc];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[md];"
                      f"[md][v]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]")
            else:
                fc = f"{mus},loudnorm=I=-14:TP=-1.5[a]"
            cmd += ["-filter_complex", fc, "-map", "0:v", "-map", "[a]"]
        elif p:
            cmd += ["-ss", str(p.get("start", 0)), "-t", f"{dur:.3f}", "-i", os.path.expanduser(p["src"]), "-map", "0:v", "-map", "1:a"]
        else:
            cmd += ["-map", "0:v"]
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{dur:.3f}", out]
        subprocess.run(cmd, check=True)
        os.remove(tmp)
        print("done", out, f"{dur:.2f}s", " / ".join(f"{s['template']} {s['t0']:.2f}-{s['t1']:.2f}" + (f"（{len(s['cuts'])} 切）" if s.get("cuts") else "") for s in self.shots))


# ---------------------------------------------------------------- 线框图（模板总表里的预览）
def wire(tid, out, style="koubo"):
    S = Style(style)
    tpl = load("shot", tid)
    W, H = S.W, S.H
    im = Image.new("RGB", (W, H), (236, 232, 224))
    d = ImageDraw.Draw(im)
    role = next(r for r in ("title", "subtitle") if r in S.d["fonts"])  # 线框图里的中文标注
    f = S.font(role, 64)
    bgt = tpl.get("background", {}).get("type", "paper")
    if bgt == "content":
        d.rectangle((0, 0, W, H), fill=(186, 205, 222))
        d.text((W / 2, H * 0.12), "素材铺满", font=f, fill=(90, 110, 130), anchor="mm")
    elif bgt == "portrait_blur":
        d.rectangle((0, 0, W, H), fill=(120, 116, 112))
        d.text((W / 2, H * 0.12), "人像虚化压暗", font=f, fill=(200, 200, 200), anchor="mm")
    for L in tpl["layers"]:
        s, sh = L["slot"], L.get("shape")
        col = {"content": (120, 160, 200), "portrait": (232, 170, 120)}.get(s)
        if sh in GEOM:
            x, y, w, h = px_box(S, L["box"])
            if sh == "circle":
                d.ellipse((x, y, x + w, y + h), fill=col, outline="white", width=8)
            else:
                d.rounded_rectangle((x, y, x + w, y + h), int(L.get("radius", 0) * W), fill=col)
            d.text((x + w / 2, y + h / 2), {"content": "素材", "portrait": "人像"}[s], font=f, fill="white", anchor="mm")
        elif sh == "cutout":
            x, y, w, h = px_box(S, L["box"])
            cx = {"left": x + h * 0.28, "right": x + w - h * 0.28, "center": x + w / 2}[L.get("align", "center")]
            st = L.get("stroke", {})
            d.ellipse((cx - h * 0.17, y + h * 0.05, cx + h * 0.17, y + h * 0.45), fill=(232, 170, 120), outline="white", width=10)
            d.rounded_rectangle((cx - h * 0.3, y + h * 0.48, cx + h * 0.3, y + h), int(h * 0.12), fill=(232, 170, 120), outline="white", width=10)
            d.text((cx, y + h * 0.75), "抠像" + ("·虚线" if st.get("style") == "dashed" else "·描边" if st else ""), font=f, fill="white", anchor="mm")
        elif s == "panel":
            d.polygon([(p[0] * W, p[1] * H) for p in L["points"]], fill=(40, 40, 40))
        elif sh == "polygon":
            d.polygon([(p[0] * W, p[1] * H) for p in L["points"]], fill=col)
            xs = [p[0] for p in L["points"]]
            ys = [p[1] for p in L["points"]]
            d.text((sum(xs) / len(xs) * W, sum(ys) / len(ys) * H), {"content": "素材", "portrait": "人像"}[s], font=f, fill="white", anchor="mm")
        elif s == "lines":
            for yy in L["ys"]:
                d.line((0, yy * H, W, yy * H), fill="white", width=8)
        elif s in ("title", "subtitle"):
            ax, ay = L["anchor"][0] * W, L["anchor"][1] * H
            anchor = {"center": "mm", "left": "lm", "right": "rm"}[L.get("align", "center")]
            txt = (L.get("key") or "标题") if s == "title" else "字幕在这里"
            fs = S.font(role, 120 if s == "title" else 60)
            if s == "title" and L.get("key") and L.get("text_style"):
                fs = S.font(role, max(40, int(S.text_style(L["text_style"])["size"] * H * 0.8)))
            d.text((ax, ay), txt, font=fs, fill=(255, 210, 63) if s == "title" else "white", anchor=anchor, stroke_width=6, stroke_fill=(30, 30, 30))
    d.text((40, H - 60), f"{tpl['name']}（{tpl['id']}）", font=S.font(role, 52), fill=(60, 60, 60), anchor="ls")
    im.resize((W // 3, H // 3), Image.LANCZOS).save(out, quality=88)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "list":
        for d in [x for x in LIB_DIRS if os.path.isdir(os.path.join(x, "templates", "shots"))][:1]:
            for kind in ("shots", "sequences"):
                for p in sorted(glob.glob(os.path.join(d, "templates", kind, "*.json"))):
                    t = json.load(open(p, encoding="utf-8"))
                    print(f"{kind[:-1]:8} {t['id']:18} {t.get('status', ''):2} {t['name']}  {t.get('summary', '')}")
        return
    if cmd == "wire":
        wire(sys.argv[2], sys.argv[3], *(sys.argv[4:5] or []))
        return
    jp = sys.argv[2]
    job = json.load(open(jp, encoding="utf-8"))
    R = Renderer(job, os.path.dirname(os.path.abspath(jp)))
    if cmd == "plan":
        tl = json.dumps(R.timeline(), ensure_ascii=False, indent=1)
        if len(sys.argv) > 3:
            open(sys.argv[3], "w", encoding="utf-8").write(tl)
        else:
            print(tl)
        return
    if cmd == "render":
        R.render(sys.argv[3])
    elif cmd == "still":
        im = R.frame(float(sys.argv[3]))
        Image.fromarray(im).save(sys.argv[4], quality=90)


if __name__ == "__main__":
    main()
