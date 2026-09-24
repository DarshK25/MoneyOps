# Service Map

**Last updated:** 2026-09-24

Per-service breakdown: responsibility, tech, entry points, key files, and current health. Health legend: 🟢 real & working · 🟡 real but partial/buggy · 🔴 fake/theater/broken.

## backend (core) — Spring Boot 3.2 / Java 21
- **Responsibility:** system of record for invoices, clients, transactions; auth (JWT + OAuth2); finance metrics; gRPC server.
- **Ports:** HTTP 8000, gRPC 50051.
- **Entry points:** Spring Boot main app; gRPC services under `com.moneyops.grpc`.
- **Key files:** `grpc/FinanceGrpcService.java`, `intelligence/FinanceIntelligenceService.java`, `jpa/persistence/InvoiceDocumentStore.java`, `events/dto/DomainEvent.java`.
- **Health:** 🟡 CRUD + auth + gRPC transport + PDF gen are 🟢 real; finance metrics over gRPC return zeros (ThreadLocal bug); Kafka producer real but no consumer.

## api-gateway — Spring Cloud Gateway (WebFlux)
- **Responsibility:** single front door; routing, auth filtering, public-endpoint allowlist.
- **Port:** 8002.
- **Entry points:** gateway routes; `filter/AuthenticationFilter.java`.
- **Key files:** `filter/AuthenticationFilter.java` (X-Org-Id handling), `JwtTokenProvider`.
- **Health:** 🟡 routing/filtering real; `X-Org-Id` tenant-spoofing gap at `AuthenticationFilter.java:74` (dead `validateHeadersAgainstToken` guard). Largely a teammate's work historically.

## ai-gateway — FastAPI / Python
- **Responsibility:** the "brain" — agents (FinanceOps/Compliance/Collections/TReDS/Growth), MasterOrchestrator, AgentOS (message bus/governance/observation/memory), Pinecone memory, semantic cache, multi-provider LLM.
- **Ports:** HTTP 8005, gRPC 50052.
- **Entry points:** `app/main.py`, `app/api/v1/agent.py`.
- **Key files:** `agents/base_executor.py`, `agents/master_orchestrator.py`, `agentos/*`, `memory/pinecone_manager.py`, `cache/semantic_cache.py`, `adapters/backend_adapter.py`, `adapters/grpc_client.py`.
- **Health:** 🟡 boots again after the `base_executor.py:253` fix; transport, memory manager, semantic cache real; but routing is keyword-based (`_classify_action`), not LLM reasoning, and a whole second brain under `orchestration/*` + `tools/*` is dead code referenced only by tests. 🔴 on the "real agents" claim.

## voice-service — LiveKit Agents / Python
- **Responsibility:** voice front door — voice-to-invoice and spoken queries. STT/TTS/VAD + turn detection.
- **Port:** 8003.
- **Entry points:** `app/agent/entrypoint.py`, `app/main.py`.
- **Key files:** `app/agent/entrypoint.py` (:340 sanitizer, :536 placeholder prompt, :848 broken prewarm), `app/agent/guard.py:11`, `app/agent/config.py:53` (timeout=30), `app/agent/instructions.py` (real prompt, never imported).
- **Health:** 🟡 pipeline exists and can produce real answers, but a 10s client timeout + error-laundering + a placeholder prompt made it "always fall back." See `bugs/voice-fallback-timeout.md`.

## Frontend — React 18 / Vite 7
- **Responsibility:** the ~22-page product UI (dashboard, invoices, clients, agent chat, voice).
- **Port:** 3000 (Vite default 5173).
- **Entry points:** `src/main.jsx`.
- **Key files:** `src/lib/api.js` (cache/dedup, timeout), `src/pages/InvoicesPage.jsx`.
- **Health:** 🟢 mostly real and substantial; had a `getToken()` ReferenceError in `InvoicesPage.jsx` breaking PDF download, and `api.js` lacked AbortController/timeout despite a "chat timeout" commit.
