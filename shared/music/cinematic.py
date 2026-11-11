"""城市电影感配乐：弦乐铺底 + 柔和钢琴琶音 + 每两拍一下低音，没有鼓。全部用代码合成，不用 AI 模型。

对应「城市电影感」vlog 模板（city-cinematic）：这种片子不是逐拍硬切，镜头跟着乐句和画面里的动作走，
所以配乐要的是「呼吸」而不是鼓点：
- 律动：没有鼓，每两拍（半小节）一下低音，是镜头长度的参照，章节在这一下上换。
- 调式与和声：A 大调 vi–IV–I–V（F#m D A E），开阔、带一点怀念。
- 配器：弦乐铺底（慢起慢收）、钢琴分解和弦、低音。前奏只有高处的弦乐和一点钢琴。
- 前奏最后两拍一个「呼」（噪声上扫，压掉高频），正好盖住开场的两下快闪，落点进全编制。
- 质感：大混响，像在户外。

节拍表格式和 beatgen 其他预设一样，模板直接用。
"""
import numpy as np
import beatgen as B
import melody as M

SR = B.SR
PRESETS = {
    "open": {"key": "A", "chords": ["F#m", "D", "A", "E"]},      # vi IV I V
    "calm": {"key": "D", "chords": ["D", "Bm", "G", "A"]},       # I vi IV V
}


def strings(freqs, secs, a=0.6, r=0.8, cutoff=1800, seed=0):
    """弦乐铺底：每个音几条略微失谐的锯齿波叠起来再低通，慢起慢收。"""
    n = int(secs * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for f in freqs:
        for d in (-0.06, 0.0, 0.07):
            x += B.saw(f * 2 ** (d / 12), n, rng.random())
    x /= max(1, len(freqs) * 3)
    e = np.clip(t / a, 0, 1) ** 1.5 * np.clip((secs - t) / r, 0, 1)
    return B.hp(B.lp(x * e, cutoff), 110)


def piano(f, secs, vel=1.0):
    """柔和钢琴：几个谐波，高次衰减得快，琴槌声很轻。"""
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for h, (amp, dec) in enumerate([(1.0, 1.6), (0.42, 2.6), (0.18, 4.0), (0.08, 6.0), (0.04, 8.0)], 1):
        if f * h > 5000:
            break
        x += amp * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * dec)
    x *= np.clip(t / 0.006, 0, 1) * np.clip((secs - t) / 0.08, 0, 1)
    return B.lp(x, 3200) * vel * 0.5


def low(f, secs):
    """低音：正弦 + 一点二次谐波，软起，像低音提琴拨弦被混响包住。"""
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)
    return x * np.clip(t / 0.02, 0, 1) * np.exp(-t * 1.3) * np.clip((secs - t) / 0.1, 0, 1)


def whoosh(rng, secs):
    """「呼」：噪声从低往高扫再收，压掉 5kHz 以上，不刺耳。"""
    x = B.riser(rng, secs)
    n = len(x)
    t = np.arange(n) / SR
    x = B.lp(x, 5000)
    tail = np.clip((secs - t) / (secs * 0.25), 0, 1)
    return x * tail[:, None]


def build(mood, bpm, intro, drop, outro, seed, key=None):
    P = PRESETS.get(mood, PRESETS["open"])
    key = key or P["key"]
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = beat * 4
    bars = intro + drop + outro
    tail = 3.0
    dur = bars * bar + tail
    N = int(dur * SR)
    pad, pno, bass, fx = (np.zeros((N, 2)) for _ in range(4))
    chords = P["chords"]
    k0 = M.NOTE[key]

    for b in range(bars):
        ch = chords[(b - intro) % len(chords)]
        root, _ = M.parse_chord(ch, k0)
        v_low = M.chord_midi(ch, key, lo=50)               # 中音区和弦
        v_high = [m + 12 for m in v_low]
        t0 = b * bar
        in_intro, in_outro = b < intro, b >= intro + drop
        secs = bar + (tail if in_outro else 0.35)
        if in_intro:
            # 前奏：只有高处的弦乐，慢慢打开；钢琴每小节点一个音
            fr = [M.midi_hz(m) for m in v_high]
            B.place(pad, strings(fr, secs, a=1.2, cutoff=1400 + 500 * b, seed=b), t0, 0.32, pan=0.15)
            B.place(pno, piano(M.midi_hz(v_high[1] + 12), bar * 1.5, 0.6), t0 + beat, 0.5, pan=-0.2)
            continue
        fr = [M.midi_hz(m) for m in v_low + [v_low[0] + 12]]
        B.place(pad, strings(fr, secs, a=0.5 if b == intro else 0.25, seed=b), t0, 0.42 if not in_outro else 0.36)
        rootm = 33 + (root - 33) % 12  # A1 往上
        if in_outro:
            B.place(bass, low(M.midi_hz(rootm), tail + bar), t0, 0.75)
            B.place(pno, piano(M.midi_hz(v_high[0] + 12), tail + bar, 0.7), t0, 0.5)
            continue
        # 每两拍一下低音（根音、五度）——镜头和章节的参照点
        B.place(bass, low(M.midi_hz(rootm), beat * 2.2), t0, 0.8)
        B.place(bass, low(M.midi_hz(rootm + 7), beat * 2.2), t0 + 2 * beat, 0.6)
        # 钢琴分解和弦：八分音符 1-5-8-10 往上再回来，力度有点起伏
        arp = [v_low[0], v_low[2] if len(v_low) > 2 else v_low[1], v_low[0] + 12, v_low[1] + 12]
        arp = arp + arp[::-1][1:3] + [arp[1], arp[2]]
        for i, m in enumerate(arp):
            vel = 0.55 + 0.25 * (i % 4 == 0) + rng.uniform(-0.05, 0.05)
            B.place(pno, piano(M.midi_hz(m + 12), beat * 1.6, vel), t0 + i * beat / 2, 0.42, pan=-0.15 + 0.3 * (i % 2))
        # 每小节一个高音（和弦的三音或五音），轻轻勾一下
        top = v_high[1] + 12 if b % 2 == 0 else v_high[2] + 12 if len(v_high) > 2 else v_high[1] + 12
        B.place(pno, piano(M.midi_hz(top), bar, 0.5), t0, 0.35, pan=0.2)

    if intro:  # 前奏最后两拍的「呼」，落点一下轻的低频下潜
        w = 2 * beat
        B.place(fx, whoosh(rng, w), intro * bar - w, 0.5)
        B.place(fx, B.impact(rng) * 0.6, intro * bar, 0.6)

    pad = B.reverb(pad, 2.6, 0.35)
    pno = B.reverb(pno, 2.2, 0.3)
    bass = B.reverb(bass, 1.2, 0.12)
    fx = B.reverb(fx, 2.0, 0.3)
    mix = pad * 1.3 + pno * 1.6 + bass * 0.32 + fx * 0.7
    mix /= max(1e-6, np.abs(mix).max()) / 0.89
    fade = int(2.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]

    beats = [round(k * beat, 4) for k in range(bars * 4 + 1)]
    t_drop = intro * bar
    secs_ = [{"name": "intro", "start": 0.0, "beats": intro * 4}] if intro else []
    secs_.append({"name": "drop", "start": round(t_drop, 4), "beats": drop * 4})
    if outro:
        secs_.append({"name": "outro", "start": round((intro + drop) * bar, 4), "beats": outro * 4})
    meta = {"preset": f"cinematic-{mood}", "bpm": bpm, "key": key, "chords": chords, "beats": beats,
            "downbeats": beats[::4], "phrase_hits": beats[::2], "drop": round(t_drop, 4),
            "end_hit": round((intro + drop) * bar, 4), "sections": secs_, "duration": round(dur, 3),
            "source": "beatgen cinematic（合成，免版权，没有鼓）"}
    return mix, meta
