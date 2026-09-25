"""Kokoro-82M TTS. Usage: python voice.py <out_dir> <voice> <speed> "<text 0>" "<text 1>" ...   (text may be "")
Writes vo_NN.wav (24 kHz) and voice.json with word timings [[word, start, end], ...] per slide.
reel.py calls this with KOKORO_PYTHON (a separate env with kokoro installed) if set, else the current Python."""
import json, os, sys
from pathlib import Path


def main():
    out, voice, speed, texts = Path(sys.argv[1]), sys.argv[2], float(sys.argv[3]), sys.argv[4:]
    os.environ.setdefault("HF_HUB_OFFLINE", "0")
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a" if voice[0] == "a" else "b")
    result = []
    for i, text in enumerate(texts):
        if not text.strip():
            result.append({"words": [], "dur": 0})
            continue
        audio, words, t0 = [], [], 0.0
        for gs, ps, chunk in pipe(text, voice=voice, speed=speed, split_pattern=r"\n+"):
            chunk = chunk.cpu().numpy() if hasattr(chunk, "cpu") else np.asarray(chunk)
            toks = getattr(gs, "tokens", None) or []
            for tk in toks:
                if getattr(tk, "start_ts", None) is not None and getattr(tk, "end_ts", None) is not None and tk.text.strip():
                    words.append([tk.text, t0 + tk.start_ts, t0 + tk.end_ts])
            audio.append(chunk)
            t0 += len(chunk) / 24000
        wav = np.concatenate(audio)
        sf.write(out / f"vo_{i:02d}.wav", wav, 24000)
        if not words:  # no token timings: spread evenly
            ws = text.split()
            words = [[w, t0 * k / len(ws), t0 * (k + 1) / len(ws)] for k, w in enumerate(ws)]
        result.append({"words": words, "dur": t0})
    (out / "voice.json").write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    main()
