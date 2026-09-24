# AI Gateway — Audit

**Stack:** FastAPI / Python · **Ports:** 8005 (HTTP), 50052 (gRPC) · **~16,671 LOC** · **Last updated:** 2026-09-24

## Genuinely real & good 🟢
- **API gateway filters / routes** and the FastAPI app structure.
- **Pinecone memory manager** (`memory/pinecone_manager.py`) — real client wiring (index not yet seeded for RAG).
- **Semantic cache** (`cache/semantic_cache.py`) — real.
- **Multi-provider LLM** wiring (Groq / Cerebras / Gemini) with failover.
- **Backend adapter** (`adapters/backend_adapter.py`) over HTTP (httpx) — the reliable path to the backend.
- **GrowthExecutor statistics** and the compliance/intelligence math surfaced here — real.

## Fake / partial / broken 🔴🟡
- **Boots again** as of 2026-09-24 — was fully dead from a `SyntaxError` at `base_executor.py:253`. See [`../bugs/ai-gateway-boot-syntaxerror.md`](../bugs/ai-gateway-boot-syntaxerror.md).
- **"AI agents" are keyword routing, not reasoning.** `_classify_action` pattern-matches on keywords; the LLM only extracts entities and phrases the fallback sentence — it never *decides* the action. This is the headline gap.
- **A dead second brain exists.** `orchestration/intent_classifier.py`, `entity_extractor.py`, `agent_router.py`, `tools/*`, and `agents/compliance_agent.py` are referenced **only by tests** — a whole parallel agent system that never runs in production.
- **RAG index never seeded** — the memory plumbing exists but has nothing to retrieve.
- **gRPC client** (`adapters/grpc_client.py`) exists but the HTTP adapter is the dependable path (backend gRPC has the zero-metrics bug).

## AgentOS layer
`agentos/*` (message bus, governance, observation, memory, types) is real scaffolding for a multi-agent runtime — but it's plumbing waiting on real reasoning to sit on top of it.

## Security
- Wildcard CORS with credentials (needs scoping).
- Rate limiter fail-open (should fail-closed or degrade explicitly).

## Top priorities
1. Replace keyword routing with **real LLM tool-calling** — the model decides which tool/executor to call; demote executors to tools.
2. Seed the RAG index and wire retrieval into agent context.
3. Add guardrails + a small eval set so agent quality is measured, not asserted.
4. Decide the fate of the dead `orchestration/*` brain — adopt or delete, don't leave two.
