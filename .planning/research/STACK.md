# Technology Stack

**Project:** MoneyOps  
**Researched:** 2026-07-14

---

## Recommended Stack

### Core Frameworks

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Spring Boot** | 3.2.x | Backend REST + gRPC | Mature, enterprise-grade, strong ecosystem for financial systems; Java 21 LTS |
| **Spring Cloud Gateway** | 2023.x | API Gateway | Reactive, integrates with Spring Security, Redis rate limiting, circuit breaker |
| **FastAPI** | 0.109+ | AI Gateway | Async-native, best-in-class Python for LLM orchestration, Pydantic validation |
| **React** | 18.3+ | Frontend | Ecosystem, hiring pool, concurrent features; Vite 7 for fast builds |
| **LiveKit Agents** | 0.8+ | Voice Service | WebRTC-native, STT/TTS/VAD pluggable, scales via LiveKit Cloud |

### Databases

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **MongoDB Atlas** | 7.0+ | Primary operational DB | Flexible schema for invoices, documents, audit logs; Atlas manages scaling/backup |
| **PostgreSQL (Neon)** | 16+ | Relational/Reporting | ACID for users, orgs, clients, transactions; Neon serverless = cost-efficient dev |
| **Redis** | 7.2+ | Cache + Queues + Rate Limit | Single Redis for all three patterns; Upstash/ElastiCache for prod |
| **Pinecone** | Serverless | Vector DB for Agent Memory | Managed, namespace isolation per org, hybrid search |

### Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Docker** | 24+ | Containerization | Multi-stage builds per service; standard |
| **Kubernetes (EKS/GKE)** | 1.28+ | Orchestration | Industry standard; HPA, pod disruption budgets, OIDC |
| **Terraform** | 1.8+ | IaC | GitOps prerequisite; state management, module reuse |
| **ArgoCD** | 2.9+ | GitOps | Declarative deploy, automated sync, rollback, RBAC |
| **Helm** | 3.13+ | K8s packaging | Templating, dependencies, releases |

### Observability (NEW — Phase 1)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **OpenTelemetry** | 1.42+ (Java), 1.22+ (Python), 1.9+ (JS) | Instrumentation | Vendor-neutral, auto-instrumentation for Spring/FastAPI/React |
| **Prometheus** | 2.50+ | Metrics storage | CNCF standard, PromQL, integrates with everything |
| **Grafana** | 11+ | Dashboards/Alerting | Best-in-class viz, Loki/Tempo/Jaeger datasources, alerting |
| **Loki** | 3.0+ | Log aggregation | Label-based, cheap object storage backend, Grafana-native |
| **Tempo** | 2.5+ | Distributed tracing | Object storage backend, no index, cost-effective at scale |
| **Alertmanager** | 0.27+ | Alert routing | Grouping, inhibition, silences; PagerDuty/Slack/email receivers |
| **k6** | 0.50+ | Load testing | Scriptable, CI-integratable, Prometheus output |

### Security (NEW — Phase 2)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **cert-manager** | 1.14+ | mTLS certificates | Automates Let's Encrypt / private CA for service mesh |
| **Istio** | 1.22+ or **Linkerd** | 2.16+ | Service mesh | mTLS, traffic splitting, retries, timeouts, authz policies declaratively |
| **Trivy** | 0.50+ | Vulnerability scanning | Container + FS + repo scanning; fast, low false positives |
| **GitLeaks** | 8.18+ | Secret scanning | Pre-commit + CI; catches keys in history |
| **CodeQL / SonarQube** | Latest | SAST | GitHub Advanced Security free for public; deep semantic analysis |
| **OWASP ZAP** | 2.14+ | DAST | Active scanning in staging pipeline |
| **Kyverno** | 1.12+ | K8s policy engine | Admission control for pod security, image verification |

### AI Security (NEW — Phase 3)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Microsoft Presidio** | 2.2+ | PII detection/redaction | NER + regex + context; supports custom entities (GSTIN, PAN, Aadhaar) |
| **Rebuff / Lakera Guard** | Latest | Prompt injection detection | Purpose-built for LLM security; heuristic + embedding classifiers |
| **LangSmith / LangFuse** | Latest | LLM observability | Tracing, evaluation, cost tracking, prompt versioning |
| **Guardrails AI** | 0.5+ | Output validation | Pydantic-based schema enforcement, competitor detection |
| **LiteLLM** | 1.40+ | LLM gateway / cost control | Unified API, fallbacks, budgets, routing, logging |

### CI/CD (NEW — Phase 4)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **GitHub Actions** | — | CI/CD runner | Native, OIDC for cloud auth, reusable workflows |
| **Docker Buildx** | — | Multi-arch builds | BuildKit, cache, SBOM generation |
| **Cosign / Syft** | — | Image signing + SBOM | SLSA compliance, supply chain security |
| **Pact** | 2.2+ (JVM), 1.2+ (Python) | Contract testing | Consumer-driven contracts between Gateway↔Backend, Gateway↔AI |
| **Renovate** | 37+ | Dependency updates | Automated PRs, grouping, scheduling |

### Developer Experience (NEW — Phase 5)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Backstage** | 1.28+ | Developer portal | Service catalog, docs, templates, scorecards |
| **Unleash** | 5.5+ | Feature flags | Open source, Gradual rollouts, kill switches |
| **Redocly / Scalar** | Latest | API docs portal | OpenAPI 3.1, interactive, versioned |
| **Sentry** | Latest | Frontend error tracking | Session replay, release tracking, alerts |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| **Service Mesh** | Istio | Linkerd | Istio has larger ecosystem, WASM plugins, better multi-cluster; Linkerd simpler but less flexible |
| **Observability Backend** | Prometheus + Loki + Tempo | Datadog / New Relic / Grafana Cloud | Cost at scale; self-hosted stack is free and portable |
| **AI Gateway** | LiteLLM | Portkey / Helicone | LiteLLM has broader provider support, budgets, fallbacks, open source |
| **PII Detection** | Presidio | AWS Comprehend / Google DLP | Presidio is self-hosted, extensible, no data egress |
| **GitOps** | ArgoCD | Flux | ArgoCD UI better for multi-cluster, App of Apps pattern |
| **Load Testing** | k6 | Locust / JMeter | k6 is scriptable in JS, CI-native, Prometheus output |

---

## Installation

```bash
# Core (already present)
# Backend: Maven wrapper in MoneyOps/backend/
# AI Gateway: pip install -r MoneyOps/ai-gateway/requirements.txt
# Frontend: npm install in MoneyOps/Frontend/

# Observability (Phase 1)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts

# Install kube-prometheus-stack (Prometheus + Grafana + Alertmanager)
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Install Loki + Tempo
helm install loki grafana/loki-stack -n monitoring
helm install tempo grafana/tempo-distributed -n monitoring

# OpenTelemetry Operator for auto-instrumentation
helm install opentelemetry-operator open-telemetry/opentelemetry-operator \
  -n observability --create-namespace

# Security (Phase 2)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace --set installCRDs=true

# Istio (or Linkerd)
istioctl install --set profile=default -y

# AI Security (Phase 3)
pip install presidio-analyzer presidio-anonymizer guardrails-ai litellm

# CI/CD (Phase 4) - GitHub Actions workflows in .github/workflows/
# Terraform in infra/terraform/
# ArgoCD: kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

---

## Sources

- **Context7 / Official Docs**: Spring Boot 3.2, Spring Cloud 2023, FastAPI 0.109, React 18, LiveKit Agents 0.8
- **Codebase**: `MoneyOps/backend/pom.xml`, `MoneyOps/ai-gateway/requirements.txt`, `MoneyOps/Frontend/package.json`, `MoneyOps/docker-compose.yml`
- **Architecture Docs**: `docs/architecture.md`, `docs/enterprise_upgrade_guide.md`
- **Industry Standards**: CNCF Landscape 2024, OWASP Top 10 for LLMs 2024, SLSA Supply Chain Levels