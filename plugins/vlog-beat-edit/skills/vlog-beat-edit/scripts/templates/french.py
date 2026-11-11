"""法式 vlog 配乐：手风琴主旋律 + 吉他「la pompe」扫弦 + 低音提琴 + 鼓刷，全部用代码合成，不用 AI 模型。

为什么这样配（对应维度 14 的子属性）：
- 律动：吉他在 1、3 拍放低音和和弦、2、4 拍短促地「切」一下（la pompe），是巴黎咖啡馆、吉普赛爵士最典型的律动；
  八分音符带一点摇摆。速度留在 110–124，照样能每半拍卡点。
- 调式与和声：nostalgic 用 D 小调 i6–iv6–V7–i6（Dm6 Gm6 A7 Dm6），带一点怀旧；
  bright 用 F 大调 vi–ii–V–I（Dm7 Gm7 C7 Fmaj7），像晴天的巴黎街头。
- 配器：手风琴（三片簧片故意调得略有差异，产生法式 musette 那种颤音）、尼龙弦吉他、低音提琴、鼓刷。
- 旋律：melody.py 按乐理规则生成，前奏最后两拍有一串上行的弱起音，正好把人带进落点。
- 质感：小房间混响，像在小酒馆里。

结构和 beatgen 其他预设一样：前奏（钩子）→ 落点（全乐队 + 旋律）→ 结尾和弦，节拍表格式也一样。
"""
import numpy as np
import beatgen as B
import melody as M

SR = B.SR

PRESETS = {
    "nostalgic": {"key": "D", "scale": "minor", "chords": ["Dm6", "Gm6", "A7", "Dm6"]},
    "bright": {"key": "F", "scale": "major", "chords": ["Dm7", "Gm7", "C7", "Fmaj7"]},
}


# ---------------------------------------------------------------- 乐器
def ks(f, secs, decay=0.996, bright=0.6, seed=0):
    """拨弦（Karplus-Strong）：一小段噪声在一条按音高长度的延迟线里来回衰减，听起来就是弦。按块算，长音也快。"""
    n = int(secs * SR)
    N = max(2, int(round(SR / f)))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, N)
    if bright < 1:
        buf = B.lp(buf, 800 + 9000 * bright)
    buf -= buf.mean()  # 去掉直流，不然低音会变成一个往一边偏的「闷」
    y = np.zeros(n + 2 * N + 1)
    y[1:N + 1] = buf  # y[0] 是补的 0
    i = N + 1
    while i < len(y):
        m = min(N, len(y) - i)
        y[i:i + m] = decay * 0.5 * (y[i - N:i - N + m] + y[i - N - 1:i - N - 1 + m])
        i += m
    return y[1:1 + n]


def damp(x, keep):
    """手掌闷音：keep 秒之后很快收掉。"""
    n = len(x)
    t = np.arange(n) / SR
    return x * np.where(t < keep, 1.0, np.exp(-(t - keep) * 60))


def accordion(f, secs, vel=1.0, detune=0.0045, seed=0):
    """手风琴：三片簧片（中间准、两边各偏一点）叠在一起，簧片音色用谐波相加；两边偏的那一点就是 musette 颤音。"""
    n = int(secs * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for k, dt in enumerate((-detune, 0.0, detune)):
        ff = f * (1 + dt)
        for h in range(1, 13):
            if ff * h > 9000:
                break
            amp = (1 / h) ** 0.75 * (1.15 if h % 2 else 0.85)
            x += amp * np.sin(2 * np.pi * ff * h * t + rng.uniform(0, 2 * np.pi))
    # 低八度的一片，声音更厚
    for h in range(1, 7):
        x += 0.18 * (1 / h) * np.sin(2 * np.pi * f / 2 * h * t + rng.uniform(0, 2 * np.pi))
    x /= 6
    a, r = 0.025, 0.07
    e = np.clip(t / a, 0, 1) * np.clip((secs - t) / r, 0, 1)
    e *= 1 + 0.06 * np.sin(2 * np.pi * 0.8 * t)  # 风箱的轻微起伏
    return B.hp(B.lp(x * e, 5200), 140) * vel


def brush(rng, secs=0.22):
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = B.bp(rng.normal(0, 1, n), 1800, 9000)
    e = np.clip(t / 0.02, 0, 1) * np.exp(-t * 14)
    return x * e * 0.35


# ---------------------------------------------------------------- 编排
def build(mood, bpm, intro, drop, outro, seed, key=None):
    P = PRESETS[mood]
    key = key or P["key"]
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = beat * 4
    bars = intro + drop + outro
    tail = 2.0
    dur = bars * bar + tail
    N = int(dur * SR)
    gtr, bass, drums, lead, pad = (np.zeros((N, 2)) for _ in range(5))
    swing = 0.16
    chords = P["chords"]

    def at(b, k):  # 第 b 小节第 k 拍（可小数）的秒数，反拍加摇摆
        frac = k % 1
        return b * bar + (k + (swing * 0.5 if abs(frac - 0.5) < 1e-6 else 0)) * beat

    # 旋律：落点之后的每 4 小节编一句，第二句用新的 seed 但从第一句结尾的音接着走
    notes = []
    prev = None
    for p0 in range(intro, intro + drop, 4):
        nb = min(4, intro + drop - p0)
        ch = [chords[(p0 - intro + i) % len(chords)] for i in range(nb)]
        ph = M.phrase(ch, key, P["scale"], seed=seed * 7 + p0, start=prev, swing=swing)
        notes += [(p0 * 4 + o, d, m, v) for (o, d, m, v) in ph]
        prev = ph[-1][2]
    # 前奏最后两拍：顺着第一个和弦往上走的弱起，把人带进落点
    if intro and notes:
        first = notes[0][2]
        _, pcs = M.parse_chord(chords[0], M.NOTE[key])
        run, m = [], first
        for _ in range(4):
            m = M.step(sorted(set(pcs) | {(M.NOTE[key] + s) % 12 for s in M.SCALES[P["scale"]]}), m, -1, 55, 90)
            run.append(m)
        run = run[::-1]
        for i, m in enumerate(run):
            notes.insert(i, ((intro * 4 - 2) + i * 0.5, 0.5, m, 0.7))
    # 结尾：主音长音
    if outro:
        notes.append(((intro + drop) * 4, 4 + tail / beat * 0.6, M.near([M.NOTE[key]], notes[-1][2], 60, 84), 0.9))

    for (o, d, m, v) in notes:
        b, k = divmod(o, 4)
        t0 = at(int(b), k)
        x = accordion(M.midi_hz(m), d * beat * 0.96, v, seed=int(m))
        B.place(lead, x, t0, 0.55, pan=0.05)
        if d >= 1 and rng.random() < 0.5:  # 长音前加一个半音下方的倚音，手风琴常用的装饰
            g = accordion(M.midi_hz(m - 1), 0.06, 0.6, seed=int(m) + 1)
            B.place(lead, g, t0 - 0.06, 0.45, pan=0.05)

    for b in range(bars):
        ch = chords[(b - intro) % len(chords)]
        root_pc, _ = M.parse_chord(ch, M.NOTE[key])
        voicing = M.chord_midi(ch, key, lo=52)
        in_drop = intro <= b < intro + drop
        if b < intro:  # 前奏：手风琴左手轻轻铺一个和弦
            for m in voicing:
                B.place(pad, accordion(M.midi_hz(m), bar * 0.98, 0.5, seed=m), b * bar, 0.16, pan=-0.1)
            continue
        if b >= intro + drop:  # 结尾：吉他慢扫一下 + 低音 + 和弦长音
            for i, m in enumerate(voicing + [voicing[0] + 12]):
                B.place(gtr, ks(M.midi_hz(m), 3.0, 0.9985, 0.55, seed=m), b * bar + i * 0.03, 0.32, pan=-0.3)
            B.place(bass, B.lp(ks(M.midi_hz(36 + (root_pc - 36) % 12), 3.0, 0.998, 0.3), 900), b * bar, 0.9)
            for m in voicing:
                B.place(pad, accordion(M.midi_hz(m), bar + tail * 0.8, 0.5, seed=m), b * bar, 0.14)
            continue
        # la pompe：1、3 拍低音 + 和弦稍长，2、4 拍短切；扫弦从低到高错开几毫秒
        for k in range(4):
            t0 = at(b, k)
            chop = k in (1, 3)
            for i, m in enumerate(voicing):
                s = ks(M.midi_hz(m), 0.4, 0.995, 0.65 if chop else 0.5, seed=b * 16 + k * 4 + i)
                s = damp(s, 0.07 if chop else 0.16)
                B.place(gtr, s, t0 + i * 0.007, 0.34 if chop else 0.26, pan=-0.3)
            if not chop:  # 低音提琴：1 拍根音，3 拍五度
                bm = 36 + (root_pc - 36) % 12 + (7 if k == 2 else 0)
                B.place(bass, B.lp(ks(M.midi_hz(bm), 0.7, 0.997, 0.3, seed=b * 8 + k), 900), t0, 0.85)
            else:
                B.place(drums, brush(rng), t0, 0.6, pan=0.3)
        # 鼓刷在八分音符上轻轻擦
        for k in range(8):
            B.place(drums, brush(rng, 0.12), at(b, k / 2), 0.18, pan=0.3)

    lead = B.reverb(lead, 1.1, 0.2)
    pad = B.reverb(pad, 1.4, 0.3)
    gtr = B.reverb(gtr, 0.8, 0.15)
    mix = lead * 1.0 + pad * 1.0 + gtr * 1.0 + bass * 1.6 + drums * 0.6
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    mix /= max(1e-6, np.abs(mix).max()) / 0.89
    fade = int(1.2 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]

    beats = [round(k * beat, 4) for k in range(bars * 4 + 1)]
    t_drop = intro * bar
    secs = [{"name": "intro", "start": 0.0, "beats": intro * 4}] if intro else []
    secs.append({"name": "drop", "start": round(t_drop, 4), "beats": drop * 4})
    if outro:
        secs.append({"name": "outro", "start": round((intro + drop) * bar, 4), "beats": outro * 4})
    meta = {"preset": f"french-{mood}", "bpm": bpm, "key": key, "scale": P["scale"], "chords": chords, "beats": beats,
            "downbeats": beats[::4], "drop": round(t_drop, 4), "end_hit": round((intro + drop) * bar, 4),
            "sections": secs, "duration": round(dur, 3), "melody_notes": len(notes),
            "source": "beatgen french（合成，免版权；旋律按乐理规则生成）"}
    return mix, meta
