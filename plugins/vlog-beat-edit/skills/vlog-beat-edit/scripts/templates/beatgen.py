"""配乐生成器：用合成器现场做一段免版权的 vlog 配乐，同时输出精确的节拍表。

节拍表就是维度 14「配乐与卡点」的底：片段模板按「几拍」排镜头，渲染器按节拍表换素材，
所以切点天然落在鼓点上，不用再去对。

用法：
  python beatgen.py <预设> <out.wav> [--bpm 122] [--intro 1] [--drop 4] [--outro 1] [--key C] [--seed 1]
  预设：
    house   ins 感快节奏卡点（默认 122 BPM）：前奏铺底 + 上扬 → 落点进鼓 → 结尾一下重音收住
    lofi    日常慢 vlog（默认 86 BPM）：电钢琴 + 黑胶底噪 + 松弛的鼓
    pop     明亮流行（默认 128 BPM）：拍手 + 合成器拨弦，适合旅行快剪
    french  法式（默认 116 BPM）：手风琴旋律 + 吉他 la pompe 扫弦 + 低音提琴 + 鼓刷，有旋律（melody.py 按乐理规则生成）；
            --mood nostalgic（D 小调，怀旧）/ bright（F 大调，明亮）；换 --seed 就换一句旋律
  --intro / --drop / --outro 是小节数（4 拍一小节）。开头模板一般 intro 1 小节（钩子）、drop 4 小节（快切 + 标题）。

输出：<out.wav>（44.1kHz 立体声）和 <out>.beats.json：
  {"bpm":122, "beats":[每拍的秒数...], "downbeats":[每小节第一拍], "drop": 落点秒数,
   "sections":[{"name":"intro","start":0,"beats":4}, ...], "duration": 总长}

只用 numpy，Mac / Windows / Linux 都能跑。音色是合成器做的，比较基础；正片想要更好的音色，
从曲库挑一首再用 beats.py 测节拍，模板用法完全一样。
"""
import argparse, json, math, os, wave
import numpy as np

SR = 44100
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

# 和弦进行：每小节一个，写成相对主音的半音
PROG = {
    "house": [[5, 9, 12, 16], [7, 11, 14, 17], [4, 7, 11, 14], [9, 12, 16, 19]],    # IVmaj7 V6 iii7 vi7
    "lofi": [[2, 5, 9, 12], [7, 11, 14, 17], [0, 4, 7, 11], [9, 12, 16, 19]],      # ii7 V7 Imaj7 vi7
    "pop": [[0, 4, 7, 12], [7, 11, 14, 19], [9, 12, 16, 21], [5, 9, 12, 17]],      # I V vi IV
}
DEFAULT_BPM = {"house": 122, "lofi": 86, "pop": 128, "french": 116}


def hz(semi):  # semi 相对 A4=440
    return 440.0 * 2 ** (semi / 12)


# ---------------------------------------------------------------- 基础件
def lp(x, fc, q=0.0):
    """频域低通（静态）：比逐点滤波快得多，长音频也只要一瞬间。"""
    n = len(x)
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    h = 1 / np.sqrt(1 + (f / fc) ** 4)
    if q:
        h *= 1 + q * np.exp(-((f - fc) / (fc * 0.25)) ** 2)
    return np.fft.irfft(X * (h[:, None] if x.ndim == 2 else h), n, axis=0)


def hp(x, fc):
    n = len(x)
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    h = 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** 4)
    return np.fft.irfft(X * (h[:, None] if x.ndim == 2 else h), n, axis=0)


def bp(x, lo, hi):
    return hp(lp(x, hi), lo)


def env(n, a=0.002, d=0.2, s=0.0, r=0.05, hold=None):
    t = np.arange(n) / SR
    e = np.where(t < a, t / max(a, 1e-6), 1.0)
    if hold is None:
        e = e * np.where(t < a, 1, np.exp(-(t - a) / max(d, 1e-4)) * (1 - s) + s)
    else:
        rel = np.clip((t - hold) / max(r, 1e-4), 0, 1)
        e = e * (1 - rel)
    return e


def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1.0) - 1


def place(buf, x, at, gain=1.0, pan=0.0):
    i = int(round(at * SR))
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    if x.ndim == 1:
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        buf[i:i + len(x), 0] += x * gain * l * 1.414
        buf[i:i + len(x), 1] += x * gain * r * 1.414
    else:
        buf[i:i + len(x)] += x * gain


def reverb(x, secs=1.8, mix=0.25, seed=3):
    rng = np.random.default_rng(seed)
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, (n, 2)) * np.exp(-t * 6.9 / secs)[:, None]
    ir = lp(ir, 5000)
    ir[: int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum(0))
    L = len(x) + n
    N = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N, axis=0) * np.fft.rfft(ir, N, axis=0), N, axis=0)[: len(x)]
    return x * (1 - mix) + y * mix * 1.6


# ---------------------------------------------------------------- 乐器
def kick(punch=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 7.5)
    click = np.random.default_rng(1).normal(0, 1, n) * np.exp(-t * 400) * 0.25
    return np.tanh((x + click) * 1.6 * punch) * 0.9


def clap(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    noise = bp(rng.normal(0, 1, n), 1000, 6000)
    e = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        e += np.where(t >= off, np.exp(-(t - off) * (180 if k < 2 else 16)), 0)
    return noise * e * 1.4


def snare_lofi(rng):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t * 28) * 0.5
    noise = bp(rng.normal(0, 1, n), 1200, 6000) * np.exp(-t * 18) * 0.5
    return body + noise


def hat(rng, open_=False):
    n = int((0.22 if open_ else 0.05) * SR)
    t = np.arange(n) / SR
    x = hp(rng.normal(0, 1, n), 7500)
    return x * np.exp(-t * (14 if open_ else 70)) * (0.9 if open_ else 0.75)


def crash(rng, secs=2.2):
    n = int(secs * SR)
    t = np.arange(n) / SR
    return hp(rng.normal(0, 1, (n, 2)), 5000) * np.exp(-t * 2.6)[:, None] * 0.22


def riser(rng, secs):
    """前奏最后一小节的上扬：白噪声从低往高扫，越来越响。"""
    n = int(secs * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, (n, 2))
    parts = 8
    out = np.zeros_like(x)
    for k in range(parts):  # 分段换截止频率，交叉淡化
        fc = 400 * (16 ** (k / (parts - 1)))
        y = bp(x, fc * 0.5, fc * 1.6)
        w = np.clip(1 - np.abs(t / secs * (parts - 1) - k), 0, 1)
        out += y * w[:, None]
    return out * ((t / secs) ** 2.2)[:, None] * 0.5


def impact(rng):
    """落点那一下：低频下潜 + 一点噪声。"""
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    f = 38 + 60 * np.exp(-t * 6)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    return np.tanh(sub * 1.4) * 0.7


def supersaw(freqs, n, cutoff, detune=0.12, rng=None):
    x = np.zeros(n)
    for f in freqs:
        for d in (-detune, 0, detune):
            x += saw(f * 2 ** (d / 12), n, rng.random() if rng is not None else 0)
    return lp(x / (len(freqs) * 3), cutoff, q=0.6)


def epiano(freqs, n):
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        x += (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 5)
              + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    trem = 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
    return x / len(freqs) * trem * np.exp(-t * 0.9) * 0.6


def pluck(f, n):
    t = np.arange(n) / SR
    x = saw(f, n) * np.exp(-t * 9)
    return lp(x, 5000) * 0.5


def vinyl(rng, n):
    x = lp(rng.normal(0, 1, (n, 2)), 3000) * 0.012
    pops = (rng.random((n, 2)) < 0.00012) * rng.normal(0, 0.25, (n, 2))
    return x + lp(pops, 4000)


# ---------------------------------------------------------------- 编排
def build(preset, bpm, intro, drop, outro, key, seed):
    rng = np.random.default_rng(seed)
    beat = 60.0 / bpm
    bar = beat * 4
    bars = intro + drop + outro
    tail = 1.6  # 结尾留的余音
    dur = bars * bar + tail
    N = int(dur * SR)
    drums = np.zeros((N, 2))
    music = np.zeros((N, 2))
    fx = np.zeros((N, 2))
    root = NOTE[key.upper()] - 9  # 相对 A
    prog = PROG[preset]
    t_drop = intro * bar
    swing = 0.12 if preset == "lofi" else 0.0
    K = kick(1.0 if preset != "lofi" else 0.7)
    side = np.ones(N)  # 侧链：底鼓一响，和声让一下，听起来更「泵」

    for b in range(bars):
        t0 = b * bar
        chord = [hz(root + s - 12) for s in prog[b % len(prog)]]
        in_drop = intro <= b < intro + drop
        is_outro = b >= intro + drop
        # ---- 和声
        if b < intro:  # 前奏：闷着的铺底，听得出是「还没开始」
            n = int(bar * SR)
            pad = supersaw(chord, n, 700 if preset != "lofi" else 1200, rng=rng) if preset != "lofi" else epiano(chord, n)
            place(music, pad * env(n, a=0.25, hold=bar - 0.1, r=0.1), t0, 0.55)
        elif in_drop:
            if preset == "house":  # 和弦短促的切分节奏
                for st, ln in ((0, 0.5), (1.5, 0.5), (2.5, 0.5), (3.5, 0.4)):
                    n = int(ln * beat * SR)
                    place(music, supersaw(chord, n, 5200, rng=rng) * env(n, a=0.004, hold=ln * beat * 0.8, r=0.03), t0 + st * beat, 0.6)
            elif preset == "pop":
                n = int(bar * SR)
                place(music, supersaw(chord, n, 4200, 0.08, rng) * env(n, a=0.02, hold=bar - 0.05, r=0.05), t0, 0.35)
                for k in range(8):  # 合成器拨弦琶音
                    f = chord[(k * 3) % len(chord)] * 2
                    place(music, pluck(f, int(0.4 * SR)), t0 + k * beat / 2, 0.35, pan=0.4 if k % 2 else -0.4)
            else:  # lofi
                n = int(bar * SR)
                place(music, epiano(chord, n), t0, 0.7)
            # 贝斯
            bn = int(beat * 0.45 * SR)
            if preset == "house":
                hits = [k * beat + beat / 2 for k in range(4)]  # 反拍贝斯
            elif preset == "pop":
                hits = [k * beat / 2 for k in range(8)]
            else:
                hits = [0, beat * 1.5, beat * 2.5]
            for h in hits:
                f = chord[0] / 2
                tt = np.arange(bn) / SR
                bass = np.tanh(1.5 * (np.sin(2 * np.pi * f * tt) + 0.3 * saw(f, bn))) * env(bn, a=0.003, hold=beat * 0.38, r=0.04)
                place(music, lp(bass, 420), t0 + h, 0.16)
        elif is_outro:  # 结尾：一个长和弦收住
            n = int((bar + tail) * SR)
            x = supersaw(chord, n, 1500, rng=rng) if preset != "lofi" else epiano(chord, n)
            place(music, x * env(n, a=0.01, d=1.2), t0, 0.5)

        # ---- 鼓
        if in_drop:
            for k in range(4):
                if preset == "lofi" and k in (1, 3):
                    place(drums, snare_lofi(rng), t0 + k * beat, 0.55)
                    if k == 3:
                        place(drums, K, t0 + (k + 0.5 + swing) * beat, 0.6)
                    continue
                if preset == "lofi" and k == 2:
                    place(drums, K, t0 + (k + 0.5 + swing) * beat, 0.7)
                    continue
                place(drums, K, t0 + k * beat, 0.95)
                i = int((t0 + k * beat) * SR)
                d = np.arange(int(beat * SR)) / SR
                seg = side[i:i + len(d)]
                seg *= 1 - 0.55 * np.exp(-d * 9)[: len(seg)]
                if preset != "lofi" and k in (1, 3):
                    place(drums, clap(rng), t0 + k * beat, 0.55)
            for k in range(8):
                off = k * beat / 2 + (swing * beat if k % 2 else 0)
                open_ = preset == "house" and k % 2 == 1
                place(drums, hat(rng, open_), t0 + off, 0.5 if k % 2 else 0.35, pan=0.25)
        if b == intro + drop - 1 and preset != "lofi":  # 最后一小节末尾空一拍，让结尾重音更有力
            i0 = int((t0 + 3 * beat) * SR)
            i1 = int((t0 + bar) * SR)
            drums[i0:i1] *= np.linspace(1, 0, i1 - i0)[:, None]

    # ---- 效果：前奏上扬、落点、结尾重音
    if intro:
        r = riser(rng, bar)
        place(fx, r, t_drop - bar, 0.55 if preset != "lofi" else 0.25)
    if preset != "lofi":
        place(fx, crash(rng), t_drop, 0.8)
        place(fx, impact(rng), t_drop, 0.7)
        t_end = (intro + drop) * bar
        place(fx, impact(rng), t_end, 0.8)
        place(fx, crash(rng, 2.8), t_end, 0.7)
        place(drums, K, t_end, 1.0)
    if preset == "lofi":
        music += vinyl(rng, N)

    music *= side[:, None]
    music = reverb(music, 1.6 if preset != "lofi" else 1.1, 0.22)
    fx = reverb(fx, 2.2, 0.3)
    # 总线配比：鼓 / 和声 / 效果（按频段能量调过，低频不压过和声）
    g = {"house": (0.55, 2.6, 0.5), "pop": (0.55, 2.6, 0.5), "lofi": (0.6, 2.0, 0.6)}[preset]
    mix = drums * g[0] + music * g[1] + fx * g[2]
    if preset == "lofi":
        mix = lp(mix, 5200)
    mix = np.tanh(mix * 1.3) / np.tanh(1.3)
    mix /= max(1e-6, np.abs(mix).max()) / 0.89  # -1 dBFS 峰值
    fade = int(0.8 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]

    beats = [round(k * beat, 4) for k in range(bars * 4 + 1)]
    secs = [{"name": "intro", "start": 0.0, "beats": intro * 4}] if intro else []
    secs.append({"name": "drop", "start": round(t_drop, 4), "beats": drop * 4})
    if outro:
        secs.append({"name": "outro", "start": round((intro + drop) * bar, 4), "beats": outro * 4})
    meta = {"preset": preset, "bpm": bpm, "key": key, "beats": beats, "downbeats": beats[::4],
            "drop": round(t_drop, 4), "end_hit": round((intro + drop) * bar, 4), "sections": secs,
            "duration": round(dur, 3), "source": "beatgen（合成，免版权）"}
    return mix, meta


def save_wav(path, x):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("preset", choices=sorted(PROG) + ["french"])
    ap.add_argument("out")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--intro", type=int, default=1)
    ap.add_argument("--drop", type=int, default=4)
    ap.add_argument("--outro", type=int, default=1)
    ap.add_argument("--key", default="C")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mood", default="nostalgic", help="french 用：nostalgic / bright")
    a = ap.parse_args()
    bpm = a.bpm or DEFAULT_BPM[a.preset]
    if a.preset == "french":
        import sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import french
        mix, meta = french.build(a.mood, bpm, a.intro, a.drop, a.outro, a.seed)
    else:
        mix, meta = build(a.preset, bpm, a.intro, a.drop, a.outro, a.key, a.seed)
    save_wav(a.out, mix)
    jp = os.path.splitext(a.out)[0] + ".beats.json"
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"done {a.out} {meta['duration']}s {bpm} BPM，落点 {meta['drop']}s，节拍表 {jp}")


if __name__ == "__main__":
    main()
