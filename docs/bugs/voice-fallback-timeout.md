# Bug: Voice agent "always falls back"

**Severity:** SEV-1 · **Status:** root-caused, fix pending · **Found:** 2026-09-24

## Symptom
The voice agent connected slowly (sometimes minutes) and then almost always replied with a canned "this is taking too long" line instead of a real answer.

## How I found it
Traced the request path from the LiveKit worker → voice-service → ai-gateway and compared configured timeouts against the real pipeline time.

## Root cause — three compounding bugs
1. **Timeout mismatch.** `voice-service/app/agent/config.py:53` sets the gateway timeout to **30s**, but `docker-compose.yml:143` overrides `AI_GATEWAY_TIMEOUT` to **10s**. The LLM + gRPC pipeline routinely takes >10s, so the client aborted and emitted the fallback line **while the gateway was still successfully producing the real answer**.
2. **Error laundering.** `guard.py:11` discarded real gateway text on a `FAILED` stage and returned a canned "I hit a snag," and a broad regex sanitizer at `entrypoint.py:340` rewrote legitimate replies into fallbacks.
3. **Wrong prompt entirely.** The agent was built with `Agent(instructions="MoneyOps Voice Agent")` — a placeholder string. The real prompt in `instructions.py` was never imported, so even successful replies had no persona or tool guidance.

Separately, the **minutes-to-connect** was cold start: LiveKit worker control-socket drops (getaddrinfo/PONG failures) plus ~10–40s per call from redundant health checks, STT/TTS built ~3×, VAD cold-load, and a broken prewarm using `asyncio.get_event_loop()` with no running loop (`entrypoint.py:848`).

## Blast radius
The single most-visible feature (voice-to-invoice) looked completely broken to every user.

## Fix (planned)
- One source of truth for the timeout (a single env var, no docker override fighting `config.py`), raised to a realistic budget.
- Remove the guard/sanitizer laundering so real errors and real replies pass through honestly.
- Import the real `instructions.py` prompt.
- Fix prewarm (run inside the running loop) and build STT/TTS/VAD once and reuse.

## Tradeoff
A longer client timeout means a genuinely stuck request takes longer to surface. Acceptable — I'd rather occasionally wait than routinely discard correct answers. The real answer is to make the pipeline faster (prewarm + reuse), not to keep the timeout artificially short.

## Interview lesson
Config-precedence bugs are brutal because **nothing errors** — the value is just wrong, and a too-tight client timeout turns a slow-but-working backend into a "broken" one. And never launder a real error into a friendly fallback *before* logging the truth; you blind yourself.
