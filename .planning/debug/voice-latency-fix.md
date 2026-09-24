---
status: root-caused
trigger: "Apply all fixes for 3-minute voice agent latency: pre-warm STT/TTS, gRPC keepalive, health checks, LiveKit connection optimization"
created: "2026-07-15T00:00:00Z"
updated: "2026-09-24T00:00:00Z"
---

## Current Focus

hypothesis: TWO distinct problems were conflated under "latency": (a) minutes-to-connect from LiveKit worker cold start, and (b) "always falls back" from a client-side timeout that is shorter than the real backend response time.
test: Trace the request path end-to-end and compare configured timeouts against measured pipeline time.
expecting: The fallback is fired by a 10s client timeout while the gateway is still working; connect delay is cold-start, not network.
next_action: Unify the timeout to a single env-driven value, remove error-laundering, import the real prompt, add provider prewarm.

## Symptoms

expected: Voice agent should be ready within 3 seconds of call initiation
actual: Voice agent takes 3+ minutes to respond after call connects
errors: No explicit errors - just extreme latency on first call
reproduction: 
1. Start all services with docker compose
2. Initiate a LiveKit voice call
3. Measure time from call connect to first agent response
4. Observe ~3 minute delay
started: Always broken - cold start issue

## Eliminated

- "Pure network latency to the LLM provider" — eliminated. The gateway does produce a correct answer; it is the client that gives up first.
- "The model is slow/dumb" — eliminated. The agent was constructed with a placeholder `instructions="MoneyOps Voice Agent"` string; the real prompt in `instructions.py` was never imported, so output quality was never actually exercised.

## Evidence

- `voice-service/app/agent/config.py:53` sets the AI-gateway timeout to 30s.
- `docker-compose.yml:143` overrides `AI_GATEWAY_TIMEOUT` to 10s — this is the value that actually wins at runtime.
- The LLM + gRPC pipeline routinely exceeds 10s, so the client aborts and emits the canned "taking too long" line while the gateway is still succeeding.
- `guard.py:11` discards real gateway text on a FAILED stage and returns "I hit a snag."
- `entrypoint.py:340` broad regex sanitizer rewrites legitimate replies into fallbacks.
- `entrypoint.py:536` `Agent(instructions="MoneyOps Voice Agent")` — placeholder, real prompt never loaded.
- `entrypoint.py:848` prewarm uses `asyncio.get_event_loop()` with no running loop → prewarm is broken; STT/TTS built ~3× and VAD cold-loads per call. LiveKit worker control-socket drops (getaddrinfo/PONG) add the minutes-to-connect.

## Resolution

root_cause: A client-side timeout (10s, from the docker-compose override) shorter than the real end-to-end response time, converting slow-but-successful gateway responses into canned fallbacks; compounded by error-laundering in guard/sanitizer, a placeholder prompt, and broken prewarm.
fix: (1) single source of truth for the timeout via one env var and raise it to a realistic budget; (2) remove guard/sanitizer laundering so real errors and real replies pass through; (3) import the real `instructions.py` prompt into the Agent; (4) fix prewarm (run inside the running loop) and build STT/TTS/VAD once and reuse.
verification: measure time-to-first-response before/after; confirm real answers reach the caller (no canned fallback on success); measure cold-start connect time before/after prewarm fix. (PENDING — fixes not yet applied.)
files_changed: []