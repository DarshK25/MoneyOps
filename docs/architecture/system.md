# System Architecture

**Last updated:** 2026-09-24

MoneyOps is a polyglot microservice system: an AI finance back-office for Indian SMEs. Five application services, backed by data stores and a couple of background workers, orchestrated with docker-compose.

## Services

| Service | Stack | HTTP port | gRPC port | Approx. LOC (app code) |
|---|---|---|---|---|
| backend (core) | Spring Boot 3.2 / Java 21 | 8000 | 50051 | ~13,189 |
| api-gateway | Spring Cloud Gateway (WebFlux) | 8002 | — | ~1,947 |
| ai-gateway | FastAPI / Python | 8005 | 50052 | ~16,671 |
| voice-service | LiveKit Agents / Python | 8003 | — | ~1,742 |
| Frontend | React 18 / Vite 7 | 3000 (Vite default 5173) | — | ~19,339 |

LOC excludes dependencies and generated code.

## How they communicate

- **Frontend → api-gateway (8002):** all browser traffic enters through the Spring Cloud Gateway, which handles auth filtering and routing.
- **api-gateway → backend / ai-gateway:** routed HTTP.
- **backend ↔ ai-gateway:** **gRPC** is the intended primary transport (backend serves gRPC on `50051`, ai-gateway on `50052`), with **HTTP as fallback**. In practice the ai-gateway `BackendHttpAdapter` (REST/httpx) is the reliable path; gRPC has known bugs (see the finance-metrics zero bug in `audits/backend.md`).
- **voice-service → ai-gateway (8005):** the voice agent calls the gateway for reasoning; this hop is where the 10s-timeout fallback bug lived (see `bugs/voice-fallback-timeout.md`).
- **Auth:** JWT bearer tokens, plus OAuth2 (Google) login. The token must propagate User → gateway → agent → adapter → backend.

## Full docker-compose topology (10 containers)

Application: `backend`, `api-gateway`, `ai-gateway`, `voice-service`, `frontend`.
Infra: `redis` (6379), `kafka` (9092), `zookeeper`.
Workers: `email-worker`, `notification-worker`.

**Config discrepancy I found:** `docker-compose.yml` sets `KAFKA_ENABLED: "true"` (line 64) while the root `.env` sets `KAFKA_ENABLED=false`. The Kafka producer is real but there is no working consumer (topic mismatch + a `System.out` stub), so the pipeline is non-functional regardless — see `audits/backend.md`.

## Current health snapshot (2026-09-24)

- ai-gateway now **imports and boots** after I fixed a fatal `SyntaxError` (`base_executor.py:253`) — see `bugs/ai-gateway-boot-syntaxerror.md`.
- Redis was pointed at a non-running `localhost:6379` with no backoff, which caused a 44 GB log storm — decision recorded in `decisions/ADR-001-redis-and-degradation.md`.
- The "AI agents" are still keyword routing, not real LLM reasoning (the next phase of work).
