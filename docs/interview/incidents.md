# Interview — Incident War Stories

**Last updated:** 2026-09-24

Each of these is a real debugging story framed the way I'd tell it in an interview: situation → investigation → root cause → fix → lesson. Full technical write-ups live in [`../bugs/`](../bugs/).

## Headliner: the 44 GB Redis reconnect storm
**Situation:** My disk was filling up. Two log files were 34.8 GB and 9.68 GB.
**Investigation:** Before deleting them I sampled the contents — thousands of identical Lettuce `RedisConnectionException` stack traces.
**Root cause:** The backend was pointed at a `localhost:6379` Redis that wasn't running. The client retried unboundedly, no backoff, no circuit breaker, and logged a full stack trace *per attempt*. A missing optional dependency filled the disk.
**Fix:** Unify Redis behind one `REDIS_URL` (Docker local / Upstash hosted), and make it a graceful-degradation dependency — capped backoff, circuit breaker, log-once, in-memory fallback with one loud warning (ADR-001).
**Lesson:** Retries need backoff, breakers, and log deduplication. The failure of something that *wasn't even there* took down the machine — that's what makes it memorable.

## The service that couldn't even start — a one-line SyntaxError
**Situation:** The entire Python AI gateway was dead; "the agents are dumb" was the report.
**Investigation:** Tried to import it; got a `SyntaxError` deep in `base_executor.py`.
**Root cause:** Two statements collapsed onto one line (a lost newline). Because it's imported by everything, that one line blocked the whole import graph.
**Fix:** Split the line; then AST-checked all 91 files to be sure nothing else hid.
**Lesson:** A syntax error in a hot-path module is a fail-closed dependency. A trivial pre-commit compile step in CI would have caught it — cheap static gates pay for themselves.

## The voice agent that discarded its own correct answers
**Situation:** Voice agent connected slowly and almost always said "this is taking too long."
**Investigation:** Traced the LiveKit → voice-service → AI gateway path and compared timeouts to real pipeline time.
**Root cause:** A docker-compose override set the client timeout to 10s while `config.py` intended 30s; the pipeline takes longer than 10s, so the client aborted a *successful* request and emitted a canned fallback. Compounded by error-laundering and a placeholder prompt.
**Fix:** One env-driven timeout at a realistic budget, remove the laundering, load the real prompt, fix prewarm.
**Lesson:** Config-precedence bugs never throw — the value is just wrong. And never rewrite a real error into a friendly fallback before logging the truth.

## The metrics that were always zero — ThreadLocal across gRPC threads
**Situation:** `getFinanceMetrics` returned all zeros regardless of tenant.
**Investigation:** Compared the HTTP path (worked) to the gRPC path (zeros).
**Root cause:** Tenant scoping uses an `OrgContext` ThreadLocal set by an HTTP filter. gRPC runs on its own worker threads, and no interceptor set the context there — so every query ran with a null org.
**Fix:** A gRPC `ServerInterceptor` that populates `OrgContext` from call metadata (with a `finally` clear), mirroring the HTTP filter.
**Lesson:** ThreadLocal context doesn't cross execution boundaries for free — every entry point (HTTP, gRPC, async, Kafka) must set and clear it.
