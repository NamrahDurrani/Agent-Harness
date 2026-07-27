#!/usr/bin/env python3
"""
find_mms_urdu.py  —  Diagnostic: find the correct MMS-TTS Urdu repo ID
==========================================================================
The "facebook/mms-tts-urd" guess failed with "not a valid model identifier".
This script queries the HuggingFace Hub search API directly to find every
MMS-TTS repo that mentions Urdu, so we get the EXACT correct ID instead of
guessing again.

Usage:
    python find_mms_urdu.py
"""

from huggingface_hub import HfApi

api = HfApi()

print("\n" + "=" * 60)
print("  Searching HuggingFace Hub for MMS-TTS Urdu models")
print("=" * 60)

print("\n[1] Searching 'facebook/mms-tts' models containing 'urd'...")
try:
    models = api.list_models(author="facebook", search="mms-tts-urd", limit=20)
    found = list(models)
    if found:
        for m in found:
            print(f"    FOUND: {m.id}")
    else:
        print("    No exact match for 'mms-tts-urd'")
except Exception as e:
    print(f"    Search failed: {e}")

print("\n[2] Broader search: 'mms-tts' models mentioning 'urdu'...")
try:
    models = api.list_models(search="mms-tts urdu", limit=20)
    found = list(models)
    if found:
        for m in found:
            print(f"    FOUND: {m.id}")
    else:
        print("    No matches")
except Exception as e:
    print(f"    Search failed: {e}")

print("\n[3] Checking if 'facebook/mms-tts' (base, no suffix) exists...")
try:
    info = api.model_info("facebook/mms-tts")
    print(f"    EXISTS: facebook/mms-tts")
    print(f"    This may be a multi-language checkpoint — check its model card")
    print(f"    at https://huggingface.co/facebook/mms-tts for the Urdu language code")
except Exception as e:
    print(f"    Not found or error: {e}")

print("\n[4] Testing common Urdu language code variants directly...")
candidates = [
    "facebook/mms-tts-urd",
    "facebook/mms-tts-urd-script_arabic",
    "facebook/mms-tts-ur",
    "facebook/mms-tts-urd-script_devanagari",
]
for candidate in candidates:
    try:
        info = api.model_info(candidate)
        print(f"    OK EXISTS: {candidate}")
    except Exception as e:
        err_type = type(e).__name__
        print(f"    NO  {candidate}  ({err_type})")

print("\n" + "=" * 60)
print("  Done. Use whichever repo ID above showed EXISTS/FOUND.")
print("  If NONE were found, open this in your browser:")
print("    https://huggingface.co/models?search=mms-tts-urd")
print("  and copy the exact repo ID shown there.")
print("=" * 60 + "\n")