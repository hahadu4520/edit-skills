"""测节拍：给一首现成的歌（剪映曲库、买的版权音乐），测出 BPM 和每一拍的时间，输出和 beatgen 一样的节拍表。

用法：
  python beats.py <歌.mp3|wav|m4a> [--start 秒] [--dur 秒] [--bpm 已知的BPM] [--drop 秒]
输出：<歌>.beats.json，格式见 beatgen.py。
  --start / --dur：只用歌里的这一段（开头模板通常 10–15 秒）；节拍表时间从 --start 起算。
  --bpm：知道 BPM 就填，只测相位，最准。
  --drop：落点（鼓进来那一下）在这段里的秒数；不填就找能量突然变大的那一拍。

只用 numpy + ffmpeg。测法：频谱通量做起音曲线 → 自相关找节拍周期 → 扫相位让拍点压在起音上 → 低频能量最大的那一路当小节第一拍。
"""
import argparse, json, os, subprocess
import numpy as np

SR = 22050
HOP = 256


def load(path, start, dur):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", str(start)] + (["-t", str(dur)] if dur else []) + \
          ["-i", os.path.expanduser(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def onset_env(x):
    n = 2048
    win = np.hanning(n).astype(np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(x, (n // 2, n // 2)), n)[::HOP] * win
    S = np.abs(np.fft.rfft(frames, axis=1))
    S = np.log1p(100 * S)
    flux = np.maximum(np.diff(S, axis=0, prepend=S[:1]), 0)
    f = np.fft.rfftfreq(n, 1 / SR)
    full = flux.sum(1)
    low = flux[:, f < 160].sum(1)
    def norm(v):
        v = v - np.convolve(v, np.ones(16) / 16, "same")
        v = np.maximum(v, 0)
        return v / (v.max() + 1e-9)
    return norm(full), norm(low)


def tempo(o, lo=70, hi=180, prior=118):
    fps = SR / HOP
    ac = np.correlate(o, o, "full")[len(o) - 1:]
    lags = np.arange(len(ac))
    bpms = 60 * fps / np.maximum(lags, 1)
    ok = (bpms >= lo) & (bpms <= hi)
    # 偏好常见的中速，避免测成一半或两倍
    w = np.exp(-0.5 * (np.log2(bpms / prior) / 0.9) ** 2)
    score = np.where(ok, ac * w, -np.inf)
    lag = int(np.argmax(score))
    # 在峰附近做抛物线插值，拿到小数拍长
    if 1 <= lag < len(ac) - 1:
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        lag = lag + 0.5 * (a - c) / (a - 2 * b + c + 1e-9)
    return 60 * fps / lag


def phase(o, period_f):
    best, bo = -1, 0
    for off in np.arange(0, period_f, 0.25):
        idx = np.arange(off, len(o) - 1, period_f)
        s = np.interp(idx, np.arange(len(o)), o).sum()
        if s > best:
            best, bo = s, off
    return bo


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--dur", type=float)
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--drop", type=float)
    ap.add_argument("--out")
    a = ap.parse_args()
    x = load(a.src, a.start, a.dur)
    dur = len(x) / SR
    full, low = onset_env(x)
    o = full + low
    bpm = a.bpm or tempo(o)
    fps = SR / HOP
    per = 60 * fps / bpm
    # 相位主要按底鼓（低频）对，免得被反拍的镲带偏半拍；先抹宽一点，拍点不用正好压在峰尖上
    sm = np.ones(5) / 5
    off = phase(np.convolve(0.3 * full + low, sm, "same"), per)
    beat = 60 / bpm
    t0 = off / fps
    while t0 - beat >= -0.02:
        t0 -= beat
    beats = [round(max(0.0, t0 + k * beat), 4) for k in range(int((dur - t0) / beat) + 1)]
    # 小节第一拍：4 路相位里低频起音最强的那一路
    lowv = [np.interp(np.array(beats[j::4]) * fps, np.arange(len(low)), low).mean() if beats[j::4] else 0 for j in range(4)]
    j = int(np.argmax(lowv))
    downbeats = beats[j::4]
    # 落点：前后各两拍的能量比最大的那一拍
    if a.drop is not None:
        drop = min(beats, key=lambda b: abs(b - a.drop))
    else:
        # 鼓进来的那一下：之后一小节的起音（打击感）比之前一小节多得最多；上扬是渐强的，不算起音
        def kick(t0_, t1_):
            i0, i1 = int(max(t0_, 0) * fps), int(min(t1_, dur) * fps)
            return full[i0:i1].mean() if i1 > i0 else 0.0
        cands = [b for b in downbeats if b >= 2 * beat and b <= dur - 4 * beat] or downbeats
        drop = max(cands, key=lambda b: kick(b, b + 4 * beat) - kick(b - 4 * beat, b))
    meta = {"bpm": round(bpm, 2), "beats": beats, "downbeats": downbeats, "drop": drop,
            "sections": [{"name": "intro", "start": 0.0}, {"name": "drop", "start": drop}],
            "duration": round(dur, 3), "source": f"beats.py 测自 {os.path.basename(a.src)}（从 {a.start}s 起）"}
    out = a.out or os.path.splitext(a.src)[0] + ".beats.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"done {out}：{bpm:.1f} BPM，第一拍 {beats[0]}s，落点 {drop}s，共 {len(beats)} 拍")


if __name__ == "__main__":
    main()
