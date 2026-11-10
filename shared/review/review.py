"""审片台：出完一版后在浏览器（或 Agent 的侧边栏浏览器）里看片、定点改，提交成修改单交回 Agent。

  python review.py serve <工作目录> [--video 成片.mp4] [--port 8765] [--no-open]
      起本地网页 http://127.0.0.1:<port>/ ：读这一集的工程文件生成多轨时间轴。
      用户点「提交」后，修改单写到 <工作目录>/review/<旧版>_to_<新版>.json。
  python review.py changes <工作目录>
      打印最新一份还没处理的修改单（Agent 读这个来改）。处理完运行 `done` 标记。
  python review.py done <工作目录>
      把最新修改单标记为已处理，下次 serve 版本号自动 +1。

现在支持：课程横版（工作目录里有 ed/segs.json）。口播和像素风的读法之后加。
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


STYLES = {"course": (course, lambda wd: os.path.exists(os.path.join(wd, "ed", "segs.json")) or os.path.exists(os.path.join(wd, "segs.json")))}


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
    n = cur_ver(wd)
    D.update(duration=dur, video="video", videoName=os.path.basename(video), ver=f"v{n}", next=f"v{n+1}",
             title=os.path.basename(os.path.abspath(wd)), history=history(wd))
    D["layout"]["def"] = D["layout"].pop("def_")
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
    video = os.path.abspath(video or find_video(wd))
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

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
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
        head = f"{c['n']}. {c['t']:.1f}s · " + (f"{e['track']}「{e['name']}」 {e.get('source') or ''}" if e else "未选元素")
        print(head)
        for k, v in c["set"].items(): print(f"   {k}: {v['from']} → {v['to']}")
        if c.get("ask_ai"): print(f"   一句话：{c['ask_ai']}")


def done(wd):
    s = sheets(wd)
    if not s: raise SystemExit("没有修改单")
    p = s[-1][1]; j = jload(p); j["done"] = True
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"已标记处理完：{p}")


def detect(wd):
    for k, (_, ok) in STYLES.items():
        if ok(wd): return k
    raise SystemExit("认不出这个工作目录是哪个风格：用 --style 指定")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("serve", "changes", "done"): raise SystemExit(__doc__)
    cmd, wd = a[0], a[1]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if cmd == "serve":
        serve(wd, opt("--video"), opt("--style") or detect(wd), int(opt("--port", 8765)), "--no-open" not in a)
    elif cmd == "changes": changes(wd)
    else: done(wd)
