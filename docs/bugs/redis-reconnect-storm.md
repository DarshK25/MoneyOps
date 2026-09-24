# Bug: Redis reconnect storm filled 44 GB of disk

**Severity:** SEV-1 · **Status:** fix decided (see [ADR-001](../decisions/ADR-001-redis-and-degradation.md)) · **Found:** 2026-09-24

## Symptom
Disk was filling. Two untracked log files: `backend_out_v5.log` at **34.8 GB** and a backend log at **9.68 GB**.

## How I found it
Before deleting them I tailed and sampled both. They were wall-to-wall `io.lettuce.core.RedisConnectionException` / `java.net.ConnectException` stack traces — the same failure repeating thousands of times.

## Root cause
The backend was configured to reach Redis at `localhost:6379`, but no Redis was running there. The Lettuce client retried **unboundedly, with no backoff and no circuit breaker**, and logged a **full multi-line stack trace on every single attempt**. An Upstash serverless Redis was available in `.env` but unused.

So: a *missing* optional dependency + naïve retry + verbose per-attempt logging = a disk-filling outage.

## Blast radius
44 GB of pure-noise logs; disk pressure on the dev machine; real signal buried; both startup and steady-state spammed.

## Fix
Recorded as ADR-001:
1. Unify Redis behind a single `REDIS_URL` (Docker locally, Upstash hosted) so nothing is silently aimed at a dead `localhost`.
2. Make Redis a graceful-degradation dependency: capped exponential backoff + circuit breaker + **log-once-then-suppress** + in-memory fallback with one loud "degraded" warning.

## Tradeoff
Fail-open (in-memory fallback) keeps the app usable without Redis but silently loses queue/cache/rate-limit guarantees; fail-closed is honest but blocks boot. I chose **degrade-with-one-loud-warning** — usable *and* not silent.

## Interview lesson
Unbounded retry + per-attempt stack-trace logging + a hard assumption that an optional dependency is present = an outage caused by something that *wasn't even there*. Retries need backoff, breakers, and log deduplication. This is my strongest "I debugged a production-shaped failure" story.
