from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import time

from app.cache.semantic_cache import semantic_cache
from app.cache.benchmark import cache_benchmark, BENCHMARK_QUERY_SETS
from app.llm.multi_provider import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/cache", tags=["Semantic Cache"])


class CacheStatusResponse(BaseModel):
    status: str
    cache_stats: Dict[str, Any]
    backends: Dict[str, bool]


class CacheClearResponse(BaseModel):
    success: bool
    entries_cleared: int
    message: str


class CacheManualSetRequest(BaseModel):
    query: str
    response: str
    provider: str = "manual"
    tokens_used: int = 0
    latency_ms: float = 0.0


class CacheManualSetResponse(BaseModel):
    success: bool
    message: str


class BenchmarkQuerySet(BaseModel):
    category: str
    seed: str
    system: Optional[str] = "You are a financial assistant. Answer concisely."
    variants: list[str]


class BenchmarkRequest(BaseModel):
    query_sets: Optional[list[BenchmarkQuerySet]] = None
    clear_first: bool = True


class BenchmarkResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/health", response_model=CacheStatusResponse)
async def cache_health():
    """Check cache system health"""
    stats = semantic_cache.stats()
    return CacheStatusResponse(
        status="healthy" if stats["backends"]["redis"] or stats["backends"]["pinecone"] else "degraded",
        cache_stats={
            "enabled": stats["config"]["enabled"],
            "memory_entries": stats["memory_entries"],
            "threshold": stats["config"]["threshold"],
            "ttl_seconds": stats["config"]["ttl_seconds"],
        },
        backends=stats["backends"],
    )


@router.get("/stats")
async def cache_stats():
    """Get cache performance statistics"""
    return {"success": True, "data": semantic_cache.stats()}


@router.post("/clear", response_model=CacheClearResponse)
async def clear_cache():
    """Clear all cached entries"""
    count = await semantic_cache.clear()
    return CacheClearResponse(
        success=True,
        entries_cleared=count,
        message=f"Cleared {count} cached entries",
    )


@router.post("/clear-stats")
async def clear_cache_stats():
    """Reset cache statistics counters without clearing entries"""
    await semantic_cache.clear_stats()
    return {"success": True, "message": "Cache stats reset"}


@router.post("/set", response_model=CacheManualSetResponse)
async def manual_cache_set(request: CacheManualSetRequest):
    """Manually populate a cache entry"""
    success = await semantic_cache.set(
        query=request.query,
        response=request.response,
        provider=request.provider,
        tokens_used=request.tokens_used,
        latency_ms=request.latency_ms,
    )
    return CacheManualSetResponse(
        success=success,
        message="Cached" if success else "Failed to cache",
    )


@router.post("/query")
async def cache_query(query: str = Query(..., description="Query to check against cache")):
    """Check if a query would hit the cache (without calling LLM)"""
    start = time.time()
    cached = await semantic_cache.get(query)
    lookup_ms = (time.time() - start) * 1000
    if cached:
        return {
            "success": True,
            "hit": True,
            "matched_query": cached.query,
            "response_preview": cached.response[:200],
            "provider": cached.provider,
            "tokens_used": cached.tokens_used,
            "original_latency_ms": cached.latency_ms,
            "lookup_time_ms": round(lookup_ms, 2),
        }
    return {"success": True, "hit": False, "lookup_time_ms": round(lookup_ms, 2)}


@router.post("/benchmark", response_model=BenchmarkResponse)
async def run_benchmark(request: BenchmarkRequest = None):
    """Run semantic cache benchmark with real LLM calls.
    Measures cold vs hot latency for semantically similar query pairs.
    Returns detailed per-category and overall results with real numbers.
    """
    if not llm_client or not llm_client.providers:
        raise HTTPException(status_code=503, detail="No LLM providers configured")

    try:
        query_sets = None
        if request and request.query_sets:
            query_sets = [qs.model_dump() for qs in request.query_sets]

        clear_first = True
        if request:
            clear_first = request.clear_first

        report = await cache_benchmark.run_all(
            query_sets=query_sets,
            clear_first=clear_first,
        )

        return BenchmarkResponse(success=True, report=report)

    except Exception as e:
        logger.error("benchmark_failed", error=str(e))
        return BenchmarkResponse(success=False, error=str(e))


@router.get("/benchmark-queries")
async def list_benchmark_queries():
    """List all predefined benchmark query sets"""
    return {
        "success": True,
        "total_categories": len(BENCHMARK_QUERY_SETS),
        "total_variants": sum(len(qs["variants"]) for qs in BENCHMARK_QUERY_SETS),
        "query_sets": [
            {
                "category": qs["category"],
                "seed": qs["seed"],
                "variant_count": len(qs["variants"]),
                "variants": qs["variants"],
            }
            for qs in BENCHMARK_QUERY_SETS
        ],
    }
