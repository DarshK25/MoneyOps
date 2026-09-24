# Interview — Architecture Talking Points

**Last updated:** 2026-09-24

How I explain MoneyOps' architecture out loud, with the *why* behind each choice.

## The one-liner
"MoneyOps is a polyglot microservice system — an AI finance back-office for Indian SMEs. Five services: a Java/Spring Boot core, a Spring Cloud Gateway, a Python FastAPI AI gateway, a Python LiveKit voice service, and a React frontend."

## Why polyglot (Java + Python)?
- **Java/Spring Boot for the core** — transactional business data (invoices, clients, money), strong typing, mature persistence/JPA, and a battle-tested auth/security stack. This is where correctness and consistency matter most.
- **Python for the AI layer** — the LLM, vector, and voice ecosystems (Pinecone, LiveKit Agents, the provider SDKs) are Python-first. Fighting that in Java would be self-inflicted pain.
- The boundary is deliberate: **money logic in Java, intelligence in Python**, talking over a well-defined contract.

## Why a dedicated API gateway?
- One front door for auth, routing, CORS, rate limiting, and a public-endpoint allowlist — so each downstream service doesn't re-implement cross-cutting concerns.
- It's also where I found (and am fixing) an `X-Org-Id` tenant-spoofing gap — a good example of *why* centralizing trust decisions matters: get it right in one place.

## Why gRPC + HTTP fallback between core and AI gateway?
- **gRPC** for the hot internal path: typed contracts, smaller payloads, lower latency, streaming.
- **HTTP fallback** because it's trivially debuggable (readable JSON, curl-able) and unblocks iteration when the gRPC path has issues — which it did (the ThreadLocal zero-metrics bug). Being honest: today HTTP is the reliable path and gRPC is being repaired.

## Why the AgentOS layer?
- A multi-agent runtime needs shared plumbing: a message bus, governance/guardrails, observation/tracing, and memory. `agentos/*` is that scaffolding. The honest current state: the plumbing is real, but the reasoning that should sit on top is still keyword routing — that's the next phase.

## What I'd change / what's next
- Replace keyword routing with real **LLM tool-calling** so the model *decides*, with executors demoted to tools.
- Single **system of record** (Postgres) instead of the split-brain PG/Mongo setup.
- Real **observability** (the current Prometheus/Grafana config is dead scaffolding).
