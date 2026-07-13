import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from app.cache.semantic_cache import semantic_cache, CacheEntry
from app.llm.multi_provider import llm_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


BENCHMARK_QUERY_SETS = [
    {
        "category": "EV Charger Revenue",
        "seed": "What was our total EV charger installation revenue last month?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "How much revenue did we generate from charger installations last month?",
            "What were our EV charging earnings for last month?",
            "Show me last month's total charger installation income",
            "What's our monthly revenue from EV charger projects?",
            "How much did we make from charger installations last month?",
        ],
    },
    {
        "category": "Overdue Client Payments",
        "seed": "Which clients have overdue payments for EV charger installations?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "Show me all overdue invoices from hospitality clients",
            "What payments are past due from our clients?",
            "List all overdue charger installation payments",
            "Which invoices haven't been paid on time?",
            "Show me pending payments that are late from our customers",
        ],
    },
    {
        "category": "Cash Position",
        "seed": "What's our current cash position after Marriott's partial payment?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "How much cash do we have on hand including advance payments?",
            "What's our current account balance after client payments?",
            "Show me our cash position considering pending invoices",
            "What's the available cash for new charger projects?",
            "How much liquidity do we have for procurement?",
        ],
    },
    {
        "category": "Monthly Financial Performance",
        "seed": "Give me a financial performance summary for VoltNest this quarter",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "How is VoltNest performing financially this quarter?",
            "Show me the quarterly financial report for the EV charging business",
            "Summarize our finances for this quarter",
            "How are we doing financially with our charger projects?",
            "Give me this quarter's financial performance overview",
        ],
    },
    {
        "category": "Project Expense Analysis",
        "seed": "What were our hardware procurement costs for EV charger installations this month?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "How much did we spend on charger hardware this month?",
            "What's our total cost of EV charger equipment for this period?",
            "Show me this month's procurement spending on chargers",
            "List all hardware and installation expenses for this period",
            "What are our DC fast charger procurement costs this month?",
        ],
    },
    {
        "category": "GST & Tax Compliance",
        "seed": "What are our upcoming GST filing requirements for EV charger installations?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "When is the next GST return due for our charger projects?",
            "Show me GST compliance deadlines for equipment purchases",
            "What GST filings are pending for this quarter?",
            "List upcoming tax submission dates for VoltNest",
            "What tax deadlines are approaching for our business?",
        ],
    },
    {
        "category": "Marriott Invoice Status",
        "seed": "What's the payment status of Marriott Hotels' EV charger installation invoice?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "Has Marriott paid their DC fast charger invoice?",
            "Show me Marriott Hotels invoice history",
            "What does Marriott owe us for the charger project?",
            "Find Marriott's billing records and payment status",
            "Get me the payment details for Marriott's charger installation",
        ],
    },
    {
        "category": "Cash Flow Forecast",
        "seed": "What's our projected cash flow for next quarter with BlueDart and Marriott projects?",
        "system": "You are a financial assistant for VoltNest Energy Solutions, a B2B EV charging infrastructure company.",
        "variants": [
            "Forecast our cash position for Q2 with pending projects",
            "What's the cash flow outlook with BlueDart warehouse installation?",
            "Project our cash flow considering upcoming charger installations",
            "How will our cash position look after Marriott's final payment?",
            "What's the expected cash flow including new project advances?",
        ],
    },
]


@dataclass
class BenchmarkResult:
    category: str
    seed_latency_ms: float
    variant_results: List[Dict[str, Any]] = field(default_factory=list)
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    avg_cold_latency_ms: float = 0.0
    avg_hot_latency_ms: float = 0.0
    latency_reduction_pct: float = 0.0
    total_tokens_saved: int = 0
    total_time_saved_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "seed_latency_ms": round(self.seed_latency_ms, 2),
            "variant_results": self.variant_results,
            "cache_hit_count": self.cache_hit_count,
            "cache_miss_count": self.cache_miss_count,
            "avg_cold_latency_ms": round(self.avg_cold_latency_ms, 2),
            "avg_hot_latency_ms": round(self.avg_hot_latency_ms, 2),
            "latency_reduction_pct": round(self.latency_reduction_pct, 2),
            "total_tokens_saved": self.total_tokens_saved,
            "total_time_saved_ms": round(self.total_time_saved_ms, 2),
            "error": self.error,
        }


class CacheBenchmark:

    @staticmethod
    def _format_variant_label(query: str) -> str:
        return query[:80] + ("..." if len(query) > 80 else "")

    async def _measure_llm(self, query: str, system_prompt: Optional[str] = None,
                           max_tokens: int = 100) -> Tuple[float, str, int]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": query})

        start = time.time()
        result = await llm_client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        elapsed_ms = (time.time() - start) * 1000
        response = result["choices"][0]["message"]["content"]
        tokens = result.get("usage", {}).get("total_tokens", 0)
        return elapsed_ms, response, tokens

    async def run_single_set(self, query_set: Dict[str, Any]) -> BenchmarkResult:
        category = query_set["category"]
        seed = query_set["seed"]
        variants = query_set["variants"]
        system_prompt = query_set.get("system")

        logger.info("benchmark_starting", category=category, variants=len(variants))

        try:
            # Step 1: Measure seed query cold (no cache)
            seed_latency, seed_response, seed_tokens = await self._measure_llm(seed, system_prompt)
            logger.info("benchmark_seed_done", category=category, latency_ms=round(seed_latency, 2))

            # Step 2: Cache the seed response
            await semantic_cache.set(
                query=seed,
                response=seed_response,
                provider="groq",
                tokens_used=seed_tokens,
                latency_ms=seed_latency,
            )

            # Step 3: Measure each variant (should hit cache)
            variant_results = []
            hot_latencies = []
            cache_hits = 0
            cache_misses = 0
            time_saved = 0.0
            tokens_saved = 0

            for variant in variants:
                v_start = time.time()
                cached = await semantic_cache.get(variant)
                v_elapsed = (time.time() - v_start) * 1000
                if cached:
                    hot_latencies.append(v_elapsed)
                    cache_hits += 1
                    time_saved += seed_latency - v_elapsed
                    tokens_saved += seed_tokens
                    variant_results.append({
                        "query": self._format_variant_label(variant),
                        "latency_ms": round(v_elapsed, 2),
                        "source": "cache",
                        "matched_query": cached.query[:80],
                        "score": None,
                    })
                else:
                    # Fallback: actually call LLM
                    v_latency, v_response, v_tokens = await self._measure_llm(variant, system_prompt)
                    hot_latencies.append(v_latency)
                    cache_misses += 1
                    variant_results.append({
                        "query": self._format_variant_label(variant),
                        "latency_ms": round(v_latency, 2),
                        "source": "llm_direct",
                        "score": None,
                    })
                    await semantic_cache.set(
                        query=variant,
                        response=v_response,
                        provider="groq",
                        tokens_used=v_tokens,
                        latency_ms=v_latency,
                    )

            avg_cold = seed_latency
            avg_hot = sum(hot_latencies) / len(hot_latencies) if hot_latencies else 0
            reduction = ((avg_cold - avg_hot) / avg_cold * 100) if avg_cold > 0 else 0

            result = BenchmarkResult(
                category=category,
                seed_latency_ms=seed_latency,
                variant_results=variant_results,
                cache_hit_count=cache_hits,
                cache_miss_count=cache_misses,
                avg_cold_latency_ms=avg_cold,
                avg_hot_latency_ms=avg_hot,
                latency_reduction_pct=reduction,
                total_tokens_saved=tokens_saved,
                total_time_saved_ms=time_saved,
            )

            logger.info("benchmark_category_done", category=category,
                        reduction_pct=round(reduction, 1), hits=cache_hits)

            return result

        except Exception as e:
            logger.error("benchmark_category_failed", category=category, error=str(e))
            return BenchmarkResult(category=category, seed_latency_ms=0, error=str(e))

    async def run_all(self, query_sets: Optional[List[Dict]] = None,
                      clear_first: bool = True) -> Dict[str, Any]:
        if clear_first:
            await semantic_cache.clear()

        sets = query_sets or BENCHMARK_QUERY_SETS
        results: List[BenchmarkResult] = []
        total_start = time.time()

        for qs in sets:
            result = await self.run_single_set(qs)
            results.append(result)

        total_time = (time.time() - total_start) * 1000

        successful = [r for r in results if r.error is None]

        overall_avg_cold = sum(r.avg_cold_latency_ms for r in successful) / len(successful) if successful else 0
        overall_avg_hot = sum(r.avg_hot_latency_ms for r in successful) / len(successful) if successful else 0
        overall_reduction = ((overall_avg_cold - overall_avg_hot) / overall_avg_cold * 100) if overall_avg_cold > 0 else 0
        total_hits = sum(r.cache_hit_count for r in results)
        total_misses = sum(r.cache_miss_count for r in results)
        total_tokens_saved = sum(r.total_tokens_saved for r in results)
        total_time_saved = sum(r.total_time_saved_ms for r in results)

        report = {
            "summary": {
                "total_query_sets": len(sets),
                "total_variants_tested": sum(len(s["variants"]) for s in sets),
                "overall_avg_cold_latency_ms": round(overall_avg_cold, 2),
                "overall_avg_hot_latency_ms": round(overall_avg_hot, 2),
                "overall_latency_reduction_pct": round(overall_reduction, 2),
                "total_cache_hits": total_hits,
                "total_cache_misses": total_misses,
                "overall_hit_rate_pct": round(total_hits / (total_hits + total_misses) * 100, 2) if (total_hits + total_misses) > 0 else 0,
                "total_time_saved_ms": round(total_time_saved, 2),
                "total_tokens_saved": total_tokens_saved,
                "benchmark_duration_ms": round(total_time, 2),
                "estimated_cost_saved_usd": round(total_tokens_saved * 0.00000015, 4),
            },
            "per_category": [r.to_dict() for r in results],
        }

        logger.info("benchmark_complete", reduction_pct=round(overall_reduction, 1),
                    hits=total_hits, tokens_saved=total_tokens_saved)

        return report


cache_benchmark = CacheBenchmark()
