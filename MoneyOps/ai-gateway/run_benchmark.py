import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CACHE_SEMANTIC_ENABLED"] = "true"

from app.cache.benchmark import cache_benchmark

async def main():
    print("=" * 70)
    print("  VoltNest Energy Solutions - Semantic Cache Benchmark")
    print("=" * 70)
    print()
    report = await cache_benchmark.run_all(clear_first=True)
    s = report["summary"]
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"  Categories tested: {s['total_query_sets']}")
    print(f"  Variants tested:   {s['total_variants_tested']}")
    print(f"  Cache hit rate:    {s['overall_hit_rate_pct']}%")
    print(f"  Avg cold latency:  {s['overall_avg_cold_latency_ms']}ms")
    print(f"  Avg hot latency:   {s['overall_avg_hot_latency_ms']}ms")
    print(f"  Latency reduction: {s['overall_latency_reduction_pct']}%")
    print(f"  Time saved:        {s['total_time_saved_ms']}ms")
    print(f"  Tokens saved:      {s['total_tokens_saved']}")
    print(f"  Est. cost saved:   ${s['estimated_cost_saved_usd']}")
    print(f"  Duration:          {s['benchmark_duration_ms']}ms")
    print()
    print(f"  {'Category':<35} {'Hits':<6} {'Cold(ms)':<10} {'Hot(ms)':<10} {'Reduction':<10}")
    print(f"  {'-'*35} {'-'*6} {'-'*10} {'-'*10} {'-'*10}")
    for cat in report["per_category"]:
        hits = f"{cat['cache_hit_count']}/{cat['cache_hit_count'] + cat['cache_miss_count']}"
        reduction = f"{cat['latency_reduction_pct']}%"
        print(f"  {cat['category']:<35} {hits:<6} {cat['avg_cold_latency_ms']:<10} {cat['avg_hot_latency_ms']:<10} {reduction:<10}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
