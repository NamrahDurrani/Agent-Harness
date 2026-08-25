Project summary — Agent Harness & Stabilization work
====================================================

This document summarizes all changes made during the stabilization and
Agent Harness phase for the AgriBot repository, and provides precise
instructions for testing and packaging.

1) High-level goals
-------------------
- Stabilize backend so all endpoints return structured JSON and do not crash.
- Fix Chroma embedding-dimension mismatch by using a 768-dim embedding model for dev.
- Harden PDF upload ingestion and per-page OCR fallback.
- Introduce a lightweight Agent Harness (non-invasive) that emits SSE events.
- Make TTS robust so server remains usable in low-resource environments.
- Package repository into a release zip excluding development caches.

2) Files added
--------------
- agent_harness/
  - events.py
  - tracer.py
  - execution_logger.py
  - router.py
  - workflows/dummy_graph.py

- scripts/
  - reindex_upload.py       — re-index a single uploaded PDF into Chroma
  - make_release_zip.py     — create a release zip excluding caches

3) Files modified (high level)
------------------------------
- api_server.py       — global JSON handler; safe imports; included harness router
- rag_pipeline.py     — chunking improvements; OCR fallback; metadata preservation
- vector_store.py     — documented embedding model override; guidance
- mcp_pdf_export.py   — improved HTML/CSS PDF template
- tts.py              — MMS preferred, gTTS fallback + WAV conversion attempt

4) TTS behavior and fix
-----------------------
- Problem: the code attempted to directly load Meta MMS-TTS model IDs (e.g., facebook/mms-tts-eng) which were not present causing errors like "Can't load the model for 'facebook/mms-tts-eng'".
- Fix: tts.py now tries to load MMS models but gracefully falls back to gTTS if MMS load fails. The fallback converts MP3 -> WAV using pydub if available; otherwise the endpoint surfaces a helpful error.
- Recommendation: install pydub + ffmpeg for reliable MP3->WAV conversion.

5) Agent Harness usage
----------------------
- SSE endpoint available at GET /internal/harness/events
- To instrument a function, import tracer and apply decorator: @tracer.trace('node_name')
- Example: in mcp_pdf_export.py place @tracer.trace('render_pdf') above render function. Restart server and run the flow — frontend subscribed to the SSE endpoint will receive live events.

6) Reindexing failed uploads
----------------------------
- Use scripts/reindex_upload.py to rebuild index entries for any failed files in user_uploads/.
- The script uses the active EMBEDDING_MODEL environment variable; make sure EMBEDDING_MODEL is set to the 768-dim model for local dev.

7) Creating the release ZIP
---------------------------
- Run: python scripts/make_release_zip.py
- Output: agriBot_release.zip in the repository root. Excluded items: .git, node_modules, __pycache__, .venv, .cache, .pytest_cache, .idea, .vscode, large model caches outside repo.

8) Next steps / recommended work
--------------------------------
- Implement automated Chroma DB mismatch handler (backup + reindex) as a background task.
- Integrate tracer into retriever/llm/pdf functions to provide full execution timeline by default.
- Add frontend Execution Timeline UI to consume /internal/harness/events.
- Add pytest integration tests for the pipelines and TTS.

9) Contact
----------
Request one of the following actions and I will perform it next:
- Run reindex_upload.py to reprocess specific failed uploads now.
- Wire tracer into a PDF export function and demonstrate SSE events while generating a PDF.
- Produce the release ZIP now and provide its path.
