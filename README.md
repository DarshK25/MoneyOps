# 💸 MoneyOps: Intelligent Financial Orchestration

> **Status**: Phase 5 Complete (Smart CRM & Market Intelligence) 🚀
> **Architecture**: Distributed AI Microservices with Founder Intelligence Layer

MoneyOps is a next-generation financial platform that orchestrates **AI Agents** to handle invoicing, payments, CRM, and business intelligence via **Voice** and **Chat** interfaces. It leverages a "CEO Brain" architecture to go beyond simple CRUD operations.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    classDef default font-size:16px,padding:8px;
    classDef subgraphTitle font-size:18px,font-weight:bold;

    subgraph ClientLayer [Client Layer]
        direction LR
        WebApp[Web App - React]
        LiveKitVoice[Voice Interface - LiveKit]
    end

    subgraph APIGatewayLayer [API Gateway - Spring Boot]
        direction TB
        APIGateway[Cloud Gateway] --> RateLimiter[Redis Rate Limiter] & Auth[JWT / Clerk Validation]
    end

    subgraph VoiceServiceLayer [Voice Service - Python/LiveKit]
        direction LR
        LiveKitAgent[LiveKit Framework] --> VAD[Silero VAD] & STT[AssemblyAI/Groq] & TTS[Cartesia/Groq]
    end

    subgraph AIGatewayLayer [AI Gateway - FastAPI]
        direction TB
        Intent[Intent Classifier] --> AgentRouter[Agent Router] 
        AgentRouter --> AgentsBox[Agents: Finance, Sales, Compliance, Market, Orchestrator]
        AgentsBox --> SessionMgr[Session Manager - Redis]
    end

    subgraph BackendCoreLayer [Backend Core - Spring Boot]
        direction TB
        CoreServices[OrgAdmin, Invoice, Client, Onboarding Services]
        Intelligence[Founder Intelligence Layer]
        CoreServices -->|Lead Scoring| Intelligence
    end

    subgraph DataLayer [Data Layer]
        direction LR
        MongoDB[(MongoDB Atlas)]
        RedisCache[(Redis - Cache/Sessions)]
        KafkaBus{Kafka Event Bus}
    end

    subgraph ExternalAPIs [External Integrations]
        direction LR
        Groq[Groq LLM]
        Tavily[Tavily Search]
        LiveKitCloud[LiveKit RTC Cloud]
    end

    %% Optimized Cross-Connections to avoid spreading
    WebApp -->|HTTPS| APIGateway
    LiveKitVoice -->|WebRTC| LiveKitCloud <--> LiveKitAgent
    
    APIGateway --> BackendCoreLayer & AIGatewayLayer
    LiveKitAgent -->|Intercept| AIGatewayLayer
    
    AgentsBox -->|Synthesis| Groq
    AgentsBox -->|Search| Tavily
    
    BackendCoreLayer --> MongoDB & RedisCache & KafkaBus
    AIGatewayLayer --> RedisCache
```

---

## 🧠 Data Flow & Intelligence Pipeline

1. **Transcript Interception**: Speech is captured via LiveKit, transcribed (AssemblyAI/Groq), and intercepted by the `Voice Service`.
2. **Intent Classification**: The `AI Gateway` classifies input into Operational, Strategic, or Conversational intents using Llama 3.3.
3. **Founder Enrichment**: For actions like `CLIENT_CREATE`, the system automatically:
    - Infers industry and business type.
    - Calculates a Lead Score (CEO-level value assessment).
    - Generates Smart Notes for CRM (pitch angles, ESG compliance).
4. **Backend Execution**: Core services update MongoDB and broadcast events via Kafka.
5. **CEO Summary**: The `Orchestrator` synthesizes data from Finance, Market, and Compliance agents to provide an actionable voice response.

---

## 🚀 System Components

| Service | Tech Stack | Description |
| :--- | :--- | :--- |
| **Backend Core** | Java 17, Spring Boot, MongoDB | REST API, Business Logic, Organization Isolation |
| **API Gateway** | Spring Cloud Gateway, Redis | Traffic Routing, Auth, Rate Limiting |
| **AI Gateway** | Python, FastAPI, Groq | multi-Agent Orchestration, Tool Registry, LLM Synthesis |
| **Voice Service** | Python, LiveKit Agents | Real-time Voice I/O with VAD-split utterance buffering |
| **Frontend** | React, LiveKit SDK | Intelligent Web Dashboard & Voice UI |

---

## 🛠️ Technology Stack & Third-party APIs

- **LLM**: Groq (Llama 3.3 70B Versatile)
- **Voice**: LiveKit (Cloud), AssemblyAI (STT), Cartesia (TTS), Silero (VAD)
- **Search**: Tavily (Market Intelligence), SearchAPI
- **Auth**: Clerk (Identity & Organization Management)
- **Database**: MongoDB (Persistence), Redis (Context & Rate Limiting)
- **Infrastructure**: Kafka (Event Bus), Docker Compose

---

## 📚 Documentation

- **[Architecture Deep Dive](docs/architecture.md)**: Original design document. (Legacy reference)
- **[Troubleshooting](docs/troubleshooting_and_tradeoffs.md)**: Decisions on UUID representation and VAD split handling.
- **[Testing Results](docs/test_results.md)**: Latest pipeline verification.
