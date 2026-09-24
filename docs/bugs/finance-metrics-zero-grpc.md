# Bug: Finance metrics gRPC always returns zeros

**Severity:** SEV-2 · **Status:** root-caused, fix pending · **Found:** 2026-09-24

## Symptom
`getFinanceMetrics` returned an all-zeros object no matter the tenant or the data.

## How I found it
Compared the working HTTP path against the gRPC path for the same query. HTTP scoped correctly; gRPC returned nothing.

## Root cause
Tenant scoping uses an `OrgContext` **ThreadLocal**. On the HTTP path a servlet filter populates it per request. But gRPC calls are served on gRPC's own worker threads, and **no server interceptor set `OrgContext` there** (`FinanceGrpcService.java:28`). So every tenant-scoped query ran with a null org and matched nothing → zeros.

There was also hardcoded "VoltNest" demo text at `FinanceIntelligenceService.java:360`.

## Blast radius
Every finance metric surfaced over gRPC was silently zero — read as "the numbers don't work" rather than "tenant scoping is broken on this transport."

## Fix (planned)
Add a gRPC `ServerInterceptor` that extracts the org from call metadata and populates `OrgContext` (with a `finally` clear), mirroring the HTTP filter. Remove the demo text.

## Tradeoff
An interceptor centralizes context setup but adds one more place that must stay in sync with the HTTP filter's contract. Worth it — the alternative (threading org through every method signature) is far messier.

## Interview lesson
`ThreadLocal` context does **not** cross execution boundaries for free. Every entry point — HTTP filter, gRPC interceptor, async executor, Kafka consumer — must establish and tear down the context itself. Classic multi-transport tenancy bug.
