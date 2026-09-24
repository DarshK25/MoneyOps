# External Dependencies

**Last updated:** 2026-09-24

Everything runs on **free tiers**. Keys live in the root `.env` (gitignored) and are real, not decorative. This is the inventory and which service consumes each.

## LLM providers
| Provider | Used by | Notes |
|---|---|---|
| Groq (3 keys) | ai-gateway | primary fast inference; multiple keys for rate-limit headroom |
| Cerebras | ai-gateway | alternate fast inference |
| Gemini | ai-gateway | fallback / multimodal |

Multi-provider routing lets me fail over between them on rate limits.

## Vector / memory
| Provider | Used by | Notes |
|---|---|---|
| Pinecone | ai-gateway (`memory/pinecone_manager.py`) | vector memory; manager is real, RAG index not yet seeded |

## Voice pipeline
| Provider | Role | Used by |
|---|---|---|
| Deepgram | STT (flux-general-en) + optional TTS | voice-service |
| AssemblyAI | STT alternate | voice-service |
| ElevenLabs | TTS | voice-service |
| Cartesia | TTS alternate | voice-service |
| LiveKit | realtime room/transport | voice-service |

## Data stores
| Provider | Role | Notes |
|---|---|---|
| Neon Postgres | primary system of record | core writes go here |
| MongoDB Atlas | legacy store | still used by Compliance/Recurring/Payments/Bulk → split-brain |
| Upstash Redis | serverless Redis | **available in `.env` but currently unused**; app falls back to in-memory |

## Messaging / infra
| Provider | Role | Status |
|---|---|---|
| Kafka | event pipeline | producer real, **no working consumer**; `KAFKA_ENABLED=false` in `.env` (but `true` in docker-compose) |
| Redis (local docker) | queue / cache / rate-limit | compose exposes 6379; local wasn't running → reconnect storm (see ADR-001) |

## Outbound integrations
| Provider | Role | Used by |
|---|---|---|
| Resend | transactional email | email-worker / collections |
| Twilio | WhatsApp / SMS | notification-worker / collections |
| Tavily | web search | ai-gateway (agent tool) |
| Razorpay | payments | backend (LIVE key present; disabled by default) |

## Current posture
- **Redis:** in-memory fallback today; decision to unify on `REDIS_URL` (docker local + Upstash hosted) recorded in `../decisions/ADR-001-redis-and-degradation.md`.
- **Kafka:** effectively off until a real consumer exists.
- **Secrets:** rotation is a known to-do before going live (not done yet by choice).
