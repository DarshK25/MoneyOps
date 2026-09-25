"""
Intent-routing accuracy benchmark for the live /agent/chat brain.

Runs a labeled set of business queries through the REAL LLM IntentClassifier
(no mocks), applies the exact same Intent -> AgentRole mapping the
MasterOrchestrator uses in production (_route_via_classifier), and reports how
often the selected executor matches the expected one.

Usage (from the ai-gateway/ directory):
    python -m tests.eval_intent_routing            # single pass
    python -m tests.eval_intent_routing --repeat 3 # 3 passes, cache cleared between, for consistency

This is a real evaluation harness, not a unit test: it makes live LLM calls and
is meant to quantify routing quality and catch regressions after prompt changes.
"""
import argparse
import asyncio
import logging
import time
from collections import defaultdict

# Quiet the app's structured logging so the report is readable.
logging.disable(logging.INFO)

from app.orchestration.intent_classifier import intent_classifier
from app.agents.master_orchestrator import INTENT_TO_ROLE, AgentRole, master_orchestrator


# (query, expected AgentRole.value). Covers every executor + realistic edge phrasings.
DATASET = [
    # --- finance_ops: money in/out, invoices, clients, balances, analytics, reports ---
    ("What is my current revenue this month?", "finance_ops"),
    ("Show me all unpaid invoices", "finance_ops"),
    ("Create an invoice for Acme Corp for 50000 rupees", "finance_ops"),
    ("What's my cash balance right now?", "finance_ops"),
    ("List my recent transactions", "finance_ops"),
    ("Add a new client called Reliance Retail", "finance_ops"),
    ("Generate a profit and loss report for last quarter", "finance_ops"),
    ("How much profit did I make last month?", "finance_ops"),
    ("Give me an account statement for this year", "finance_ops"),
    ("Record a payment of 20000 from Tata", "finance_ops"),
    ("Show me spending trends over the last 6 months", "finance_ops"),
    # --- collections: reminders / chasing overdue clients ---
    ("Send payment reminders to my overdue clients", "collections"),
    ("Follow up with everyone who hasn't paid their invoice", "collections"),
    ("Chase the late payers for me", "collections"),
    ("Nudge clients whose invoices are past due", "collections"),
    ("Remind Acme Corp that their payment is overdue", "collections"),
    # --- compliance: GST, tax, audit, regulatory ---
    ("Do I need to file GST this quarter?", "compliance"),
    ("When is my GST return due?", "compliance"),
    ("How much tax do I owe this year?", "compliance"),
    ("Am I compliant with my filing deadlines?", "compliance"),
    ("Help me get ready for an audit", "compliance"),
    ("How can I reduce my tax liability legally?", "compliance"),
    ("What are my upcoming compliance obligations?", "compliance"),
    # --- growth: strategy, forecasting, benchmarking, pricing, acquisition ---
    ("Forecast my revenue for the next 6 months", "growth"),
    ("How can I increase my sales?", "growth"),
    ("What's the best strategy to grow my business?", "growth"),
    ("How do I compare against others in my industry?", "growth"),
    ("Suggest a better pricing strategy for my products", "growth"),
    ("How do I get more customers?", "growth"),
    ("How can I retain my existing customers?", "growth"),
    ("Predict my cash flow for next quarter", "growth"),
    # --- treds: dedicated TREDS_DISCOUNT / TREDS_QUERY intents now exist in the
    #     taxonomy and route straight through the classifier (no keyword fallback). ---
    ("Can I discount this invoice on TReDS for early cash?", "treds"),
    ("I want to raise working capital against my receivables", "treds"),
]

def route_for(intent) -> str:
    """Exact production mapping used by MasterOrchestrator._route_via_classifier."""
    return INTENT_TO_ROLE.get(intent, AgentRole.FINANCE_OPS).value


async def run_pass(delay: float = 0.8):
    """Run every query once; return (results, elapsed_seconds).

    Mirrors production: if the LLM classifier raises (e.g. every provider is
    rate-limited), MasterOrchestrator._route_via_classifier falls back to the
    keyword router, so we do the same here and record which path decided.
    """
    results = []
    t0 = time.time()
    for query, expected in DATASET:
        source = "classifier"
        try:
            c = await intent_classifier.classify(user_input=query, conversation_history=[])
            got_role = route_for(c.intent)
            intent_name, confidence = c.intent.value, round(float(c.confidence), 3)
        except Exception as e:  # total LLM failure -> keyword safety net
            got_role = master_orchestrator._select_executor_fallback(query).value
            intent_name, confidence, source = f"FALLBACK({type(e).__name__})", 0.0, "fallback"
        results.append({
            "query": query,
            "expected": expected,
            "intent": intent_name,
            "confidence": confidence,
            "role": got_role,
            "ok": got_role == expected,
            "source": source,
        })
        if delay:
            await asyncio.sleep(delay)  # throttle to respect provider rate limits
    return results, time.time() - t0


def summarize(results):
    total = len(results)
    correct = sum(1 for r in results if r["ok"])
    per_role_total = defaultdict(int)
    per_role_ok = defaultdict(int)
    for r in results:
        per_role_total[r["expected"]] += 1
        if r["ok"]:
            per_role_ok[r["expected"]] += 1
    return total, correct, per_role_total, per_role_ok


def print_report(results):
    total, correct, per_role_total, per_role_ok = summarize(results)
    print("\n" + "=" * 78)
    print(f"INTENT ROUTING ACCURACY: {correct}/{total} = {100.0 * correct / total:.1f}%")
    print("=" * 78)
    print(f"{'':2} {'expected':<12} {'got_role':<12} {'intent':<22} {'conf':>5}  query")
    print("-" * 78)
    for r in results:
        mark = "OK" if r["ok"] else "XX"
        print(f"{mark:2} {r['expected']:<12} {r['role']:<12} {r['intent']:<22} {r['confidence']:>5}  {r['query'][:40]}")
    print("-" * 78)
    print("Per-role accuracy:")
    for role in sorted(per_role_total):
        print(f"  {role:<12} {per_role_ok[role]}/{per_role_total[role]}")
    misses = [r for r in results if not r["ok"]]
    if misses:
        print("\nMisses (query -> chose intent -> routed role, expected role):")
        for r in misses:
            print(f"  '{r['query']}' -> {r['intent']} -> {r['role']} (expected {r['expected']})")
    return correct, total


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=1, help="passes; cache cleared between passes")
    parser.add_argument("--delay", type=float, default=0.8, help="seconds between queries (rate-limit throttle)")
    args = parser.parse_args()

    pass_scores = []
    all_results_by_query = defaultdict(set)
    for i in range(args.repeat):
        intent_classifier._cache.clear()  # measure the classifier, not its cache
        results, elapsed = await run_pass(delay=args.delay)
        correct, total = print_report(results)
        pass_scores.append((correct, total))
        print(f"\nPass {i + 1}/{args.repeat}: {correct}/{total} in {elapsed:.1f}s "
              f"({elapsed / total:.2f}s/query)")
        for r in results:
            all_results_by_query[r["query"]].add(r["role"])

    if args.repeat > 1:
        print("\n" + "=" * 78)
        print("CONSISTENCY ACROSS PASSES")
        print("=" * 78)
        avg = sum(c for c, _ in pass_scores) / len(pass_scores)
        print(f"Scores per pass: {[f'{c}/{t}' for c, t in pass_scores]}  (mean correct {avg:.1f})")
        unstable = {q: roles for q, roles in all_results_by_query.items() if len(roles) > 1}
        if unstable:
            print("NON-DETERMINISTIC queries (routed to >1 role across passes):")
            for q, roles in unstable.items():
                print(f"  '{q}' -> {sorted(roles)}")
        else:
            print("All queries routed deterministically across every pass.")


if __name__ == "__main__":
    asyncio.run(main())
