#!/usr/bin/env python3
"""
test_speech_layer.py  —  Standalone STT validation, no server needed
========================================================================
Usage:
    python test_speech_layer.py path\\to\\your\\audio.wav
    python test_speech_layer.py path\\to\\your\\audio.wav ur   # force Urdu

Record a few short test clips on your phone (voice memo app is fine):
    1. English: "What diseases affect wheat in Punjab"
    2. Urdu: same question, spoken in Urdu
    3. Roman-Urdu-accented English: however you'd naturally ask it

Transfer them to this folder (any format: .wav, .mp3, .m4a, .webm all work
— faster-whisper decodes via ffmpeg internally) and run this script on each.
"""

import sys
from speech_layer import transcribe_audio


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_speech_layer.py <audio_file> [language_hint]")
        print("Example: python test_speech_layer.py my_recording.wav")
        print("Example: python test_speech_layer.py my_recording.wav ur")
        sys.exit(1)

    audio_path = sys.argv[1]
    lang_hint  = sys.argv[2] if len(sys.argv) > 2 else None

    print("\n" + "=" * 60)
    print("  Speech Layer — Standalone STT Test")
    print("=" * 60)
    print(f"  File: {audio_path}")
    print(f"  Language hint: {lang_hint or '(auto-detect)'}")
    print()

    result = transcribe_audio(audio_path, language_hint=lang_hint)

    print("\n" + "-" * 60)
    print(f"  Detected language : {result['language']}")
    print(f"  Confidence        : {result['confidence']}  (closer to 0 is better)")
    print(f"  Audio duration    : {result['duration']}s")
    print(f"  Transcribed text  :")
    print(f"    {result['text']}")
    print("-" * 60)
    print("\n  Compare the transcribed text against what you actually said.")
    print("  If accuracy is poor, try a larger model:")
    print('    $env:WHISPER_MODEL = "large-v3"')
    print("    python test_speech_layer.py " + audio_path)
    print()


if __name__ == "__main__":
    main()
