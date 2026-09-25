"""Voice message -> text (faster-whisper). Usage: python stt.py <audio file>  (prints text)
Runs with KOKORO_PYTHON's environment if you keep GPU libs there; otherwise pip install faster-whisper."""
import sys

from faster_whisper import WhisperModel

model = WhisperModel("small", device="auto", compute_type="int8")
segs, _ = model.transcribe(sys.argv[1], language=None)
print(" ".join(s.text.strip() for s in segs))
