"""拼贴清单开场编排：读素材表（每段素材的抽象标签），按角色和关系规则排出「标题 → 定格拼贴 → 地点清单 → 正片 → 致谢卡」，
写成渲染器能直接用的任务文件。适合团建、朋友出游、一晚上跑好几家店。

用法：
  python collage.py <collage.json> <job.json> [--music 歌.wav] [--bpm 124] [--seed 1]
  不给 --music 就现场合成一段 beatgen house（默认 124 BPM，有鼓），长度按排出来的总时长定（和 job.json 放在一起）。

素材表 collage.json：
{
 "titles": {"hello": "Welcome", "to": "to", "city": "Singapore", "thanks": "TO MY BEST TEAM", "memo": "2026 新加坡团建纪念"},
 "plate": {"src": "street.mp4", "start": 2.0},          可选：标题和拼贴的底板；不给就用第一段街景远景
 "stickers": [{"src": "receipt.png"}, {"src": "bar.mp4", "t": 3.1}, ...],   可选：不给就从素材里自动挑
 "clips": [
  {"src": "a.mp4", "place": "Native", "subject": "sign", "scale": "wide"},
  {"src": "b.mp4", "place": "Native", "subject": "people", "scale": "medium", "list": true},
  {"src": "c.mp4", "place": "Native", "subject": "drink", "scale": "detail", "action_at": 1.4},
  {"src": "d.mp4", "place": "Native", "subject": "selfie", "talk": [0.5, 3.2]},
  {"src": "e.mp4", "place": "街头", "subject": "people", "screen": [0.32, 0.38, 0.36, 0.2]},
  {"src": "p.jpg", "place": "小贩中心", "photo": true},
  {"src": "g.jpg", "group": true}
 ]
}
每段素材的标签（看一眼关键帧就能填）：
  place     地点（一站），同一站的素材排在一起；站的先后按素材在表里第一次出现的顺序（也就是时间顺序）
  subject   主体：sign 店招门头 / street 街景 / people 人在干嘛 / selfie 自拍口播 / drink 饮品 / food 食物 /
            object 物件（菜单、小票、海报、唱片）/ animal 动物 / group 合照
  scale     景别：wide / medium / close / detail
  list      清单那一刀用它（这一站最有气氛的镜头：干杯、做酒、笑）；一站最多标一段，没标就自动挑
  talk      [开始秒, 结束秒]：有人说话，整句用完再切（最多 4 秒）
  action_at 关键动作在第几秒（端上来、干杯），切在动作之后 0.4 秒
  screen    [x, y, 宽, 高]：画面里有相机 / 手机屏幕，框是屏幕在竖屏画面里的位置（比例）；下一段就是屏幕里拍的东西
  photo     照片（不单独占一刀，贴成白边小照片压在同一站的一刀上）
  group     合照，留给结尾致谢卡
  sticker   可以拿来做贴纸；值为 true 或秒数（取哪一帧）；cut: alpha / person / card 见 engine.py sticker()
  start / len / crop / focus  和别的模板一样

输出的 job.json 就是普通任务文件（style=vlog，显式 shots），渲染、审片台、改稿都和别的模板一样；
每个镜头带 role（角色）、chapter（哪一站）、why（为什么这样接）。
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "music")):
    if p not in sys.path:
        sys.path.insert(0, p)

STICKERS_PER_BEAT = 2  # 贴纸每拍换几张（八分音符）
MAX_STICKERS = 12  # 拼贴最多几张，约 6 拍
LIST_COLORS = ["list_1", "list_2", "list_3", "list_4", "list_5", "list_6", "list_7"]
SECS = {"wide": 2.0, "medium": 1.6, "close": 1.4, "detail": 1.2}  # 正片每刀默认秒数（按内容切，不卡拍）
EST = ("sign", "street")  # 一站开头用来交代地方的
STICKY = ("object", "drink", "food", "sign", "animal")  # 能截一帧做贴纸的


def norm(c, i):
    c = dict(c)
    c["i"] = i
    c.setdefault("subject", "people")
    c.setdefault("scale", "medium")
    c.setdefault("place", "")
    return c


def shot_len(c):
    """正片这一刀多长（秒）、从素材第几秒开始。"""
    st = c.get("start", 0)
    if c.get("talk"):
        a, b = c["talk"]
        st, d = a, min(b - a, 4.0)
    elif c.get("action_at") is not None:
        d = max(1.0, c["action_at"] + 0.4 - st)
    else:
        d = SECS.get(c["scale"], 1.6) + (0.4 if c["subject"] == "selfie" else 0)
    if c.get("len"):
        d = min(d, c["len"])
    return st, round(round(d * 30) / 30, 3)


def list_beats(n):
    """清单 n 刀的拍数：前两刀 2 拍、1.5 拍，之后每刀 1 拍（越切越快，但每刀至少 1 拍，字看得清），
    总长补到整拍（最后一刀落在拍上冲进正片）。原片 124 BPM 是 1、1、½、½…，du 看了说太快读不清，所以放慢一倍。"""
    if n <= 0:
        return []
    if n == 1:
        return [2]
    b = [2, 1.5] + [1] * (n - 2)
    b = b[:n]
    pad = math.ceil(sum(b) - 1e-6) - sum(b)
    b[0] += pad
    return [round(x, 3) for x in b]


def arrange(spec):
    clips = [norm(c, i) for i, c in enumerate(spec["clips"])]
    places = []
    for c in clips:
        if c["place"] and c["place"] not in places and not c.get("photo") and not c.get("group"):
            places.append(c["place"])
    usable = [c for c in clips if not c.get("photo") and not c.get("group")]

    # ---- 底板：给了就用，没给就挑第一段街景 / 店招远景，定格
    plate = spec.get("plate")
    plate_clip = None
    if not plate:
        cands = [c for c in usable if c["subject"] in EST and c["scale"] in ("wide", "medium")] or usable
        plate_clip = cands[0]
        plate = {"src": plate_clip["src"], "start": plate_clip.get("start", 0) + 0.5}
    plate = dict(plate, freeze=True)

    # ---- 清单：每站一刀，标了 list 的优先；没标就挑人在干杯 / 做酒的中景
    lst = []
    paired = {c["i"] for c in usable if c.get("screen")} | {c["i"] + 1 for c in usable if c.get("screen")}  # 屏中屏那两段留给正片
    for p in places:
        g = [c for c in usable if c["place"] == p and c is not plate_clip and (c["i"] not in paired or c.get("list"))]
        if not g:
            continue
        pick = next((c for c in g if c.get("list")), None) or max(
            g, key=lambda c: (c["subject"] == "people") * 3 + (c["scale"] == "medium") * 2 + (c["subject"] in ("drink", "food")) - (c["subject"] == "sign"))
        lst.append(pick)
    in_list = {c["i"] for c in lst}

    # ---- 贴纸：给了就用；没给就从素材里截：物件 / 饮品 / 店招 / 动物的特写，先物后动物，自拍最后自动抠人
    stickers = spec.get("stickers")
    if not stickers:
        things = [c for c in usable if c.get("sticker") or (c["subject"] in STICKY and c["scale"] in ("close", "detail"))]
        things.sort(key=lambda c: (c["subject"] == "animal", c["i"]))
        stickers = []
        for c in things[:20]:
            t = c["sticker"] if isinstance(c.get("sticker"), (int, float)) and not isinstance(c.get("sticker"), bool) else (c.get("action_at") or c.get("start", 0) + 0.5)
            s = {"src": c["src"], "t": t}
            for k in ("crop", "cut"):
                if k in c:
                    s[k] = c[k]
            stickers.append(s)
        me = next((c for c in usable if c["subject"] == "selfie"), None)
        if me:
            t = me["talk"][0] + 0.3 if me.get("talk") else me.get("start", 0) + 0.5
            stickers.append({"src": me["src"], "t": t, "cut": me.get("cut", "person"), "scale": 1.25})

    # ---- 正片：按站走，每站先交代再按拍摄顺序；清单用过的、照片、合照不进正片
    body = []
    for p in places + [""]:
        g = [c for c in usable if c["place"] == p and c["i"] not in in_list]
        if not g:
            continue
        # 交代地方：店招、门口、街景；城市旅行没有这些就用地标 / 建筑 / 风景的远景
        est = next((c for c in g if c["subject"] in EST), None) or next(
            (c for c in g if c["scale"] == "wide" and c["subject"] in ("landmark", "building", "nature")), None)
        seq = ([est] if est else []) + [c for c in g if c is not est]
        # 避免跳切：同主体同景别连着的，和后面第一个不一样的换个位置
        for k in range(1, len(seq) - 1):
            a, b = seq[k - 1], seq[k]
            if a["subject"] == b["subject"] and a["scale"] == b["scale"]:
                j = next((j for j in range(k + 1, len(seq)) if (seq[j]["subject"], seq[j]["scale"]) != (a["subject"], a["scale"])), None)
                if j:
                    seq.insert(k, seq.pop(j))
        body += seq
    # 屏中屏：拍屏幕的那段如果被挪动了，把它后面的那段跟回来
    for c in [c for c in body if c.get("screen")]:
        k = body.index(c)
        nxt = next((x for x in clips[c["i"] + 1:] if x in body), None)
        if nxt and body.index(nxt) != k + 1:
            body.remove(nxt)
            body.insert(body.index(c) + 1, nxt)

    # 画中画：照片贴到同一站第一刀不说话的中远景上
    insets = {}
    for ph in [c for c in clips if c.get("photo")]:
        host = next((c for c in body if c["place"] == ph["place"] and not c.get("talk") and c["scale"] in ("wide", "medium") and c["i"] not in insets), None) \
            or next((c for c in body if c["place"] == ph["place"] and c["i"] not in insets), None)
        if host:
            insets[host["i"]] = ph
    group = next((c for c in clips if c.get("group")), None) or next((c for c in reversed(body) if c["subject"] in ("people", "selfie")), None)
    return {"plate": plate, "stickers": stickers, "list": lst, "body": body, "insets": insets, "group": group}


def to_job(spec, A, bpm, music):
    beat = 60.0 / bpm
    T = dict({"hello": "Welcome", "to": "to"}, **spec.get("titles", {}))
    content, shots = [], []

    def add(c, **kw):
        ent = {"src": c["src"], "start": round(kw.pop("start", c.get("start", 0)), 3)}
        for k in ("focus", "crop", "push", "freeze"):
            if k in c:
                ent[k] = c[k]
        content.append(ent)
        return len(content) - 1

    pi = add(A["plate"])
    shots.append({"template": "vlog-collage-title", "beats": 2, "content": pi, "role": "标题",
                  "why": "定格底板，Welcome / to / 地名 每半拍跳一个词（前奏）"})
    # 贴纸跟着八分音符走：每拍 2 张（原片 124 BPM ≈ 每秒 4 张），最多 MAX_STICKERS 张，多了均匀抽，最后一张（自己）一定留
    st = A["stickers"]
    if len(st) > MAX_STICKERS:
        idx = [round(k * (len(st) - 2) / (MAX_STICKERS - 2)) for k in range(MAX_STICKERS - 1)] + [len(st) - 1]
        st = [st[k] for k in idx]
    A["stickers"] = st
    n = len(st)
    sfps = STICKERS_PER_BEAT / beat
    sb = max(2, math.ceil(n / STICKERS_PER_BEAT + 1))  # 最后一张多停 1 拍
    shots.append({"template": "vlog-collage", "beats": sb, "content": pi, "on_drop": True, "role": "拼贴", "sticker_fps": round(sfps, 4),
                  "why": f"落点进鼓：同一张底板、同一个位置，{n} 张贴纸每拍 2 张换上来" + ("，先物后人，最后一张是自己" if any(x.get("cut") == "person" for x in A["stickers"]) else "")})
    lb = list_beats(len(A["list"]))
    for k, (c, b) in enumerate(zip(A["list"], lb)):
        ci = add(c)
        shots.append({"template": "vlog-place-list", "beats": b, "content": ci, "role": "清单", "chapter": c["place"],
                      "texts": {"place": c["place"]}, "accent": LIST_COLORS[k % len(LIST_COLORS)],
                      "why": f"第 {k + 1} 站：{round(b, 2)} 拍" + ("，越切越快" if k else "，清单开始")})
    prev = None
    for c in A["body"]:
        st, d = shot_len(c)
        ci = add(c, start=st)
        why = []
        if prev is None:
            why.append("正片开始：清单最后一刀落在拍上冲进来")
        elif prev["place"] != c["place"]:
            why.append(f"下一站：{c['place']}" + ("，先交代地方" if c["subject"] in EST else ""))
        if c.get("talk"):
            why.append("话说完再切")
        if c.get("action_at") is not None:
            why.append("切在动作之后")
        sh = {"template": "vlog-plain", "seconds": d, "content": ci, "role": "正片", "chapter": c["place"]}
        if prev is not None and prev.get("screen"):
            sh["from_box"] = prev["screen"]
            why.append("屏中屏：从上一刀的屏幕里放大出来")
        if c["i"] in A["insets"]:
            sh["template"] = "vlog-photo-inset"
            sh["inset"] = add(A["insets"][c["i"]])
            why.append("压一张同一站的白边照片")
        sh["why"] = "，".join(why) or "按时间线"
        shots.append(sh)
        prev = c
    g = A["group"]
    if g:
        shots.append({"template": "vlog-thanks-card", "seconds": 2.6, "content": add(g), "role": "致谢卡",
                      "why": "黑底致谢卡 + 合照收尾"})
    pre = sum(s.get("beats", 0) for s in shots[:1])
    open_beats = sum(s.get("beats", 0) for s in shots)
    total = open_beats * beat + sum(s.get("seconds", 0) for s in shots)
    job = {"style": "vlog", "sequence": "collage-list", "content": content, "stickers": A["stickers"], "shots": shots,
           "titles": T, "transition": {"type": "cut"}, "music": music, "duration": round(total, 3)}
    return job, pre, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips")
    ap.add_argument("job")
    ap.add_argument("--music", help="现成的歌（同目录要有 .beats.json，可用 beats.py 测）；不给就合成 house")
    ap.add_argument("--bpm", type=float, default=124)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    spec = json.load(open(a.clips, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.clips))
    jdir = os.path.dirname(os.path.abspath(a.job))

    def rel(p):  # 素材路径按素材表所在目录算，任务文件放哪都能找到
        return os.path.relpath(os.path.join(base, os.path.expanduser(p)), jdir)
    for c in spec["clips"] + spec.get("stickers", []) + ([spec["plate"]] if spec.get("plate") else []):
        c["src"] = rel(c["src"])
    A = arrange(spec)
    if a.music:
        mp = os.path.relpath(os.path.abspath(a.music), jdir)
        bpm = json.load(open(os.path.splitext(a.music)[0] + ".beats.json", encoding="utf-8"))["bpm"]
        job, pre, total = to_job(spec, A, bpm, {"src": mp, "start": "auto", "fade_out": 1.5})
    else:
        import beatgen
        bpm = a.bpm
        job, pre, total = to_job(spec, A, bpm, None)
        bar = 4 * 60 / bpm
        drop = math.ceil((total - pre * 60 / bpm) / bar)
        mix, meta = beatgen.build("house", bpm, 1, drop, 1, "C", a.seed)
        wav = os.path.join(jdir, "music_house.wav")
        beatgen.save_wav(wav, mix)
        json.dump(meta, open(os.path.splitext(wav)[0] + ".beats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        job["music"] = {"src": os.path.basename(wav), "start": "auto", "fade_out": 1.5}
        print(f"配乐：beatgen house {bpm:g} BPM，前奏 1 小节 + {drop} 小节 → {wav}")
    json.dump(job, open(a.job, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    beat = 60 / bpm
    print(f"done {a.job}：{len(job['shots'])} 个镜头，约 {total:.1f} 秒；贴纸 {len(A['stickers'])} 张，清单 {len(A['list'])} 站，正片 {len(A['body'])} 刀")
    t = 0
    for s in job["shots"]:
        d = s["beats"] * beat if "beats" in s else s["seconds"]
        tag = f"{s['beats']:g} 拍" if "beats" in s else f"{s['seconds']:.2f} 秒"
        print(f"  {t:6.2f}s  {tag:>9}  {s['role']:<4} {s.get('chapter', ''):<10} {s['why']}")
        t += d


if __name__ == "__main__":
    main()
