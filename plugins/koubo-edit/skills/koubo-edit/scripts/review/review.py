"""审片台：出完一版后在浏览器（或 Agent 的侧边栏浏览器）里看片、定点改，提交成修改单交回 Agent。

  python review.py serve <工作目录> [--video 成片.mp4] [--port 8765] [--no-open]
      起本地网页 http://127.0.0.1:<port>/ ：读这一集的工程文件生成多轨时间轴。
      用户点「提交」后，修改单写到 <工作目录>/review/<旧版>_to_<新版>.json。
  python review.py changes <工作目录>
      打印最新一份还没处理的修改单（Agent 读这个来改）。处理完运行 `done` 标记。
  python review.py done <工作目录>
      把最新修改单标记为已处理，下次 serve 版本号自动 +1。
  python review.py apply <工作目录>
      只给版式模板出的片（工作目录里有 job.json）：把修改单里的版式、句数、素材、取景、转场、标题、字幕
      直接写回 job.json，「存为模板」存成新的片段模板；一句话要求打印出来给 Agent 改。然后重新 render。
  python review.py export <工作目录> <输出目录> [--video 成片.mp4] [--style ...]
      在 Claude 对话里直接审片：导出一个能发布成 Artifact 的审片台（index.html + 预览视频 + 缩略图），
      Agent 用 Artifact 工具发布（capabilities={"db": {}}）。用户点「提交」后修改单存进页面的 db，
      Agent 用 ArtifactData 读 review/submit_<版本>，存成 json，再 import。
  python review.py import <工作目录> <修改单.json>
      把从 Artifact 读回来的修改单放进 <工作目录>/review/，之后 changes / apply / done 照常用。
  python review.py launch <工作目录> [--port 8765]
      给 Claude 桌面版写 <工作目录>/.claude/launch.json，让审片台在它的 Browser 侧栏里打开。

现在支持：课程横版（工作目录里有 ed/segs.json）、朴素版口播（有 config.json）、像素风（有 render_full.py）、
版式模板出的片（有 job.json，任何风格：口播开头、vlog 卡点开头都是这一种）。
只用 Python 标准库和 ffmpeg/ffprobe，Mac 和 Windows 都能跑。
这个文件和 page.html 的正本在仓库 shared/review/，各风格 scripts/review/ 是复制品。
"""
import glob, json, os, re, subprocess, sys, threading, webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))


def sh(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"命令失败：{' '.join(cmd)}\n{r.stderr[-800:]}")
    return r.stdout


def probe(path):
    out = json.loads(sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", path))
    st = out["streams"][0]
    return float(out["format"]["duration"]), st["width"], st["height"]


def jload(p):
    with open(p, encoding="utf-8") as f: return json.load(f)


# ---------- 选项清单（和 DIMENSIONS.md、各风格 rules 对应） ----------
TRANS_OPTS = [{"v": "叠化"}, {"v": "硬切"}, {"v": "推入", "tag": "待试"}, {"v": "匹配剪辑", "tag": "待试"},
              {"v": "闪白", "off": "不允许"}, {"v": "旋转", "off": "不允许"}]
TRANS_NAME = {"dissolve": "叠化", "cut": "硬切", "slide": "推入", "match": "匹配剪辑"}
MOVE_OPTS = [{"v": "固定"}, {"v": "快推定格"}, {"v": "快拉"}, {"v": "跳切推近"}, {"v": "快移"},
             {"v": "冲击推", "tag": "待试"}, {"v": "慢推", "off": "不允许"}]
DUR_OPTS = [{"v": "0.4s"}, {"v": "0.6s"}, {"v": "0.8s"}, {"v": "1.2s", "off": "太慢"}]


def move_el(t0, t1, kind, scale, dur, src):
    d = min(["0.4s", "0.6s", "0.8s"], key=lambda x: abs(float(x[:-1]) - dur))
    return dict(t0=round(t0, 2), t1=round(t1, 2), name=f"{kind} {scale}×", src=src, ph="例：推到能看见输入框",
                f=[{"k": "kind", "label": "手法", "type": "seg", "v": kind, "opts": MOVE_OPTS},
                   {"k": "scale", "label": "倍数", "type": "range", "min": 1.0, "max": 3.0, "step": 0.1, "v": scale, "unit": "×"},
                   {"k": "dur", "label": "用时", "type": "seg", "v": d, "opts": DUR_OPTS}])


def kind_of(w0, w1, dt):
    if dt < 0.05: return "跳切推近"
    return "快推定格" if w1 < w0 else "快拉" if w1 > w0 else "快移"


# ---------- 课程横版 ----------
COURSE_TYPES = {"slide": "课件", "scene": "标题卡", "anim": "动效卡", "rec": "录屏", "clips": "录屏",
                "cmp": "开场对比", "vid": "成品展示"}


def course(wd, dur):
    ed = os.path.join(wd, "ed") if os.path.isdir(os.path.join(wd, "ed")) else wd
    segs = jload(os.path.join(ed, "segs.json"))
    clips = jload(os.path.join(ed, "clips.json")) if os.path.exists(os.path.join(ed, "clips.json")) else {}
    W, H = 1920, 1080
    C, P, S = [48, 112, 1360, 765], [1440, 357, 432, 520], [560, 940, 800, 80]
    layout_opts = [{"v": "分屏"}, {"v": "全屏内容"}, {"v": "内容+小窗", "tag": "待试"}, {"v": "全屏人像", "off": "不允许"}]
    shots, trans, moves = [], [], []
    for i, s in enumerate(segs):
        ty, name = s["layer"].split(":", 1)
        nm = os.path.splitext(os.path.basename(name))[0] if ty == "scene" else name
        lay = "全屏内容" if ty == "cmp" else "分屏"
        shots.append(dict(id=f"shot-{i+1}", t0=s["t0"], t1=s["t1"], name=f"{COURSE_TYPES.get(ty, ty)} {nm}", thumb=i,
                          src=f"segs.json[{i}]", ph="例：换成点「发布」那段",
                          f=[{"k": "src", "label": "画面", "type": "ro", "v": s["layer"]},
                             {"k": "layout", "label": "版式", "type": "seg", "v": lay, "opts": layout_opts},
                             {"k": "cbox", "label": "内容框", "type": "box", "v": ",".join(map(str, C[:3]))},
                             {"k": "pbox", "label": "人像框", "type": "box", "v": ",".join(map(str, P[:3]))},
                             {"k": "sbox", "label": "字幕高度", "type": "box", "v": str(S[1])}]))
        if i:
            k = TRANS_NAME.get(s.get("trans", "dissolve"), s.get("trans"))
            trans.append(dict(t0=s["t0"], t1=s["t0"] + 0.3, name=f"S{i} → S{i+1}", src=f"segs.json[{i}].trans",
                              ph="例：改成硬切", f=[{"k": "kind", "label": "转场", "type": "seg", "v": k, "opts": TRANS_OPTS}]))
        if ty == "rec" and s.get("zoom"):
            z = s["zoom"]; full = max(k[3] for k in z)
            ch = [(a, b) for a, b in zip(z, z[1:]) if a[1:] != b[1:]]
            for j, (a, b) in enumerate(ch):
                t0 = s["t0"] + a[0]; t1 = s["t0"] + (ch[j+1][0][0] if j + 1 < len(ch) else s["t1"] - s["t0"])
                moves.append(move_el(t0, min(t1, s["t1"]), kind_of(a[3], b[3], b[0] - a[0]), round(full / b[3], 1),
                                     b[0] - a[0], f"segs.json[{i}].zoom[{z.index(b)}]"))
        if ty == "clips" and name in clips:
            for j, c in enumerate(clips[name]):
                b0, b1 = c[3], c[4]
                if b0 != b1:
                    pt = c[5] if len(c) > 5 else 0.5
                    moves.append(move_el(s["t0"] + c[0] + pt, s["t0"] + c[1], kind_of(b0[2], b1[2], 0.6),
                                         round(b0[2] / b1[2], 1), 0.6, f"clips.json[{name}][{j}]"))
    chap = jload(os.path.join(ed, "chap.json")); names = jload(os.path.join(ed, "chap_names.json"))
    chaps = [dict(t0=a, t1=b, name=n, src=f"chap_names.json[{k}]", ph="例：缩成 4 个字",
                  f=[{"k": "name", "label": "章节名", "type": "text", "v": n}])
             for k, (a, b, n) in enumerate(zip(chap, chap[1:], names))]
    subs = jload(os.path.join(ed, "subs.json"))
    en = []
    if os.path.exists(os.path.join(ed, "en.txt")):
        en = open(os.path.join(ed, "en.txt"), encoding="utf-8").read().splitlines()
    sub_els = []
    for j, (a, b, t) in enumerate(subs):
        f = [{"k": "text", "label": "文字", "type": "text", "v": t},
             {"k": "t0", "label": "出现", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(a, 2)},
             {"k": "t1", "label": "消失", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(b, 2)}]
        if j < len(en): f.append({"k": "en", "label": "英文", "type": "text", "v": en[j]})
        sub_els.append(dict(t0=a, t1=b, name=t, src=f"subs.json[{j}]", ph="例：「生成」放下一句", f=f))
    first = next((s["t0"] for s in segs if not s["layer"].startswith("cmp:")), 0)
    por = [dict(t0=first, t1=dur, name="人像框", src="compose.py", ph="例：这段先隐藏",
                f=[{"k": "size", "label": "尺寸", "type": "ro", "v": "432×520，固定"}])]
    tracks = [dict(key="chap", name="进度条", items=chaps), dict(key="shot", name="镜头", items=shots),
              dict(key="trans", name="转场", items=trans), dict(key="move", name="运镜", items=moves),
              dict(key="sub", name="字幕", items=sub_els), dict(key="por", name="人像框", items=por)]
    ep = [{"k": "title", "label": "集数标题", "type": "text", "v": os.path.basename(os.path.abspath(wd))},
          {"k": "look", "label": "进度条", "type": "seg", "v": "分段条",
           "opts": [{"v": "分段条"}, {"v": "细线", "tag": "待试"}, {"v": "胶囊", "tag": "待试"}]},
          {"k": "bi", "label": "字幕", "type": "seg", "v": "中英" if en else "只中文", "opts": [{"v": "中英"}, {"v": "只中文"}]},
          {"k": "color", "label": "主题色", "type": "seg", "lv": "系列", "v": "蓝",
           "opts": [{"v": "蓝"}, {"v": "橙", "tag": "待试"}, {"v": "绿", "tag": "待试"}, {"v": "紫", "tag": "待试"}]},
          {"k": "series", "label": "系列名", "type": "text", "lv": "系列", "v": "电商 + AI 系列"}]
    return dict(style="course", styleName="课程横版", W=W, H=H, bg="#F4F2EE", tracks=tracks, ep=ep,
                epHint="例：开场对比换掉第 2 组",
                themes={"蓝": "#2F6BFF", "橙": "#F06A1C", "绿": "#1F9D74", "紫": "#7B5CFF"},
                chapBar=dict(x0=64, x1=1856, gap=8, stripH=84, font=19, color="#2F6BFF"),
                subRect=[S[0] / W, S[1] / H, S[2] / W, S[3] / H],
                layout=dict(src=dict(c=C, p=P, s=S), top=96, def_="分屏",
                            presets={"分屏": dict(c=C, p=P, s=S[1]),
                                     "全屏内容": dict(c=[240, 104, 1440, 810], p=None, s=S[1]),
                                     "内容+小窗": dict(c=[48, 104, 1440, 810], p=[1530, 560, 330, 397], s=S[1])}),
                thumbs_at=[(s["t0"] + s["t1"]) / 2 for s in segs])


# ---------- 朴素版口播（竖版 1088×1920，工作目录里有 config.json） ----------
HL_OPTS = [{"v": "A 黄色重点"}, {"v": "B 红色警示"}, {"v": "C1 黄对比"}, {"v": "C2 蓝对比"}, {"v": "H 放大"}]
HL_NAME = {o["v"].split()[0]: o["v"] for o in HL_OPTS}
KB_MOVE = {"jump": "跳切推近", "punch": "快推定格", "reset": "复位"}
KB_MOVE_OPTS = [{"v": "跳切推近"}, {"v": "快推定格"}, {"v": "复位"}, {"v": "震屏", "tag": "待试"}, {"v": "甩镜", "tag": "待试"},
                {"v": "慢推", "off": "不允许"}]


def koubo_cfg(wd):
    return jload(os.path.join(wd, "config.json"))


def koubo_video(wd):
    cfg = koubo_cfg(wd); od = os.path.expanduser(cfg.get("out_dir", wd)); i = cfg.get("id", "")
    c = glob.glob(os.path.join(od, f"{i}_成片*.mp4")) or glob.glob(os.path.join(od, f"{i}_粗剪.mp4"))
    return max(c, key=os.path.getmtime) if c else find_video(wd)


def koubo(wd, dur):
    cfg = koubo_cfg(wd); W, H = 1088, 1920
    cues = []
    cp = os.path.join(wd, "cues.txt")
    if os.path.exists(cp):
        for ln in open(cp, encoding="utf-8").read().splitlines():
            m = re.match(r"(\d+)\t([\d.]+)-([\d.]+)\t(.*)", ln)
            if m: cues.append((float(m.group(2)), float(m.group(3)), m.group(4)))
    en = jload(os.path.join(wd, "en.json")) if os.path.exists(os.path.join(wd, "en.json")) else []
    subs = []
    for j, (a, b, t) in enumerate(cues):
        f = [{"k": "text", "label": "文字", "type": "text", "v": t},
             {"k": "t0", "label": "出现", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(a, 2)},
             {"k": "t1", "label": "消失", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(b, 2)}]
        if j < len(en): f.append({"k": "en", "label": "英文", "type": "text", "v": en[j]})
        subs.append(dict(t0=a, t1=b, name=t, src=f"cues.txt[{j}]", ph="例：这句断在「其实」后面", f=f))
    fx = [dict(t0=h[0], t1=h[0] + 1.5, name=h[1], src=f"config.json highlights[{k}]", ph="例：换成「30倍」",
               f=[{"k": "word", "label": "词", "type": "text", "v": h[1]},
                  {"k": "style", "label": "样式", "type": "seg", "v": HL_NAME.get(h[2], h[2]), "opts": HL_OPTS}])
          for k, h in enumerate(cfg.get("highlights", []))]
    lists = []
    for k, l in enumerate(cfg.get("lists", [])):
        f = [{"k": f"item{i+1}", "label": it[0], "type": "text", "v": it[1]} for i, it in enumerate(l["items"])]
        lists.append(dict(t0=l["reveal"][0], t1=l["end"], name="清单 " + "、".join(it[1] for it in l["items"])[:16],
                          src=f"config.json lists[{k}]", ph="例：第 3 条晚 1 秒出", f=f))
    beeps = [dict(t0=b[0], t1=max(b[1], b[0] + 0.4), name=b[2], src=f"config.json beeps[{k}]", ph="例：这个词不用哔",
                  f=[{"k": "on", "label": "哔声", "type": "seg", "v": "哔掉", "opts": [{"v": "哔掉"}, {"v": "不哔"}]}])
             for k, b in enumerate(cfg.get("beeps", []))]
    cam = sorted(cfg.get("camera", []), key=lambda e: e[0]); moves = []
    for k, e in enumerate(cam):
        t1 = cam[k + 1][0] if k + 1 < len(cam) else dur
        z = 1.0 if e[1] == "reset" else float(e[2])
        moves.append(dict(t0=e[0], t1=t1, name=f"{KB_MOVE.get(e[1], e[1])} {z}×", src=f"config.json camera[{k}]",
                          ph="例：推得再近一点",
                          f=[{"k": "kind", "label": "手法", "type": "seg", "v": KB_MOVE.get(e[1], e[1]), "opts": KB_MOVE_OPTS},
                             {"k": "scale", "label": "倍数", "type": "range", "min": 1.0, "max": 1.2, "step": 0.01, "v": z, "unit": "×"}]))
    tracks = [dict(key="sub", name="字幕", items=subs), dict(key="fx", name="花字", items=fx),
              dict(key="list", name="清单", items=lists), dict(key="move", name="运镜", items=moves),
              dict(key="beep", name="哔声", items=beeps)]
    ep = [{"k": "bi", "label": "字幕", "type": "seg", "v": "中英" if en else "只中文", "opts": [{"v": "中英"}, {"v": "只中文"}]},
          {"k": "max_chars", "label": "每行字数", "type": "seg", "v": str(cfg.get("max_chars", 14)),
           "opts": [{"v": "12"}, {"v": "14"}, {"v": "16"}]},
          {"k": "hlcolor", "label": "花字配色", "type": "seg", "lv": "系列", "v": "黄红蓝",
           "opts": [{"v": "黄红蓝"}, {"v": "单色", "tag": "待试"}]},
          {"k": "cover", "label": "封面版式", "type": "seg", "v": "stack",
           "opts": [{"v": "stack"}, {"v": "brush"}, {"v": "stagger"}]}]
    sy = 0.76
    return dict(style="koubo", styleName="朴素版口播", W=W, H=H, bg="#000000", tracks=tracks, ep=ep,
                epHint="例：封面换一句「除了A股都有」", subRect=[(W - 1000) / 2 / W, sy - 0.035, 1000 / W, 0.07], thumbs_at=[])


# ---------- 像素风（竖版 1080×1440，工程里有 render_full.py） ----------
PX_KIND = {"A": "A 真人", "B": "B 像素", "C": "C 界面", "S": "S 总结"}


def pixel_src(wd):
    for p in (os.path.join(wd, "render_full.py"), os.path.join(wd, "scripts", "render_full.py")):
        if os.path.exists(p): return p


def pixel(wd, dur):
    import ast
    src = pixel_src(wd); tree = ast.parse(open(src, encoding="utf-8").read()); V = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SEG", "PUSH", "CUES"):
            try: V[n.targets[0].id] = ast.literal_eval(n.value)
            except Exception: pass
    W, H = 1080, 1440
    work = os.environ.get("PIXEL_WORK", os.path.join(os.path.dirname(src), "work"))
    cues = list(V.get("CUES", []))
    if os.path.exists(os.path.join(work, "full", "cues.json")): cues += [tuple(c) for c in jload(os.path.join(work, "full", "cues.json"))]
    seg = [(k, a, min(b, dur)) for k, a, b in V.get("SEG", []) if a < dur]
    kind_opts = [{"v": v} for v in PX_KIND.values()]
    shots, trans = [], []
    for i, (k, a, b) in enumerate(seg):
        kk = k.split(":")[0][0]; nm = k.split(":", 1)[1] if ":" in k else k
        shots.append(dict(id=f"shot-{i+1}", t0=a, t1=b, name=f"{PX_KIND.get(kk, kk)} {nm}", thumb=i, src=f"render_full.py SEG[{i}]",
                          ph="例：这段换成像素场景讲存档", f=[{"k": "kind", "label": "镜头", "type": "seg", "v": PX_KIND.get(kk, kk), "opts": kind_opts}]))
        if i:
            pk = seg[i - 1][0][0]
            tv = "像素溶解" if "B" in (pk, kk) else "弹出" if kk == "C" and pk != "C" else "硬切"
            trans.append(dict(t0=a, t1=a + 0.3, name=f"S{i} → S{i+1}", src=f"render_full.py SEG[{i}]", ph="例：改成硬切",
                              f=[{"k": "kind", "label": "转场", "type": "seg", "v": tv,
                                  "opts": [{"v": "像素溶解"}, {"v": "弹出"}, {"v": "硬切"}, {"v": "叠化", "off": "不用"}]}]))
    moves = [dict(t0=a, t1=b, name="缓推 1.08×", src=f"render_full.py PUSH[{k!r}]", ph="例：这段不要推",
                  f=[{"k": "kind", "label": "手法", "type": "seg", "v": "缓推", "opts": [{"v": "缓推"}, {"v": "固定"}, {"v": "快推定格", "tag": "待试"}]},
                     {"k": "scale", "label": "倍数", "type": "range", "min": 1.0, "max": 1.1, "step": 0.01, "v": 1.08, "unit": "×"}])
             for k, (a, b) in V.get("PUSH", {}).items()]
    subs = [dict(t0=c[0], t1=c[1], name=c[2], src=("render_full.py CUES" if j < len(V.get("CUES", [])) else "work/full/cues.json") + f"[{j}]",
                 ph="例：GitHub 写错了",
                 f=[{"k": "text", "label": "文字", "type": "text", "v": c[2]},
                    {"k": "t0", "label": "出现", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(c[0], 2)},
                    {"k": "t1", "label": "消失", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(c[1], 2)}])
            for j, c in enumerate(cues)]
    tracks = [dict(key="shot", name="镜头", items=shots), dict(key="trans", name="转场", items=trans),
              dict(key="move", name="运镜", items=moves), dict(key="sub", name="字幕", items=subs)]
    ep = [{"k": "scene", "label": "布景", "type": "seg", "v": "草地",
           "opts": [{"v": "草地"}, {"v": "港口", "tag": "待试"}, {"v": "教室", "tag": "待试"}, {"v": "太空站", "tag": "待试"}, {"v": "图书馆", "tag": "待试"}]},
          {"k": "season", "label": "季节", "type": "seg", "v": "春夏", "opts": [{"v": "春夏"}, {"v": "秋"}, {"v": "冬", "tag": "待试"}]},
          {"k": "weather", "label": "天气", "type": "seg", "v": "晴", "opts": [{"v": "晴"}, {"v": "雨", "tag": "待试"}, {"v": "雪", "tag": "待试"}]},
          {"k": "hero", "label": "主角", "type": "text", "lv": "系列", "v": "棕色像素小熊"}]
    return dict(style="pixel", styleName="像素风", W=W, H=H, bg="#7fb069", tracks=tracks, ep=ep,
                epHint="例：布景换成像素教室，先出 3 张关键帧", subRect=[0.08, (1272 - 45) / H, 0.84, 90 / H],
                thumbs_at=[(a + b) / 2 for _, a, b in seg])


# ---------- 版式模板出的片（工作目录里有 job.json，用 templates/engine.py 渲染） ----------
ENGINE = os.path.normpath(os.path.join(HERE, "..", "templates", "engine.py"))
TR_NAME = {"morph": "形变", "fade": "叠化", "cut": "硬切"}
TR_KEY = {v: k for k, v in TR_NAME.items()}
TR_OPTS = [{"v": "形变"}, {"v": "叠化"}, {"v": "硬切"}]
CUT_OPTS = [{"v": "不切"}, {"v": "每半拍"}, {"v": "每拍"}, {"v": "每两拍"}]
CUT_KEY = {"不切": None, "每半拍": 0.5, "每拍": 1, "每两拍": 2}


JOB_NAMES = ("job.json", "opening.json")


def job_path(wd):
    """模板任务文件：job.json 或 opening.json；都没有就找目录里第一份带 style + sequence/shots 的 json。"""
    for n in JOB_NAMES:
        if os.path.exists(os.path.join(wd, n)): return os.path.join(wd, n)
    for p in sorted(glob.glob(os.path.join(wd, "*.json"))):
        try: j = jload(p)
        except Exception: continue
        if isinstance(j, dict) and "style" in j and ("sequence" in j or "shots" in j): return p
    return None


def job_plan(wd):
    """engine.py plan 的时间轴（镜头、切点、文字、拍点），口播开头和 vlog 卡点同一个格式。"""
    jp = job_path(wd); cache = os.path.splitext(jp)[0] + ".plan.json"
    # 有比任务文件新的时间轴就直接用（engine plan 要读视频、跑人脸，机器上没装 opencv / mediapipe 也能打开审片台）
    if os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(jp):
        return jload(cache)
    out = sh(sys.executable, ENGINE, "plan", jp)
    try: open(cache, "w", encoding="utf-8").write(out)
    except OSError: pass
    return json.loads(out)


# 模板库：插件里在 scripts/templates/library，仓库里在仓库根目录
LIB_DIRS = [os.path.join(os.path.dirname(ENGINE), "library"), os.path.normpath(os.path.join(HERE, "..", ".."))]


def lib_load(sub, name):
    for d in LIB_DIRS:
        p = os.path.join(d, sub, name + ".json")
        if os.path.exists(p): return jload(p)
    return None


def lib_dir():
    return next(d for d in LIB_DIRS if os.path.isdir(os.path.join(d, "templates", "sequences")))


def job_lib(job):
    """风格开放的镜头模板（id → 名字、状态）和这一集的片段模板。"""
    sty = lib_load("styles", job.get("style", "koubo")) or {}
    shots = {}
    for k, st in sty.get("templates", {}).get("shots", {}).items():
        t = lib_load("templates/shots", k)
        if t: shots[k] = {"name": t.get("name", k), "status": st}
    seq = {"shots": job["shots"], "transition": job.get("transition", {})} if "shots" in job else lib_load("templates/sequences", job["sequence"])
    return sty, shots, seq


def job_srcs(wd):
    j = jload(job_path(wd))
    ps = [c["src"] for c in j.get("content", [])] + ([j["portrait"]["src"]] if j.get("portrait") else [])
    if j.get("music"): ps.append(j["music"]["src"])
    return {os.path.abspath(os.path.join(wd, os.path.expanduser(p))) for p in ps}


def job_video(wd):
    srcs = job_srcs(wd)
    c = [p for p in glob.glob(os.path.join(wd, "*.mp4")) if os.path.abspath(p) not in srcs]
    if not c: raise SystemExit("找不到这一版的成片：先 python engine.py render <任务>.json <名字>.mp4，或用 --video 指定")
    return max(c, key=os.path.getmtime)


def tline(t):  # 标题里的换行在输入框里写成 " / "
    return t.replace("\n", " / ")


def tmpl(wd, dur):
    job = jload(job_path(wd)); P = job_plan(wd); sty, lib, seq = job_lib(job)
    W, H = P["canvas"]
    cues = job.get("cues", []); content = job.get("content", [])
    cidx = {c["src"]: i for i, c in enumerate(content)}
    lay_opts = [{"v": v["name"], **({"tag": "待试"} if v["status"] == "△" else {}), **({"off": "这个风格不允许"} if v["status"] == "✗" else {})}
                for v in lib.values()]
    c_opts = [{"v": "无"}] + [{"v": f"{i+1} {os.path.splitext(os.path.basename(c['src']))[0]}"} for i, c in enumerate(content)]
    tr = seq.get("transition", {}); default_tr = tr.get("type", "morph"); T = tr.get("duration", 0.4)
    shots, trans, titles, cuts = [], [], {}, []
    n_sh = len(P["shots"])
    for k, s in enumerate(P["shots"]):
        spec = seq["shots"][k] if k < len(seq["shots"]) else {}
        nm = lib.get(s["template"], {}).get("name") or (lib_load("templates/shots", s["template"]) or {}).get("name", s["template"])
        f = [{"k": "layout", "label": "版式", "type": "seg", "v": nm, "opts": lay_opts}]
        if s.get("beats"):
            f.append({"k": "beats", "label": "占几拍", "type": "range", "min": 1, "max": 32, "step": 1, "v": s["beats"]})
            f.append({"k": "cut_every", "label": "素材快切", "type": "seg",
                      "v": next((a for a, b in CUT_KEY.items() if b == s.get("cut_every")), "不切"), "opts": CUT_OPTS})
        elif k < n_sh - 1 and cues:
            n = sum(1 for c in cues if s["t0"] - 0.05 <= c[0] < s["t1"] - 0.05)
            f.append({"k": "cues", "label": "占几句", "type": "range", "min": 1, "max": len(cues), "step": 1, "v": max(1, n)})
        else:
            f.append({"k": "len", "label": "长度", "type": "ro", "v": "到结尾"})
        segs = s.get("segments", [])
        if content and len(segs) == 1:  # 一个镜头一段素材：能换素材、调取景
            ci = cidx.get(segs[0]["content"])
            if ci is not None:
                fx, fy = content[ci].get("focus", [0.5, 0.5])
                f += [{"k": "content", "label": "素材", "type": "seg", "v": c_opts[ci + 1]["v"], "opts": c_opts},
                      {"k": "fx", "label": "取景左右", "type": "range", "min": 0, "max": 1, "step": 0.05, "v": fx},
                      {"k": "fy", "label": "取景上下", "type": "range", "min": 0, "max": 1, "step": 0.05, "v": fy}]
        elif len(segs) > 1:  # 按拍快切：每一刀单独一条，在「素材」轨上
            for j, g in enumerate(segs):
                ci = cidx.get(g["content"])
                cuts.append(dict(t0=g["t0"], t1=g["t1"], name=os.path.splitext(os.path.basename(g["content"]))[0],
                                 src=f"job.content[{ci}]", ph="例：这一刀换成海边那段",
                                 f=[{"k": "content", "label": "素材", "type": "ro", "v": g["content"]},
                                    {"k": "fx", "label": "取景左右", "type": "range", "min": 0, "max": 1, "step": 0.05,
                                     "v": content[ci].get("focus", [0.5, 0.5])[0]},
                                    {"k": "fy", "label": "取景上下", "type": "range", "min": 0, "max": 1, "step": 0.05,
                                     "v": content[ci].get("focus", [0.5, 0.5])[1]}]))
        shots.append(dict(id=f"shot-{k+1}", t0=s["t0"], t1=s["t1"], name=f"{k+1} {nm}", thumb=k,
                          src=f"job.shots[{k}]", ph="例：这段换成斜切分屏，素材用第 3 段", f=f))
        if k:
            tv = TR_NAME.get(spec.get("transition", default_tr), "形变")
            trans.append(dict(t0=s["t0"], t1=s["t0"] + T, name=f"{k} → {k+1}", src=f"job.shots[{k}].transition", ph="例：改成硬切",
                              f=[{"k": "kind", "label": "转场", "type": "seg", "v": tv, "opts": TR_OPTS}]))
        for tk, tx in s.get("texts", {}).items():
            a, b, _ = titles.get(tk, (s["t0"], s["t1"], tx))
            titles[tk] = (min(a, s["t0"]), max(b, s["t1"]), tx)
    fx = [dict(t0=a, t1=b, name=tline(tx), src=f"job.titles.{tk}", ph="例：改成「别再这样写提示词」",
               f=[{"k": "text", "label": "标题", "type": "text", "v": tline(tx), "note": "「 / 」是换行"}])
          for tk, (a, b, tx) in titles.items()]
    subs = []
    for j, (a, b, t) in enumerate(cues):
        subs.append(dict(t0=a, t1=b, name=t, src=f"job.cues[{j}]", ph="例：这句断在「其实」后面",
                         f=[{"k": "text", "label": "文字", "type": "text", "v": t},
                            {"k": "t0", "label": "出现", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(a, 2)},
                            {"k": "t1", "label": "消失", "type": "range", "min": 0, "max": dur, "step": 0.1, "v": round(b, 2)}]))
    tracks = [dict(key="shot", name="镜头", items=shots), dict(key="trans", name="转场", items=trans)]
    if cuts: tracks.append(dict(key="move", name="快切", items=cuts))
    if P.get("music"):  # 拍点：只读，看切点有没有落在拍上
        m = P["music"]; bl = 60 / m["bpm"]
        tracks.append(dict(key="beep", name="拍点", items=[dict(t0=t, t1=t + min(0.12, bl / 3), name="落点" if abs(t - m["drop"]) < 0.02 else "",
                                                               src="music", ph="例：落点往后挪一拍",
                                                               f=[{"k": "t", "label": "时间", "type": "ro", "v": f"{t:.2f}s"}]) for t in m["beats"]]))
    tracks.append(dict(key="fx", name="标题", items=fx))
    if subs: tracks.append(dict(key="sub", name="字幕", items=subs))
    ep = [{"k": "tdur", "label": "转场用时", "type": "seg", "v": f"{T}s",
           "opts": [{"v": "0.3s"}, {"v": "0.4s"}, {"v": "0.6s"}, {"v": "0.8s"}]},
          {"k": "save_as", "label": "存为模板", "type": "text", "v": "",
           "note": "填一个名字，提交后这一版的镜头顺序存成新的片段模板，下一集能直接套"}]
    sname = seq.get("name") or "自己排的镜头"
    return dict(style="template", styleName=f"{sname} · {sty.get('name', job.get('style', ''))}", W=W, H=H, bg="#000000",
                tracks=tracks, ep=ep, epHint="例：整段节奏再快一点", subRect=[0.05, 0.76, 0.9, 0.06],
                thumbs_at=[(s["t0"] + s["t1"]) / 2 for s in P["shots"]])


def focus(c, st):
    fo = list(c.get("focus", [0.5, 0.5]))
    if "fx" in st: fo[0] = float(st["fx"])
    if "fy" in st: fo[1] = float(st["fy"])
    c["focus"] = fo


def tmpl_apply(wd):
    """把最新修改单里能直接改的字段写回 job.json；改不了的（一句话要求）打印出来给 Agent 处理。"""
    s = sheets(wd)
    if not s or jload(s[-1][1]).get("done"):
        print("没有待处理的修改单。"); return
    sheet = jload(s[-1][1]); jp = job_path(wd); job = jload(jp); P = job_plan(wd); sty, lib, seq = job_lib(job)
    bak = os.path.join(rdir(wd), f"job_{sheet['from']}.json")
    if not os.path.exists(bak): json.dump(job, open(bak, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    names = {v["name"]: k for k, v in lib.items()}
    if "shots" not in job:  # 第一次改：把片段模板摊开写进任务文件，句数按这一集的 split
        job["shots"] = []
        for k, sp in enumerate(seq["shots"]):
            d = dict(sp)
            if job.get("split") and k < len(job["split"]) and "beats" not in d: d["cues"] = job["split"][k]
            job["shots"].append(d)
        job["transition"] = seq.get("transition", {"type": "morph", "duration": 0.4})
        job["from_sequence"] = job.pop("sequence"); job.pop("split", None)
    cidx = {c["src"]: i for i, c in enumerate(job.get("content", []))}
    left = []
    for c in sheet["changes"]:
        e = c.get("element") or {}; src = e.get("source") or ""; st = {k: v["to"] for k, v in c["set"].items()}
        m = re.match(r"job\.shots\[(\d+)\](\.transition)?$", src)
        if m:
            sh_ = job["shots"][int(m.group(1))]
            if m.group(2):
                if "kind" in st: sh_["transition"] = TR_KEY[st["kind"]]
            else:
                if "layout" in st: sh_["template"] = names[st["layout"]]
                if "cues" in st: sh_["cues"] = int(st["cues"])
                if "beats" in st: sh_["beats"] = float(st["beats"])
                if "cut_every" in st:
                    if CUT_KEY[st["cut_every"]] is None: sh_.pop("cut_every", None)
                    else: sh_["cut_every"] = CUT_KEY[st["cut_every"]]
                if "content" in st:
                    if st["content"] == "无": sh_.pop("content", None)
                    else: sh_["content"] = int(st["content"].split()[0]) - 1
                if ("fx" in st or "fy" in st):
                    segs = P["shots"][int(m.group(1))].get("segments", [])
                    ci = sh_["content"] if "content" in st and isinstance(sh_.get("content"), int) else (cidx.get(segs[0]["content"]) if segs else None)
                    if ci is not None: focus(job["content"][ci], st)
        m = re.match(r"job\.content\[(\d+)\]$", src)
        if m: focus(job["content"][int(m.group(1))], st)
        m = re.match(r"job\.titles\.(\w+)$", src)
        if m and "text" in st: job["titles"][m.group(1)] = st["text"].replace(" / ", "\n")
        m = re.match(r"job\.cues\[(\d+)\]$", src)
        if m:
            cu = job["cues"][int(m.group(1))]
            if "text" in st: cu[2] = st["text"]
            if "t0" in st: cu[0] = float(st["t0"])
            if "t1" in st: cu[1] = float(st["t1"])
        if "tdur" in st: job.setdefault("transition", {})["duration"] = float(st["tdur"].rstrip("s"))
        if c.get("ask_ai"): left.append(f"{c['t']:.1f}s {e.get('name') or ''}：{c['ask_ai']}")
        if st.get("save_as"): job["_save_as"] = st["save_as"]
    name = job.pop("_save_as", None)
    json.dump(job, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已写回 {jp}（改前的备份：{bak}）")
    if name:
        ld = lib_dir(); sid = "my-" + __import__("time").strftime("%Y%m%d-%H%M")
        seq = {"id": sid, "name": name, "kind": "sequence", "status": "△",
               "summary": " → ".join(lib.get(x["template"], {}).get("name", x["template"]) for x in job["shots"]),
               "from": job.get("from_sequence"), "transition": job.get("transition", {}),
               "shots": [{k: v for k, v in x.items()} for x in job["shots"]]}
        seq["shots"][-1]["cues"] = "rest"
        out = os.path.join(ld, "templates", "sequences", sid + ".json")
        json.dump(seq, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        sp = os.path.join(ld, "styles", job.get("style", "koubo") + ".json"); sty = jload(sp)
        sty.setdefault("templates", {}).setdefault("sequences", {})[sid] = "△"
        json.dump(sty, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"已存成片段模板「{name}」：{out}（风格 {job.get('style', 'koubo')} 里挂成 △）")
    if left:
        print("下面这些要 Agent 自己处理（改完再渲染）：")
        for x in left: print("  " + x)
    print(f"重新出片：python {ENGINE} render {jp} <新版本>.mp4，再运行 review.py done")


# 风格：(读工程, 认目录, 找成片)
STYLES = {"course": (course, lambda wd: os.path.exists(os.path.join(wd, "ed", "segs.json")) or os.path.exists(os.path.join(wd, "segs.json")), None),
          "koubo": (koubo, lambda wd: os.path.exists(os.path.join(wd, "config.json")) and "src" in koubo_cfg(wd), koubo_video),
          "pixel": (pixel, lambda wd: bool(pixel_src(wd)), None),
          "template": (tmpl, lambda wd: bool(job_path(wd)), job_video)}


# ---------- 版本和修改单 ----------
def rdir(wd):
    d = os.path.join(wd, "review"); os.makedirs(d, exist_ok=True); return d


def sheets(wd):
    out = []
    for p in glob.glob(os.path.join(rdir(wd), "v*_to_v*.json")):
        m = re.search(r"v(\d+)_to_v(\d+)\.json$", p)
        if m: out.append((int(m.group(1)), p))
    return sorted(out)


def cur_ver(wd):
    s = sheets(wd)
    if not s: return 1
    last_n, last_p = s[-1]
    return last_n + 1 if jload(last_p).get("done") else last_n


def history(wd):
    h = []
    for n, p in sheets(wd):
        j = jload(p)
        if not j.get("done"): continue
        items = [c["element"]["name"] if c.get("element") else (c.get("ask_ai") or "") for c in j["changes"]]
        h.append(dict(**{"from": j["from"], "to": j["to"]}, n=len(j["changes"]), summary="、".join(i for i in items if i)[:80]))
    return h[::-1]


def find_video(wd):
    c = [p for p in glob.glob(os.path.join(wd, "*.mp4")) + glob.glob(os.path.join(wd, "ed", "*.mp4"))
         if not os.path.basename(p).startswith(("src", "src_cut"))]
    if not c: raise SystemExit("找不到成片：用 --video 指定这一版的 mp4")
    return max(c, key=os.path.getmtime)


def thumbs(wd, video, times):
    d = os.path.join(rdir(wd), "thumbs"); os.makedirs(d, exist_ok=True)
    key = f"{os.path.getmtime(video):.0f}"
    for i, t in enumerate(times):
        p = os.path.join(d, f"{key}_{i}.jpg")
        if not os.path.exists(p):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                            "-vf", "scale=160:-2", "-q:v", "5", p])
    return [f"thumb/{key}_{i}.jpg" for i in range(len(times))]


def build(wd, video, style):
    dur, w, h = probe(video)
    fn = STYLES[style][0]
    D = fn(wd, dur)
    D.pop("_names", None)
    n = cur_ver(wd)
    D.update(duration=dur, video="video", videoName=os.path.basename(video), ver=f"v{n}", next=f"v{n+1}",
             title=os.path.basename(os.path.abspath(wd)), history=history(wd))
    if "layout" in D: D["layout"]["def"] = D["layout"].pop("def_")
    D["thumbs"] = thumbs(wd, video, D.pop("thumbs_at"))
    draft = os.path.join(rdir(wd), "draft.json")
    if os.path.exists(draft):
        try: D["saved"] = jload(draft).get(D["ver"], [])
        except Exception: pass
    if (w, h) != (D["W"], D["H"]):
        D["notes"] = f"成片是 {w}×{h}，这个风格按 {D['W']}×{D['H']} 排版，拖框预览可能不准。"
    return D


def serve(wd, video, style, port, open_it):
    wd = os.path.abspath(wd)
    video = os.path.abspath(video or (STYLES[style][2] or find_video)(wd))
    D = build(wd, video, style)
    page = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
    html = page.replace("const D=/*DATA*/null;", "const D=" + json.dumps(D, ensure_ascii=False) + ";").encode("utf-8")
    vsize = os.path.getsize(video)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(body)

        def do_GET(self):
            p = self.path.split("?")[0]
            if p in ("/", "/index.html"): return self.send(200, html, "text/html; charset=utf-8")
            if p == "/video": return self.video()
            if p.startswith("/thumb/"):
                f = os.path.join(rdir(wd), "thumbs", os.path.basename(p))
                if os.path.exists(f): return self.send(200, open(f, "rb").read(), "image/jpeg")
            self.send(404, b"{}")

        def video(self):
            rng = self.headers.get("Range")
            a, b = 0, vsize - 1
            if rng:
                m = re.match(r"bytes=(\d*)-(\d*)", rng)
                if m.group(1): a = int(m.group(1))
                if m.group(2): b = min(int(m.group(2)), vsize - 1)
                elif not m.group(1): a = max(0, vsize - int(m.group(2)))
            self.send_response(206 if rng else 200)
            self.send_header("Content-Type", "video/mp4"); self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(b - a + 1))
            if rng: self.send_header("Content-Range", f"bytes {a}-{b}/{vsize}")
            self.end_headers()
            with open(video, "rb") as f:
                f.seek(a); left = b - a + 1
                try:
                    while left > 0:
                        chunk = f.read(min(1 << 20, left))
                        if not chunk: break
                        self.wfile.write(chunk); left -= len(chunk)
                except (BrokenPipeError, ConnectionResetError): pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
            try: data = json.loads(body or b"null")
            except ValueError: return self.send(400, b'{"error":"bad json"}')
            if self.path == "/draft":
                p = os.path.join(rdir(wd), "draft.json")
                d = jload(p) if os.path.exists(p) else {}
                d[D["ver"]] = data
                json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
                return self.send(200, b"{}")
            if self.path == "/submit":
                out = os.path.join(rdir(wd), f"{D['ver']}_to_{D['next']}.json")
                data["done"] = False
                json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"[审片台] 收到修改单 {len(data.get('changes', []))} 处：{out}", flush=True)
                return self.send(200, json.dumps({"path": out}, ensure_ascii=False).encode())
            self.send(404, b"{}")

    for p in range(port, port + 20):  # 端口被上一版占着就往后找
        try: srv = ThreadingHTTPServer(("127.0.0.1", p), H); break
        except OSError: continue
    else: raise SystemExit(f"{port}~{port+19} 端口都被占用了")
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"[审片台] {D['title']} {D['ver']}（{D['styleName']}）：{url}", flush=True)
    print("[审片台] 改完点「提交」，修改单会写进 review/；Ctrl+C 结束。", flush=True)
    if open_it: threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass


def changes(wd):
    s = sheets(wd)
    if not s or jload(s[-1][1]).get("done"):
        print("没有待处理的修改单。"); return
    p = s[-1][1]; j = jload(p)
    print(f"# 修改单 {j['from']} → {j['to']}（{p}）")
    for c in j["changes"]:
        e = c.get("element")
        head = f"{c['n']}. {c['t']:.1f}s · " + (f"{e.get('track', '')}「{e['name']}」 {e.get('source') or ''}" if e else "未选元素")
        print(head)
        for k, v in c["set"].items(): print(f"   {k}: {v['from']} → {v['to']}")
        if c.get("ask_ai"): print(f"   一句话：{c['ask_ai']}")


def done(wd):
    s = sheets(wd)
    if not s: raise SystemExit("没有修改单")
    p = s[-1][1]; j = jload(p); j["done"] = True
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已标记处理完：{p}")


def launch(wd, port):
    """Claude 桌面版的 Browser 侧栏按 .claude/launch.json 起服务并打开。不带 --video，serve 会自己找最新成片。"""
    d = os.path.join(os.path.abspath(wd), ".claude"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "launch.json")
    j = jload(p) if os.path.exists(p) else {"version": "0.0.1", "configurations": []}
    j["configurations"] = [c for c in j.get("configurations", []) if c.get("name") != "审片台"] + [{
        "name": "审片台", "runtimeExecutable": sys.executable,
        "runtimeArgs": [os.path.abspath(__file__), "serve", os.path.abspath(wd), "--no-open", "--port", str(port)],
        "port": port}]
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"已写入 {p}：在 Claude 桌面版里打开预览「审片台」即可。")



def export(wd, out, video, style):
    """出一个能发布成 Claude Artifact 的审片台：out/index.html + out/video.mp4（压到 15MB 以内的预览）+ out/thumbs/。
    页面里点「提交」，修改单存进 Artifact 自己的 db（review/submit_<版本>），Claude 读回来后用 `review.py import` 落盘。"""
    wd = os.path.abspath(wd); out = os.path.abspath(out); os.makedirs(os.path.join(out, "thumbs"), exist_ok=True)
    video = os.path.abspath(video or (STYLES[style][2] or find_video)(wd))
    D = build(wd, video, style)
    D.pop("saved", None)
    for i, t in enumerate(D["thumbs"]):
        src = os.path.join(rdir(wd), "thumbs", os.path.basename(t))
        dst = os.path.join(out, "thumbs", os.path.basename(t))
        if os.path.exists(src): open(dst, "wb").write(open(src, "rb").read())
        D["thumbs"][i] = "thumbs/" + os.path.basename(t)
    pv = os.path.join(out, "video.mp4")
    dur = D["duration"]; kbps = max(300, int(13 * 8 * 1024 / max(dur, 1)) - 128)  # 目标 13MB 以内
    w = 540 if D["H"] >= D["W"] else 960
    sh("ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"scale={w}:-2", "-c:v", "libx264", "-preset", "veryfast",
       "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{2 * kbps}k", "-c:a", "aac", "-b:a", "96k",
       "-movflags", "+faststart", pv)
    D.update(mode="artifact", video="video.mp4")
    page = open(os.path.join(HERE, "page.html"), encoding="utf-8").read()
    html = page.replace("const D=/*DATA*/null;", "const D=" + json.dumps(D, ensure_ascii=False) + ";")
    html = html.replace("<title>审片台</title>", f"<title>审片台 {D['title']}</title>", 1)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
    mb = os.path.getsize(pv) / 1e6
    print(f"[审片台] 已导出 {out}/index.html，预览视频 {mb:.1f}MB，缩略图 {len(D['thumbs'])} 张")
    print("发布：Artifact 工具 file_path=index.html，files 里带 video.mp4 和 thumbs/*.jpg，capabilities={\"db\": {}}")


def import_sheet(wd, path):
    """把从 Artifact db 读回来的修改单（review/submit_<版本> 那条文档，存成 json 文件）放进 review/，之后 changes / apply / done 照常用。"""
    j = jload(path)
    if "changes" not in j: raise SystemExit("这不是修改单：没有 changes")
    j["done"] = False
    j.pop("at", None)
    out = os.path.join(rdir(wd), f"{j['from']}_to_{j['to']}.json")
    json.dump(j, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已放进 {out}（{len(j['changes'])} 处）")


def detect(wd):
    for k, (_, ok, _v) in STYLES.items():
        if ok(wd): return k
    raise SystemExit("认不出这个工作目录是哪个风格：用 --style 指定")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("serve", "changes", "done", "launch", "apply", "export", "import"): raise SystemExit(__doc__)
    cmd, wd = a[0], a[1]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if cmd == "serve":
        serve(wd, opt("--video"), opt("--style") or detect(wd), int(opt("--port", 8765)), "--no-open" not in a)
    elif cmd == "launch": launch(wd, int(opt("--port", 8765)))
    elif cmd == "changes": changes(wd)
    elif cmd == "apply": tmpl_apply(wd)
    elif cmd == "export": export(wd, a[2], opt("--video"), opt("--style") or detect(wd))
    elif cmd == "import": import_sheet(wd, a[2])
    else: done(wd)
