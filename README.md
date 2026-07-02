# MoneyOps — Financial SaaS Platform

## Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Frontend    │────>│  API Gateway  │────>│   Backend    │
│  (React/Vite)│     │  (Spring Cloud)│    │  (Spring Boot)│
│  Port 3000   │     │  Port 8002    │     │  Port 8000   │
└─────────────┘     └──────────────┘     └──────────────┘
       │                                       │
       │    ┌──────────────────────────┐       │
       └───>│     AI Gateway           │<──────┘
            │     (FastAPI)            │  gRPC :50051
            │     Port 8005            │  HTTP :8000
            └──────────────────────────┘
                     │
            ┌────────┴────────┐
            │                  │
       ┌────┴────┐      ┌─────┴─────┐
       │ MongoDB │      │ PostgreSQL │
       │ (Atlas) │      │  (Neon)    │
       └─────────┘      └───────────┘
```

## Services

| Service | Language | Port | Description |
|---------|----------|------|-------------|
| **Backend** | Java 17 / Spring Boot 3.2 | 8000 | Core business logic, REST API, MongoDB + PostgreSQL |
| **AI Gateway** | Python 3.11 / FastAPI | 8005 | Multi-agent orchestration, LLM routing, gRPC server |
| **Frontend** | React 18 / Vite 7 | 3000 | Web UI, dashboard, analytics |
| **API Gateway** | Java 17 / Spring Cloud Gateway | 8002 | API routing, JWT validation, rate limiting |
| **Voice Service** | Python / FastAPI | 8003 | Voice processing, STT/TTS (LiveKit) |

## Communication

- **Frontend → Backend**: HTTP REST (JSON)
- **Frontend → AI Gateway**: HTTP REST (JSON)
- **AI Gateway → Backend**: gRPC (primary, port 50051) + HTTP fallback (port 8000)
- **All services**: JWT-based auth via `Authorization: Bearer <token>`

## Data Stores

- **MongoDB Atlas** (primary): invoices, transactions, clients, users, organizations, budgets, documents, audit logs, org memory
- **PostgreSQL / Neon** (relational): users, organizations, clients (structured queries)
- **Pinecone** (vector): agent memory, compliance rules, semantic search
- **In-memory** (fallback): Redis sessions, rate limiting (Redis TBD)

## Agent System

The AI Gateway hosts a multi-agent orchestration system:

| Agent | Role | Capabilities |
|-------|------|-------------|
| **FinanceOps** | Financial operations | Invoices, payments, expenses, balances, summaries |
| **Compliance** | Regulatory | GST, TDS, tax filing, compliance deadlines |
| **Collections** | Receivables | Payment reminders, overdue escalation, aging analysis |
| **TReDS** | Working capital | Invoice discounting, marketplace rates |
| **Growth** | Strategy | Revenue forecasting, upsell, churn risk, optimization |

**Key features:**
- Multi-agent execution plans (sequential delegation)
- Cross-agent shared context (namespace-isolated memory)
- Decision evaluation — agents assess business impact before acting
- Goal-oriented routing — orchestrator derives business goals from health metrics
- BusinessContextProvider — real-time health scores, risk/opportunity detection

## Getting Started

```powershell
# 1. Start all services
.\start.ps1

# 2. Verify
curl http://localhost:8000/api/auth/register -X POST -H "Content-Type: application/json" -d '{"email":"demo@test.com","password":"test123","name":"Demo"}'
curl http://localhost:8005/api/v1/health
curl http://localhost:3000

# 3. Chat with agents
curl http://localhost:8005/api/v1/agent/chat -X POST -H "Content-Type: application/json" -d '{"message":"show me my financial summary","org_id":"<org_id>","user_id":"<user_id>"}'
```

## Environment Variables

See `.env.example` in each service for required configuration. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017/moneyops` | MongoDB connection string |
| `DATABASE_URL` | `jdbc:postgresql://localhost:5432/moneyops` | PostgreSQL connection string |
| `JWT_SECRET` | (must be 32+ chars) | JWT signing key |
| `GROQ_API_KEY` | — | LLM provider key |
| `REDIS_HOST` | (empty = in-memory) | Redis host |
| `GRPC_PORT` | `50051` | gRPC server port |

## CI/CD

GitHub Actions at `.github/workflows/ci.yml`:
- Python lint (ruff, flake8) + tests (pytest, coverage)
- Java build + tests (Maven)
- Runs on PR to `MoneyOps/**`
