# Backend (core) — Audit

**Stack:** Spring Boot 3.2 / Java 21 · **Ports:** 8000 (HTTP), 50051 (gRPC) · **~13,189 LOC** · **Last updated:** 2026-09-24

## Genuinely real & good 🟢
- **Auth:** JWT + OAuth2 (Google) login, `OAuth2SuccessHandler`, JWT filter chain. Real and working.
- **CRUD:** invoices, clients, transactions — real persistence to Postgres.
- **gRPC transport:** server on 50051, generated stubs under `com.moneyops.grpc`. Transport itself works.
- **PDF generation:** real.
- **Redis queue + workers:** the queue design and email/notification workers are real.
- **Compliance / intelligence MATH:** the GST/TDS and finance calculations themselves are real and correct.

## Fake / partial / broken 🔴🟡
- **Finance metrics over gRPC return zeros** — `OrgContext` ThreadLocal never set on gRPC threads; no server interceptor (`FinanceGrpcService.java:28`). See [`../bugs/finance-metrics-zero-grpc.md`](../bugs/finance-metrics-zero-grpc.md).
- **Hardcoded demo text** "VoltNest" at `FinanceIntelligenceService.java:360`.
- **Split-brain persistence** — core writes to Postgres only (`jpa/persistence/InvoiceDocumentStore.java`), while Compliance/Recurring/Payments/Bulk still use MongoDB with no sync. See [`../bugs/split-brain-persistence.md`](../bugs/split-brain-persistence.md).
- **Kafka:** producer is real, but there is **no working consumer** (topic mismatch + a `System.out` stub) — the event pipeline is non-functional. `DomainEvent.java` exists.

## Security issues
- **Committed JWT secret** in the old `start_services.ps1` (now deleted, but still in git history → rotate before going live).
- **X-Org-Id tenant spoofing** is really the api-gateway's problem (see [`api-gateway.md`](api-gateway.md)), but the backend trusts the resulting context.
- Razorpay **LIVE** key present in `.env` (disabled by default).

## Observability
- `prometheus.yml` scrapes `/metrics` endpoints that **don't exist**; no Grafana dashboards; no Prometheus/Grafana container. Dead scaffolding.

## Top priorities
1. gRPC `ServerInterceptor` to fix zero-metrics.
2. Consolidate to Postgres as the single system of record.
3. Real Kafka consumer or turn Kafka off honestly until then.
