"""
Voice Service - FastAPI Health API
Provides health and readiness endpoints for Kubernetes probes
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import httpx

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="MoneyOps Voice Service", version="1.0.0")

startup_time = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    checks: Dict[str, Any]


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    error: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    uptime = time.time() - startup_time
    
    checks = {
        "api": "healthy",
        "stt": "checking...",
        "tts": "checking...",
        "ai_gateway": "checking...",
        "livekit": "checking...",
    }
    
    # Check STT providers
    stt_health = await _check_stt_providers()
    checks["stt"] = stt_health
    
    # Check TTS providers
    tts_health = await _check_tts_providers()
    checks["tts"] = tts_health
    
    # Check AI Gateway
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.AI_GATEWAY_URL}/api/v1/health")
            checks["ai_gateway"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as e:
        checks["ai_gateway"] = f"unhealthy: {str(e)}"
    
    # Check LiveKit
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.LIVEKIT_URL.replace('wss://', 'https://')}/health")
            checks["livekit"] = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as e:
        checks["livekit"] = f"unhealthy: {str(e)}"
    
    overall_healthy = all(
        v == "healthy" or (isinstance(v, dict) and v.get("available") == True)
        for v in checks.values()
    )
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        uptime_seconds=round(uptime, 2),
        checks=checks,
    )


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - checks if service can accept traffic"""
    checks = {}
    
    # Check STT
    stt_health = await _check_stt_providers()
    checks["stt"] = stt_health
    
    # Check TTS
    tts_health = await _check_tts_providers()
    checks["tts"] = tts_health
    
    # Check AI Gateway
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.AI_GATEWAY_URL}/api/v1/health")
            checks["ai_gateway"] = resp.status_code == 200
    except Exception:
        checks["ai_gateway"] = False
    
    all_ready = all(
        v.get("available") if isinstance(v, dict) else v
        for v in checks.values()
    )
    
    if not all_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready", "checks": checks}


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - simple check that process is alive"""
    return {"status": "alive"}


async def _check_stt_providers() -> Dict[str, Any]:
    """Check STT provider availability"""
    providers_checked = {}
    
    # Deepgram
    if settings.DEEPGRAM_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.deepgram.com/v1/projects",
                    headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
                )
                providers_checked["deepgram"] = resp.status_code == 200
        except Exception as e:
            providers_checked["deepgram"] = False
    else:
        providers_checked["deepgram"] = "not_configured"
    
    # AssemblyAI
    if settings.ASSEMBLYAI_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.assemblyai.com/v2/account",
                    headers={"authorization": settings.ASSEMBLYAI_API_KEY}
                )
                providers_checked["assemblyai"] = resp.status_code == 200
        except Exception:
            providers_checked["assemblyai"] = False
    else:
        providers_checked["assemblyai"] = "not_configured"
    
    # Groq (Whisper)
    if settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                )
                providers_checked["groq"] = resp.status_code == 200
        except Exception:
            providers_checked["groq"] = False
    else:
        providers_checked["groq"] = "not_configured"
    
    return {
        "available": any(v is True for v in providers_checked.values()),
        "providers": providers_checked,
    }


async def _check_tts_providers() -> Dict[str, Any]:
    """Check TTS provider availability"""
    providers_checked = {}
    
    # ElevenLabs
    api_key = settings.ELEVENLABS_API_KEY or settings.ELEVEN_API_KEY
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": api_key}
                )
                providers_checked["elevenlabs"] = resp.status_code == 200
        except Exception:
            providers_checked["elevenlabs"] = False
    else:
        providers_checked["elevenlabs"] = "not_configured"
    
    # Deepgram TTS
    if settings.DEEPGRAM_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.deepgram.com/v1/projects",
                    headers={"Authorization": f"Token {settings.DEEPGRAM_API_KEY}"}
                )
                providers_checked["deepgram"] = resp.status_code == 200
        except Exception:
            providers_checked["deepgram"] = False
    else:
        providers_checked["deepgram"] = "not_configured"
    
    # Cartesia
    if settings.CARTESIA_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.cartesia.ai/voices",
                    headers={"Authorization": f"Bearer {settings.CARTESIA_API_KEY}"}
                )
                providers_checked["cartesia"] = resp.status_code == 200
        except Exception:
            providers_checked["cartesia"] = False
    else:
        providers_checked["cartesia"] = "not_configured"
    
    # Groq TTS
    if settings.GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
                )
                providers_checked["groq"] = resp.status_code == 200
        except Exception:
            providers_checked["groq"] = False
    else:
        providers_checked["groq"] = "not_configured"
    
    return {
        "available": any(v is True for v in providers_checked.values()),
        "providers": providers_checked,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)