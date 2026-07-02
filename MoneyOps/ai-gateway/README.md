# MoneyOps AI Gateway

FastAPI microservice that routes natural-language requests to domain executors, backed by multi-provider LLM and gRPC/HTTP backend integration. Serves the voice-agent and REST API clients.

## Data Flow (request → response)

```
Client (HTTP)
  │ POST /api/v1/agent/chat
  │ POST /api/v1/voice/process
  │ POST /api/v1/compliance/check
  │ GET  /api/v1/health
  ▼
┌─────────────────────────────────────┐
│  API Layer (app/api/v1/)            │
│  - agent.py → MasterOrchestrator    │
│  - voice.py → AgentRouter           │
│  - compliance.py → MasterOrchestrator│
│  - market.py → MasterOrchestrator   │
│  - health.py → HeartbeatScheduler   │
│  - test_agents.py, test_llm.py (DEV)│
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  Orchestration (app/orchestration/) │
│  - agent_router.py: Intent→Executor │
│  - intent_classifier.py: NL→Intent  │
│  - entity_extractor.py: NL→Entities │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  MasterOrchestrator (agents/)       │
│  Delegates to specialized executor  │
│  based on classified intent         │
└──────┬──────────────────────┬───────┘
       │                      │
┌──────▼──────┐     ┌────────▼───────┐
│ Backend API  │     │  LLM Client    │
│ gRPC :50051  │     │  (fallback)    │
│ HTTP :8000   │     │  Groq/Anthropic│
└──────────────┘     └────────────────┘
       │
       ▼  External Backend (MoneyOps API)
```

## Directory Structure

```
ai-gateway/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, routers
│   ├── config.py                # pydantic-settings (env-driven)
│   ├── voice_processor.py       # Voice utterance → text pipeline
│   ├── api/v1/
│   │   ├── agent.py             # POST /agent/chat
│   │   ├── voice.py             # POST /voice/process
│   │   ├── compliance.py        # POST+GET /compliance/*
│   │   ├── market.py            # GET /market/*
│   │   ├── health.py            # GET /health
│   │   ├── test_agents.py       # Dev-only test endpoints
│   │   └── test_llm.py          # Dev-only LLM test
│   ├── agents/                  # Agent system (executors + helpers)
│   │   ├── master_orchestrator.py   # CEO agent, delegates to executors
│   │   ├── base_executor.py         # FinanceExecutor, ComplianceExecutor, CollectionsExecutor, TReDSExecutor
│   │   ├── base_agent.py            # BaseAgent base class
│   │   ├── compliance_agent.py      # ComplianceAgent (BaseAgent subclass - dead code)
│   │   ├── general_agent.py         # GeneralAgent (BaseAgent subclass - test-only)
│   │   ├── growth.py                # GrowthExecutor
│   │   ├── business_context.py      # Real-time metrics, health score
│   │   ├── heartbeat.py             # APScheduler autonomous cycles
│   │   ├── activity_stream.py       # WebSocket event publisher
│   │   └── voice_helpers.py         # Voice intent→action, parser functions
│   ├── agentos/                 # Agent Operating System
│   │   ├── message_bus.py       # Inter-agent pub/sub
│   │   ├── decision.py          # Decision engine (scoring)
│   │   ├── governance.py        # Policy/rules engine
│   │   ├── observation.py       # Audit trail registry
│   │   ├── memory.py            # Agent memory (short/long-term)
│   │   ├── learning.py          # Learning layer (outcome tracking)
│   │   ├── roi.py               # ROI tracker (value generated)
│   │   ├── identity.py          # Agent identity definitions
│   │   └── types.py             # Shared type definitions
│   ├── orchestration/
│   │   ├── agent_router.py      # Intent→executor routing
│   │   ├── intent_classifier.py # NL→Intent classification
│   │   └── entity_extractor.py  # NL→Entity extraction
│   ├── adapters/
│   │   ├── backend_adapter.py   # HTTP adapter to backend API
│   │   └── grpc_client.py       # gRPC client to backend :50051
│   ├── llm/
│   │   └── multi_provider.py    # Multi-LLM client (Groq, Anthropic, OpenAI)
│   ├── tools/
│   │   └── tool_registry.py     # Tool definitions + executor
│   ├── schemas/
│   │   ├── entities.py          # Entity schemas
│   │   ├── heartbeat.py         # Heartbeat schemas
│   │   ├── intents.py           # Intent + AgentType enums
│   │   └── treds.py             # TReDS schemas
│   ├── models/
│   │   └── draft.py             # InvoiceDraft, ClientDraft, etc.
│   ├── memory/
│   │   └── pinecone_manager.py  # Pinecone vector DB
│   ├── integrations/
│   │   ├── redis_client.py      # Redis (in-memory fallback)
│   │   └── treds_client.py      # TReDS platform client
│   ├── state/
│   │   └── session_manager.py   # Voice session state
│   ├── middleware/
│   │   └── rate_limit.py        # Token-bucket rate limiter
│   ├── grpc/
│   │   ├── server.py            # gRPC server :50052
│   │   └── gen/                 # Generated protobuf stubs
│   └── utils/
│       ├── amount_parser.py     # Amount text→number
│       ├── date_parser.py       # Date text→datetime
│       ├── logger.py            # Structured logging
│       ├── tts_sanitizer.py     # TTS-safe text
│       └── voice_text.py        # Voice text utilities
├── tests/
│   ├── test_pipeline_fixes.py   # Bug regression tests
│   ├── test_voice_gateway_regressions.py
│   └── test_llm_client.py
├── voice_agent_worker.py        # LiveKit Agent worker (standalone)
├── _test_learning_roi.py        # Ad-hoc learning/ROI test script
├── conftest.py                  # Pytest fixtures
├── pyproject.toml
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Agents and Their Roles

### Executors (task executors, used by MasterOrchestrator)

| Agent | Role | Operations |
|-------|------|------------|
| `FinanceExecutor` | `finance_ops` | create invoice, record payment, record expense, balance check, invoice query, financial summary |
| `ComplianceExecutor` | `compliance` | GST calculation, compliance deadlines, reconciliation, dashboard |
| `CollectionsExecutor` | `collections` | send reminders, escalate overdue, collections dashboard |
| `TReDSExecutor` | `treds` | invoice discounting, eligible invoices, rates, dashboard |
| `GrowthExecutor` | `growth` | revenue forecast, upsell, churn risk, TReDS optimization |

### Agents (BaseAgent subclasses)

| Agent | File | Status |
|-------|------|--------|
| `ComplianceAgent` | `app/agents/compliance_agent.py` | **Active** - wired into `AgentRouter.route()` for `GST_QUERY`, `COMPLIANCE_QUERY`, `COMPLIANCE_CHECK`, `COMPLIANCE_REPORT`, `TAX_OPTIMIZATION`, `TAX_CALCULATION`, `AUDIT_READINESS` intents. Calls backend via `BackendHttpAdapter`, returns tool-driven `AgentResponse`. |
| `GeneralAgent` | `app/agents/general_agent.py` | **Active** - wired into `AgentRouter.route()` for `GREETING`, `HELP`, `GENERAL_QUERY` intents. Rule-based responses + fallback LLM. |

### Orchestrator

| Agent | Role | Responsibility |
|-------|------|----------------|
| `MasterOrchestrator` | CEO | Receives all user messages, classifies intent, delegates to executor, evaluates decisions, returns response. Coordinates goal-aligned multi-agent execution. |
| `AgentRouter` | Bridge | Translates voice intents into `MasterOrchestrator.process()` calls. Used by `voice.py` and `voice_agent_worker.py`. |
| `IntentClassifier` | Classifier | Maps NL text to `Intent` enum. |
| `EntityExtractor` | Parser | Extracts structured entities from NL text. |

### AgentOS (operating system for agents)

| Component | File | Function |
|-----------|------|----------|
| `message_bus` | `app/agentos/message_bus.py` | Pub/sub message bus for inter-agent communication |
| `decision_engine` | `app/agentos/decision.py` | Scores decisions 0-100, recommends proceed/caution/block |
| `governance` | `app/agentos/governance.py` | Policy registry, rule enforcement |
| `audit_registry` | `app/agentos/observation.py` | Immutable audit trail for agent actions |
| `agent_memory` | `app/agentos/memory.py` | Short-term + long-term memory per agent |
| `agent_learning` | `app/agentos/learning.py` | Outcome tracking, action recommendation |
| `roi_tracker` | `app/agentos/roi.py` | Value generated per agent |
| `identity` | `app/agentos/identity.py` | Agent identity definitions + capabilities |
| `types` | `app/agentos/types.py` | Shared type definitions (AgentID, etc.) |

## API Endpoints

| Method | Path | Description | Router |
|--------|------|-------------|--------|
| GET | `/` | API info | main.py |
| GET | `/api/v1/health` | Service health + executor status | health.py |
| POST | `/api/v1/agent/chat` | Multi-agent chat | agent.py |
| GET | `/api/v1/agent/health` | Orchestrator health | agent.py |
| GET | `/api/v1/agent/executors` | List available executors | agent.py |
| POST | `/api/v1/voice/process` | Voice command | voice.py |
| POST | `/api/v1/compliance/check` | Compliance check | compliance.py |
| POST | `/api/v1/compliance/gst/file` | File GST return | compliance.py |
| GET | `/api/v1/compliance/tds/status` | TDS status | compliance.py |
| GET | `/api/v1/market/*` | Market intelligence | market.py |
| POST | `/api/v1/test/agents` | Test agents (dev only) | test_agents.py |
| POST | `/api/v1/test/llm` | Test LLM (dev only) | test_llm.py |

## Infrastructure

| Infrastructure | Technology | Port |
|----------------|------------|------|
| HTTP server | uvicorn + FastAPI | 8005 |
| gRPC server | grpcio | 50052 |
| Backend gRPC | grpcio (client) | 50051 |
| Backend HTTP | httpx (client) | 8000 |
| Cache | Redis (optional, in-memory fallback) | 6379 |
| Vector DB | Pinecone | - |
| LLM providers | Groq, Anthropic, OpenAI | - |

## Configuration

All config via environment variables (see `.env.example`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | - | JWT signing key (≥32 chars) |
| `INTERNAL_SERVICE_TOKEN` | Yes | - | Inter-service auth token |
| `GROQ_API_KEY` | No | - | Groq LLM provider |
| `ANTHROPIC_API_KEY` | No | - | Anthropic LLM provider |
| `REDIS_HOST` | No | `localhost` | Redis for rate-limit storage |
| `REDIS_PASSWORD` | No | - | Redis auth |
| `PINECONE_API_KEY` | No | - | Pinecone vector DB |
| `HOST` | No | `0.0.0.0` | HTTP bind address |
| `PORT` | No | `8005` | HTTP port |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

## Running

```bash
# Install
cd ai-gateway
python -m venv venv && venv\Scripts\activate  # Windows
# python -m venv venv && source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# Production
docker build -t moneyops-ai-gateway .
docker run -p 8005:8005 -p 50052:50052 --env-file .env moneyops-ai-gateway

# Tests
python -m pytest tests/ -v

# Lint
ruff check app/
```
