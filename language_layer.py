"""
language_layer.py  —  AgriBot Multilingual Text Layer  (v2 — LLM-based)
==========================================================================
Stage 3-5-10 of the Multilingual Voice Agentic RAG doc, text-only.

CHANGED FROM v1: NLLB-200 removed entirely.
  - No transformers/torch dependency, no 2.4GB download, no pipeline()
    task-registry version issues.
  - Translation now uses your existing Groq LLM (Llama 3.3 70B) via the
    same client the RAG pipeline already has loaded — one model doing
    everything, zero extra install.
  - Fixes the Hindi-word contamination problem: the translation prompt
    explicitly instructs pure Urdu (Persian/Arabic-origin vocabulary,
    Arabic script) and forbids Hindi/Sanskrit-derived words, which NLLB
    had no mechanism to control at all.

Functions:
    detect_language(text)                        → "en" | "ur" | "roman_ur" | "mixed"
    normalize_roman_urdu(text)                    → dictionary term substitution
    translate_to_english(text, lang, llm_client)  → English string for RAG
    translate_from_english(text, lang, llm_client)→ back to Urdu for the farmer

llm_client is the SAME object rag_pipeline.py already builds (self.llm) —
no new API key, no new client, no separate config needed.
"""

import re
from typing import Optional

# ══════════════════════════════════════════════════════════════════════════════
#  Language Detection  (Stage 3) — unchanged from v1, no model needed
# ══════════════════════════════════════════════════════════════════════════════

_URDU_SCRIPT_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')

_ROMAN_URDU_SIGNAL_WORDS = {
    "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "main", "aur",
    "kya", "kaise", "kab", "kahan", "kyun", "nahi", "nahin", "ap", "aap",
    "mera", "mujhe", "hum", "unka", "iska", "uska",
    "gehun", "gandum", "kheti", "fasal", "zameen", "pani", "beej", "khad",
    "zang", "keeda", "keere", "spray", "dawa", "mausam", "barish",
    "kisan", "zarai", "phasal", "sona", "chawal", "makai", "kapas",
    "ganna", "aalu", "tamatar", "sabzi", "phal", "bagh",
}


def detect_language(text: str) -> str:
    """Returns one of: "en", "ur", "roman_ur", "mixed"."""
    text = text.strip()
    if not text:
        return "en"

    urdu_chars  = len(_URDU_SCRIPT_RE.findall(text))
    total_chars = max(len(re.sub(r'\s', '', text)), 1)
    urdu_ratio  = urdu_chars / total_chars

    words = re.findall(r"[a-zA-Z]+", text.lower())
    roman_hits  = sum(1 for w in words if w in _ROMAN_URDU_SIGNAL_WORDS)
    roman_ratio = roman_hits / max(len(words), 1)

    if urdu_ratio > 0.5:
        return "ur"
    if urdu_ratio > 0.15:
        return "mixed"
    if roman_ratio > 0.15 and len(words) >= 2:
        return "roman_ur"
    return "en"


# ══════════════════════════════════════════════════════════════════════════════
#  Roman Urdu Normalization  (Stage 4) — unchanged, still useful as a
#  cheap pre-pass before the LLM sees the text (helps retrieval keywords)
# ══════════════════════════════════════════════════════════════════════════════

ROMAN_URDU_DICT = {
    "gehun": "wheat", "gandum": "wheat", "chawal": "rice", "makai": "maize",
    "kapas": "cotton", "ganna": "sugarcane", "aalu": "potato",
    "tamatar": "tomato", "pyaz": "onion", "channa": "chickpea",
    "masoor": "lentil", "sarson": "mustard", "amrud": "guava", "aam": "mango",
    "kheti": "farming", "fasal": "crop", "phasal": "crop",
    "zameen": "land", "beej": "seed", "khad": "fertilizer",
    "keeda": "pest", "keere": "insects", "zang": "rust disease",
    "bemari": "disease", "dawa": "medicine/pesticide", "spray": "spray",
    "sinchai": "irrigation", "pani": "water", "mausam": "weather",
    "barish": "rain", "garmi": "heat", "sardi": "cold",
    "kisan": "farmer", "zarai": "agricultural", "bagh": "orchard",
    "sabzi": "vegetable", "phal": "fruit",
}

_ROMAN_URDU_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in sorted(ROMAN_URDU_DICT, key=len, reverse=True)) + r')\b',
    re.IGNORECASE,
)


def normalize_roman_urdu(text: str) -> str:
    """Best-effort Roman Urdu -> English keyword substitution (unchanged)."""
    def _sub(m):
        word = m.group(1).lower()
        return ROMAN_URDU_DICT.get(word, m.group(1))
    return _ROMAN_URDU_PATTERN.sub(_sub, text)


# ══════════════════════════════════════════════════════════════════════════════
#  LLM-based Translation  (Stage 5 + Stage 10) — replaces NLLB entirely
# ══════════════════════════════════════════════════════════════════════════════

_TO_ENGLISH_SYSTEM = (
    "You are a precise translator. Translate the user's text into clear, "
    "natural English. The text may be Urdu (Arabic script), Roman Urdu "
    "(Urdu written in Latin letters), or a mix of Urdu and English. "
    "It is about agriculture (crops, farming, pests, weather, irrigation).\n\n"
    "RULES:\n"
    "1. Output ONLY the English translation. No explanation, no notes, "
    "no quotation marks.\n"
    "2. Preserve agricultural terminology precisely (crop names, disease "
    "names, place names like Lahore, Punjab, Sindh).\n"
    "3. If the text is already in English, return it unchanged."
)

# FIX for Hindi-word contamination: explicit instruction to use pure Urdu
# vocabulary (Persian/Arabic-origin words), not Hindi/Sanskrit-origin words
# that sound similar but are technically Hindi, not Urdu. This is the exact
# problem you saw — the model needs to be told this directly, it won't
# infer "pure Urdu only" on its own.
_FROM_ENGLISH_TO_URDU_SYSTEM = (
    "You are a precise translator specializing in PURE URDU (not Hindi).\n\n"
    "Translate the user's English text into natural, standard Urdu using "
    "Arabic script.\n\n"
    "CRITICAL RULES:\n"
    "1. Use ONLY authentic Urdu vocabulary — words of Persian, Arabic, or "
    "Turkic origin, as used in Pakistani Urdu newspapers and formal writing.\n"
    "2. Do NOT use Hindi words or Sanskrit-derived vocabulary, even if they "
    "sound similar to Urdu. For example, use standard Urdu agricultural "
    "and everyday vocabulary, not Hindi equivalents.\n"
    "3. Write entirely in Arabic script (اردو رسم الخط), never Devanagari.\n"
    "4. Preserve crop names, disease names, and place names accurately.\n"
    "5. Output ONLY the Urdu translation. No English, no explanation, "
    "no transliteration, no quotation marks.\n"
    "6. Keep any [1] [2] [3] style citation numbers exactly as they appear "
    "in the original text — do not translate or remove them.\n"
    "7. Every single character in your output must be either: Urdu (Arabic "
    "script), an ASCII digit, or basic punctuation (.,!?():-[]/%). NEVER "
    "output Chinese, Japanese, Korean, or Cyrillic characters under any "
    "circumstances, even for a technical term or code you're unsure how to "
    "translate — if unsure, use the closest plain Urdu phrasing instead, or "
    "transliterate the term into Urdu script rather than leaving it or any "
    "part of it in another script."
)

_FROM_ENGLISH_TO_URDU_RETRY_SUFFIX = (
    "\n\n8. IMPORTANT: A previous attempt at this exact translation "
    "accidentally included characters from Chinese, Japanese, Korean, or "
    "Cyrillic scripts. This is strictly forbidden and must not happen "
    "again. Translate carefully — every character must be Urdu script, a "
    "digit, or basic punctuation, with absolutely nothing from any other "
    "script."
)

# Detects stray CJK / Hangul / Cyrillic characters that occasionally slip
# into a Groq-generated Urdu translation — this is the exact failure mode
# seen in production (e.g. "普ائش", "相対ی", "инфекیشن"): the model
# briefly drifts into the wrong script mid-word while translating long,
# technical, citation-heavy text. Not an NLLB artifact — this project
# doesn't use NLLB; it's an LLM generation-degeneration issue, so the fix
# has to be a deterministic post-generation check, not just prompt wording.
_SCRIPT_CONTAMINATION_RE = re.compile(
    r'[\u4E00-\u9FFF\u3400-\u4DBF'   # CJK Unified Ideographs (Chinese)
    r'\u3040-\u30FF'                  # Hiragana + Katakana (Japanese)
    r'\uAC00-\uD7AF'                  # Hangul (Korean)
    r'\u0400-\u04FF]'                 # Cyrillic
)


def _has_script_contamination(text: str) -> bool:
    return bool(_SCRIPT_CONTAMINATION_RE.search(text))


def _strip_script_contamination(text: str) -> str:
    """Last-resort cleanup if even the stricter retry still contaminates —
    removes the stray characters rather than ever shipping them to the
    user. A missing character or two reads far better than visible
    mid-word garbage like '普ائش' or '相対ی'."""
    return _SCRIPT_CONTAMINATION_RE.sub('', text)


def _llm_translate(text: str, system_prompt: str, llm_client, max_tokens: int = 700) -> str:
    """Call the shared Groq LLM client for a translation pass."""
    if not text.strip():
        return text
    if llm_client is None:
        print("[LANG] No llm_client provided — returning text untranslated.")
        return text
    try:
        translated, _usage = llm_client.call(
            system_prompt, text, max_tokens=max_tokens, temperature=0.1
        )
        return translated.strip().strip('"').strip()
    except Exception as e:
        print(f"[LANG] LLM translation failed: {e}")
        return text   # fail open — never crash the pipeline over a translation error


def translate_to_english(text: str, detected_lang: str, llm_client) -> str:
    """
    Prepare non-English text for the RAG pipeline.
    detected_lang == "en" → unchanged.
    Otherwise → Roman Urdu dictionary pre-pass (cheap, helps keywords),
    then LLM translation to English for retrieval + generation.
    """
    if detected_lang == "en":
        return text

    # Cheap pre-pass for Roman Urdu / mixed: swap known ag terms first.
    # This helps even after LLM translation, since it primes obvious
    # keywords the LLM might otherwise leave ambiguous.
    working_text = text
    if detected_lang in ("roman_ur", "mixed"):
        working_text = normalize_roman_urdu(text)

    return _llm_translate(working_text, _TO_ENGLISH_SYSTEM, llm_client)


def translate_from_english(text: str, detected_lang: str, llm_client) -> str:
    """
    Translate the LLM's English answer back into the farmer's language.
    All non-English cases translate to NATIVE URDU SCRIPT (most accessible
    and avoids the ambiguity of romanized output).

    Includes a deterministic safety net against script contamination
    (stray Chinese/Japanese/Korean/Cyrillic characters the model
    occasionally produces on long, technical, citation-heavy text): if
    detected, retries once with a stricter prompt; if it still happens,
    strips the offending characters rather than ever shipping garbage.
    """
    if detected_lang == "en":
        return text

    translated = _llm_translate(text, _FROM_ENGLISH_TO_URDU_SYSTEM, llm_client, max_tokens=900)

    if _has_script_contamination(translated):
        print("[LANG] Script contamination detected in Urdu translation — retrying once with a stricter prompt")
        translated = _llm_translate(
            text, _FROM_ENGLISH_TO_URDU_SYSTEM + _FROM_ENGLISH_TO_URDU_RETRY_SUFFIX,
            llm_client, max_tokens=900,
        )

    if _has_script_contamination(translated):
        print("[LANG] Script contamination persisted after retry — stripping contaminated characters as a last resort")
        translated = _strip_script_contamination(translated)

    return translated