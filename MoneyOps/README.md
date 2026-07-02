# MoneyOps

AI-powered financial operations platform for Indian SMEs. Agents automate invoicing, compliance (GST/TDS), collections, cash flow analysis, and financial intelligence.

## System Architecture

```
                             ┌──────────────────────────────────────────────────────────────┐
                             │                        Frontend                             │
                             │              React 18 / Vite 7 / Tailwind                   │
                             │                    Port 3000 / :80                          │
                             └──────────────────────┬───────────────────────────────────────┘
                                                     │ HTTP / WebSocket
                             ┌──────────────────────▼───────────────────────────────────────┐
                             │                     API Gateway                             │
                             │              Spring Cloud Gateway (WebFlux)                 │
                             │                    Port 8002                                │
                             │  ┌──────────┬──────────┬───────────┬────────────────────┐    │
                             │  │ JWT Auth │ Rate     │ CORS      │ Request Logging   │    │
                             │  │ Filter   │ Limiting │           │ + Duration         │    │
                             │  └──────────┴──────────┴───────────┴────────────────────┘    │
                             └──────┬───────────────────────────────┬───────────────────────┘
                                     │                               │
                    ┌────────────────▼────────────┐     ┌───────────▼────────────────┐
                    │          Backend             │     │       AI Gateway           │
                    │    Spring Boot 3.2 / Java 21 │     │    Python FastAPI          │
                    │         Port 8000            │     │     Port 8005              │
                    │  ┌──────────────────────┐    │     │  ┌─────────────────────┐   │
                    │  │ REST API (JSON)      │    │     │  │ Agent Orchestrator  │   │
                    │  │ gRPC Server :50051   │    │     │  │ Intent Classifier   │   │
                    │  │ JWT Auth + OAuth2    │    │     │  │ 5 Executors         │   │
                    │  │ Razorpay Payments    │    │     │  │ AgentOS Framework   │   │
                    │  │ PDF Invoices         │    │     │  │ Multi-LLM (Groq,    │   │
                    │  │ Async Workers (Redis)│    │     │  │  Anthropic, OpenAI) │   │
                    │  └──────────────────────┘    │     │  │ gRPC Client :50051  │   │
                    └─────────┬────────────────────┘     │  │ Voice Processor     │   │
                              │                          │  │ Pinecone Vector DB  │   │
                    ┌─────────▼────────────────┐         └──────────────────────────┘   │
                    │  Dual Persistence       │                                          │
                    │  ┌─────────┐┌────────┐  │         ┌───────────────────────────────┘
                    │  │ MongoDB ││Postgres│  │         │
                    │  │ (Atlas) ││(Neon)  │  │         │
                    │  │Primary  ││Dual-   │  │         │
                    │  │         ││write   │  │         │
                    │  └─────────┘└────────┘  │         │
                    └─────────────────────────┘         │
                                                        │
                    ┌────────────────────────────┐      │
                    │      Voice Service         │◄─────┘
                    │   Python / LiveKit Agent   │
                    │        Port 8003           │
                    │  ┌────────────────────┐    │
                    │  │ Deepgram STT       │    │
                    │  │ ElevenLabs /       │    │
                    │  │ Deepgram TTS       │    │
                    │  │ VAD (WebRTC)       │    │
                    │  │ Session Manager    │    │
                    │  └────────────────────┘    │
                    └────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Async Workers (Redis Queue)                               │
│           email_worker.py              notification_worker.py                       │
│           Sends transactional emails   Sends push notifications                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Microservices Overview

| Service | Stack | Port | Purpose |
|---------|-------|------|---------|
| **API Gateway** | Spring Cloud Gateway / Java 21 | 8002 | Edge routing, JWT auth, rate limiting, CORS |
| **Backend** | Spring Boot 3.2 / Java 21 | 8000 | REST API, business logic, dual persistence |
| **AI Gateway** | Python FastAPI | 8005 | LLM orchestration, multi-agent system, compliance |
| **Voice Service** | Python / LiveKit Agent | 8003 | Real-time voice conversations with AI |
| **Frontend** | React 18 / Vite 7 / Tailwind | 3000 | Web dashboard (25+ pages) |
| **Email Worker** | Python / Redis Queue | — | Async email dispatch |
| **Notification Worker** | Python / Redis Queue | — | Async notification dispatch |

## Quick Start (Local Development)

**Prerequisites:** Java 21, Python 3.11+, Node.js 20+, Docker (for Redis), MongoDB Atlas account, Neon PostgreSQL account.

```bash
# 1. Clone and configure
git clone <repo>
cd MoneyOps
cp .env.example .env   # Fill in secrets (see section below)

# 2. Start Redis (required for rate limiting + workers)
docker compose up -d redis

# 3. Start Backend
cd backend
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# 4. Start AI Gateway (in another terminal)
cd ai-gateway
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# 5. Start Frontend (in another terminal)
cd Frontend
npm install
npm run dev

# 6. (Optional) Start API Gateway
cd api-gateway
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev

# 7. (Optional) Start Voice Service
cd voice-service
pip install -r requirements.txt
python -m app.cli.entrypoint  # or run agent directly
```

### Docker (Full Stack)

```bash
docker compose up -d --build
```

This starts all services plus Redis and workers. See `docker-compose.yml`.

## Required Environment Variables

Copy `.env.example` to `.env` and fill in:

| Category | Variable | Required | Source |
|----------|----------|----------|--------|
| **MongoDB** | `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| **PostgreSQL** | `DATABASE_URL` | Yes | Neon / any PostgreSQL JDBC URL |
| **JWT** | `JWT_SECRET` | Yes | 256-bit key (min 32 chars) |
| **Google OAuth** | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Optional | Google Cloud Console |
| **Email** | `RESEND_API_KEY` | Yes | Resend.com |
| **Groq** | `GROQ_API_KEY`, `GROQ_API_KEY_FAST` | Yes | Groq console |
| **Anthropic** | `ANTHROPIC_API_KEY` | Optional | Anthropic console |
| **LiveKit** | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | Yes* | LiveKit Cloud (*required for voice) |
| **Deepgram** | `DEEPGRAM_API_KEY` | Optional | Deepgram console (STT/TTS) |
| **ElevenLabs** | `ELEVENLABS_API_KEY` | Optional | ElevenLabs console (TTS) |
| **Pinecone** | `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | Optional | Pinecone console (agent memory) |

> For local dev without voice, you can skip LiveKit/Deepgram/ElevenLabs vars.

## Database

### MongoDB Atlas (Primary Operational DB)
13 collections: `clients`, `users`, `invoices`, `transactions`, `business_organizations`, `invites`, `recurring_invoices`, `budgets`, `documents`, `audit_logs`, `org_memory`, `regulatory_profiles`, `team_invites`.

### Neon PostgreSQL (Relational Data - Dual Write)
Tables: `organizations`, `users`, `clients`, `invoices`, `transactions`.

The backend writes to **both** MongoDB (primary) and PostgreSQL (dual-write) on create/update operations. Reads prefer PostgreSQL and fall back to MongoDB. This is a live migration strategy — MongoDB remains the source of truth until PostgreSQL is fully validated.

### Pinecone (Vector DB)
Stores embeddings for agent memory and RAG. Used by `MemoryManager` for long-term agent recall.

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Dual persistence** | Live migration from MongoDB to PostgreSQL; write to both, read from PG with Mongo fallback |
| **gRPC between services** | Low-latency communication for agent→backend calls |
| **API Gateway as edge** | Single entry point for auth, rate limiting, routing; backend and AI gateway are not exposed directly |
| **AgentOS framework** | Modular agent architecture with message bus, governance, decision engine, audit trail |
| **Multi-provider LLM** | Groq primary (speed), Anthropic fallback (accuracy), OpenAI as final fallback |
| **Redis for rate limiting + queues** | Shared cache for distributed rate limiting across gateway instances; async job queue |
| **JWT-based auth** | Stateless authentication shared between backend and API gateway via same JWT secret |

## Development Workflow

```bash
# Backend (Java)
cd backend
./mvnw clean compile                    # Build
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev  # Run
./mvnw test -pl=service-module          # Tests

# Frontend (React)
cd Frontend
npm run dev                             # Dev server with hot reload
npm run build                           # Production build
npm run lint                            # Lint check
npm run preview                         # Preview production build

# AI Gateway (Python)
cd ai-gateway
python -m pytest tests/ -v              # Run tests
ruff check app/                         # Lint
mypy app/                               # Type check

# API Gateway (Java - optional standalone)
cd api-gateway
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev
```

## Project Structure

```
MoneyOps/
├── backend/                # Spring Boot (REST + gRPC + persistence)
│   ├── src/main/java/com/moneyops/
│   │   ├── auth/           # JWT, OAuth2, login/register
│   │   ├── invoices/       # Invoice CRUD, PDF, recurring
│   │   ├── clients/        # Client management
│   │   ├── transactions/   # Income/expense ledger
│   │   ├── organizations/  # Business orgs + verification
│   │   ├── users/          # Users + team invites
│   │   ├── payments/       # Razorpay integration
│   │   ├── compliance/     # GST/TDS calculation
│   │   ├── intelligence/   # Financial metrics
│   │   ├── grpc/           # gRPC service stubs
│   │   ├── jpa/            # JPA entities + repos (PostgreSQL)
│   │   ├── queue/          # Redis async job queue
│   │   ├── documents/      # Document management
│   │   ├── audit/          # Audit logging
│   │   └── security/       # Team auth, security codes
│   └── src/main/resources/
│       ├── application.yml
│       ├── application-dev.yml
│       └── db/migration/   # Flyway migrations
│
├── api-gateway/            # Spring Cloud Gateway (edge)
│   ├── src/main/java/com/moneyops/gateway/
│   │   ├── config/         # Security, Redis, WebFlux, RateLimit keys
│   │   ├── filter/         # Auth, RateLimit, Logging, Tenant, Duration
│   │   └── security/       # JWT token provider
│   └── src/main/resources/
│       ├── application.yml       # Main config (env defaults)
│       ├── application-dev.yml   # Dev overrides
│       └── application-prod.yml  # Production overrides
│
├── ai-gateway/             # FastAPI (LLM orchestration)
│   └── app/
│       ├── main.py         # FastAPI app + routers
│       ├── agents/         # MasterOrchestrator + executors
│       ├── agentos/        # Agent Operating System
│       ├── orchestration/  # Intent classifier, entity extractor
│       ├── adapters/       # Backend HTTP/gRPC adapters
│       ├── llm/            # Multi-provider LLM client
│       ├── memory/         # Pinecone vector memory
│       └── integrations/   # Redis, TReDS client
│
├── voice-service/           # Python LiveKit Agent (voice)
│   └── app/
│       ├── agent/          # LiveKit voice agent
│       ├── api/            # Health endpoint
│       ├── cli/            # CLI entrypoint
│       ├── config.py       # Config from env
│       └── utils/          # VAD, TTS utilities
│
├── Frontend/               # React 18 / Vite 7
│   └── src/
│       ├── pages/          # 25+ page components
│       ├── components/     # Shared UI components
│       ├── lib/            # API client, auth helpers
│       ├── contexts/       # Auth, onboarding state
│       └── utils/          # Date formatting, chart config
│
├── scripts/                # Backfill + workers
│   ├── backfill_compliance_fields.py
│   ├── backfill_voltnest_compliance_fields.py
│   └── workers/            # email_worker, notification_worker
│
├── data/                   # Local SQLite fallback (dev)
├── docker-compose.yml       # Full stack orchestration
└── .env.example             # Env template
```

## Service Dependencies

```
Frontend ───> API Gateway ──┬──> Backend ──┬──> MongoDB Atlas
                             │              └──> Neon PostgreSQL
                             ├──> AI Gateway ─┬──> Groq / Anthropic / OpenAI
                             │                ├──> Pinecone
                             │                └──> Backend (gRPC :50051 / HTTP :8000)
                             └──> Voice Service ─┬──> Deepgram / ElevenLabs
                                                  └──> AI Gateway
              Redis ◄──────────────────────────── All services (cache + queues)
```

## Security Model

1. **Authentication**: JWT-based stateless auth. Backend issues tokens on login/register.
2. **API Gateway**: Validates every JWT on protected routes; injects `X-User-Id` and `X-Org-Id` headers from the token (not from client input — prevents spoofing).
3. **Rate Limiting**: Redis-based token bucket per route type — auth (10/min per IP), AI (20/min per user), backend (100/min per user), voice (30/min per user).
4. **Tenant Isolation**: `TenantContextFilter` ensures every tenant-scoped request has a valid `X-Org-Id` (from JWT). Returns 403 if missing.
5. **CORS**: Restrictive in production (only specific frontend origins).
6. **gRPC**: Internal only (not exposed publicly). Service token validation.

## API Documentation

- **Backend Swagger UI**: `http://localhost:8000/swagger-ui.html` (when running)
- **Backend endpoints**: All under `/api/` with JWT auth
- **AI Gateway**: All under `/api/v1/` through API Gateway
- **Public endpoints**: `/api/auth/login`, `/api/auth/register`, `/actuator/health`

## Testing

```bash
# Backend
cd backend && ./mvnw test

# AI Gateway
cd ai-gateway && python -m pytest tests/ -v

# Frontend (if tests configured)
cd Frontend && npm test

# API Gateway
cd api-gateway && ./mvnw test
```

## Deployment

Services deploy as Docker containers. Production requires:

- **Redis**: Upstash (serverless) or ElastiCache
- **MongoDB**: Atlas M10+ cluster
- **PostgreSQL**: Neon (serverless) or RDS
- **Compute**: Any Docker host (ECS, K8s, VPS)
- **API Gateway**: Must set `JWT_SECRET`, `SPRING_PROFILES_ACTIVE=prod`
