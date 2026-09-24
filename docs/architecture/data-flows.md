# Data Flows

**Last updated:** 2026-09-24

The key end-to-end paths through MoneyOps. Arrows are the real runtime hops.

## 1. Auth / login
```
Browser → api-gateway(8002) → backend(8000)
  - Email/password: backend validates, issues JWT.
  - Google OAuth2: OAuth2SuccessHandler → JWT issued.
Token then rides every request: Browser → gateway → backend/ai-gateway.
```
The api-gateway `AuthenticationFilter` validates the JWT and sets tenant/user headers. **Known gap:** it trusts `X-Org-Id` from the client without cross-checking the token (`AuthenticationFilter.java:74`).

## 2. Create invoice
```
Browser → api-gateway → backend → Postgres (InvoiceDocumentStore, Postgres-only write)
                                → PDF generation (real)
```
Invoices are written to **Postgres only**. This matters — see split-brain below.

## 3. Voice-to-invoice
```
Caller → LiveKit room → voice-service(8003)
  → STT (Deepgram) → text
  → voice-service → ai-gateway(8005) [reasoning/intent]   ← 10s timeout bug lived here
  → backend [create invoice]
  → TTS (ElevenLabs/Cartesia/Deepgram) → spoken confirmation
```
This is the flagship demo path. It worked underneath but surfaced canned fallbacks because the client timeout (10s) was shorter than the real pipeline time. See `bugs/voice-fallback-timeout.md`.

## 4. Agent chat / query
```
Browser → api-gateway → ai-gateway(8005) → MasterOrchestrator
  → _classify_action (KEYWORD routing, not LLM reasoning)
  → executor (FinanceOps/Compliance/Collections/Growth)
  → backend_adapter (HTTP; gRPC fallback) → backend → data store
  → LLM used only to extract entities + phrase the reply
```
The LLM does **not** decide which action to take today — that's the core gap the next phase fixes.

## 5. Finance metrics
```
ai-gateway → gRPC(50051) → backend FinanceGrpcService → FinanceIntelligenceService → Postgres
```
**Returns zeros.** `OrgContext` is a ThreadLocal set by the HTTP filter but never set on gRPC worker threads (no server interceptor), so tenant-scoped queries match nothing. See `bugs/finance-metrics-zero-grpc.md`.

## Split-brain persistence (important)

The README claimed "dual persistence" across Postgres + MongoDB. In reality:
- **Postgres** = core writes (invoices, clients, transactions).
- **MongoDB** = still read/written by Compliance / Recurring / Payments / Bulk modules — an abandoned store with no sync.

So the compliance dashboard queries an **empty Mongo** while the real data sits in Postgres, and bulk-created invoices are invisible to the Postgres-backed list. There is no CDC/outbox syncing them — it's split-brain, not redundancy. See `bugs/split-brain-persistence.md`.
