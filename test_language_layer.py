#!/usr/bin/env python3
"""
test_language_layer.py  —  Standalone validation (v2, LLM-based)
====================================================================
Run this FIRST, before testing through the actual chat.

Uses your existing Groq LLM client (same as rag_pipeline.py) — no NLLB,
no transformers/torch, no separate model download. Just needs GROQ_API_KEY.

Usage:
    $env:GROQ_API_KEY = "gsk_..."
    python test_language_layer.py
"""

import os
from language_layer import (
    detect_language, normalize_roman_urdu,
    translate_to_english, translate_from_english,
)

TEST_CASES = [
    ("English",
     "What diseases affect wheat in Punjab?"),
    ("Native Urdu",
     "پنجاب میں گندم کو کون سی بیماریاں متاثر کرتی ہیں؟"),
    ("Roman Urdu",
     "gehun mein zang ki bemari ka ilaj kya hai"),
    ("Roman Urdu (weather)",
     "kal Lahore mein gehun ki kasht ke liye mausam kaisa hai"),
    ("Mixed Urdu-English",
     "wheat ki فصل میں rust disease کا علاج کیا ہے"),
]


def get_llm_client():
    """Build the same Groq client rag_pipeline.py uses."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set.")
        print('  $env:GROQ_API_KEY = "gsk_..."')
        raise SystemExit(1)
    from groq import Groq
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    class SimpleClient:
        def __init__(self):
            self.client = Groq(api_key=api_key)
        def call(self, system_prompt, user_prompt, max_tokens=512, temperature=0.1):
            resp = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}],
                max_tokens=max_tokens, temperature=temperature,
            )
            text = resp.choices[0].message.content.strip()
            usage = {"prompt_tokens": resp.usage.prompt_tokens,
                     "completion_tokens": resp.usage.completion_tokens,
                     "total_tokens": resp.usage.total_tokens}
            return text, usage
    return SimpleClient()


def main():
    print("\n" + "=" * 70)
    print("  Language Layer — Standalone Test (v2, LLM-based)")
    print("=" * 70)

    llm = get_llm_client()

    for label, text in TEST_CASES:
        print(f"\n── {label} ──────────────────────────────────────")
        print(f"  Input:      {text}")

        detected = detect_language(text)
        print(f"  Detected:   {detected}")

        if detected == "roman_ur":
            normalized = normalize_roman_urdu(text)
            print(f"  Pre-pass:   {normalized}")

        translated = translate_to_english(text, detected, llm)
        print(f"  -> English: {translated}")

        if detected != "en":
            fake_answer = ("DIRECT ANSWER: Yellow rust is the most common "
                           "wheat disease in Punjab.[1]")
            back = translate_from_english(fake_answer, detected, llm)
            print(f"  <- Back:    {back}")

    print("\n" + "=" * 70)
    print("  Done. Check the Urdu output above for Hindi-word contamination.")
    print("  If you spot Hindi vocabulary instead of Urdu, tell me which")
    print("  words — I'll tighten the translation prompt further.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()