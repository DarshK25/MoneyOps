import hashlib
import json
import time
import uuid
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Tier 1: Pinecone vector search
try:
    from pinecone import Pinecone as PineconeClient
    PINECONE_AVAILABLE = bool(settings.PINECONE_API_KEY)
except ImportError:
    PINECONE_AVAILABLE = False

# Tier 2: Redis exact-match
try:
    from app.integrations.redis_client import cache_get, cache_set, get_redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Tier 3: RapidFuzz fallback
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False


@dataclass
class CacheEntry:
    query: str
    response: str
    provider: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    hit_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "response": self.response,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
            "hit_count": self.hit_count,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CacheEntry":
        return cls(
            query=d.get("query", ""),
            response=d.get("response", ""),
            provider=d.get("provider", ""),
            tokens_used=d.get("tokens_used", 0),
            latency_ms=d.get("latency_ms", 0.0),
            timestamp=d.get("timestamp", time.time()),
            hit_count=d.get("hit_count", 1),
        )


class SemanticCache:
    CACHE_NAMESPACE = "semantic-cache"
    DEFAULT_THRESHOLD = 0.40
    DEFAULT_TTL = 3600
    MAX_MEMORY_ENTRIES = 2000

    def __init__(self, threshold: Optional[float] = None, ttl: Optional[int] = None):
        self.threshold = threshold if threshold is not None else \
            getattr(settings, "CACHE_SEMANTIC_THRESHOLD", self.DEFAULT_THRESHOLD)
        self.ttl = ttl if ttl is not None else \
            getattr(settings, "CACHE_SEMANTIC_TTL", self.DEFAULT_TTL)
        self.enabled = getattr(settings, "CACHE_SEMANTIC_ENABLED", True)

        self._pinecone = None
        self._pinecone_available = False
        self._init_pinecone()

        self._memory_store: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0, "misses": 0,
            "exact_hits": 0, "semantic_hits": 0, "fuzzy_hits": 0,
            "total_latency_saved_ms": 0.0,
            "total_tokens_saved": 0,
        }

    def _init_pinecone(self):
        if not PINECONE_AVAILABLE:
            return
        try:
            pc = PineconeClient(api_key=settings.PINECONE_API_KEY)
            self._index = pc.Index(settings.PINECONE_INDEX_NAME, host=settings.PINECONE_HOST) if settings.PINECONE_HOST else pc.Index(settings.PINECONE_INDEX_NAME)
            self._pinecone_available = True
            logger.info("semantic_cache_pinecone_ready", index=settings.PINECONE_INDEX_NAME)
        except Exception as e:
            logger.info("semantic_cache_pinecone_unavailable", error=str(e))

    @staticmethod
    def _normalize(query: str) -> str:
        return " ".join(query.lower().split())

    @staticmethod
    def _query_hash(query: str) -> str:
        return hashlib.sha256(SemanticCache._normalize(query).encode()).hexdigest()[:16]

    @staticmethod
    def _cache_key(query_hash: str) -> str:
        return f"semantic_cache:{query_hash}"

    async def get(self, query: str) -> Optional[CacheEntry]:
        if not self.enabled:
            return None
        if not query or not query.strip():
            return None

        normalized = self._normalize(query)
        qhash = self._query_hash(query)
        cache_key = self._cache_key(qhash)

        # Tier 1: Redis exact-match (O(1), fastest path)
        entry = await self._try_redis_get(cache_key)
        if entry:
            self._stats["hits"] += 1
            self._stats["exact_hits"] += 1
            self._stats["total_latency_saved_ms"] += entry.latency_ms
            self._stats["total_tokens_saved"] += entry.tokens_used
            logger.info("cache_hit_exact", query=normalized[:60], saved_ms=round(entry.latency_ms, 1))
            return entry

        # Tier 2: In-memory exact match (ultra-fast)
        entry = self._memory_store.get(cache_key)
        if entry and (time.time() - entry.timestamp) < self.ttl:
            self._stats["hits"] += 1
            self._stats["exact_hits"] += 1
            self._stats["total_latency_saved_ms"] += entry.latency_ms
            self._stats["total_tokens_saved"] += entry.tokens_used
            logger.info("cache_hit_memory_exact", query=normalized[:60])
            return entry

        # Tier 3: Pinecone semantic search (best similarity)
        entry = await self._try_pinecone_get(query, normalized)
        if entry:
            self._stats["hits"] += 1
            self._stats["semantic_hits"] += 1
            self._stats["total_latency_saved_ms"] += entry.latency_ms
            self._stats["total_tokens_saved"] += entry.tokens_used
            return entry

        # Tier 4: In-memory fuzzy match (fallback)
        entry = self._try_fuzzy_get(normalized)
        if entry:
            self._stats["hits"] += 1
            self._stats["fuzzy_hits"] += 1
            self._stats["total_latency_saved_ms"] += entry.latency_ms
            self._stats["total_tokens_saved"] += entry.tokens_used
            return entry

        self._stats["misses"] += 1
        return None

    async def _try_redis_get(self, cache_key: str) -> Optional[CacheEntry]:
        if not REDIS_AVAILABLE:
            return None
        try:
            cached = await cache_get(cache_key)
            if cached:
                data = json.loads(cached)
                return CacheEntry.from_dict(data)
        except Exception as e:
            logger.debug("cache_redis_get_failed", error=str(e))
        return None

    async def _try_pinecone_get(self, query: str, normalized: str) -> Optional[CacheEntry]:
        if not self._pinecone_available:
            return None
        try:
            raw = self._index.search(
                namespace=self.CACHE_NAMESPACE,
                inputs={"text": query},
                top_k=5,
            )
            hits = []
            if hasattr(raw, 'result') and hasattr(raw.result, 'hits'):
                for hit in raw.result.hits:
                    score = hit.score if hasattr(hit, 'score') else 0
                    if score >= self.threshold:
                        fields = hit.fields if hasattr(hit, 'fields') else {}
                        hits.append(dict(score=score, id=hit.id if hasattr(hit, 'id') else ""))
                        for key in ("query", "response", "provider", "tokens_used", "latency_ms", "timestamp"):
                            hits[-1][key] = fields.get(key, "")

            if hits:
                best = max(hits, key=lambda h: h["score"])
                entry = CacheEntry(
                    query=best["query"], response=best["response"],
                    provider=best.get("provider", ""),
                    tokens_used=int(best.get("tokens_used", 0) or 0),
                    latency_ms=float(best.get("latency_ms", 0) or 0),
                    timestamp=float(best.get("timestamp", 0) or time.time()),
                )
                await self._warm_redis(self._query_hash(query), entry)
                logger.info("cache_hit_semantic", query=normalized[:60],
                            score=round(best["score"], 3), matched=best["query"][:60])
                return entry
        except Exception as e:
            logger.debug("cache_pinecone_search_failed", error=str(e))
        return None

    def _try_fuzzy_get(self, normalized: str) -> Optional[CacheEntry]:
        if not RAPIDFUZZ_AVAILABLE:
            return None
        best_score = 0.0
        best_entry = None
        now = time.time()
        for key, entry in self._memory_store.items():
            if (now - entry.timestamp) >= self.ttl:
                continue
            ratio = fuzz.token_sort_ratio(normalized, self._normalize(entry.query)) / 100.0
            if ratio > best_score and ratio >= self.threshold:
                best_score = ratio
                best_entry = entry

        if best_entry:
            logger.info("cache_hit_fuzzy", query=normalized[:60], score=round(best_score, 3))
            return best_entry
        return None

    async def set(self, query: str, response: str, provider: str = "",
                  tokens_used: int = 0, latency_ms: float = 0.0,
                  metadata: Optional[Dict] = None) -> bool:
        if not self.enabled or not query or not response:
            return False

        normalized = self._normalize(query)
        qhash = self._query_hash(query)
        cache_key = self._cache_key(qhash)
        entry = CacheEntry(
            query=normalized, response=response,
            provider=provider, tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

        success = False

        # Pinecone store (async, fire-and-forget)
        if self._pinecone_available:
            try:
                self._index.upsert_records(
                    namespace=self.CACHE_NAMESPACE,
                    records=[{
                        "id": f"cache-{qhash}-{uuid.uuid4().hex[:6]}",
                        "text": normalized,
                        "query": normalized,
                        "response": response,
                        "provider": provider,
                        "tokens_used": str(tokens_used),
                        "latency_ms": str(round(latency_ms, 2)),
                        "timestamp": str(time.time()),
                    }]
                )
                success = True
            except Exception as e:
                logger.debug("cache_pinecone_set_failed", error=str(e))

        # Redis store
        if REDIS_AVAILABLE:
            try:
                await cache_set(cache_key, json.dumps(entry.to_dict()), ttl_seconds=self.ttl)
                success = True
            except Exception as e:
                logger.debug("cache_redis_set_failed", error=str(e))

        # Memory store
        self._memory_store[cache_key] = entry
        if len(self._memory_store) > self.MAX_MEMORY_ENTRIES:
            self._trim_memory()

        if success:
            logger.info("cache_stored", query=normalized[:60], provider=provider)
        return success

    async def _warm_redis(self, qhash: str, entry: CacheEntry):
        if not REDIS_AVAILABLE:
            return
        try:
            await cache_set(self._cache_key(qhash), json.dumps(entry.to_dict()), ttl_seconds=self.ttl)
        except Exception:
            pass

    def _trim_memory(self):
        sorted_keys = sorted(self._memory_store.keys(),
                             key=lambda k: self._memory_store[k].timestamp)
        excess = len(self._memory_store) - int(self.MAX_MEMORY_ENTRIES * 0.8)
        for key in sorted_keys[:excess]:
            del self._memory_store[key]

    async def clear(self) -> int:
        count = len(self._memory_store)
        self._memory_store.clear()
        self._stats = {"hits": 0, "misses": 0, "exact_hits": 0,
                       "semantic_hits": 0, "fuzzy_hits": 0,
                       "total_latency_saved_ms": 0.0, "total_tokens_saved": 0}
        logger.info("cache_cleared", entries=count)
        return count

    def stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0.0
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": round(hit_rate, 2),
            "exact_hits": self._stats["exact_hits"],
            "semantic_hits": self._stats["semantic_hits"],
            "fuzzy_hits": self._stats["fuzzy_hits"],
            "total_requests": total,
            "total_latency_saved_ms": round(self._stats["total_latency_saved_ms"], 1),
            "total_tokens_saved": self._stats["total_tokens_saved"],
            "memory_entries": len(self._memory_store),
            "backends": {
                "pinecone": self._pinecone_available,
                "redis": REDIS_AVAILABLE,
                "rapidfuzz": RAPIDFUZZ_AVAILABLE,
            },
            "config": {
                "enabled": self.enabled,
                "threshold": self.threshold,
                "ttl_seconds": self.ttl,
            },
        }

    async def clear_stats(self):
        self._stats = {"hits": 0, "misses": 0, "exact_hits": 0,
                       "semantic_hits": 0, "fuzzy_hits": 0,
                       "total_latency_saved_ms": 0.0, "total_tokens_saved": 0}


semantic_cache = SemanticCache()
