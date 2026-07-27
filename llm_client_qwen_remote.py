"""
QwenRemoteClient — OpenAI-compatible client for a remote Qwen server
(e.g. ngrok-tunneled transformers serve / vLLM / SGLang).

Speed + reliability improvements over a plain requests.post:
  - Connection timeout separate from read timeout, so a dead tunnel
    fails in ~5s instead of hanging for the default (often 60s+).
  - A requests.Session with connection pooling/keep-alive, so repeated
    calls within one query (rewriter -> orchestrator -> evaluator ->
    generator) reuse the same TCP connection instead of renegotiating
    TLS through ngrok every time -- this alone often saves 200-500ms
    per call.
  - Raises clear, catchable exceptions on connection resets/timeouts
    so the retry wrapper in api_server.py can act on them.
"""

import os
import requests
from typing import Tuple, Dict

QWEN_REMOTE_MODEL = os.environ.get("QWEN_REMOTE_MODEL", "Qwen/Qwen3.5-2B")

# (connect_timeout, read_timeout) in seconds.
# connect: how long to wait for the TCP/TLS handshake (ngrok tunnel up?)
# read:    how long to wait for the model to finish generating
CONNECT_TIMEOUT = float(os.environ.get("QWEN_CONNECT_TIMEOUT", "5"))
READ_TIMEOUT    = float(os.environ.get("QWEN_READ_TIMEOUT", "45"))


class QwenRemoteClient:
    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or QWEN_REMOTE_MODEL
        self.base_url = (base_url or os.environ.get("QWEN_REMOTE_BASE_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError(
                "QWEN_REMOTE_BASE_URL environment variable not set.\n"
                "Set it to your ngrok/server URL, e.g.\n"
                '  $env:QWEN_REMOTE_BASE_URL = "https://xxxx.ngrok-free.app"'
            )
        # Reused session = connection pooling + keep-alive.
        # Meaningfully faster than a fresh requests.post() per call when
        # several LLM calls happen back-to-back for one user query.
        self.session = requests.Session()
        # ngrok intercepts browser-like requests and returns its own HTML
        # warning page unless this header is present. Without it every call
        # gets a 404/HTML response instead of the Qwen API JSON — exactly
        # the "Qwen server returned HTTP 404: <!DOCTYPE html>" error.
        self.session.headers.update({
            "ngrok-skip-browser-warning": "true",
            "Content-Type": "application/json",
        })
        adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=4)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.1,
    ) -> Tuple[str, Dict]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
        except requests.exceptions.ConnectTimeout as exc:
            raise ConnectionError(
                f"Could not reach Qwen server at {self.base_url} within "
                f"{CONNECT_TIMEOUT}s. Is the tunnel/server still running?"
            ) from exc
        except requests.exceptions.ReadTimeout as exc:
            raise TimeoutError(
                f"Qwen server took longer than {READ_TIMEOUT}s to respond. "
                f"Consider lowering max_tokens or increasing QWEN_READ_TIMEOUT."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            # Covers ConnectionResetError(10054) and similar resets —
            # surfaced as a plain ConnectionError so api_server.py's
            # retry wrapper catches it.
            raise ConnectionError(f"Connection to Qwen server was reset: {exc}") from exc

        if resp.status_code != 200:
            raise RuntimeError(
                f"Qwen server returned HTTP {resp.status_code}: {resp.text[:300]}"
            )

        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()

        usage = data.get("usage", {})
        usage_dict = {
            "prompt_tokens":     usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens":      usage.get("total_tokens", 0),
        }
        return text, usage_dict