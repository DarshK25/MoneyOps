# ADR-001: Redis topology + graceful degradation

**Status:** Accepted (2026-09-24)

## Context

MoneyOps uses Redis for the job queue, caching, and rate limiting. During the revival I found two untracked log files eating **~44 GB of disk** (`backend_out_v5.log` at 34.8 GB and a backend log at 9.68 GB). Sampling them showed thousands of `io.lettuce.core.RedisConnectionException` / `java.net.ConnectException` stack traces.

Root cause: the backend was configured to reach Redis at `localhost:6379`, but no Redis was running locally. Lettuce retried **unboundedly, with no backoff and no circuit breaker**, and logged a full multi-line stack trace on *every* attempt. Meanwhile an Upstash serverless Redis instance already existed in `.env` but nothing pointed at it.

Two questions had to be answered:
1. **What Redis do we run** — a local Docker container, or the hosted Upstash instance?
2. **How does the app behave when Redis is unreachable** — so a missing dependency can never fill the disk again?

## Decision

**1. Both, unified behind one env var.**
- **Local development:** the Docker Redis container from `docker-compose.yml` (already there on `6379`).
- **Hosted / anywhere non-local:** the Upstash serverless Redis (free tier, no container to run, survives laptop restarts).
- The app reads a **single `REDIS_URL`** (e.g. `redis://localhost:6379` locally, the `rediss://…upstash…` URL when hosted). No code path hardcodes host/port. Switching environments is a one-line env change, not a code change.

Rationale: Docker Redis is the right *local* default (zero external dependency, fast, offline-friendly), while Upstash is the right *hosted* default on free tier (nothing to operate, no always-on container). Unifying on `REDIS_URL` means the two are interchangeable and I never again have a service silently aimed at a dead `localhost`.

**2. Redis is a graceful-degradation dependency, never a fatal one.**
- **Capped exponential backoff** on reconnects (not tight-loop retry).
- **Circuit breaker:** after N consecutive failures, stop hammering and mark Redis down; probe periodically.
- **Log-once, then suppress:** the first failure logs one concise warning (not a stack trace); repeats are counted, not re-dumped.
- **In-memory fallback** for cache/rate-limit so the app stays usable when Redis is down — with a single loud startup warning that it's degraded, so degradation is never silent.

## Consequences

**Better**
- A missing/unreachable Redis can no longer storm the logs or fill the disk.
- One config switch moves between local Docker and hosted Upstash.
- The app boots and serves even with Redis down (degraded, but honest about it).

**Costs / tradeoffs**
- In-memory fallback loses cross-process guarantees (rate limits become per-instance; queued jobs aren't durable) while degraded. This is acceptable for dev and a brief outage, **not** as a steady state — the loud warning exists so I don't forget it's degraded.
- A circuit breaker adds a little complexity and a window where Redis is back but we haven't re-probed yet.

## Related
- Bug write-up: [`../bugs/redis-reconnect-storm.md`](../bugs/redis-reconnect-storm.md)
- Interview framing: [`../interview/incidents.md`](../interview/incidents.md)
