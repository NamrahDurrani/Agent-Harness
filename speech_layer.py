"""
speech_layer.py  —  AgriBot Speech-to-Text  (Stage 2: STT only, no TTS yet)
==============================================================================
Wraps Faster-Whisper for audio -> text transcription. Standalone module —
does NOT touch rag_pipeline.py or api_server.py yet. Test this in isolation
first with test_speech_layer.py before wiring it into the live chat.

INSTALL (run once):
    pip install faster-whisper

MODEL SIZE — pick based on your free disk space (check with Get-PSDrive C):
    tiny    ~75 MB   fastest, lowest accuracy — OK for a first smoke test
    base    ~145 MB
    small   ~490 MB
    medium  ~1.5 GB  good accuracy/size balance
    large-v3 ~3 GB   best accuracy, what the original architecture doc recommends

Set via env var, defaults to "medium" (good balance, reasonable download):
    $env:WHISPER_MODEL = "large-v3"   # upgrade later once everything works
"""

import os
from typing import Optional, Dict

_WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "medium")
_model = None   # lazy-loaded singleton, same pattern as your embedding model


def _get_model():
    global _model
    if _model is None:
        print(f"[STT] Loading Faster-Whisper '{_WHISPER_MODEL_SIZE}' "
              f"(first run downloads the model, then cached)...")
        from faster_whisper import WhisperModel
        _model = WhisperModel(_WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
        print("[STT] Whisper model ready.")
    return _model


# ── Domain vocabulary hint ────────────────────────────────────────────────
# Whisper's initial_prompt parameter biases transcription toward words it
# contains — this is the fix for the "گندم" -> "گنتوں" mis-hearing without
# needing a bigger (and much larger disk footprint) model. Cheap, targeted,
# no download required. Extend this list as you find more mis-transcribed
# agricultural terms during testing.
_URDU_AG_VOCAB_PROMPT = (
    "گندم، فصل، بیماری، زنگ، کیڑا، کھاد، بیج، پانی، آبپاشی، پنجاب، سندھ، "
    "کپاس، چاول، مکئی، گنا، آلو، موسم، بارش، کسان."
)
_EN_AG_VOCAB_PROMPT = (
    "wheat, crop, disease, rust, pest, fertilizer, seed, irrigation, "
    "Punjab, Sindh, cotton, rice, maize, sugarcane, potato, weather, "
    "rainfall, farmer."
)


def transcribe_audio(audio_path: str, language_hint: Optional[str] = None) -> Dict:
    """
    Transcribe an audio file to text.

    Args:
        audio_path:    path to a .wav/.mp3/.m4a/.webm file
        language_hint: optional ISO code ("ur", "en") to bias detection.
                       Leave None to let Whisper auto-detect — it's quite
                       good at this, no need to force it in most cases.

    Returns dict:
        {
            "text":       transcribed text,
            "language":   detected language code (e.g. "ur", "en"),
            "confidence": average log-probability confidence (rough proxy),
            "duration":   audio duration in seconds,
        }
    """
    model = _get_model()

    # Pick the domain vocabulary hint based on language_hint. If no hint
    # given, pass both — Whisper handles a longer prompt fine and this
    # covers the auto-detect case too.
    if language_hint == "ur":
        vocab_prompt = _URDU_AG_VOCAB_PROMPT
    elif language_hint == "en":
        vocab_prompt = _EN_AG_VOCAB_PROMPT
    else:
        vocab_prompt = _URDU_AG_VOCAB_PROMPT + " " + _EN_AG_VOCAB_PROMPT

    segments, info = model.transcribe(
        audio_path,
        language=language_hint,
        beam_size=5,
        vad_filter=True,   # basic built-in VAD — trims silence automatically,
                           # a lightweight version of the Silero VAD stage
                           # from the architecture doc
        initial_prompt=vocab_prompt,
    )

    text_parts = []
    confidences = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        confidences.append(seg.avg_logprob)

    full_text = " ".join(text_parts).strip()
    avg_conf  = sum(confidences) / len(confidences) if confidences else 0.0

    result = {
        "text":       full_text,
        "language":   info.language,
        "confidence": round(avg_conf, 3),
        "duration":   round(info.duration, 2),
    }
    print(f"[STT] '{audio_path}' -> lang={result['language']} "
          f"conf={result['confidence']} dur={result['duration']}s")
    print(f"[STT] Text: {full_text}")
    return result