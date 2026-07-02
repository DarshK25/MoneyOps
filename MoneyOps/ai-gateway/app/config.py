"""
Configuration management for AI Gateway
"""

from pathlib import Path
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv as _load_dotenv

_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_load_dotenv(dotenv_path=_ROOT_ENV, override=True)

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    APP_NAME: str = "MoneyOps AI Gateway"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8005

    GROQ_API_KEY: str
    GROQ_API_KEY_FAST: Optional[str] = None
    GROQ_API_KEY_FALLBACK_1: Optional[str] = None
    GROQ_API_KEY_FALLBACK_2: Optional[str] = None
    CEREBRAS_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GITHUB_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    SERPAPI_KEY: Optional[str] = None

    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_MODEL_COMPLEX: str = "llama-3.1-8b-instant"
    GROQ_VOICE_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VOICE_FINAL_MODEL: str = "llama-3.3-70b-versatile"

    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2000
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 3
    GROQ_VOICE_HISTORY_MESSAGES: int = 8
    GROQ_VOICE_TOOL_ROUNDS: int = 3

    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"
    BACKEND_TIMEOUT: int = 30
    INTERNAL_SERVICE_TOKEN: str = "moneyops-internal-ai-gateway-service-secret-2024"

    GRPC_ENABLED: bool = True
    GRPC_SERVER_HOST: str = "127.0.0.1"
    GRPC_SERVER_PORT: int = 50051
    GRPC_CLIENT_HOST: str = "127.0.0.1"
    GRPC_CLIENT_PORT: int = 50051

    @model_validator(mode="after")
    def validate_service_token(self) -> "Settings":
        import os
        env = os.environ.get("ENVIRONMENT", os.environ.get("NODE_ENV", "development"))
        default = "moneyops-internal-ai-gateway-service-secret-2024"
        if self.INTERNAL_SERVICE_TOKEN == default and env == "production":
            raise ValueError(
                "INTERNAL_SERVICE_TOKEN must be set to a non-default value in production."
            )
        return self

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_TLS: bool = False

    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "moneyops-agent-memory"
    PINECONE_HOST: str = ""

    CACHE_TTL_SHORT: int = 300
    CACHE_TTL_MEDIUM: int = 1800
    CACHE_TTL_LONG: int = 3600

    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    MAX_CONVERSATION_HISTORY: int = 10
    CONVERSATION_TTL: int = 3600

    AGENT_TIMEOUT: int = 60
    MAX_TOOL_ITERATIONS: int = 5

    TREDS_ENABLED: bool = False
    TREDS_API_BASE_URL: str = "https://api.rxil.in/v1"
    TREDS_API_KEY: Optional[str] = None
    TREDS_RXIL_API_URL: str = "https://api.rxil.in/v1"
    TREDS_M1XCHANGE_API_URL: str = "https://api.m1xchange.com/v1"
    TREDS_INVOICEMART_API_URL: str = "https://api.invoicemart.com/v1"
    TREDS_DEFAULT_DISCOUNT_RATE: float = 10.0

    BUSINESS_NAME: str = "MoneyOps"
    BUSINESS_EMAIL: str = "hello@moneyops.ai"

    LIVEKIT_URL: str = "wss://your-project.livekit.cloud"
    LIVEKIT_API_KEY: Optional[str] = None
    LIVEKIT_API_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def require_groq_key():
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is required")


settings = get_settings()
