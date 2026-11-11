"""旋律生成：按乐理规则编一句旋律，不用 AI 模型。

思路就是作曲课上教的那一套，写成规则：
1. 和弦进行定每小节能用哪些音（和弦音 + 调式音阶）。
2. 节奏从一小组「节奏型」里挑，强拍、长音落在和弦音上，弱拍用级进（相邻音阶音）连过去。
3. 一句 4 小节按「动机 → 模进（把动机搬到下一个和弦上）→ 展开 → 收束」排，最后一个音落在主音上。
4. 整句有一个弧线：先往上走到最高点，再落回来。
5. 同一个 seed 出同一句，换 seed 就换一句；不抄任何现成的曲子。

输出是音符列表 [(开始拍, 时值拍, MIDI 音高, 力度)]，拍子从这一句的第 0 拍算起，乐器怎么发声交给调用方。
"""
import numpy as np

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],          # 自然小调；属和弦那一小节会自动换成升高的导音
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "pentatonic": [0, 2, 4, 7, 9],
}

# 和弦：相对和弦根音的半音
CHORD = {"": [0, 4, 7], "m": [0, 3, 7], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9], "7": [0, 4, 7, 10],
         "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "m7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9]}

# 一小节（4 拍）的节奏型，单位是拍
RHYTHMS = {
    "motif": [[1, .5, .5, 1, 1], [.5, .5, 1, .5, .5, 1], [1.5, .5, 1, 1], [.5, .5, .5, .5, 1, 1]],
    "run": [[.5] * 8, [.5, .5, .5, .5, .5, .5, 1], [1, .5, .5, .5, .5, 1]],
    "cadence": [[1, .5, .5, 2], [.5, .5, 1, 2], [1, 1, 2]],
}


def parse_chord(name, key_root):
    """'Dm6' → (根音音级, 和弦音音级集合)"""
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    q = name[len(root):]
    r = NOTE[root]
    return r, sorted({(r + i) % 12 for i in CHORD[q]})


def allowed(scale_pcs, chord_pcs):
    """这一小节能用的音：音阶音，但和和弦音只差半音的那个音阶音让给和弦音（比如属和弦的升 7 级）。"""
    out = set(chord_pcs)
    for p in scale_pcs:
        if any((p - c) % 12 in (1, 11) and p not in chord_pcs for c in chord_pcs if c not in scale_pcs):
            continue
        out.add(p)
    return sorted(out)


def near(pcs, target, lo, hi, prefer=0):
    """离 target 最近的、音级在 pcs 里的 MIDI 音；prefer>0 偏向往上，<0 偏向往下。"""
    best, bd = None, 1e9
    for m in range(lo, hi + 1):
        if m % 12 in pcs:
            d = abs(m - target) + (0.4 if prefer and np.sign(m - target) == -np.sign(prefer) else 0)
            if d < bd:
                best, bd = m, d
    return best


def step(pcs, m, direction, lo, hi):
    """从 m 往 direction 方向走一个音阶音（级进）。"""
    x = m + direction
    while lo <= x <= hi and x % 12 not in pcs:
        x += direction
    return x if lo <= x <= hi else m - direction


def phrase(chords, key, scale="minor", seed=1, lo=67, hi=86, start=None, swing=0.0):
    """编一句旋律。chords：每小节一个和弦名（4 小节最常见）。返回 [(拍, 时值, midi, 力度)]。"""
    rng = np.random.default_rng(seed)
    k = NOTE[key]
    scale_pcs = [(k + s) % 12 for s in SCALES[scale]]
    bars = len(chords)
    info = [parse_chord(c, k) for c in chords]
    # 弧线：每小节一个目标高度，第 2/3 小节到最高，最后落回主音
    peak = lo + (hi - lo) * rng.uniform(0.62, 0.8)
    arc = [lo + (hi - lo) * 0.4 + (peak - lo - (hi - lo) * 0.4) * np.sin(np.pi * (b + 0.5) / bars) for b in range(bars)]
    # 收尾音：最后一个和弦是主和弦就落主音，不是就落这个和弦里离主音最近的音（根音优先）
    last_root, last_pcs = info[-1]
    end_pcs = [k] if k in last_pcs else [last_root]
    tonic = near(end_pcs, arc[-1] - 3, lo, hi)
    notes = []
    prev = start or near(info[0][1], arc[0], lo, hi)
    motif = None
    for b, (root, cpcs) in enumerate(info):
        pcs = allowed(scale_pcs, cpcs)
        last = b == bars - 1
        if last:
            rh = RHYTHMS["cadence"][rng.integers(len(RHYTHMS["cadence"]))]
        elif b == 0 or (b % 2 == 0 and b < bars - 1 and motif is None):
            rh = RHYTHMS["motif"][rng.integers(len(RHYTHMS["motif"]))]
        elif b % 2 == 1 and motif is not None and b < bars - 2:
            rh = motif[0]  # 模进：同一个节奏
        else:
            rh = RHYTHMS["run"][rng.integers(len(RHYTHMS["run"]))]
        t = 0.0
        bar_notes = []
        if b % 2 == 1 and motif is not None and rh is motif[0]:
            # 模进：把动机的音程走向搬到这个和弦上，再贴到能用的音上
            shift = (root - info[b - 1][0]) % 12
            shift = shift - 12 if shift > 6 else shift
            for (o, d, m, v) in motif[1]:
                bar_notes.append((o, d, near(pcs, m + shift, lo, hi), v))
        else:
            for i, d in enumerate(rh):
                strong = t in (0.0, 2.0) or d >= 1
                if last and i == len(rh) - 1:
                    m = tonic  # 收在主音
                elif strong:
                    direction = np.sign(arc[b] - prev) or (1 if rng.random() < 0.5 else -1)
                    m = near(cpcs, prev + direction * rng.integers(1, 5), lo, hi, direction)
                else:
                    direction = np.sign(arc[b] - prev) or 1
                    if rng.random() < 0.25:
                        direction = -direction  # 偶尔回一下，不要一直单向爬
                    m = step(pcs, prev, int(direction), lo, hi)
                v = 0.95 if t in (0.0, 2.0) else 0.75
                bar_notes.append((t, d, m, v))
                prev = m
                t += d
        if b % 2 == 0 and not last:
            motif = (rh, bar_notes)
        for (o, d, m, v) in bar_notes:
            notes.append((b * 4 + o, d, int(m), v))
            prev = m
    # 摇摆：反拍的八分音符往后挪一点，长音不动
    if swing:
        out = []
        for (o, d, m, v) in notes:
            frac = o % 1
            if abs(frac - 0.5) < 1e-6:
                o2 = o + swing * 0.5
                out.append((o2, d - swing * 0.5, m, v))
            elif abs(frac) < 1e-6 and d == 0.5:
                out.append((o, d + swing * 0.5, m, v))
            else:
                out.append((o, d, m, v))
        notes = out
    return notes


def chord_midi(name, key, lo=48):
    """和弦的一个紧凑排列（吉他、手风琴左手用）：根音放在 lo 往上的第一个八度里，其他音依次往上叠。"""
    root = name[:2] if len(name) > 1 and name[1] in "#b" else name[:1]
    r = NOTE[root]
    base = lo + (r - lo) % 12
    return [base + i for i in CHORD[name[len(root):]]]


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- 好唱的写法
# phrase() 每小节都现编，听起来像在乱走。song() 换成流行歌、香颂常用的写法：
# 一个节奏 + 一个音型（动机）定下来以后，前三小节反复用它，只是搬到每个和弦上；
# 第 4 小节往下级进落到长音。8 小节是「问句 + 答句」：答句前两小节原样重复问句，
# 问句停在和弦的三音/五音（没说完），答句停在主音（说完了）。音域压在一个八度左右，几乎全是级进。
SING_RHYTHMS = [[1.5, .5, 1, 1], [1, .5, .5, 2], [.5, .5, 1, 2], [1, 1, 1, 1], [1.5, .5, 2]]
CADENCES = [[1.5, .5, 2], [1, 1, 2], [2, 2]]


def _scale_notes(pcs, lo, hi):
    return [m for m in range(lo, hi + 1) if m % 12 in pcs]


def _walk(notes, m, k):
    """在音阶音列表里从 m 走 k 级。"""
    i = min(range(len(notes)), key=lambda j: abs(notes[j] - m))
    return notes[max(0, min(len(notes) - 1, i + k))]


def song(chords, key, scale="minor", seed=1, lo=62, hi=77):
    """编一段 len(chords) 小节（4 或 8）的旋律。返回 [(拍, 时值, midi, 力度)]。"""
    rng = np.random.default_rng(seed)
    k = NOTE[key]
    scale_pcs = [(k + s) % 12 for s in SCALES[scale]]
    info = [parse_chord(c, k) for c in chords]
    rh = SING_RHYTHMS[rng.integers(len(SING_RHYTHMS))]
    cad = CADENCES[rng.integers(len(CADENCES))]
    # 动机音型：相对第一个音走几级；一个小跳 + 级进，整体略往上
    shapes = [[0, 1, 2, 1], [0, -1, 0, 2], [0, 1, 0, -1], [0, 2, 1, 0], [0, 1, 2, 4], [0, -1, -2, 0]]
    shape = shapes[rng.integers(len(shapes))]
    lift = [0, 1, 2, -1]  # 4 小节里每小节起音相对第一小节高几级：往上走到第 3 小节，再回落

    def bar(b, start_hint, rhythm, shp):
        root, cpcs = info[b]
        pcs = allowed(scale_pcs, cpcs)
        sn = _scale_notes(pcs, lo, hi)
        first = near(cpcs, start_hint, lo, hi)
        out, t, m = [], 0.0, first
        for i, d in enumerate(rhythm):
            m = _walk(sn, first, shp[i % len(shp)])
            if t in (0.0, 2.0) or d >= 1.5:
                m = near(cpcs, m, lo, hi)  # 强拍、长音一定是和弦音
            out.append((b * 4 + t, d, m, 0.9 if t in (0.0, 2.0) else 0.72))
            t += d
        return out

    def cadence(b, target):
        root, cpcs = info[b]
        sn = _scale_notes(allowed(scale_pcs, cpcs), lo, hi)
        n = len(cad)
        out, t = [], 0.0
        for i, d in enumerate(cad):
            m = target if i == n - 1 else _walk(sn, target, n - 1 - i)  # 从上往下级进落到目标音
            out.append((b * 4 + t, d, m, 0.85))
            t += d
        return out

    center = (lo + hi) // 2 - 2
    sn_all = _scale_notes(scale_pcs, lo, hi)
    notes = []
    nb = len(chords)
    for p0 in range(0, nb, 4):
        answer = p0 > 0
        for i in range(min(4, nb - p0)):
            b = p0 + i
            last = i == 3 or b == nb - 1
            if last:
                _, cpcs = info[b]
                if answer or nb <= 4:
                    tgt_pcs = [k] if k in cpcs else [info[b][0]]
                else:
                    tgt_pcs = [p for p in cpcs if p != k] or cpcs  # 问句停在不是主音的和弦音
                target = near(tgt_pcs, center - 1, lo, hi)
                notes += cadence(b, target)
            elif answer and i < 2:
                src = [n for n in notes if i * 4 <= n[0] < (i + 1) * 4]
                notes += [(o + p0 * 4, d, m, v) for (o, d, m, v) in src]  # 答句开头原样重复
            else:
                hint = _walk(sn_all, center, lift[i])
                shp = shape if not (answer and i == 2) else [-s for s in shape]  # 答句第 3 小节把音型倒过来
                notes += bar(b, hint, rh, shp)
    return notes
