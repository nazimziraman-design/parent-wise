"""Voice message -> text (faster-whisper, multilingual 'small' model, Turkish by default).
Usage: python stt.py <audio file>  -> prints the transcript.  Also importable: transcribe(path)."""
import sys

_MODEL = None


def _load():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("small", device="cpu", compute_type="int8")  # CPU int8: plenty fast for short voice notes, no CUDA libs needed
    return _MODEL


def transcribe(path, language="tr"):
    # a hint about our vocabulary keeps product words and platform names spelled right
    prompt = "Parent Wise, Instagram, TikTok, Reel, carousel, tara, adayları göster, yayınla, reddet, revize, klip, viral."
    segs, _ = _load().transcribe(str(path), language=language, initial_prompt=prompt, vad_filter=True, beam_size=5)
    return " ".join(s.text.strip() for s in segs).strip()


if __name__ == "__main__":
    print(transcribe(sys.argv[1]))
