"""课程横版的运镜和转场规则：合成前自动校验，违规直接报错，不出片。

单独检查时间轴：python rules.py        （在 ed/ 目录里跑，读 segs.json / clips.json / chap.json / chap_names.json）
compose.py 每次合成前也会自动调用 check()。

术语（和 SKILL.md 第四节一致）：
- 运镜：画面里的镜头运动。传统说法「推、拉、摇、移、跟、升降」；我们对录屏/截图做的是后期运镜（数码推拉）。
- 快推定格（punch-in）：用很短的时间推到目标框，然后画面完全不动。允许。
- Ken Burns：对画面做缓慢的推拉或平移。du 明确不要，禁止。
- 转场：两个镜头之间怎么接。
"""
import json, os, sys

# ---- 运镜手法总表（三个风格共用一套名字，手册「运镜手法总表」一节和这里一一对应）----
# 课程横版的运镜只发生在左侧内容区（录屏 rec、截图 clips）；人像框是锚点，不做运镜。
MOVES_OK = {
    "fixed": "固定：画面不动",
    "punch": "快推定格：0.8s 内推近到目标框，然后定住",
    "pullout": "快拉：0.8s 内拉远，交代全貌，然后定住",
    "jump": "跳切推近/拉回：同一个时间点写两个关键帧，取景框瞬间变化",
    "reframe": "快移：取景框大小不变，0.8s 内移到另一块区域，然后定住",
}
MOVES_TRY = {  # 待试：先做小样给 du 看
    "snap": "冲击推：推近时带一点回弹或运动模糊",
    "whip": "甩镜：带运动模糊的快速横移，接到下一块内容",
}
MOVES_BANNED = {"kenburns": "慢推、慢拉、慢移（Ken Burns），du 明确不要"}

# ---- 运镜 ----
# 镜头取景框 [x, y, w] 每次变化必须在 MOVE_MAX 秒内完成，变化之间画面完全不动。
# clips 里的推近固定用 PUSH_DUR 秒（合成器写死），所以只需要检查 rec 的关键帧。
MOVE_MAX = 0.8
PUSH_DUR = 0.6

# ---- 转场（segs.json 每段可写 "trans"，表示从上一段切进这一段的方式）----
TRANS_OK = {
    "dissolve": "叠化（交叉淡化）0.3s ease-out，默认",
    "cut": "硬切",
}
TRANS_TRY = {  # 待试：先做小样给 du 看，认可后在 compose.py 实现并移到 TRANS_OK
    "slide": "推入/滑入：同章节下一步从右往左推入",
    "match": "匹配剪辑/元素转场：如提示词框放大成录屏输入框",
}
TRANS_BANNED = {
    "flash": "闪白", "spin": "旋转", "flip": "翻页", "kenburns": "缓慢推拉平移",
}


class RuleError(Exception):
    pass


def _check_trans(segs, errs):
    for i, s in enumerate(segs):
        tr = s.get("trans", "dissolve")
        if tr in TRANS_OK:
            continue
        if tr in TRANS_BANNED:
            errs.append(f"segs[{i}] {s['layer']}: 转场「{tr}」({TRANS_BANNED[tr]}) 是禁用的")
        elif tr in TRANS_TRY:
            errs.append(f"segs[{i}] {s['layer']}: 转场「{tr}」({TRANS_TRY[tr]}) 还是待试，先做小样给 du 确认，再在 compose.py 实现")
        else:
            errs.append(f"segs[{i}] {s['layer']}: 未知转场「{tr}」，可用：{', '.join(TRANS_OK)}")


def _check_rec(segs, errs):
    for i, s in enumerate(segs):
        if not s["layer"].startswith("rec:"):
            continue
        Z = s.get("zoom") or []
        for a, b in zip(Z, Z[1:]):
            if a[1:] == b[1:]:
                continue  # 定住
            dt = b[0] - a[0]
            if dt > MOVE_MAX + 1e-6:
                errs.append(f"segs[{i}] {s['layer']}: {a[0]}s→{b[0]}s 取景框从 {a[1:]} 变到 {b[1:]} 用了 {dt:.2f}s，"
                            f"超过 {MOVE_MAX}s 就是慢推/慢移。改成在 {MOVE_MAX}s 内推到位，前后加一个相同取景框的关键帧定住")


def _check_clips(clips, errs):
    for name, CLP in clips.items():
        for j, c in enumerate(CLP):
            b0, b1 = c[3], c[4]
            if b0 != b1 and b0[2] == b1[2]:
                errs.append(f"clips.json {name}[{j}]: 起止框一样大、位置不同，会变成整段慢慢平移。"
                            f"要换位置就拆成两段（硬切），或者改成推近/拉远")


def _check_chapters(chap, names, errs):
    if len(chap) != len(names) + 1:
        errs.append(f"chap.json 有 {len(chap)} 个时间点，应该是章节数 {len(names)} + 1（最后一个是全片终点）")
    if any(b <= a for a, b in zip(chap, chap[1:])):
        errs.append("chap.json 的时间点必须递增")


def check(segs, clips, chap=None, names=None):
    errs = []
    _check_trans(segs, errs)
    _check_rec(segs, errs)
    _check_clips(clips, errs)
    if chap is not None and names is not None:
        _check_chapters(chap, names, errs)
    if errs:
        raise RuleError("时间轴不符合课程横版规则：\n- " + "\n- ".join(errs))


if __name__ == "__main__":
    E = os.path.dirname(os.path.abspath(__file__)) if len(sys.argv) < 2 else sys.argv[1]
    ld = lambda n, d=None: json.load(open(os.path.join(E, n))) if os.path.exists(os.path.join(E, n)) else d
    try:
        check(ld("segs.json", []), ld("clips.json", {}), ld("chap.json"), ld("chap_names.json"))
    except RuleError as e:
        print(e); sys.exit(1)
    print("OK：运镜、转场、章节表都符合规则")
