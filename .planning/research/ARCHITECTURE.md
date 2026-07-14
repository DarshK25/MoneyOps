# Architecture Patterns

**Domain:** AI-powered financial operations platform (MoneyOps)
**Researched:** 2026-07-14

---

## Current Architecture (As-Built)

### System Context Diagram

```
┌─────────────┐     HTTPS/WSS      ┌──────────────────────┐
│   Browser   │◄──────────────────►│   React Frontend     │
│  (User)     │                    │  (Vite + Tailwind)   │
└─────────────┘                    └──────────┬───────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
           ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
           │  API Gateway    │        │   AI Gateway    │        │  Voice Service  │
           │ (Spring Cloud   │        │   (FastAPI)     │        │  (LiveKit)      │
           │  Gateway)       │        │                 │        │                 │
           │  Port: 8002     │        │  Port: 8005     │        │  Port: 8003     │
           └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
                    │                          │                          │
          ┌─────────┴─────────┐                │                          │
          ▼                   ▼                ▼                          ▼
   ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        ┌───────────────┐
   │   Backend     │  │   Backend     │  │   Backend     │        │   AI Gateway  │
   │ (Spring Boot) │◄─┤  (gRPC:50051) │  │  (REST:8000)  │◄───────│  (REST:8005)  │
   │  Port: 8000   │  └───────────────┘  └───────────────┘        └───────────────┘
   └───────┬───────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌───────┐   ┌──────────┐
│MongoDB│   │PostgreSQL│
│ Atlas │   │  (Neon)  │
└───────┘   └──────────┘
    ▲             ▲
    │             │
    └──────┬──────┘
           ▼
      ┌─────────┐
      │  Redis  │
      │ (Cache  │
      │  +Queue)│
      └─────────┘
           ▲
           │
    ┌──────┴──────┐
    ▼             ▼
┌─────────┐ ┌─────────────┐
│ Email   │ │Notification │
│ Worker  │ │  Worker     │
└─────────┘ └─────────────┘
```

### Service Communication Matrix

| Source | Target | Protocol | Pattern | Auth |
|--------|--------|----------|---------|------|
| Frontend | API Gateway | HTTPS/REST | Request-Response | JWT in Authorization header |
| Frontend | API Gateway | WSS | WebSocket (Voice) | JWT in query param |
| API Gateway | Backend | HTTP/REST | Request-Response | JWT validated → X-User-Id, X-Org-Id headers |
| API Gateway | AI Gateway | HTTP/REST | Request-Response | Internal service token |
| API Gateway | Voice Service | HTTP/REST | Request-Response | Internal service token |
| AI Gateway | Backend | gRPC | Request-Response | Service token + mTLS (planned) |
| AI Gateway | Backend | HTTP/REST | Async (via adapter) | Service token |
| AI Gateway | LLM Providers | HTTPS/REST | Request-Response | API Keys |
| AI Gateway | Pinecone | gRPC/HTTPS | Vector ops | API Key |
| Voice Service | AI Gateway | HTTP/REST | Request-Response | Service token |
| Voice Service | LiveKit | WSS | WebRTC signaling | LiveKit token |
| Backend | Redis | RESP | Cache/Queue/PubSub | Password |
| Backend | MongoDB | Wire Protocol | CRUD | URI auth |
| Backend | PostgreSQL | JDBC | CRUD | User/Pass |
| Workers | Redis | RESP | Queue (BRPOPLPUSH) | Password |

---

## Recommended Target Architecture

### Layer 1: Observability (Phase 1)

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenTelemetry Collector                      │
│  (DaemonSet on each node / Sidecar per pod)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Prometheus  │  │     Loki      │  │    Jaeger     │
│  (Metrics)    │  │    (Logs)     │  │  (Traces)     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
              ┌───────────────────────┐
              │      Grafana          │
              │  (Dashboards + Alerts)│
              └───────────────────────┘
```

**Instrumentation Points:**
- **Java (Spring Boot 3.2+):** `micrometer-registry-prometheus`, `micrometer-tracing-bridge-brave`, `zipkin-reporter-brave`
- **Python (FastAPI):** `opentelemetry-instrument`, `opentelemetry-exporter-otlp`, `opentelemetry-instrumentation-fastapi`
- **React:** `@opentelemetry/sdk-trace-web`, `@opentelemetry/exporter-collector`
- **Infrastructure:** kube-state-metrics, node-exporter, redis-exporter, postgres-exporter

**Key Metrics to Export (RED + USE):**
- Rate, Errors, Duration per endpoint per service
- Queue depth, worker latency, job success rate
- LLM: tokens/sec, cost/request, latency p50/p95/p99, fallback rate
- Voice: STT latency, TTS latency, turn detection accuracy
- Business: invoices_created, payments_received, compliance_filings

### Layer 2: Security (Phase 2)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Service Mesh (Istio/Linkerd)                 │
│  mTLS ◄──────────────────────────────────────────────────────►  │
│  AuthZ Policies ◄──────────────────────────────────────────►    │
│  Traffic Split ◄──────────────────────────────────────────►     │
│  Retry/Timeout ◄──────────────────────────────────────────►     │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  API Gateway  │    │  AI Gateway   │    │    Backend    │
│  (Envoy/      │    │  (FastAPI +   │    │  (Spring Boot │
│   Spring CG)  │    │   Istio sidecar)       + sidecar) │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │  WAF    │          │  AI     │          │  Data   │
   │ (ModSec/│          │  Guard  │          │  Encrypt│
   │ Coraza) │          │         │          │         │
   └─────────┘          └─────────┘          └─────────┘
```

**Security Controls per Layer:**

| Layer | Control | Implementation |
|-------|---------|----------------|
| **Network** | mTLS everywhere | Istio `PeerAuthentication: STRICT`, `DestinationRule` |
| **Network** | Egress control | `ServiceEntry` for external APIs (Groq, Pinecone, LiveKit) |
| **Application** | JWT validation | API Gateway filter + Spring Security (stateless) |
| **Application** | Rate limiting | Gateway: Redis token bucket; AI Gateway: sliding window |
| **Application** | Input validation | Pydantic (Python), Bean Validation (Java), Zod (Frontend) |
| **Application** | Output encoding | Auto via React (XSS), Jackson (JSON), FastAPI (JSON) |
| **Data** | Encryption at rest | MongoDB Atlas / Neon managed; Redis TLS; Pinecone managed |
| **Data** | Encryption in transit | TLS 1.3 everywhere; cert-manager + Let's Encrypt / ACME |
| **Secrets** | External secrets | `ExternalSecrets` operator → AWS Secrets Manager / Vault |
| **AI** | Prompt injection guard | Heuristic + embedding classifier pre-LLM |
| **AI** | PII redaction | Presidio analyzer/anonymizer pre-LLM; re-identify post |
| **AI** | Output validation | Pydantic schema enforcement; forbidden pattern regex |

### Layer 3: AI Security (Phase 3)

```
┌─────────────────────────────────────────────────────────────────┐
│                      AI Gateway Request Flow                     │
└─────────────────────────────────────────────────────────────────┘

Request
  │
  ▼
┌─────────────────┐
│  Rate Limit     │  (per-org, per-user, per-model)
│  (Redis)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PII Detection  │  Microsoft Presidio / custom NER
│  + Redaction    │  → Replace with [PII_TYPE_N]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Prompt Guard   │  Heuristic: instruction overlap, role play,
│  (Injection)    │  embedding similarity to known attacks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Schema Valid.  │  Pydantic model for each tool/executor
│  (Input)        │  Reject if doesn't match
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cost Check     │  Per-org daily token budget; route to cheaper
│  (Budget)       │  model if >80% consumed
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Call       │  Multi-provider: Groq → Cerebras → Anthropic → OpenAI
│  (with fallback)│  Timeout + retry per provider
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Output Guard   │  PII re-identification; schema validation;
│  (Validation)   │  forbidden phrases; length limits
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Audit Log      │  Structured: request_id, model, tokens, cost,
│  (Immutable)    │  latency, guard_results, user_id, org_id
└────────┬────────┘
         │
         ▼
   Response
```

### Layer 4: CI/CD + GitOps (Phase 4)

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Build & Test │    │  Security     │    │  Contract     │
│  (per service)│    │  Scan         │    │  Test (Pact)  │
│               │    │  - SAST       │    │               │
│  - Unit       │    │  - DAST       │    │  Provider:    │
│  - Integration│    │  - Deps       │    │  Backend,     │
│  - Lint/Type  │    │  - Secrets    │    │  AI Gateway   │
│  - Coverage   │    │  - Container  │    │  Consumer:    │
└───────┬───────┘    └───────┬───────┘    │  Frontend,    │
        │                    │            │  Voice Svc    │
        ▼                    ▼            └───────┬───────┘
┌────────────────────────────────────────────────┘
│              Build & Push Docker Images                    │
│  GHCR: ghcr.io/moneyops/{backend,api-gateway,ai-gateway,  │
│         voice-service,frontend,workers}:{sha}              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ArgoCD (GitOps)                             │
│  Repository: github.com/moneyops/infra-config                   │
│  Apps: backend, api-gateway, ai-gateway, voice, frontend,       │
│        workers, monitoring, ingress                              │
│  Sync: Auto + Prune + Self-Heal                                 │
│  Strategy: Canary (Argo Rollouts) → Analysis → Promote/Abort    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Staging     │    │  Production   │    │   DR Region   │
│   (EKS/GKE)   │    │  (EKS/GKE)    │    │  (warm standby)│
│   Canary 10%  │    │  Blue/Green   │    │  RPO<5m/RTO<1h │
└───────────────┘    └───────────────┘    └───────────────┘
```

**Pipeline Stages:**

| Stage | Tools | Gates |
|-------|-------|-------|
| **Code** | pre-commit (ruff, black, ktlint, spotless) | Local |
| **PR** | SAST (CodeQL), Secret scan (GitLeaks), Deps (Dependabot/Trivy) | Required checks |
| **Build** | Multi-stage Docker, BuildKit, SBOM (Syft) | Image scan (Trivy Critical/High=0) |
| **Test** | Unit (coverage >80%), Integration (Testcontainers), Contract (Pact) | All green |
| **Staging** | ArgoCD sync, Smoke tests, Load test (k6 50 VU) | SLO: p95<500ms, error<0.1% |
| **Prod** | Canary 5% → 25% → 100% (Argo Rollouts), Metric analysis | Burn rate <1%, no new errors |
| **Post** | Synthetic monitoring, Error budget alert | Auto-rollback on SLO breach |

### Layer 5: Resilience Patterns (Cross-Cutting)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Resilience4j (Java) /                        │
│                    Tenacity + Circuit Breaker (Python)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Circuit       │    │    Retry      │    │   Bulkhead    │
│ Breaker       │    │  (Exponential │    │  (Thread Pool │
│               │    │   Backoff)    │    │   / Semaphore)│
│ States:       │    │               │    │               │
│ CLOSED → OPEN │    │ maxAttempts:3 │    │ AI Gateway:   │
│ OPEN → HALF   │    │ wait: 100ms   │    │  executor pool│
│ OPEN → CLOSED │    │ *2^attempt    │    │  size=10      │
└───────────────┘    └───────────────┘    └───────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌───────────────┐
                    │  Time Limiter │
                    │  (Future/     │
                    │   Completable)│
                    │  timeout: 30s │
                    └───────────────┘
```

**Configuration (application.yml / config.py):**

```yaml
# Java (Resilience4j)
resilience4j:
  circuitbreaker:
    configs:
      default:
        registerHealthIndicator: true
        slidingWindowSize: 100
        failureRateThreshold: 50
        slowCallRateThreshold: 50
        slowCallDurationThreshold: 2s
        permittedNumberOfCallsInHalfOpenState: 3
        waitDurationInOpenState: 30s
    instances:
      aiGateway:
        baseConfig: default
      backendDatabase:
        baseConfig: default
  retry:
    configs:
      default:
        maxAttempts: 3
        waitDuration: 100ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
  timelimiter:
    configs:
      default:
        cancelRunningFuture: true
        timeoutDuration: 30s
```

```python
# Python (Tenacity + custom circuit breaker)
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

@retry(
    wait=wait_exponential_jitter(initial=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError))
)
async def call_llm_provider(request: LLMRequest) -> LLMResponse:
    ...

# Circuit breaker per provider
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.last_failure_time = None
```

---

## Patterns to Follow

### Pattern 1: API Gateway as Single Entry Point
**What:** All external traffic → API Gateway → internal services
**When:** Always (current implementation ✓)
**Example:**
```yaml
# api-gateway/application.yml
spring:
  cloud:
    gateway:
      routes:
        - id: ai-gateway
          uri: ${AI_GATEWAY_URL}
          predicates:
            - Path=/api/v1/**
          filters:
            - StripPrefix=1
            - name: RateLimitFilter
              args:
                key: "user:ai"
                limit: 20
                windowSeconds: 60
```

### Pattern 2: gRPC for High-Performance Internal Calls
**What:** AI Gateway → Backend via gRPC (protobuf)
**When:** Low-latency, high-throughput, schema-enforced calls
**Example:**
```protobuf
// backend/src/main/proto/finance.proto
service FinanceService {
  rpc CreateInvoice(CreateInvoiceRequest) returns (CreateInvoiceResponse);
  rpc GetFinancialSummary(FinancialSummaryRequest) returns (FinancialSummary);
}
```

### Pattern 3: Dual-Write Persistence (Migration Pattern)
**What:** Write to MongoDB (primary) + PostgreSQL (secondary) simultaneously
**When:** Live migration from document to relational
**Example:**
```java
// Backend: InvoiceService.create()
@Transactional
public Invoice create(CreateInvoiceRequest req) {
    Invoice mongo = invoiceMongoRepository.save(toMongo(req));
    InvoiceJpa jpa = invoiceJpaRepository.save(toJpa(req));
    // Reconciliation job verifies consistency
    return mongo;
}
```

### Pattern 4: AgentOS Message Bus (Actor Model)
**What:** In-process async message passing between agents
**When:** Multi-agent orchestration with governance
**Example:**
```python
# ai-gateway/app/agentos/message_bus.py
await message_bus.request(
    sender="ceo",
    receiver="finance_ops",
    payload={"action": "create_invoice", "params": {...}},
    correlation_id=correlation_id,
    org_id=org_id
)
```

### Pattern 5: Semantic Cache for LLM Cost Reduction
**What:** Embed query → search Pinecone → return cached if similarity > threshold
**When:** Repeated similar queries (common in finance: "cash flow", "overdue invoices")
**Example:**
```python
# ai-gateway/app/cache/semantic_cache.py
async def get_or_compute(query: str, compute_fn: Callable) -> Any:
    embedding = await embedder.embed(query)
    matches = await pinecone.query(embedding, top_k=1, threshold=0.85)
    if matches:
        return deserialize(matches[0].metadata["response"])
    result = await compute_fn()
    await pinecone.upsert(embedding, {"response": serialize(result), "query": query})
    return result
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Direct Service-to-Service HTTP Without Gateway
**What:** Frontend calls Backend directly; AI Gateway calls Backend directly without auth
**Why bad:** No central auth, rate limiting, observability, canary routing
**Instead:** All external + inter-service via Gateway (or service mesh)

### Anti-Pattern 2: Synchronous Chaining Without Timeouts
**What:** Voice → AI Gateway → Backend → MongoDB, no circuit breaker
**Why bad:** Cascading failure; one slow service blocks all
**Instead:** Timeouts + circuit breakers + async where possible

### Anti-Pattern 3: Shared Database Across Services
**What:** Backend and AI Gateway both write to same MongoDB collections
**Why bad:** Coupling, schema conflicts, scaling independence lost
**Instead:** Backend owns data; AI Gateway calls Backend API/gRPC

### Anti-Pattern 4: Hardcoded Secrets in Config
**What:** `JWT_SECRET: "dev-secret"` in application.yml
**Why bad:** Git leaks; no rotation; prod=dev
**Instead:** ExternalSecrets Operator → AWS Secrets Manager / Vault

### Anti-Pattern 5: No Request Correlation IDs
**What:** Logs don't connect Frontend → Gateway → Backend → AI Gateway
**Why bad:** Impossible to debug distributed requests
**Instead:** `X-Request-ID` generated at Gateway, propagated via headers, logged everywhere

---

## Scalability Considerations

| Concern | At 100 Users | At 10K Users | At 1M Users |
|---------|--------------|--------------|-------------|
| **API Gateway** | 2 replicas, CPU<50% | 6 replicas, HPA CPU>70% | 20+ replicas, multi-AZ, WAF |
| **Backend** | 2 replicas, H2 → PG | 6 replicas, read replicas | Sharding by org_id; CQRS |
| **AI Gateway** | 2 replicas, in-mem cache | 6 replicas, Redis cache | GPU pool for local models; model routing |
| **Voice** | 1 LiveKit node | 3 LiveKit nodes | Clustered LiveKit + media relay |
| **Redis** | Single node | Cluster mode (3 master) | Redis Enterprise / Dragonfly |
| **MongoDB** | M10 Atlas | M50 + read replicas | Sharded cluster (org_id) |
| **PostgreSQL** | Neon serverless | Neon scale + read replica | Aurora Limitless / Citus |
| **Observability** | Single Prometheus | Thanos sidecar | Cortex/Mimir + Tempo + Loki |

---

## Sources

- **Codebase**: `MoneyOps/docker-compose.yml`, `MoneyOps/api-gateway/src/main/resources/application*.yml`, `MoneyOps/ai-gateway/app/main.py`, `MoneyOps/ai-gateway/app/agentos/`, `MoneyOps/backend/src/main/java/com/moneyops/grpc/`
- **Documentation**: `docs/architecture.md` (Mermaid diagrams, service matrix)
- **Industry Patterns**: CNCF Microservices Patterns, Google SRE Book, AWS Well-Architected Framework