"""VAD-split speech and transcribe with SenseVoice (sherpa-onnx). Writes JSON segments with token timestamps.
usage: transcribe.py audio.wav out.json"""
import sys, os, json, wave, numpy as np, sherpa_onnx
D = os.path.dirname(os.path.abspath(__file__)); MD = os.path.join(D, 'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17')
src, out = sys.argv[1:3]
w = wave.open(src); sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)/32768
if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
assert sr == 16000, 'need 16k mono'
rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f'{MD}/model.int8.onnx', tokens=f'{MD}/tokens.txt', language='zh', use_itn=True, num_threads=4)
cfg = sherpa_onnx.VadModelConfig(); cfg.silero_vad.model = os.path.join(D, 'silero_vad.onnx')
cfg.silero_vad.min_silence_duration = 0.25; cfg.silero_vad.min_speech_duration = 0.2; cfg.silero_vad.max_speech_duration = 15; cfg.sample_rate = sr
vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=300)
segs = []
def drain():
    while not vad.empty():
        s = vad.front; st = rec.create_stream(); st.accept_waveform(sr, s.samples); rec.decode_stream(st)
        r = st.result; t0 = s.start/sr
        segs.append(dict(start=round(t0,2), end=round(t0+len(s.samples)/sr,2), text=r.text,
                         tokens=[dict(t=tk, s=round(t0+ts,2)) for tk, ts in zip(r.tokens, r.timestamps)]))
        vad.pop()
win = cfg.silero_vad.window_size
for i in range(0, len(x), win):
    vad.accept_waveform(x[i:i+win]); drain()
vad.flush(); drain()
json.dump(segs, open(out,'w'), ensure_ascii=False, indent=1)
for s in segs: print(f"{s['start']:7.2f}-{s['end']:7.2f} {s['text']}")
