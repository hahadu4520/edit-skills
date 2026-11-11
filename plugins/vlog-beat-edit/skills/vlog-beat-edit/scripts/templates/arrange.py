"""城市电影感编排：读素材表（每段素材的抽象标签），按镜头关系规则排出镜头表，写成渲染器能直接用的任务文件。

用法：
  python arrange.py <clips.json> <job.json> [--music 歌.wav] [--seed 1]
  不给 --music 就现场合成一段 beatgen cinematic，长度按排出来的拍数定（和 job.json 放在一起）。

素材表 clips.json：
{
 "city": "北京", "city_en": "BEIJING",
 "clips": [
  {"src": "a.mp4", "place": "北海", "scale": "wide", "subject": "landmark", "hero": true, "motifs": ["塔"]},
  {"src": "b.mp4", "place": "北海", "scale": "close", "subject": "landmark", "motifs": ["塔"]},
  {"src": "c.mp4", "place": "胡同", "scale": "detail", "subject": "object", "motifs": ["棋"], "action_at": 1.2},
  ...
 ]
}
每段素材的标签（看一眼关键帧就能填，跟哪座城市无关）：
  place    地点 / 章节名，同一地点的素材会排在一起
  scale    景别：wide 远景 / medium 中景 / close 近景 / detail 特写
  subject  主体：landmark 地标建筑 / building 普通建筑 / nature 风景 / street 街景 / people 人 /
           object 物件 / animal 动物 / vehicle 交通工具 / sky 天空飞鸟
  motion   画面里的运动：still 几乎不动 / inner 主体在动（人走、鸟飞、手在动）/ cross 有东西横穿画面
  motifs   母题：形状、颜色、物种这类能跨地点接力的东西，比如 ["狮子", "红色", "屋顶", "圆"]
  hero     主地标（开场和结尾用），可以标 1–3 段
  image    倒影、虚焦、剪影这类「意象」镜头
  occluder 有前景遮挡划过（适合放章末，遮挡划过时切走）
  action_at 素材里关键动作发生在第几秒（落子、回头），切点会放在动作之后
  start / len 素材从第几秒开始用、可用多长（秒），不填 start=0、len 不限

输出的 job.json 就是普通任务文件（style=vlog，显式 shots），渲染、审片台、改稿都和别的模板一样；
每个镜头多带 role（角色）、chapter（章节）、why（为什么这样接），审片台和改稿时都看得到。
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "music")):
    if p not in sys.path:
        sys.path.insert(0, p)

ROLE_WHY = {"意象": "开场意象，压竖排城市名", "局部": "城市名跨过这一刀再淡出", "建立": "主地标远景，交代在哪",
            "快闪": "快闪，配乐前奏的「呼」盖住", "落点": "落点：停在主地标更近的角度，正片开始", "呼应": "结尾回到地标，和开场呼应"}
SCALE = {"wide": 0, "medium": 1, "close": 2, "detail": 3}
SCALE_CN = {"wide": "远景", "medium": "中景", "close": "近景", "detail": "特写"}
LANDMARK = {"landmark", "building", "nature"}
LIFE = {"street", "people", "vehicle"}
QUIET = {"object", "animal", "sky"}


def norm(c, i):
    c = dict(c)
    c["i"] = i
    c.setdefault("scale", "medium")
    c.setdefault("subject", "object")
    c.setdefault("motion", "still")
    c["motifs"] = set(c.get("motifs", []))
    c.setdefault("place", c["subject"])
    return c


def relation(a, b):
    """上一刀 a 接下一刀 b 的关系 → (分数, 说明)。分数越高越顺。"""
    if a is None:
        return 0, ""
    s, why = 0, []
    common = a["motifs"] & b["motifs"]
    if a.get("image") and not b.get("image") and (common or a["place"] == b["place"]):
        s += 3
        why.append("虚 → 实")
    if common:
        s += 3
        why.append("母题接力：" + "、".join(sorted(common)))
    if a["place"] == b["place"]:
        d = SCALE[b["scale"]] - SCALE[a["scale"]]
        if d > 0:
            s += 1
            why.append(f"{SCALE_CN[a['scale']]} → {SCALE_CN[b['scale']]}")
        if d == 0 and a["subject"] == b["subject"] and (common or a["subject"] in LANDMARK):
            s -= 2
            why.append("同一主体同景别（会像跳了一下）")
        elif a["subject"] == b["subject"] == "people":
            why.append("人接人（市井蒙太奇）")
    if a["subject"] in QUIET and a["scale"] == "detail" and b["subject"] == "people" and a["place"] == b["place"]:
        s += 2
        why.append("先细节后人")
    if a.get("dir") and a.get("dir") == b.get("dir"):
        s += 1
        why.append("动势同向")
    if a.get("occluder"):
        s += 1
        why.append("遮挡划过时切")
    if not why and a["place"] != b["place"]:
        why.append(f"换章：{a['place']} → {b['place']}")
    return s, "，".join(why)


def kind_of(group):
    n = len(group)
    life = sum(c["subject"] in LIFE for c in group)
    quiet = sum(c["subject"] in QUIET for c in group)
    land = n - life - quiet
    if life >= max(land, quiet):
        return "life"
    if quiet > land:
        return "quiet"
    return "landmark"


def order_chapter(group, kind):
    """章内顺序：地标章远 → 近；市井章街景开头、细节先于人；安静章细节在前、动物压后。遮挡的放章末。"""
    g = sorted(group, key=lambda c: (SCALE[c["scale"]], c["i"]))
    if kind == "life":
        est = [c for c in g if c["subject"] == "street" and c["scale"] in ("wide", "medium")][:1]
        rest = [c for c in g if c not in est]
        out = est[:]
        details = [c for c in rest if c["subject"] not in ("people",) and c["scale"] in ("close", "detail")]
        people = [c for c in rest if c not in details]
        for d in details:  # 细节 → 和它同母题的人（象棋 → 下棋的人）；没对上的人放到后面，越往后越密
            out.append(d)
            j = next((k for k, p in enumerate(people) if p["motifs"] & d["motifs"]), None)
            if j is not None:
                out.append(people.pop(j))
        out += people
        g = out
    elif kind == "quiet":
        g = sorted(group, key=lambda c: (c["subject"] == "animal", -SCALE[c["scale"]], c["i"]))
    occ = [c for c in g if c.get("occluder")]
    return [c for c in g if not c.get("occluder")] + occ


def beats_for(c, kind, k, n):
    if kind == "landmark":
        return {"wide": 3, "medium": 2.5, "close": 2, "detail": 2}[c["scale"]]
    if kind == "life":
        if c.get("occluder"):
            return 1
        # 市井章越往后越密：后半章的人物镜头切到 1 拍、0.5 拍
        mid = k >= n // 2
        if c["scale"] == "wide":
            return 2.5
        if c["subject"] == "people":
            return 0.5 if (mid and c["motion"] != "still" and k % 2) else 1
        return 1.5
    return 2  # 安静章


def arrange(spec, seed=1):
    clips = [norm(c, i) for i, c in enumerate(spec["clips"])]
    used = set()

    def take(cands, prev=None, key=None):
        cands = [c for c in cands if c["i"] not in used]
        if not cands:
            return None
        best = max(cands, key=lambda c: (relation(prev, c)[0] if prev else 0) + (key(c) if key else 0))
        used.add(best["i"])
        return best

    heroes = [c for c in clips if c.get("hero")] or [c for c in clips if c["subject"] == "landmark"] or clips
    hero = min(heroes, key=lambda c: SCALE[c["scale"]])
    plan = []  # (clip, beats, role, template, extra)

    # ---- 开场：意象 + 城市名 → 局部 → 建立 → 两下快闪 → 落点
    used.add(hero["i"])
    img = take([c for c in clips if c.get("image")], hero, key=lambda c: 3 * (c["place"] == hero["place"])) \
        or take([c for c in clips if c["subject"] in LANDMARK and c["scale"] in ("close", "detail")], hero)
    if img:
        plan.append((img, 1.5, "意象", "vlog-city-name", {}))
    part = take([c for c in clips if c["subject"] in LANDMARK and c["scale"] in ("close", "detail", "medium") and c["place"] != hero["place"]], img) \
        or take([c for c in clips if c["subject"] in LANDMARK and c["scale"] != "wide"], img)
    if part:
        plan.append((part, 1.5, "局部", "vlog-city-name-out" if img else "vlog-city-name", {}))
    plan.append((hero, 2, "建立", "vlog-plain", {}))
    movers = [c for c in clips if c["motion"] != "still" and c["subject"] in ("sky", "vehicle", "people", "animal")]
    f1 = take(movers, hero, key=lambda c: 2 * (c["subject"] == "sky") + (c["place"] != hero["place"]))
    f2 = take(movers, f1, key=lambda c: (c["place"] not in (hero["place"], f1["place"] if f1 else None)))
    for f, b in ((f1, 0.33), (f2, 0.67)):
        if f:
            plan.append((f, b, "快闪", "vlog-plain", {}))
    land = take([c for c in clips if c["place"] == hero["place"] and c["subject"] in LANDMARK], hero,
                key=lambda c: SCALE[c["scale"]]) or take([c for c in clips if c["subject"] in LANDMARK and c["scale"] in ("wide", "medium")])
    if land:
        plan.append((land, 3, "落点", "vlog-plain", {"on_drop": True}))
    else:
        plan[-1][4]["on_drop"] = True

    # ---- 收尾地标先留出来（和开场同地点 / 同母题）
    ender = take([c for c in clips if c["subject"] in LANDMARK and c["i"] not in used],
                 key=lambda c: 4 * bool(c["motifs"] & (hero["motifs"] | (img["motifs"] if img else set())))
                 + 3 * (c["place"] in (hero["place"], img["place"] if img else None)) + 2 * bool(c.get("hero")) - SCALE[c["scale"]])

    # ---- 正片：其余素材按地点分章
    rest = [c for c in clips if c["i"] not in used]
    groups = {}
    for c in rest:
        groups.setdefault(c["place"], []).append(c)
    chapters = [(kind_of(g), p, g) for p, g in groups.items()]
    rank = {"landmark": 0, "life": 1, "quiet": 2}
    chapters.sort(key=lambda x: (rank[x[0]], min(c["i"] for c in x[2])))
    prev = plan[-1][0]
    for kind, place, g in chapters:
        seq = order_chapter(g, kind)
        # 章首：有和上一刀母题接得上的（石狮 → 门环），就让它打头，换章读成一句话
        hook = max(seq, key=lambda c: relation(prev, c)[0])
        if len(seq) > 1 and prev["motifs"] & hook["motifs"]:
            seq.remove(hook)
            seq.insert(0, hook)
        # 地标章：没有母题可接，就在同一景别级别里挑和上一刀最顺的打头
        elif kind == "landmark" and len(seq) > 1:
            first_scale = seq[0]["scale"]
            heads = [c for c in seq if SCALE[c["scale"]] <= SCALE[first_scale] + 1]
            h = max(heads, key=lambda c: relation(prev, c)[0])
            seq.remove(h)
            seq.insert(0, h)
        start = sum(p[1] for p in plan)
        for k, c in enumerate(seq):
            used.add(c["i"])
            plan.append((c, beats_for(c, kind, k, len(seq)), {"landmark": "地标章", "life": "市井章", "quiet": "安静章"}[kind] + "：" + place,
                         "vlog-plain", {"chapter": place}))
            prev = c
        # 章节换在低音上：这一章总拍数补到偶数
        tot = sum(p[1] for p in plan) - start
        pad = (2 - (start + tot) % 2) % 2
        if pad:
            c, b, r, t, e = plan[-1]
            plan[-1] = (c, round(b + pad, 2), r, t, e)
    if ender:
        plan.append((ender, 3, "呼应", "vlog-plain", {}))
    # 结尾停在低音上：总拍数补到偶数
    tot = sum(p[1] for p in plan)
    pad = (2 - tot % 2) % 2
    if pad > 1e-6:
        c, b, r, t, e = plan[-1]
        plan[-1] = (c, round(b + pad, 2), r, t, e)
    return plan


def to_job(spec, plan, bpm, music):
    beat = 60.0 / bpm
    content, shots = [], []
    prev = None
    for c, b, role, tpl, extra in plan:
        secs = b * beat
        st = c.get("start", 0)
        if c.get("action_at") is not None:  # 动作落在这一刀的后四分之三，切在动作之后
            st = max(c.get("start", 0), c["action_at"] - 0.75 * secs)
        if c.get("len"):
            secs = min(secs, c["len"])
        ent = {"src": c["src"], "start": round(st, 3)}
        for k in ("focus", "crop", "push"):
            if k in c:
                ent[k] = c[k]
        content.append(ent)
        _, why = relation(prev, c)
        if role in ROLE_WHY:
            why = ROLE_WHY[role] + ("；" + why if why and not why.startswith("换章") else "")
        sh = {"template": tpl, "beats": b, "content": len(content) - 1, "role": role, "why": why or role}
        sh.update(extra)
        shots.append(sh)
        prev = c
    city = spec.get("city", "")
    job = {"style": "vlog", "sequence": "city-cinematic", "content": content, "shots": shots,
           "titles": {"city": "\n".join(city), "city_en": spec.get("city_en", "")},
           "transition": {"type": "cut"}, "music": music}
    return job


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips")
    ap.add_argument("job")
    ap.add_argument("--music", help="现成的歌（同目录要有 .beats.json，可用 beats.py 测）；不给就合成 cinematic")
    ap.add_argument("--mood", default="open")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    spec = json.load(open(a.clips, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(a.clips))
    for c in spec["clips"]:  # 素材路径按素材表所在目录算，任务文件放哪都能找到
        c["src"] = os.path.relpath(os.path.join(base, os.path.expanduser(c["src"])), os.path.dirname(os.path.abspath(a.job)))
    plan = arrange(spec, a.seed)
    total = sum(p[1] for p in plan)
    pre = 0
    for p in plan:
        if p[4].get("on_drop"):
            break
        pre += p[1]
    jdir = os.path.dirname(os.path.abspath(a.job))
    if a.music:
        mp = os.path.relpath(os.path.abspath(a.music), jdir)
        bj = json.load(open(os.path.splitext(a.music)[0] + ".beats.json", encoding="utf-8"))
        bpm = bj["bpm"]
    else:
        import beatgen, cinematic
        bpm = 78
        intro = 2
        drop = int(-(-(total - pre) // 4))
        mix, meta = cinematic.build(a.mood, bpm, intro, drop, 1, a.seed)
        wav = os.path.join(jdir, "music_cinematic.wav")
        beatgen.save_wav(wav, mix)
        json.dump(meta, open(os.path.splitext(wav)[0] + ".beats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        mp = os.path.basename(wav)
        print(f"配乐：beatgen cinematic {bpm} BPM，前奏 {intro} 小节 + {drop} 小节 → {wav}")
    job = to_job(spec, plan, bpm, {"src": mp, "start": "auto", "fade_out": 1.5})
    json.dump(job, open(a.job, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    beat = 60 / bpm
    t = -pre * beat
    print(f"done {a.job}：{len(plan)} 个镜头，{total} 拍（约 {total * beat:.1f} 秒），落点前 {pre} 拍")
    for c, b, role, tpl, e in plan:
        _, why = relation(None, c)
        print(f"  {t + pre * beat:6.2f}s  {b:>4} 拍  {role:<10} {c['place']}·{SCALE_CN[c['scale']]}·{c['subject']}  {os.path.basename(c['src'])}")
        t += b * beat
    unused = len(spec["clips"]) - len(plan)
    if unused:
        print(f"  没用上的素材 {unused} 段")


if __name__ == "__main__":
    main()
