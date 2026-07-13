from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import time
import uuid

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Pinecone Vector Store ─────────────────────────────────────────────────────


class PineconeStore:
    """Pinecone-backed vector store for semantic memory and RAG.

    Wraps PineconeManager from app.memory.pinecone_manager.
    Stores text + metadata with auto-generated embeddings (llama-text-embed-v2).
    Falls back to in-memory search on Pinecone failure.
    """

    NAMESPACE_COMPLIANCE = "compliance-rules"
    NAMESPACE_CLIENTS = "client-patterns"
    NAMESPACE_INVOICES = "invoice-history"
    NAMESPACE_CONVERSATIONS = "conversation-memory"

    def __init__(self, fallback: Optional["MemoryStore"] = None):
        self._fallback = fallback or MemoryStore()
        self._pc = None
        self._available = False
        self._init_pinecone()

    def _init_pinecone(self):
        try:
            from app.memory.pinecone_manager import PineconeManager
            self._pc = PineconeManager()
            self._available = True
            logger.info("pinecone_store_available",
                        index=self._pc.index_name)
        except Exception as e:
            self._pc = None
            self._available = False
            logger.warning("pinecone_store_unavailable", error=str(e))

    # ── Semantic store ────────────────────────────────────────────────────────

    async def store_memory(self, namespace: str, record_id: str,
                           text: str, metadata: Optional[Dict] = None) -> bool:
        if not self._available or self._pc is None:
            return self._fallback.store(namespace, record_id,
                                        {"text": text, "metadata": metadata or {}})
        return await self._pc.store_memory(namespace, record_id, text, metadata)

    async def search_memory(self, namespace: str, query: str,
                            top_k: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        if not self._available or self._pc is None:
            results = self._fallback.search(namespace, query)
            return [{"id": k, "score": 0, "text": str(v), "metadata": {}}
                    for k, v in results]
        return await self._pc.search_memory(namespace, query, top_k, filter)

    # ── Domain-specific helpers ───────────────────────────────────────────────

    async def store_compliance_rule(self, rule_id: str, rule_text: str,
                                    rule_type: str = "gst",
                                    applicable_states: Optional[List[str]] = None) -> bool:
        if not self._available:
            return self._fallback.store(self.NAMESPACE_COMPLIANCE, f"rule_{rule_id}",
                                        {"text": rule_text, "type": rule_type})
        return await self._pc.store_compliance_rule(rule_id, rule_text, rule_type, applicable_states)

    async def search_compliance_info(self, query: str, rule_type: Optional[str] = None,
                                     top_k: int = 5) -> List[Dict]:
        if not self._available:
            return self._fallback.search(self.NAMESPACE_COMPLIANCE, query)
        return await self._pc.search_compliance_info(query, rule_type, top_k)

    async def store_client_pattern(self, client_id: str, client_name: str,
                                   payment_history: List[Dict]) -> bool:
        if not self._available:
            return self._fallback.store(self.NAMESPACE_CLIENTS, f"client_{client_id}",
                                        client_name)
        return await self._pc.store_client_pattern(client_id, client_name, payment_history)

    async def search_similar_clients(self, query: str, top_k: int = 3) -> List[Dict]:
        if not self._available:
            return self._fallback.search(self.NAMESPACE_CLIENTS, query)
        return await self._pc.search_similar_clients(query, top_k)

    async def store_conversation_context(self, org_id: str, session_id: str,
                                         messages: List[Dict]) -> bool:
        if not self._available:
            return self._fallback.store(self.NAMESPACE_CONVERSATIONS,
                                        f"{org_id}_{session_id}",
                                        {"messages": messages})
        return await self._pc.store_conversation_context(org_id, session_id, messages)

    def stats(self) -> Dict[str, Any]:
        return {
            "backend": "pinecone" if self._available else "pinecone_unavailable",
            "namespaces": [
                self.NAMESPACE_COMPLIANCE, self.NAMESPACE_CLIENTS,
                self.NAMESPACE_INVOICES, self.NAMESPACE_CONVERSATIONS,
            ] if self._available else [],
        }

    def cleanup(self):
        self._fallback.cleanup()


# ── Tiered Storage Backend ──────────────────────────────────────────────────


class MemoryStore:
    """In-memory fallback store with TTL support."""

    def __init__(self):
        self._memory: Dict[str, Dict[str, Any]] = {}
        self._index: Dict[str, List[str]] = {}
        self._ttl: float = 86400.0

    def store(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        try:
            record_key = f"{namespace}:{key}"
            self._memory[record_key] = {
                "value": value,
                "namespace": namespace,
                "key": key,
                "stored_at": time.time(),
                "ttl": ttl or self._ttl,
            }
            if namespace not in self._index:
                self._index[namespace] = []
            self._index[namespace].append(key)
            return True
        except Exception as e:
            logger.error("memory_store_failed", namespace=namespace, key=key, error=str(e))
            return False

    def get(self, namespace: str, key: str) -> Optional[Any]:
        try:
            record_key = f"{namespace}:{key}"
            record = self._memory.get(record_key)
            if record is None:
                return None
            if time.time() - record["stored_at"] > record["ttl"]:
                del self._memory[record_key]
                if namespace in self._index and key in self._index[namespace]:
                    self._index[namespace].remove(key)
                return None
            return record["value"]
        except Exception as e:
            logger.error("memory_get_failed", namespace=namespace, key=key, error=str(e))
            return None

    def delete(self, namespace: str, key: str) -> bool:
        try:
            record_key = f"{namespace}:{key}"
            if record_key in self._memory:
                del self._memory[record_key]
            if namespace in self._index and key in self._index[namespace]:
                self._index[namespace].remove(key)
            return True
        except Exception as e:
            logger.error("memory_delete_failed", namespace=namespace, key=key, error=str(e))
            return False

    def list_namespace(self, namespace: str) -> List[str]:
        keys = self._index.get(namespace, [])
        valid = []
        for key in keys:
            record_key = f"{namespace}:{key}"
            record = self._memory.get(record_key)
            if record and (time.time() - record["stored_at"] <= record["ttl"]):
                valid.append(key)
            elif record:
                del self._memory[record_key]
        self._index[namespace] = valid
        return valid

    def cleanup(self):
        now = time.time()
        expired_keys = []
        for record_key, record in self._memory.items():
            if now - record["stored_at"] > record["ttl"]:
                expired_keys.append(record_key)
        for key in expired_keys:
            ns = key.split(":", 1)[0]
            k = key.split(":", 1)[1] if ":" in key else key
            del self._memory[key]
            if ns in self._index and k in self._index[ns]:
                self._index[ns].remove(k)
        if expired_keys:
            logger.info("memory_cleanup", expired_count=len(expired_keys))

    def search(self, namespace: str, query: str) -> List[Tuple[str, Any]]:
        results = []
        query_lower = query.lower()
        for key in self.list_namespace(namespace):
            if query_lower in key.lower():
                value = self.get(namespace, key)
                if value is not None:
                    results.append((key, value))
        return results

    def get_all(self, namespace: str) -> Dict[str, Any]:
        results = {}
        for key in self.list_namespace(namespace):
            value = self.get(namespace, key)
            if value is not None:
                results[key] = value
        return results

    def stats(self) -> Dict[str, Any]:
        return {
            "total_records": len(self._memory),
            "namespaces": len(self._index),
            "namespace_details": {ns: len(keys) for ns, keys in self._index.items()},
        }


# ── Redis Backend ────────────────────────────────────────────────────────────


class RedisStore:
    """Redis-backed store for fast TTL-based memory. Falls back to in-memory on failure."""

    def __init__(self, fallback: Optional[MemoryStore] = None):
        self._client = None
        self._available = False
        self._fallback = fallback or MemoryStore()
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            import os
            from app.config import settings
            host = settings.REDIS_HOST or "127.0.0.1"
            port = settings.REDIS_PORT or 6379
            pwd = settings.REDIS_PASSWORD or None
            db = settings.REDIS_DB or 0
            use_tls = getattr(settings, "REDIS_TLS", False)

            # If standard Redis is localhost and Upstash credentials exist, use Upstash
            if host in ("127.0.0.1", "localhost") and pwd is None:
                upstash_url = os.getenv("UPSTASH_REDIS_REST_URL", "")
                upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
                if upstash_url and upstash_token:
                    host = upstash_url.replace("https://", "").replace("http://", "")
                    port = 6379
                    pwd = upstash_token
                    use_tls = True

            self._client = redis.Redis(
                host=host, port=port, db=db, password=pwd,
                ssl=use_tls,
                decode_responses=True, socket_connect_timeout=5,
            )
            self._client.ping()
            self._available = True
            logger.info("redis_store_available", host=host, port=port)
        except Exception as e:
            self._client = None
            self._available = False
            logger.warning("redis_store_unavailable", error=str(e))

    def _key(self, namespace: str, key: str) -> str:
        return f"moneyops:agentos:{namespace}:{key}"

    def store(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        if not self._available or self._client is None:
            return self._fallback.store(namespace, key, value, ttl)
        try:
            rk = self._key(namespace, key)
            data = json.dumps(value, default=str)
            if ttl:
                self._client.setex(rk, int(ttl), data)
            else:
                self._client.set(rk, data)
            return True
        except Exception as e:
            logger.warning("redis_store_fallback", namespace=namespace, key=key, error=str(e))
            return self._fallback.store(namespace, key, value, ttl)

    def get(self, namespace: str, key: str) -> Optional[Any]:
        if not self._available or self._client is None:
            return self._fallback.get(namespace, key)
        try:
            rk = self._key(namespace, key)
            data = self._client.get(rk)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning("redis_get_fallback", namespace=namespace, key=key, error=str(e))
            return self._fallback.get(namespace, key)

    def delete(self, namespace: str, key: str) -> bool:
        if not self._available or self._client is None:
            return self._fallback.delete(namespace, key)
        try:
            rk = self._key(namespace, key)
            self._client.delete(rk)
            return True
        except Exception as e:
            return self._fallback.delete(namespace, key)

    def search(self, namespace: str, query: str) -> List[Tuple[str, Any]]:
        return self._fallback.search(namespace, query)

    def get_all(self, namespace: str) -> Dict[str, Any]:
        return self._fallback.get_all(namespace)

    def list_namespace(self, namespace: str) -> List[str]:
        return self._fallback.list_namespace(namespace)

    def cleanup(self):
        self._fallback.cleanup()

    def stats(self) -> Dict[str, Any]:
        base = self._fallback.stats()
        base["backend"] = "redis" if self._available else "redis_fallback"
        return base
class MongoStore:
    """MongoDB-backed store for persistent long-term memory. Falls back to in-memory."""

    def __init__(self, fallback: Optional[MemoryStore] = None):
        self._db = None
        self._available = False
        self._fallback = fallback or MemoryStore()
        self._init_mongo()

    def _init_mongo(self):
        try:
            import os
            from pymongo import MongoClient
            uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.server_info()
            self._db = client["moneyops"]
            self._collections = {}
            self._available = True
            logger.info("mongo_store_available")
        except Exception as e:
            self._available = False
            logger.warning("mongo_store_unavailable", error=str(e))

    def _coll(self, namespace: str):
        safe = namespace.replace(":", "_")
        if safe not in self._collections:
            self._collections[safe] = self._db[safe]
            self._collections[safe].create_index("key", unique=True)
            self._collections[safe].create_index("stored_at")
        return self._collections[safe]

    def store(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        if not self._available:
            return self._fallback.store(namespace, key, value, ttl)
        try:
            doc = {
                "key": key,
                "namespace": namespace,
                "value": value,
                "stored_at": datetime.utcnow(),
                "ttl": ttl or 86400.0 * 365,
            }
            self._coll(namespace).update_one(
                {"key": key},
                {"$set": doc},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.warning("mongo_store_fallback", namespace=namespace, key=key, error=str(e))
            return self._fallback.store(namespace, key, value, ttl)

    def get(self, namespace: str, key: str) -> Optional[Any]:
        if not self._available:
            return self._fallback.get(namespace, key)
        try:
            doc = self._coll(namespace).find_one({"key": key})
            if not doc:
                return None
            elapsed = (datetime.utcnow() - doc["stored_at"]).total_seconds()
            if elapsed > doc.get("ttl", 86400.0 * 365):
                self._coll(namespace).delete_one({"key": key})
                return None
            return doc["value"]
        except Exception as e:
            logger.warning("mongo_get_fallback", namespace=namespace, key=key, error=str(e))
            return self._fallback.get(namespace, key)

    def delete(self, namespace: str, key: str) -> bool:
        if not self._available:
            return self._fallback.delete(namespace, key)
        try:
            self._coll(namespace).delete_one({"key": key})
            return True
        except Exception as e:
            return self._fallback.delete(namespace, key)

    def search(self, namespace: str, query: str) -> List[Tuple[str, Any]]:
        if not self._available:
            return self._fallback.search(namespace, query)
        try:
            results = []
            coll = self._coll(namespace)
            for doc in coll.find({"key": {"$regex": query, "$options": "i"}}).limit(50):
                elapsed = (datetime.utcnow() - doc["stored_at"]).total_seconds()
                if elapsed <= doc.get("ttl", 86400.0 * 365):
                    results.append((doc["key"], doc["value"]))
            return results
        except Exception as e:
            return self._fallback.search(namespace, query)

    def get_all(self, namespace: str) -> Dict[str, Any]:
        if not self._available:
            return self._fallback.get_all(namespace)
        try:
            results = {}
            now = datetime.utcnow()
            for doc in self._coll(namespace).find().sort("stored_at", -1).limit(500):
                elapsed = (now - doc["stored_at"]).total_seconds()
                if elapsed <= doc.get("ttl", 86400.0 * 365):
                    results[doc["key"]] = doc["value"]
            return results
        except Exception as e:
            return self._fallback.get_all(namespace)

    def list_namespace(self, namespace: str) -> List[str]:
        if not self._available:
            return self._fallback.list_namespace(namespace)
        try:
            now = datetime.utcnow()
            keys = []
            for doc in self._coll(namespace).find().sort("stored_at", -1).limit(500):
                elapsed = (now - doc["stored_at"]).total_seconds()
                if elapsed <= doc.get("ttl", 86400.0 * 365):
                    keys.append(doc["key"])
            return keys
        except Exception as e:
            return self._fallback.list_namespace(namespace)

    def cleanup(self):
        if self._available:
            try:
                now = datetime.utcnow()
                for name, coll in self._collections.items():
                    coll.delete_many({
                        "stored_at": {"$lt": now - timedelta(seconds=86400.0 * 365)}
                    })
            except Exception as e:
                logger.warning("mongo_cleanup_failed", error=str(e))
        self._fallback.cleanup()

    def stats(self) -> Dict[str, Any]:
        base = self._fallback.stats()
        base["backend"] = "mongodb" if self._available else "mongodb_fallback"
        if self._available:
            try:
                base["mongo_collections"] = list(self._collections.keys())
                base["mongo_records"] = sum(
                    coll.count_documents({}) for coll in self._collections.values()
                )
            except Exception:
                pass
        return base


# ── Tiered Store ─────────────────────────────────────────────────────────────


class TieredStore:
    """Combines Redis (fast cache) + MongoDB (persistent) + Pinecone (vector) + in-memory (fallback).

    Routing rules:
      - short_term / session        → Redis (fast TTL)        → in-memory fallback
      - long_term / business / decisions / outcomes / communications → MongoDB → in-memory fallback
      - vector: / semantic: / compliance-rules / client-patterns / conversation-memory → Pinecone → in-memory fallback
    """

    def __init__(self):
        self._in_memory = MemoryStore()
        self._redis = RedisStore(fallback=self._in_memory)
        self._mongo = MongoStore(fallback=self._in_memory)
        self._pinecone = PineconeStore(fallback=self._in_memory)
        logger.info("tiered_store_initialized",
                    redis_ok=self._redis._available,
                    mongo_ok=self._mongo._available)

    def _store_for(self, namespace: str):
        if namespace.startswith("short_term:") or namespace.startswith("session:"):
            return self._redis
        if namespace.startswith("vector:") or namespace.startswith("semantic:"):
            return self._in_memory  # falls back — Pinecone is async, not used for sync store/get
        return self._mongo

    def is_vector_namespace(self, namespace: str) -> bool:
        return namespace in (
            "compliance-rules", "client-patterns", "invoice-history", "conversation-memory",
        ) or namespace.startswith("vector:") or namespace.startswith("semantic:")

    @property
    def vector_store(self) -> PineconeStore:
        return self._pinecone

    def store(self, namespace: str, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        return self._store_for(namespace).store(namespace, key, value, ttl)

    def get(self, namespace: str, key: str) -> Optional[Any]:
        return self._store_for(namespace).get(namespace, key)

    def delete(self, namespace: str, key: str) -> bool:
        return self._store_for(namespace).delete(namespace, key)

    def search(self, namespace: str, query: str) -> List[Tuple[str, Any]]:
        return self._mongo.search(namespace, query) or self._redis.search(namespace, query)

    def get_all(self, namespace: str) -> Dict[str, Any]:
        return self._store_for(namespace).get_all(namespace)

    def list_namespace(self, namespace: str) -> List[str]:
        return self._store_for(namespace).list_namespace(namespace)

    def cleanup(self):
        self._redis.cleanup()
        self._mongo.cleanup()
        self._pinecone.cleanup()
        self._in_memory.cleanup()

    def stats(self) -> Dict[str, Any]:
        return {
            "redis": self._redis.stats(),
            "mongo": self._mongo.stats(),
            "pinecone": self._pinecone.stats(),
            "in_memory": self._in_memory.stats(),
            "total_namespaces": len(set(
                list(self._redis.stats().get("namespace_details", {}).keys()) +
                list(self._mongo.stats().get("namespace_details", {}).keys())
            )),
        }


# ── Agent Memory (unchanged interface) ──────────────────────────────────────


class AgentMemory:
    SHORT_TERM_TTL = 300.0
    SESSION_TTL = 3600.0
    LONG_TERM_TTL = 86400.0 * 30
    BUSINESS_TTL = 86400.0 * 90
    DECISION_TTL = 86400.0 * 365

    def __init__(self, store: TieredStore):
        self.store = store

    # ── Key-value (sync) ──────────────────────────────────────────────────────

    def store_short_term(self, agent: str, key: str, value: Any):
        return self.store.store(f"short_term:{agent}", key, value, ttl=self.SHORT_TERM_TTL)

    def get_short_term(self, agent: str, key: str) -> Optional[Any]:
        return self.store.get(f"short_term:{agent}", key)

    def store_session(self, session_id: str, key: str, value: Any):
        return self.store.store(f"session:{session_id}", key, value, ttl=self.SESSION_TTL)

    def get_session(self, session_id: str, key: str) -> Optional[Any]:
        return self.store.get(f"session:{session_id}", key)

    def store_long_term(self, agent: str, key: str, value: Any):
        return self.store.store(f"long_term:{agent}", key, value, ttl=self.LONG_TERM_TTL)

    def get_long_term(self, agent: str, key: str) -> Optional[Any]:
        return self.store.get(f"long_term:{agent}", key)

    def store_business(self, org_id: str, key: str, value: Any):
        return self.store.store(f"business:{org_id}", key, value, ttl=self.BUSINESS_TTL)

    def get_business(self, org_id: str, key: str) -> Optional[Any]:
        return self.store.get(f"business:{org_id}", key)

    def store_decision(self, agent: str, decision_id: str, value: Any):
        return self.store.store(f"decisions:{agent}", decision_id, value, ttl=self.DECISION_TTL)

    def get_decision(self, agent: str, decision_id: str) -> Optional[Any]:
        return self.store.get(f"decisions:{agent}", decision_id)

    def list_decisions(self, agent: str) -> List[str]:
        return self.store.list_namespace(f"decisions:{agent}")

    def store_outcome(self, agent: str, key: str, value: Any):
        return self.store.store(f"outcomes:{agent}", key, value, ttl=self.LONG_TERM_TTL)

    def get_outcome(self, agent: str, key: str) -> Optional[Any]:
        return self.store.get(f"outcomes:{agent}", key)

    def store_communication(self, message_id: str, value: Any):
        return self.store.store("communications", message_id, value, ttl=self.LONG_TERM_TTL)

    def get_communication(self, message_id: str) -> Optional[Any]:
        return self.store.get("communications", message_id)

    def get_agent_memories(self, agent: str) -> Dict[str, Any]:
        return {
            "short_term": self.store.get_all(f"short_term:{agent}"),
            "long_term": self.store.get_all(f"long_term:{agent}"),
            "decisions": self.store.get_all(f"decisions:{agent}"),
            "outcomes": self.store.get_all(f"outcomes:{agent}"),
        }

    # ── Vector / semantic (async, Pinecone) ───────────────────────────────────

    async def store_semantic(self, namespace: str, record_id: str,
                             text: str, metadata: Optional[Dict] = None) -> bool:
        ns = f"vector:{namespace}"
        return await self.store.vector_store.store_memory(ns, record_id, text, metadata)

    async def search_semantic(self, namespace: str, query: str,
                              top_k: int = 5) -> List[Dict]:
        ns = f"vector:{namespace}"
        return await self.store.vector_store.search_memory(ns, query, top_k=top_k)

    async def store_conversation(self, org_id: str, session_id: str,
                                 messages: List[Dict]) -> bool:
        return await self.store.vector_store.store_conversation_context(
            org_id, session_id, messages)

    async def search_compliance(self, query: str, rule_type: Optional[str] = None,
                                top_k: int = 5) -> List[Dict]:
        return await self.store.vector_store.search_compliance_info(query, rule_type, top_k)

    async def store_compliance_rule(self, rule_id: str, rule_text: str,
                                    rule_type: str = "gst",
                                    applicable_states: Optional[List[str]] = None) -> bool:
        return await self.store.vector_store.store_compliance_rule(
            rule_id, rule_text, rule_type, applicable_states)

    async def store_client_pattern(self, client_id: str, client_name: str,
                                   payment_history: List[Dict]) -> bool:
        return await self.store.vector_store.store_client_pattern(
            client_id, client_name, payment_history)

    async def search_similar_clients(self, query: str, top_k: int = 3) -> List[Dict]:
        return await self.store.vector_store.search_similar_clients(query, top_k)

    def vector_stats(self) -> Dict[str, Any]:
        return self.store.vector_store.stats()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def cleanup(self):
        self.store.cleanup()

    def stats(self) -> Dict[str, Any]:
        return self.store.stats()


memory_store = TieredStore()
agent_memory = AgentMemory(memory_store)
