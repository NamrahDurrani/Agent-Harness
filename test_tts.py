#!/usr/bin/env python3
"""
test_tts.py  —  Standalone TTS validation, no server needed
================================================================
Usage:
    python test_tts.py

Generates two .wav files in the current folder:
    test_output_english.wav
    test_output_urdu.wav

Play them and listen — this validates MMS-TTS for both languages before
wiring anything into the live API. Since both languages use the SAME
engine now, pay attention to whether the voice CHARACTER sounds
consistent between the two files (that consistency is the whole point
of choosing MMS over a hybrid Kokoro+MMS setup).
"""

from tts import get_tts_service

TEST_CASES = [
    ("English", "en",
     "Yellow rust is the most common wheat disease in Punjab.[1] "
     "It appears as yellow stripes on the leaves and spreads quickly "
     "in cool, humid weather."),
    ("Urdu (native script)", "ur",
     "پیلا زنگ پنجاب میں گندم کی سب سے عام بیماری ہے۔"
     "یہ پتوں پر پیلی دھاریوں کی صورت میں ظاہر ہوتا ہے۔"),
]


def main():
    print("\n" + "=" * 60)
    print("  TTS — Standalone Test (Meta MMS-TTS, single engine)")
    print("=" * 60)

    service = get_tts_service()

    for label, lang, text in TEST_CASES:
        print(f"\n── {label} ──────────────────────────────────────")
        print(f"  Text: {text[:80]}...")
        print(f"  Language: {lang}")

        try:
            wav_bytes, mime = service.speak(text, lang)
            filename = f"test_output_{'english' if lang == 'en' else 'urdu'}.wav"
            with open(filename, "wb") as f:
                f.write(wav_bytes)
            size_kb = len(wav_bytes) // 1024
            print(f"  ✓ Generated {size_kb} KB -> {filename}")
        except Exception as e:
            print(f"  ✗ FAILED: {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print("  Done. Play both .wav files back to back and listen for:")
    print("    - Clear pronunciation, natural pacing")
    print("    - No citation numbers being read aloud")
    print("    - SAME voice character across both languages (this is")
    print("      the point of using one engine instead of two)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
