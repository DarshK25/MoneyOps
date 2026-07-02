# MoneyOps Voice Service

**Python / LiveKit Agent** — Real-time voice conversations between users and AI agents for financial operations.

## Responsibility

The Voice Service enables natural voice conversations with the MoneyOps AI. Users speak naturally about invoices, payments, compliance, or collections, and the service transcribes their speech, processes it through the AI Gateway's agent system, and speaks back the response. It handles STT (speech-to-text), TTS (text-to-speech), VAD (voice activity detection), and session management.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Voice Agent Framework | LiveKit Agents SDK |
| STT Providers | Deepgram, AssemblyAI, Groq (auto-fallback) |
| TTS Providers | ElevenLabs, Deepgram, Cartesia, Groq (auto-fallback) |
| VAD | WebRTC VAD (silero fallback) |
| HTTP Client | httpx (async) → AI Gateway |
| Server | uvicorn |

## Architecture

```
User's Voice
     │
     ▼
┌─────────────────────────────┐
│   Voice Service :8003       │
│                             │
│  ┌───────────────────────┐  │
│  │ LiveKit Voice Agent   │  │
│  │                       │  │
│  │ 1. VAD detects speech │  │
│  │ 2. STT transcribes    │  │
│  │ 3. Send to AI Gateway │  │
│  │ 4. TTS speaks response│  │
│  └───────────────────────┘  │
│                             │
│  ┌───────────────────────┐  │
│  │ Session Manager       │  │
│  │ conversation history  │  │
│  │ per-call state        │  │
│  └───────────────────────┘  │
└─────────────┬───────────────┘
              │ HTTP
              ▼
      AI Gateway :8005
      (agent orchestration)
```

## Directory Structure

```
voice-service/
├── app/
│   ├── __init__.py
│   ├── config.py                # All env-driven config
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── entrypoint.py        # LiveKit Agent entrypoint
│   │   └── guard.py             # Human handoff guard logic
│   ├── api/
│   │   └── health.py            # Health endpoint
│   ├── cli/
│   │   ├── __init__.py
│   │   └── entrypoint.py        # CLI runner
│   └── utils/
│       ├── __init__.py
│       └── ...                  # VAD, TTS utilities
├── Dockerfile
├── requirements.txt
└── test_stt_config.py
```

## Key Files

| File | Purpose |
|------|---------|
| `app/config.py` | All configuration from environment variables |
| `app/agent/entrypoint.py` | LiveKit Agent — handles STT, TTS, VAD, AI Gateway communication |
| `app/agent/guard.py` | Human handoff guard — detects when AI should hand off to a human |
| `app/cli/entrypoint.py` | CLI runner for starting the agent |
| `app/api/health.py` | Health check endpoint |

## Voice Pipeline

```
1. User speaks ──► VAD detects speech start
2. ──► STT (Deepgram/AssemblyAI/Groq) ──► text transcript
3. ──► HTTP POST to AI Gateway /api/v1/voice/process
4. ──► AI Gateway classifies intent, routes to executor
5. ──► executor calls Backend gRPC/HTTP, returns response
6. ──► AI Gateway returns response text
7. ──► TTS (ElevenLabs/Deepgram/Cartesia/Groq) ──► audio
8. ──► Play audio back to user
```

## STT/TTS Provider Configuration

The voice service supports multiple STT and TTS providers with automatic fallback:

### STT Fallback Order
1. Deepgram (primary — `DEEPGRAM_API_KEY`)
2. AssemblyAI (fallback — `ASSEMBLYAI_API_KEY`)
3. Groq (final fallback — `GROQ_API_KEY`)

### TTS Fallback Order
1. ElevenLabs (primary — `ELEVENLABS_API_KEY`)
2. Deepgram (fallback — `DEEPGRAM_API_KEY`)
3. Cartesia (fallback — `CARTESIA_API_KEY`)
4. Groq (final fallback — `GROQ_API_KEY`)

Set `STT_PROVIDER=auto` or `TTS_PROVIDER=auto` for automatic selection. Set to a specific provider name to pin to one provider.

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `VOICE_SERVICE_PORT` | 8003 | HTTP port |
| `AI_GATEWAY_URL` | http://localhost:8001 | AI Gateway endpoint |
| `AI_GATEWAY_TIMEOUT` | 30 | HTTP timeout (seconds) |
| `LIVEKIT_URL` | — | LiveKit server WebSocket URL |
| `LIVEKIT_API_KEY` | — | LiveKit API key |
| `LIVEKIT_API_SECRET` | — | LiveKit API secret |
| `DEEPGRAM_API_KEY` | — | Deepgram API key (STT/TTS) |
| `ASSEMBLYAI_API_KEY` | — | AssemblyAI API key (STT) |
| `GROQ_API_KEY` | — | Groq API key (STT/TTS fallback) |
| `ELEVENLABS_API_KEY` | — | ElevenLabs API key (TTS) |
| `ELEVENLABS_TTS_MODEL` | eleven_flash_v2_5 | ElevenLabs TTS model |
| `ELEVENLABS_VOICE_ID` | EXAVITQu4vr4xnSDxMaL | ElevenLabs voice ID |
| `CARTESIA_API_KEY` | — | Cartesia API key (TTS) |
| `STT_PROVIDER` | auto | STT provider selection |
| `TTS_PROVIDER` | auto | TTS provider selection |
| `VAD_MIN_SPEECH_DURATION` | 0.3 | Minimum speech duration (seconds) |
| `VAD_MIN_SILENCE_DURATION` | 0.5 | Silence to end utterance (seconds) |
| `SESSION_TIMEOUT_S` | 600 | Max conversation duration |
| `MAX_CONVERSATION_HISTORY` | 10 | Context turns retained |

## Running

```bash
# Prerequisites: Python 3.11+, LiveKit Cloud account

cd voice-service
pip install -r requirements.txt

# Start the voice agent
python -m app.cli.entrypoint

# Or directly as LiveKit agent
python -m app.agent.entrypoint

# Health check
curl http://localhost:8003/health
```

## Dependencies

- **AI Gateway** — all voice commands are processed through the agent system at `/api/v1/voice/process`
- **LiveKit Cloud** — WebRTC infrastructure for real-time audio
- **Deepgram / ElevenLabs** — STT and TTS providers
- **Backend** — indirectly through AI Gateway
