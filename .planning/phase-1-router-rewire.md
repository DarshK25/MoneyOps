# Phase 1 — Route main chat through the real IntentClassifier

**Goal:** retire the keyword/bespoke router on the live `/api/v1/agent/chat` path and route through the genuinely intelligent LLM `IntentClassifier` in `app/orchestration/` (currently only wired to a test endpoint + voice).

## The seam (verified)
- Chat: `POST /api/v1/agent/chat` → `chat_with_agent` (`api/v1/agent.py:49`) → `master_orchestrator.process()` (`agents/master_orchestrator.py:129`).
- Old routing (to retire): `process()` line 157 calls `_select_executor_llm` (bespoke mini-LLM router, `master_orchestrator.py:66-112`) with keyword fallback `_select_executor_fallback` (`:114-127`). Returns `AgentRole`; dispatched via `self.executors[role].execute(state)`.
- Real brain: `intent_classifier.classify(user_input, conversation_history, business_context) -> IntentClassification` (`orchestration/intent_classifier.py:163`, singleton `:454`). Returns `.intent: Intent`, `.confidence`, `.reasoning`, `.category`, `.primary_agent: AgentType`, `.supporting_agents`.
- Executor registry keyed by `AgentRole` (`master_orchestrator.py:51-57`): FINANCE_OPS, COMPLIANCE, COLLECTIONS, TREDS, GROWTH. No CEO/GENERAL executor.

## Critical decision: route on `Intent`, not `AgentType`
`AgentType` enum (intents.py:153) has no COLLECTIONS/TREDS → routing on `primary_agent` loses those executors. So build `INTENT_TO_ROLE: Dict[Intent, AgentRole]` and route on `classification.intent`. Unknown/conversational → default FINANCE_OPS (matches old fallback `else`).

## Changes (surgical, master_orchestrator.py only)
1. Import `intent_classifier` + `Intent`.
2. Add module-level `INTENT_TO_ROLE` map (invoice/client/txn/payment/balance/docs → FINANCE_OPS; reminders → COLLECTIONS; compliance/gst/tax/audit → COMPLIANCE; forecast/trend/benchmark/sales/growth/strategy/customer-intel/ops → GROWTH; treds intents → TREDS; health/budget/cashflow/profit/analytics/report → FINANCE_OPS).
3. New `_route_via_classifier(user_message, conversation_history)` → calls classify, maps intent→role, logs intent+confidence+reasoning, falls back to `_select_executor_fallback` on exception.
4. `process()` :157-159 — replace `_select_executor_llm` call with `_route_via_classifier`. Keep greeting short-circuit (:143-155). Keep `_select_executor_fallback` as safety net. Remove now-dead `_select_executor_llm`.
5. Single-executor plan for now; multi-agent via `supporting_agents` = future.

## Deliberately deferred (not Phase 1)
- Wiring `conversation_history`/`SessionManager` into the chat endpoint (`agent.py` passes none today) — classify handles empty history fine.
- `business_context` fetch (needs backend call).
- Per-executor `_classify_action` (Layer B, handler selection inside executor) — untouched.
- Wiring `EntityExtractor` into executors.

## Verify
- `ast.parse` the edited file. Boot ai-gateway. Hit `/test/intent-classification` (already works) + `/agent/chat` with a revenue question → expect FINANCE_OPS, a GST question → COMPLIANCE, a forecast question → GROWTH, a reminder question → COLLECTIONS.

## Status: DONE (2026-09-25)

Implemented + verified end-to-end against the running gateway (port 8006). All four probes route correctly:
- "current revenue this month" → ANALYTICS_QUERY (0.81) → finance_ops ✓
- "file GST this quarter" → GST_QUERY (0.855) → compliance ✓
- "send payment reminders to overdue clients" → REMINDER_CREATE (0.95) → collections ✓
- "forecast revenue next 6 months" → FORECAST_REQUEST (0.855) → growth ✓

### Extra fix required (classifier prompt gap)
First verification showed GST → GENERAL_QUERY and reminders → INVOICE_QUERY (both misrouted to finance_ops). Root cause was NOT the INTENT_TO_ROLE mapping (correct) but the `IntentClassifier._build_classification_prompt` intent menu, which never listed the COMPLIANCE/GST or REMINDER intents — the LLM couldn't choose an option it was never shown, so it picked the nearest listed one. Fix (in `orchestration/intent_classifier.py`): added a COLLECTIONS intent group (REMINDER_CREATE/LIST/CANCEL) and a COMPLIANCE & TAX group (COMPLIANCE_*/GST_QUERY/TAX_*/AUDIT_READINESS) to the prompt, plus instruction #4 to prefer a specific domain intent over GENERAL_QUERY. `_parse_llm_response` validates against `Intent.__members__`, so the added names parse cleanly. `_pattern_classify` only fast-paths GREETING/HELP/CONFIRMATION/CANCELLATION, so these always reach the LLM path the fix targets.
