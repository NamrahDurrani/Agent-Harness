# ═══════════════════════════════════════════════════════════════════════════════
#  TTS — Text-to-Speech  (Stage 3: hybrid Kokoro/English + MMS-TTS/Urdu)
#  Add this block to api_server.py near the other MCP/speech imports,
#  and the endpoint near your other @app.post() routes.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Graceful import — matches the pattern used for speech_layer/mcp_pdf_export ─
try:
    from tts import get_tts_service
    _TTS_AVAILABLE = True
    print("[STARTUP] tts loaded — /api/tts enabled")
except ImportError as e:
    _TTS_AVAILABLE = False
    get_tts_service = None
    print(f"[STARTUP] tts not found — /api/tts disabled ({e})")


class TTSRequest(BaseModel):
    text:     str
    language: str = "en"   # "en" | "ur" | "roman_ur" | "mixed"


@app.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """
    Generate speech audio from text.

    Request:  { "text": "...", "language": "ur" }
    Response: audio/wav bytes (streamed directly, no temp file left behind)

    Routing:
      language == "en"                → Kokoro-82M
      language == "ur"                → MMS-TTS (text must already be
                                          native Urdu script — your RAG
                                          pipeline's translate_from_english()
                                          already produces this)
      language == "roman_ur" | "mixed"→ converted to native Urdu script via
                                          language_layer's translate_from_english()
                                          BEFORE hitting MMS (MMS was never
                                          trained on romanized Urdu — feeding
                                          it Latin-script text produces
                                          garbage audio)

    This endpoint does NOT call the chat pipeline — same separation-of-concerns
    principle as /api/stt. The frontend sends whatever the LAST assistant
    message's language was (which api_server already knows from the chat
    response's language detection) plus the message text.
    """
    if not _TTS_AVAILABLE:
        raise HTTPException(503, "TTS module not loaded on the server — "
                             "check startup logs for tts.py import error.")

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "Empty text — nothing to speak.")

    lang = req.language.lower().strip()

    try:
        # NOTE: by the time text reaches this endpoint, your chat pipeline
        # (rag_pipeline.py's run() wrapper) has ALREADY translated the
        # answer into native Urdu script before returning it to the
        # frontend — that's what the user is reading on screen. So any
        # non-English language value here ("ur", "roman_ur", "mixed") maps
        # to the SAME text-is-already-native-Urdu-script case. No
        # re-translation needed — just route to MMS.
        if lang in ("roman_ur", "mixed"):
            lang = "ur"

        service = get_tts_service()
        wav_bytes, mime_type = service.speak(text, lang)

        return Response(content=wav_bytes, media_type=mime_type)

    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        print(f"[TTS] Synthesis failed: {e}")
        raise HTTPException(500, f"TTS synthesis failed: {e}")
