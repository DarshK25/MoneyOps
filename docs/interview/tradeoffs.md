# Interview — Key Tradeoffs

**Last updated:** 2026-09-24

The tradeoffs I made (or inherited and re-decided), stated as I'd defend them.

## 1. Synchronous HTTP vs gRPC (core ↔ AI gateway)
- **gRPC pros:** typed contracts, smaller payloads, lower latency, streaming.
- **HTTP pros:** readable, debuggable, universal tooling, faster to iterate.
- **My stance:** gRPC is the right *destination* for the hot internal path; HTTP is the right *default during instability*. I kept HTTP as a working fallback while repairing gRPC (which had a real tenant-scoping bug). Ship on the reliable path, migrate deliberately.

## 2. Single system of record vs "dual persistence"
- The project claimed dual PG + Mongo persistence "for redundancy." With **no sync**, that's not redundancy — it's split-brain, and it produced empty dashboards.
- **My decision:** one system of record (Postgres). Real redundancy would need CDC/outbox syncing copies — far more machinery than this app warrants. A single well-backed-up store is simpler and honest.

## 3. Fail-open vs fail-closed dependencies (Redis)
- **Fail-open** (in-memory fallback) keeps the app usable when Redis is down but silently loses queue/cache/rate-limit guarantees.
- **Fail-closed** is honest but blocks boot on a missing optional dependency.
- **My decision:** degrade-with-one-loud-warning — usable *and* not silent — plus backoff + circuit breaker + log-once so a missing dependency can't storm the logs (this came straight out of the 44 GB incident). Recorded as ADR-001.

## 4. Keyword routing vs LLM reasoning (the agents)
- **Keyword routing** is cheap, deterministic, and easy to test — but it's not intelligence, and it can't generalize.
- **LLM tool-calling** is the real thing but costs latency, tokens, and needs guardrails + evals to be trustworthy.
- **My stance:** the current keyword routing is honestly labelled as such; the next phase moves decision-making to the LLM with executors as tools, guardrails on I/O, and a small eval set so I can *measure* quality rather than assert it. The key interview point: I can say exactly where the LLM makes a decision vs where it's decoration.

## 5. Lazy singleton backend adapter
- **Pro:** reuses the connection pool (real performance win).
- **Con:** harder to unit-test (must mock/reset the singleton).
- **Mitigation:** dependency-injection override in tests.
