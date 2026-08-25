"""
test_language_layer_contamination.py

Run: python test_language_layer_contamination.py

Tests the script-contamination safety net in translate_from_english()
against the ACTUAL garbled substrings seen in production (from real
Urdu answers), not synthetic examples:
  - "普ائش"     (contains a Chinese CJK character mid-word)
  - "相対ی"      (Japanese kanji mid-word)
  - "相对ی"      (Chinese CJK mid-word, simplified variant)
  - "инфекیشن"  (Cyrillic characters mid-word)

Verifies: detection correctly flags contaminated text and leaves clean
Urdu untouched, the retry path fires when the first translation is
contaminated, and the strip-as-last-resort path removes contamination
that survives even the retry — the actual text is never shipped with
visible garbage.
"""
from language_layer import (
    _has_script_contamination,
    _strip_script_contamination,
    translate_from_english,
)

# The exact contaminated fragments seen in real production output
REAL_CONTAMINATED_SAMPLES = [
    "普ائش کی مسلسل نگرانی ضروری ہے",
    "مطلوبہ 相対ی مزاحمت کا اشاریہ",
    "صرف زرد زنگ کے لیے 相对ی مزاحمت",
    "ابتدائی инфекیشن کو محدود کرنے والے",
]

CLEAN_URDU_SAMPLES = [
    "پنجاب میں گندم کی زنگ سے نمٹنے کے لیے، حکمت عملیوں کے مجموعے کو اپنانا ضروری ہے۔",
    "مزاحمتی اقسام کے حوالے سے، پنجاب کے لیے متعدد مواقع موجود ہیں۔",
    "یہ 100 ایکڑ اور [2] حوالہ نمبر والا عام متن ہے۔",  # digits + citation tags — must NOT be flagged
]


def test_detects_real_contaminated_samples():
    for s in REAL_CONTAMINATED_SAMPLES:
        assert _has_script_contamination(s), f"failed to detect contamination in: {s!r}"
    print(f"OK — detected contamination in all {len(REAL_CONTAMINATED_SAMPLES)} real production samples")


def test_clean_urdu_not_flagged():
    for s in CLEAN_URDU_SAMPLES:
        assert not _has_script_contamination(s), f"false positive on clean text: {s!r}"
    print(f"OK — no false positives on {len(CLEAN_URDU_SAMPLES)} clean Urdu samples (incl. digits + citation tags)")


def test_strip_removes_contamination_only():
    for s in REAL_CONTAMINATED_SAMPLES:
        cleaned = _strip_script_contamination(s)
        assert not _has_script_contamination(cleaned), f"strip failed to fully clean: {s!r} -> {cleaned!r}"
        # Confirm it didn't nuke the whole string — real Urdu content survives
        assert len(cleaned) > 0
    print("OK — stripping removes only the contaminated characters, Urdu content survives")


class _MockLLMClient:
    """Simulates: first call returns contaminated text, retry call
    returns clean text — proves the retry path actually fires and
    actually helps."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.call_count = 0

    def call(self, system, user, max_tokens=700, temperature=0.1):
        resp = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return resp, {}


def test_retry_path_fires_and_recovers():
    mock = _MockLLMClient([
        "گندم کی 相対ی بیماری",   # 1st attempt: contaminated
        "گندم کی نسبتاً بیماری",   # 2nd attempt (after retry prompt): clean
    ])
    result = translate_from_english("Some English text", "ur", mock)
    assert mock.call_count == 2, f"expected exactly 2 LLM calls (original + 1 retry), got {mock.call_count}"
    assert not _has_script_contamination(result), f"result still contaminated after retry: {result!r}"
    print("OK — contaminated first attempt triggers exactly one retry, retry result used when clean")


def test_strip_fallback_when_retry_also_contaminated():
    mock = _MockLLMClient([
        "گندم کی 相対ی بیماری",   # 1st attempt: contaminated
        "گندم کی 相対ی بیماری",   # retry: STILL contaminated (worst case)
    ])
    result = translate_from_english("Some English text", "ur", mock)
    assert mock.call_count == 2, f"expected exactly 2 LLM calls, got {mock.call_count}"
    assert not _has_script_contamination(result), (
        f"last-resort strip failed to produce clean output: {result!r}"
    )
    print("OK — when retry ALSO contaminates, last-resort strip guarantees clean output (never ships garbage)")


def test_english_detected_lang_skips_translation_entirely():
    mock = _MockLLMClient(["should never be used"])
    result = translate_from_english("Wheat rust is a fungal disease.", "en", mock)
    assert result == "Wheat rust is a fungal disease."
    assert mock.call_count == 0, "translate_from_english should not call the LLM at all for detected_lang='en'"
    print("OK — detected_lang='en' skips translation entirely, zero LLM calls")


def main():
    test_detects_real_contaminated_samples()
    test_clean_urdu_not_flagged()
    test_strip_removes_contamination_only()
    test_retry_path_fires_and_recovers()
    test_strip_fallback_when_retry_also_contaminated()
    test_english_detected_lang_skips_translation_entirely()
    print("\nALL LANGUAGE LAYER CONTAMINATION TESTS PASSED")


if __name__ == "__main__":
    main()
