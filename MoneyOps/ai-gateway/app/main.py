"""
MoneyOps AI Gateway - Main FastAPI Application
"""
import time
import asyncio
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Rate Limiting Setup
# ============================================================================
limiter = None
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address

    storage_uri = None
    if settings.REDIS_HOST and settings.REDIS_HOST != "localhost":
        redis_auth = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
        redis_scheme = "rediss" if settings.REDIS_TLS else "redis"
        storage_uri = f"{redis_scheme}://{redis_auth}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB or 0}"

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=storage_uri,
        default_limits=["100/minute"],
        in_memory_fallback_enabled=True,
    )
    logger.info("rate_limiter_ready", storage="redis" if storage_uri else "memory")
except ImportError:
    logger.warning("slowapi_not_installed")
    limiter = None

# ============================================================================
# Lifespan Events (startup/shutdown)
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup - validate config
    errors = _validate_config()
    if errors:
        for err in errors:
            logger.error("config_error", error=err)
        logger.warning("starting_with_config_errors", error_count=len(errors))

    logger.info(
        "starting_ai_gateway",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )

    # Connect to Redis
    try:
        from app.integrations.redis_client import get_redis
        await get_redis()
        logger.info("redis_ready")
    except Exception as e:
        logger.warning("redis_unavailable", error=str(e))

    # Start gRPC server (background task)
    grpc_task = None
    try:
        from app.grpc.server import serve as grpc_serve
        grpc_task = asyncio.create_task(grpc_serve(port=50052))
        logger.info("grpc_server_started_background", port=50052)
    except Exception as e:
        logger.warning("grpc_server_not_started", error=str(e))

    yield

    # Shutdown
    if grpc_task:
        grpc_task.cancel()
    try:
        from app.integrations.redis_client import close_redis
        await close_redis()
    except Exception:
        pass
    logger.info("shutting_down_ai_gateway")


def _validate_config() -> list:
    """Validate critical configuration. Returns list of error messages."""
    errors = []

    if not settings.JWT_SECRET_KEY or len(settings.JWT_SECRET_KEY) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters")

    if not settings.INTERNAL_SERVICE_TOKEN or "default" in settings.INTERNAL_SERVICE_TOKEN.lower():
        errors.append("INTERNAL_SERVICE_TOKEN must not be default")

    if not settings.GROQ_API_KEY:
        logger.warning("No GROQ_API_KEY set - LLM calls will fail")

    return errors


# ============================================================================
# Create FastAPI App
# ============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered orchestration gateway for MoneyOps",
    lifespan=lifespan,
)

# CORS
_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
try:
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.RATE_LIMIT_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )
    logger.info("rate_limit_middleware_added")
except ImportError as e:
    logger.warning("rate_limit_middleware_unavailable", error=str(e))

# Request logging + Request ID middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Log all requests with timing + add request ID"""
    import uuid
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None,
    )

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=round(duration * 1000, 2),
    )

    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with proper logging"""
    import traceback
    error_trace = traceback.format_exc()

    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        error=str(exc),
        exc_info=True,
    )

    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": "An unexpected error occurred"},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "traceback": error_trace if settings.DEBUG else None,
            },
        )


# ============================================================================
# Include Routers
# ============================================================================
from app.api.v1 import health
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

from app.api.v1 import voice
app.include_router(voice.router, prefix="/api/v1", tags=["Voice"])

from app.api.v1 import agent
if limiter:
    agent.router.limiter = limiter
app.include_router(agent.router, prefix="/api/v1", tags=["Agent"])

try:
    from app.api.v1 import compliance
    app.include_router(compliance.router, prefix="/api/v1", tags=["Compliance"])
except ImportError:
    logger.warning("compliance_router_unavailable")

try:
    from app.api.v1 import market
    app.include_router(market.router, prefix="/api/v1", tags=["Market"])
except ImportError:
    logger.warning("market_router_unavailable")

if settings.ENVIRONMENT != "production":
    for router_name in ["test_agents", "test_llm"]:
        try:
            module = __import__(f"app.api.v1.{router_name}", fromlist=["router"])
            app.include_router(module.router, prefix="/api/v1", tags=[f"Test {router_name.replace('_', ' ').title()}"])
        except ImportError:
            pass

# Semantic Cache API
try:
    from app.api.v1 import cache as cache_router
    app.include_router(cache_router.router, prefix="/api/v1", tags=["Cache"])
    logger.info("cache_router_included")
except ImportError as e:
    logger.warning("cache_router_unavailable", error=str(e))


# ============================================================================
# Root endpoint
# ============================================================================
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "endpoints": {
            "health": "/api/v1/health",
            "agent": "/api/v1/agent/chat",
            "voice": "/api/v1/voice",
        }
    }


# ============================================================================
# Run directly
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
