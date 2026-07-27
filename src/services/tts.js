/**
 * services/tts.js  —  AgriBot TTS playback service
 * =====================================================
 * Handles calling POST /api/tts, caching generated audio by message ID,
 * and the play/pause/resume/stop-previous state machine described in spec:
 *
 *   - Press speaker on a message  -> play
 *   - Press it again while playing -> pause
 *   - Press it again while paused  -> resume
 *   - Press speaker on a DIFFERENT message -> stop current, play new one
 *   - Same message played twice -> reuse cached audio blob, no re-fetch
 *
 * Usage from a component:
 *
 *   import { ttsService } from '../services/tts';
 *
 *   const handleSpeakerClick = async (messageId, text, language) => {
 *     const state = await ttsService.toggle(messageId, text, language);
 *     // state is one of: "playing" | "paused" | "stopped"
 *     setPlaybackState(state);
 *   };
 *
 *   // Subscribe to state changes (e.g. audio finishes naturally):
 *   useEffect(() => {
 *     const unsub = ttsService.onStateChange((messageId, state) => {
 *       // update UI for that specific message's speaker icon
 *     });
 *     return unsub;
 *   }, []);
 */

class TTSService {
  constructor() {
    // Map<messageId, blobUrl> — cached audio, never re-fetched for the
    // same message unless explicitly cleared.
    this._cache = new Map();

    // Currently active <Audio> element and which message it belongs to.
    this._currentAudio = null;
    this._currentMessageId = null;

    // Listeners for playback state changes, keyed by nothing (broadcast) —
    // components filter by messageId themselves.
    this._listeners = new Set();
  }

  onStateChange(callback) {
    this._listeners.add(callback);
    return () => this._listeners.delete(callback);
  }

  _emit(messageId, state) {
    for (const cb of this._listeners) cb(messageId, state);
  }

  /**
   * Main entry point — call this on every speaker button click.
   * Returns the resulting playback state: "playing" | "paused" | "stopped"
   */
  async toggle(messageId, text, language) {
    // Case 1: clicking the speaker on the message that's ALREADY loaded
    if (this._currentMessageId === messageId && this._currentAudio) {
      if (this._currentAudio.paused) {
        await this._currentAudio.play();
        this._emit(messageId, "playing");
        return "playing";
      } else {
        this._currentAudio.pause();
        this._emit(messageId, "paused");
        return "paused";
      }
    }

    // Case 2: a DIFFERENT message's speaker was clicked — stop whatever's
    // currently playing first (only one audio plays at a time).
    this._stopCurrent();

    // Case 3: fetch (or reuse cached) audio for the new message, then play.
    try {
      const blobUrl = await this._getOrFetchAudio(messageId, text, language);
      const audio = new Audio(blobUrl);

      audio.addEventListener("ended", () => {
        this._emit(messageId, "stopped");
        if (this._currentMessageId === messageId) {
          this._currentAudio = null;
          this._currentMessageId = null;
        }
      });

      this._currentAudio = audio;
      this._currentMessageId = messageId;

      await audio.play();
      this._emit(messageId, "playing");
      return "playing";
    } catch (err) {
      console.error("TTS playback failed:", err);
      this._emit(messageId, "error");
      throw err;
    }
  }

  _stopCurrent() {
    if (this._currentAudio) {
      this._currentAudio.pause();
      this._currentAudio.currentTime = 0;
      if (this._currentMessageId) {
        this._emit(this._currentMessageId, "stopped");
      }
    }
    this._currentAudio = null;
    this._currentMessageId = null;
  }

  /** Explicit stop — e.g. called when navigating away from the chat. */
  stop() {
    this._stopCurrent();
  }

  async _getOrFetchAudio(messageId, text, language) {
    if (this._cache.has(messageId)) {
      return this._cache.get(messageId);
    }

    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `TTS request failed (${res.status})`);
    }

    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    this._cache.set(messageId, blobUrl);
    return blobUrl;
  }

  /** Optional: call when a message is deleted/regenerated to free memory. */
  clearCache(messageId) {
    const url = this._cache.get(messageId);
    if (url) {
      URL.revokeObjectURL(url);
      this._cache.delete(messageId);
    }
    if (this._currentMessageId === messageId) {
      this._stopCurrent();
    }
  }
}

// Singleton — one shared instance across the whole app, so "only one audio
// plays at a time" is enforced globally, not per-component.
export const ttsService = new TTSService();