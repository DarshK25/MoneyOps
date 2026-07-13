# MoneyOps Financial SaaS Platform

Intelligent finance orchestration platform with AI agents, voice-to-action pipeline, and multi-tenant architecture.

## Architecture Overview

| Service | Framework | Port | Description |
|:---|:---|:---:|:---|
| **Frontend** | React + Vite + Tailwind | 5173 | Admin dashboard with AI workspace, voice controls |
| **API Gateway** | Spring Cloud Gateway (Java 17) | 8002 | JWT auth, rate limiting, tenant isolation, routing |
| **Backend Core** | Spring Boot (Java 17) | 8000 | REST + gRPC + JPA + MongoDB dual-write |
| **AI Gateway** | FastAPI (Python) | 8005 | Multi-agent orchestrator, LLM multi-provider, semantic cache |
| **Voice Service** | LiveKit Agents (Python) | 5001 | WebRTC, STT/TTS, VAD, voice-to-action pipeline |

## Quick Start

```bash
# Prerequisites
# Java 17, Python 3.10+, Node 18+, PostgreSQL (Neon), MongoDB Atlas, Redis

# 1. Environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
cd MoneyOps/Frontend && npm install
cd ../backend && ./mvnw clean install -DskipTests
cd ../api-gateway && ./mvnw clean install -DskipTests
cd ../ai-gateway && pip install -r requirements.txt
cd ../voice-service && pip install -r requirements.txt

# 3. Start services (from repo root)
.\start.ps1
```

## Agent System

The AI Gateway runs **5 domain executors** coordinated by a **Master Orchestrator (CEO Agent)**:

| Executor | Role | Key Tools |
|:---|:---|:---|
| **FinanceOps** | Invoices, payments, expenses | `create_invoice`, `record_payment`, `get_financial_summary` |
| **Compliance** | GST, TDS, tax compliance | `check_compliance`, `get_compliance_status` |
| **Collections** | Overdue reminders, follow-ups | `send_collection_reminder`, `get_overdue_action_plan` |
| **TReDS** | Invoice discounting, working capital | `get_invoice_discounting_offers` |
| **Growth** | Forecast, churn, upsell | `get_cash_flow_forecast`, `get_growth_opportunities` |

### AgentOS Framework
- Message bus for inter-agent communication
- Decision engine for strategic planning
- Governance for policy enforcement
- Audit registry for execution tracing
- Memory (Pinecone + Redis) for cross-session state

## Voice Pipeline

```
User > LiveKit > VAD (Silero) > STT (Deepgram/Groq) > AI Gateway
  > Master Orchestrator > Domain Executor > Backend
  > Response > TTS (ElevenLabs/Deepgram) > User
```

The voice-service handles only audio I/O; all business logic is in the AI Gateway.

## Authentication

- **JWT**: Custom token-based auth with configurable expiry
- **OAuth2**: Google OAuth2 login with redirect flow
- **Service Tokens**: Internal service-to-service authentication
- **Multi-Tenant**: Org-scoped data isolation via X-Org-Id

## Data Stores

| Store | Usage |
|:---|:---|
| PostgreSQL (Neon) | JPA entities, Flyway migrations |
| MongoDB Atlas | Document storage for flexible schemas |
| Redis | Session state, rate limiting, job queue |
| Pinecone | Semantic cache for LLM queries |

## CI/CD

GitHub Actions workflows for backend, api-gateway, ai-gateway, and frontend with:
- Build & test
- Docker image build & push
- Multi-service integration tests

## Documentation

- `docs/architecture.md` - Full system architecture
- `docs/MoneyOps_Database_Schema.md` - Database schema reference
- `docs/test_endpoints.md` - API endpoint reference
- `docs/enterprise_upgrade_guide.md` - Production hardening guide
