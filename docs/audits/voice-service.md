# Voice Service — Audit

**Stack:** LiveKit Agents / Python · **Port:** 8003 · **~1,742 LOC** · **Last updated:** 2026-09-24

## Genuinely real & good 🟢
- **Full voice pipeline exists:** STT (Deepgram flux-general-en), TTS (ElevenLabs / Deepgram / Cartesia), Silero VAD, turn detection / debouncing.
- **LiveKit integration** for realtime rooms.
- The underlying **voice-to-invoice** path can produce real results — the problem was never that it couldn't work, it's that its successes were being discarded.

## Fake / partial / broken 🟡🔴
- **"Always falls back"** — three compounding bugs (see [`../bugs/voice-fallback-timeout.md`](../bugs/voice-fallback-timeout.md)):
  1. Timeout mismatch: `config.py:53` = 30s vs `docker-compose.yml:143` `AI_GATEWAY_TIMEOUT=10`; the 10s wins and aborts a still-working request.
  2. Error laundering: `guard.py:11` discards real text on FAILED; broad regex sanitizer at `entrypoint.py:340` rewrites good replies into fallbacks.
  3. Placeholder prompt: `entrypoint.py:536` builds `Agent(instructions="MoneyOps Voice Agent")`; the real `instructions.py` is never imported.
- **Minutes to connect** — cold start: broken prewarm (`entrypoint.py:848`, `asyncio.get_event_loop()` with no running loop), STT/TTS built ~3×, VAD cold-load, redundant health checks; plus LiveKit worker control-socket drops (getaddrinfo/PONG).

## Security
- Inherits gateway auth; no service-specific issues beyond the shared ones.

## Top priorities
1. Single env-driven timeout, realistic budget.
2. Remove guard/sanitizer laundering; surface real errors and real replies.
3. Import the real `instructions.py` prompt.
4. Fix prewarm + build STT/TTS/VAD once and reuse (kills most of the connect latency).
