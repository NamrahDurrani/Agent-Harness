"""
tts.py  —  AgriBot Text-to-Speech  (Meta MMS-TTS, single engine)
====================================================================
Uses Meta's Massively Multilingual Speech (MMS) TTS for BOTH English and
Urdu — one consistent voice architecture across languages, rather than a
hybrid of two different engines.

    English  -> facebook/mms-tts-eng
    Urdu     -> facebook/mms-tts-urd
    Roman Urdu / mixed -> treated as "ur" (text arrives already converted
                           to native Urdu script by your RAG pipeline's
                           translate_from_english() before it ever reaches
                           this module — see the FastAPI endpoint)

Why MMS for English too (not Kokoro): consistency. A farmer switching
between Urdu and English mid-conversation should hear ONE voice character,
not two different TTS engines with noticeably different tone/pacing. MMS's
Urdu is purpose-built and solid; MMS's English is fully usable, just not
as polished as a dedicated English-only model — a reasonable trade for a
single, simpler, consistent architecture.

Both models load once and stay cached — same lazy-singleton pattern used
throughout this project (vector_store.py, speech_layer.py, language_layer.py).

INSTALL (run once):
    pip install transformers torch soundfile
    (transformers + torch are already installed from STT/translation work)

Each MMS language model is ~150MB — much lighter than Whisper large-v3 or
bge-m3, shouldn't hit the disk-space issues we saw with those.

Test in isolation FIRST with test_tts.py before wiring into api_server.py.
"""

import os
import io
import re
from typing import Optional, Tuple
import numpy as np

# ══════════════════════════════════════════════════════════════════════════════
#  MMS-TTS model loading — one model per language, both lazy-loaded once
# ══════════════════════════════════════════════════════════════════════════════

_MMS_ENG_MODEL = os.environ.get("MMS_ENG_MODEL", "facebook/mms-tts-eng")
# Meta ships Urdu MMS-TTS as 3 separate script-variant checkpoints:
#   facebook/mms-tts-urd-script_arabic       <- correct one for this project
#   facebook/mms-tts-urd-script_devanagari   (Hindi-script Urdu — wrong for us)
#   facebook/mms-tts-urd-script_latin        (romanized — wrong for us)
# Our pipeline always produces native Urdu in ARABIC script (that's what
# translate_from_english() outputs and what the user reads on screen), so
# script_arabic is the only correct choice — confirmed via find_mms_urdu.py.
_MMS_URD_MODEL = os.environ.get("MMS_URD_MODEL", "facebook/mms-tts-urd-script_arabic")

_models     = {}   # {"en": (model, tokenizer), "ur": (model, tokenizer)}


def _get_mms(lang: str):
    """
    Lazy-load and cache the MMS model+tokenizer for a language.
    lang: "en" | "ur"
    """
    if lang not in _models:
        model_name = _MMS_ENG_MODEL if lang == "en" else _MMS_URD_MODEL
        print(f"[TTS] Loading MMS-TTS '{model_name}' ({lang}) "
              f"— first run downloads ~150MB, then cached...")
        from transformers import VitsModel, AutoTokenizer
        model     = VitsModel.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model.eval()
        _models[lang] = (model, tokenizer)
        print(f"[TTS] MMS-TTS '{lang}' ready.")
    return _models[lang]


def _synthesize(text: str, lang: str) -> Tuple[np.ndarray, int]:
    """Returns (audio_array, sample_rate) for the given language."""
    import torch
    model, tokenizer = _get_mms(lang)
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform
    audio = output.squeeze().cpu().numpy()
    sample_rate = model.config.sampling_rate
    return audio, sample_rate


# ══════════════════════════════════════════════════════════════════════════════
#  Text chunking — long RAG answers need splitting for clean synthesis
# ══════════════════════════════════════════════════════════════════════════════

def _split_long_text(text: str, max_chars: int = 400) -> list:
    """
    Splits long text into sentence-respecting chunks. MMS handles short-
    to-medium text best; a full RAG answer with citations benefits from
    being split into sentence-level chunks and concatenated, rather than
    synthesized as one giant string.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r'(?<=[.!?۔])\s+', text)   # ۔ = Urdu full stop
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) <= max_chars:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks


# ══════════════════════════════════════════════════════════════════════════════
#  Citation-tag cleanup — [1][2] tags shouldn't be read aloud
# ══════════════════════════════════════════════════════════════════════════════

_CITATION_TAG_RE = re.compile(r'\[\d+\]')


def _strip_citation_tags(text: str) -> str:
    """Remove [1][2] style inline citation tags before speaking — they're
    visual-only artifacts from the sources panel, meaningless read aloud."""
    return _CITATION_TAG_RE.sub('', text).strip()


# ══════════════════════════════════════════════════════════════════════════════
#  TTSService — the class the FastAPI endpoint calls
# ══════════════════════════════════════════════════════════════════════════════

class TTSService:
    """
    Thread-safe-enough for FastAPI's typical usage: both underlying models
    are lazy-loaded once (module-level singletons) and are stateless during
    inference — concurrent requests each get their own local numpy arrays,
    no shared mutable state written during synthesis itself.
    """

    def speak(self, text: str, language: str) -> Tuple[bytes, str]:
        """
        Args:
            text:     the text to speak (may include [1][2] citation tags —
                      these are stripped automatically)
            language: "en" | "ur" | "roman_ur" | "mixed"
                      (matches language_layer.detect_language() output;
                      roman_ur/mixed are treated as "ur" — see module note
                      above on why the text is already native Urdu script
                      by the time it reaches here)

        Returns:
            (wav_bytes, mime_type)

        Raises:
            ValueError  — empty text or unsupported language
            RuntimeError — model failed to load or synthesize
        """
        if not text or not text.strip():
            raise ValueError("Empty text — nothing to speak.")

        clean_text = _strip_citation_tags(text)
        if not clean_text:
            raise ValueError("Text contained only citation tags — nothing to speak.")

        # Normalize language routing — both non-English variants map to "ur"
        if language in ("roman_ur", "mixed"):
            lang = "ur"
        elif language in ("en", "ur"):
            lang = language
        else:
            raise ValueError(f"Unsupported language: {language!r}. "
                             f"Use 'en', 'ur', 'roman_ur', or 'mixed'.")

        chunks = _split_long_text(clean_text)
        audio_parts = []
        sr = 16000
        for chunk in chunks:
            audio, sr = _synthesize(chunk, lang)
            audio_parts.append(audio)
        full_audio = np.concatenate(audio_parts)

        wav_bytes = _to_wav_bytes(full_audio, sr)
        return wav_bytes, "audio/wav"


def _to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Convert a numpy float audio array to WAV bytes in memory (no temp file)."""
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV")
    buf.seek(0)
    return buf.read()


# Module-level singleton — same pattern as get_pipeline() in api_server.py
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


def warm_up():
    """
    Optional: call at server startup to pre-load both language models
    instead of paying the load cost on the first real request.
    """
    for lang in ("en", "ur"):
        try:
            _get_mms(lang)
        except Exception as e:
            print(f"[TTS] Warm-up failed for '{lang}' (will retry lazily): {e}")
