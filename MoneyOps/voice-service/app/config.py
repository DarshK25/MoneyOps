"""
Voice Service Configuration
All settings loaded from environment variables
"""
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


def _resolve_env_path() -> Path:
    """Always load from monorepo root .env (single source of truth)."""
    # Path: MoneyOps/voice-service/app/config.py -> 3 levels up = MoneyOps/.env
    root_env = Path(__file__).resolve().parents[3] / ".env"
    if root_env.exists():
        return root_env

    # Fallback: try parents[2] if structure changes
    fallback = Path(__file__).resolve().parents[2] / ".env"
    return fallback

_env_path = _resolve_env_path()
load_dotenv(dotenv_path=_env_path, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Keep pydantic-settings env_file as fallback; absolute path avoids CWD issues
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",   # silently skip MONGODB_URI, VITE_*, BACKEND_PORT, etc.
    )

    # Voice service settings
    APP_NAME: str = "MoneyOps Voice Service"
    PORT: int = 8003
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # LiveKit
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    LIVEKIT_URL: str

    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # AI Gateway
    AI_GATEWAY_URL: str = "http://localhost:8005"
    # Read budget for the gateway's full LLM classify -> gRPC -> LLM reply pipeline.
    # This is applied as httpx's *read* timeout only (connect fails fast, see
    # AI_GATEWAY_CONNECT_TIMEOUT). It must be >= the pipeline's real p95 latency,
    # otherwise a slow-but-working turn is cut off and the caller hears a canned
    # "taking longer" line instead of the real answer.
    AI_GATEWAY_TIMEOUT: int = 30  # seconds
    AI_GATEWAY_CONNECT_TIMEOUT: float = 5.0  # seconds — a down gateway surfaces quickly

    # Session
    SESSION_TIMEOUT_S: int = 600  # 10 minutes
    MAX_CONVERSATION_HISTORY: int = 10  # messages

    # External APIs
    ASSEMBLYAI_API_KEY: Optional[str] = None
    CARTESIA_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVEN_API_KEY: Optional[str] = None
    STT_PROVIDER: str = "auto"
    TTS_PROVIDER: str = "auto"
    STT_FALLBACK_ORDER: str = "deepgram,assemblyai,groq"
    TTS_FALLBACK_ORDER: str = "elevenlabs,deepgram,cartesia,groq"
    DEEPGRAM_STT_MODEL: str = "flux-general-en"
    DEEPGRAM_TTS_MODEL: str = "aura-2-odysseus-en"
    DEEPGRAM_STT_EAGER_EOT_THRESHOLD: float = 0.4
    ELEVENLABS_TTS_MODEL: str = "eleven_flash_v2_5"
    ELEVENLABS_VOICE_ID: str = "EXAVITQu4vr4xnSDxMaL"

    # VAD (Voice Activity Detection) — tuned for natural conversation
    # min_speech_duration LOW  → picks up speech quickly (no missed start-of-turn)
    VAD_MIN_SPEECH_DURATION: float = 0.18  # seconds — avoid triggering on very short noise bursts
    VAD_MIN_SILENCE_DURATION: float = 0.45  # seconds — slightly longer to reduce chopped utterances
    # activation_threshold: confidence level needed to declare speech activity (0.0–1.0)
    VAD_ACTIVATION_THRESHOLD: float = 0.65  # stricter to suppress background noise
    # How long (seconds) the agent waits after end-of-speech before processing
    TURN_DETECTION_DELAY: float = 0.55      # seconds

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
