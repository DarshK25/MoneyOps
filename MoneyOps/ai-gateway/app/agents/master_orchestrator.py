"""
CEO Orchestrator - Executive layer that coordinates all agents.
Never performs direct execution - delegates all actions to specialized agents.
Uses AgentOS: message bus for communication, decision engine for oversight,
governance for policy, observation for audit trail.
"""
from typing import Dict, Any, List, Optional
import asyncio
import json
import time
from datetime import datetime

from app.agents.base_executor import (
    FinanceExecutor,
    ComplianceExecutor,
    CollectionsExecutor,
    TReDSExecutor,
    ExecutionState,
    AgentRole,
    CycleResult,
)
from app.agents.growth import GrowthExecutor
from app.agents.activity_stream import activity_stream, ActivityType, Priority
from app.agentos.message_bus import message_bus, AgentMessage, MessageType
from app.agentos.decision import decision_engine, Decision
from app.agentos.governance import governance
from app.agentos.observation import audit_registry
from app.agentos.memory import agent_memory
from app.agentos.identity import CEO_AGENT_IDENTITY
from app.llm.multi_provider import llm_client
from app.adapters.backend_adapter import get_backend_adapter
from app.schemas.intents import Intent
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Maps the classifier's rich Intent enum onto the executor roles we actually run.
# We route on Intent (not IntentClassification.primary_agent) on purpose: the
# AgentType enum has no COLLECTIONS/TReDS member, so routing on primary_agent
# would strand those executors. Anything not listed falls back to FINANCE_OPS.
INTENT_TO_ROLE: Dict[Intent, AgentRole] = {
    # Invoices, clients, transactions, payments, balances, statements, documents
    Intent.INVOICE_QUERY: AgentRole.FINANCE_OPS,
    Intent.INVOICE_CREATE: AgentRole.FINANCE_OPS,
    Intent.INVOICE_UPDATE: AgentRole.FINANCE_OPS,
    Intent.INVOICE_DELETE: AgentRole.FINANCE_OPS,
    Intent.INVOICE_SEND: AgentRole.FINANCE_OPS,
    Intent.INVOICE_STATUS_CHECK: AgentRole.FINANCE_OPS,
    Intent.INVOICE_DOWNLOAD: AgentRole.FINANCE_OPS,
    Intent.INVOICE_PAYMENT: AgentRole.FINANCE_OPS,
    Intent.INVOICE_PARTIAL_PAYMENT: AgentRole.FINANCE_OPS,
    Intent.INVOICE_MARK_PAID: AgentRole.FINANCE_OPS,
    Intent.CLIENT_QUERY: AgentRole.FINANCE_OPS,
    Intent.CLIENT_CREATE: AgentRole.FINANCE_OPS,
    Intent.CLIENT_UPDATE: AgentRole.FINANCE_OPS,
    Intent.CLIENT_DELETE: AgentRole.FINANCE_OPS,
    Intent.CLIENT_HISTORY: AgentRole.FINANCE_OPS,
    Intent.TRANSACTION_QUERY: AgentRole.FINANCE_OPS,
    Intent.TRANSACTION_CREATE: AgentRole.FINANCE_OPS,
    Intent.TRANSACTION_EXPENSE: AgentRole.FINANCE_OPS,
    Intent.TRANSACTION_INCOME: AgentRole.FINANCE_OPS,
    Intent.PAYMENT_RECORD: AgentRole.FINANCE_OPS,
    Intent.PAYMENT_QUERY: AgentRole.FINANCE_OPS,
    Intent.BALANCE_CHECK: AgentRole.FINANCE_OPS,
    Intent.ACCOUNT_STATEMENT: AgentRole.FINANCE_OPS,
    Intent.DOCUMENT_UPLOAD: AgentRole.FINANCE_OPS,
    Intent.DOCUMENT_QUERY: AgentRole.FINANCE_OPS,
    Intent.DOCUMENT_ANALYZE: AgentRole.FINANCE_OPS,
    # Current-state financial / strategic-finance queries → finance ops
    Intent.BUSINESS_HEALTH_CHECK: AgentRole.FINANCE_OPS,
    Intent.PROBLEM_DIAGNOSIS: AgentRole.FINANCE_OPS,
    Intent.BUDGET_OPTIMIZATION: AgentRole.FINANCE_OPS,
    Intent.CASH_FLOW_PLANNING: AgentRole.FINANCE_OPS,
    Intent.PROFIT_OPTIMIZATION: AgentRole.FINANCE_OPS,
    Intent.INVESTMENT_ADVICE: AgentRole.FINANCE_OPS,
    Intent.DEBT_MANAGEMENT: AgentRole.FINANCE_OPS,
    Intent.RISK_ASSESSMENT: AgentRole.FINANCE_OPS,
    Intent.REPORT_GENERATE: AgentRole.FINANCE_OPS,
    Intent.ANALYTICS_QUERY: AgentRole.FINANCE_OPS,
    # Reminders / collections
    Intent.REMINDER_CREATE: AgentRole.COLLECTIONS,
    Intent.REMINDER_LIST: AgentRole.COLLECTIONS,
    Intent.REMINDER_CANCEL: AgentRole.COLLECTIONS,
    # Compliance / tax
    Intent.COMPLIANCE_QUERY: AgentRole.COMPLIANCE,
    Intent.COMPLIANCE_CHECK: AgentRole.COMPLIANCE,
    Intent.COMPLIANCE_REPORT: AgentRole.COMPLIANCE,
    Intent.GST_QUERY: AgentRole.COMPLIANCE,
    Intent.TAX_OPTIMIZATION: AgentRole.COMPLIANCE,
    Intent.TAX_CALCULATION: AgentRole.COMPLIANCE,
    Intent.AUDIT_READINESS: AgentRole.COMPLIANCE,
    # Forward-looking / growth / sales / strategy / customer intelligence / ops
    Intent.FORECAST_REQUEST: AgentRole.GROWTH,
    Intent.TREND_ANALYSIS: AgentRole.GROWTH,
    Intent.BENCHMARK_COMPARISON: AgentRole.GROWTH,
    Intent.SALES_STRATEGY: AgentRole.GROWTH,
    Intent.CUSTOMER_ACQUISITION: AgentRole.GROWTH,
    Intent.PRICING_STRATEGY: AgentRole.GROWTH,
    Intent.MARKETING_OPTIMIZATION: AgentRole.GROWTH,
    Intent.CUSTOMER_RETENTION: AgentRole.GROWTH,
    Intent.COMPETITIVE_POSITIONING: AgentRole.GROWTH,
    Intent.GROWTH_STRATEGY: AgentRole.GROWTH,
    Intent.MARKET_EXPANSION: AgentRole.GROWTH,
    Intent.PRODUCT_STRATEGY: AgentRole.GROWTH,
    Intent.SCALING_ADVICE: AgentRole.GROWTH,
    Intent.PARTNERSHIP_OPPORTUNITIES: AgentRole.GROWTH,
    Intent.CUSTOMER_SEGMENTATION: AgentRole.GROWTH,
    Intent.CHURN_PREDICTION: AgentRole.GROWTH,
    Intent.CUSTOMER_LIFETIME_VALUE: AgentRole.GROWTH,
    Intent.CUSTOMER_FEEDBACK_ANALYSIS: AgentRole.GROWTH,
    Intent.SWOT_ANALYSIS: AgentRole.GROWTH,
    Intent.SCENARIO_PLANNING: AgentRole.GROWTH,
    Intent.GOAL_SETTING: AgentRole.GROWTH,
    Intent.PROCESS_OPTIMIZATION: AgentRole.GROWTH,
    Intent.INVENTORY_OPTIMIZATION: AgentRole.GROWTH,
    Intent.RESOURCE_ALLOCATION: AgentRole.GROWTH,
    # Invoice discounting / working capital against receivables
    Intent.TREDS_DISCOUNT: AgentRole.TREDS,
    Intent.TREDS_QUERY: AgentRole.TREDS,
}


class MasterOrchestrator:
    """
    CEO Agent - Executive orchestration layer.
    Responsibilities:
    - Business monitoring across all agents
    - Agent coordination and delegation
    - Conflict resolution between agents
    - Strategic summaries (morning briefing, evening summary)
    - Risk reporting
    - Performance tracking
    Never executes actions directly - delegates to specialized agents.
    """

    def __init__(self):
        self.executors = {
            AgentRole.FINANCE_OPS: FinanceExecutor(),
            AgentRole.COMPLIANCE: ComplianceExecutor(),
            AgentRole.COLLECTIONS: CollectionsExecutor(),
            AgentRole.TREDS: TReDSExecutor(),
            AgentRole.GROWTH: GrowthExecutor(),
        }
        self.backend = get_backend_adapter()
        self.llm = llm_client
        self.identity = CEO_AGENT_IDENTITY
        self._morning_briefings: Dict[str, Dict[str, Any]] = {}
        self._evening_summaries: Dict[str, Dict[str, Any]] = {}
        self._agent_health: Dict[str, Dict[str, Any]] = {}
        logger.info("ceo_orchestrator_initialized", executors=list(self.executors.keys()))

    async def _route_via_classifier(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> List[AgentRole]:
        """
        Route the request through the LLM IntentClassifier (the real reasoning
        'brain' that lives in app/orchestration/), then map the classified
        Intent onto an executor role via INTENT_TO_ROLE. The keyword matcher is
        kept only as a last-resort safety net if classification fails outright.
        """
        try:
            from app.orchestration.intent_classifier import intent_classifier

            classification = await intent_classifier.classify(
                user_input=user_message,
                conversation_history=conversation_history or [],
            )
            role = INTENT_TO_ROLE.get(classification.intent, AgentRole.FINANCE_OPS)
            logger.info(
                "intent_routing",
                intent=classification.intent.value,
                confidence=round(float(classification.confidence), 3),
                primary_agent=classification.primary_agent.value,
                role=role.value,
                reasoning=(classification.reasoning or "")[:160],
            )
            return [role]
        except Exception as e:
            logger.error("intent_routing_error", error=str(e))
            return [self._select_executor_fallback(user_message)]

    def _select_executor_fallback(self, user_message: str) -> AgentRole:
        msg = user_message.lower()
        if any(w in msg for w in ["gst", "tax", "compliance", "tds", "file"]):
            return AgentRole.COMPLIANCE
        elif any(w in msg for w in ["remind", "collect", "overdue", "whatsapp", "sms"]):
            return AgentRole.COLLECTIONS
        elif any(w in msg for w in ["discount", "treds", "working capital", "invoice discount"]):
            return AgentRole.TREDS
        elif any(w in msg for w in ["forecast", "growth", "upsell", "churn", "retention", "revenue projection", "predict", "future", "strategy", "scale"]):
            return AgentRole.GROWTH
        elif any(w in msg for w in ["invoice", "invoicing", "payment", "revenue", "profit", "expense", "balance", "cash", "financial", "summary", "metrics", "overdue", "due"]):
            return AgentRole.FINANCE_OPS
        else:
            return AgentRole.FINANCE_OPS

    async def process(
        self,
        user_message: str,
        context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        CEO processes a user request by delegating to the appropriate executor(s).
        The CEO never executes actions directly.
        """
        start_time = time.time()
        errors: List[str] = []

        try:
            greeting_words = {"hello", "hey", "hi", "sup", "yo", "howdy", "good morning",
                              "good afternoon", "good evening", "greetings"}
            msg_lower = user_message.strip().lower().rstrip("?!.,")
            if msg_lower in greeting_words or (len(msg_lower.split()) <= 2 and msg_lower in greeting_words):
                return {
                    "success": True,
                    "message": "Hello! I'm your MoneyOps assistant. Ask me about revenue, invoices, clients, compliance, or cash flow.",
                    "agent_type": "greeting",
                    "executor": None,
                    "data": {},
                    "execution_time_ms": 0,
                    "errors": [],
                }

            executor_roles = await self._route_via_classifier(
                user_message, conversation_history
            )
            executor_role = executor_roles[0]
            execution_plan = executor_roles

            logger.info("execution_plan_created", plan=[r.value for r in execution_plan])

            state = ExecutionState(
                user_request=user_message,
                org_id=context.get("org_id", ""),
                user_id=context.get("user_id"),
                business_id=context.get("business_id", "1"),
                thread_id=context.get("session_id", "default"),
                session_id=context.get("session_id", "default"),
                conversation_history=conversation_history or [],
            )

            all_agent_outputs = {}
            agents_run = []
            plan_index = 0

            while plan_index < len(execution_plan) and state.iteration < state.max_iterations:
                current_role = execution_plan[plan_index]
                executor = self.executors.get(current_role)
                if not executor:
                    errors.append(f"Unknown executor: {current_role}")
                    plan_index += 1
                    continue

                if state.delegation_message and executor.role.value == state.delegation_target:
                    delegated_request = state.delegation_message
                    state.delegation_target = ""
                    state.delegation_message = ""
                else:
                    delegated_request = user_message

                original_request = state.user_request
                state.user_request = delegated_request

                logger.info("executor_run", executor=executor.name, plan_index=plan_index)

                ceo_msg = AgentMessage(
                    message_type=MessageType.REQUEST,
                    sender="ceo_orchestrator",
                    receiver=executor.name,
                    payload={"action": "execute", "user_request": delegated_request},
                    org_id=state.org_id,
                    session_id=state.session_id,
                    reasoning=f"Delegated by CEO based on execution plan step {plan_index}",
                )
                await message_bus.send(ceo_msg)

                result_state = await executor.execute(state)
                state = result_state
                state.iteration += 1

                executor_output = state.agent_outputs.get(executor.name, {})
                all_agent_outputs[executor.name] = executor_output
                agents_run.append(executor.name)

                state.user_request = original_request

                if state.delegation_target:
                    target_role = None
                    for role in AgentRole:
                        if role.value == state.delegation_target:
                            target_role = role
                            break
                    if target_role and target_role not in execution_plan:
                        execution_plan.insert(plan_index + 1, target_role)
                    elif target_role and target_role in execution_plan:
                        pass
                    else:
                        errors.append(f"Delegation to unknown role: {state.delegation_target}")

                plan_index += 1

            primary_executor = self.executors.get(executor_role)
            primary_output = all_agent_outputs.get(primary_executor.name, {})

            cross_agent_data = {}
            if len(agents_run) > 1:
                for agent_name, output in all_agent_outputs.items():
                    if agent_name != primary_executor.name and output:
                        cross_agent_data[agent_name] = output.get("response") or output

            response = {
                "success": not errors and primary_output.get("success", True),
                "message": primary_output.get("response") or primary_output.get("message", "Operation completed"),
                "agent_type": executor_role.value,
                "executor": primary_executor.name,
                "data": primary_output,
                "cross_agent_data": cross_agent_data,
                "agents_involved": agents_run,
                "delegation_chain": [r.value for r in execution_plan],
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "errors": errors + state.errors,
            }

            await audit_registry.record(
                agent_name="ceo_orchestrator",
                action="process_request",
                reasoning=f"Delegated to {', '.join(agents_run)}",
                success=response["success"],
                execution_duration_ms=response["execution_time_ms"],
                org_id=state.org_id,
                actual_outcome=response["message"],
            )

            logger.info("multi_agent_execution_complete", agents=agents_run, success=response["success"])
            return response

        except Exception as e:
            logger.error("orchestrator_error", error=str(e), user_message=user_message[:100])
            return {
                "success": False,
                "message": f"Execution failed: {str(e)}",
                "agent_type": None,
                "error": str(e),
            }

    async def generate_morning_briefing(self, org_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info("ceo_morning_briefing_started", org_id=org_id)

        await activity_stream.publish(
            ActivityType.MORNING_BRIEFING, agent="ceo", org_id=org_id,
            title="Morning Briefing", message="Generating your daily financial plan...",
            priority=Priority.MEDIUM,
        )

        try:
            finance = FinanceExecutor()
            compliance = ComplianceExecutor()
            collections = CollectionsExecutor()
            growth = GrowthExecutor()

            state_finance = ExecutionState(user_request="financial summary and cash position", org_id=org_id, user_id=user_id)
            state_finance = await finance.execute(state_finance)
            finance_result = state_finance.agent_outputs.get("finance_executor", {})

            state_compliance = ExecutionState(user_request="compliance deadlines and filing status", org_id=org_id, user_id=user_id)
            state_compliance = await compliance.execute(state_compliance)
            compliance_result = state_compliance.agent_outputs.get("compliance_executor", {})

            state_collections = ExecutionState(user_request="collections dashboard and overdue", org_id=org_id, user_id=user_id)
            state_collections = await collections.execute(state_collections)
            collections_result = state_collections.agent_outputs.get("collections_executor", {})

            growth_result = await growth._find_growth_opportunities(org_id, user_id)
            forecast = await growth._calculate_forecast(org_id, user_id)

            summary_prompt = f"""You are the CEO agent for a financial SaaS platform.
Generate a concise morning briefing based on these agent reports:

Finance: {finance_result.get('response', 'No data')}
Compliance: {compliance_result.get('response', 'No data')}
Collections: {collections_result.get('response', 'No data')}
Growth: {growth_result}
Forecast: {forecast}

Return a structured briefing with:
1. Today's top 3 priorities
2. Cash position summary
3. Urgent actions needed
4. One growth opportunity to pursue"""

            try:
                briefing_text = await self.llm.simple_completion(prompt=summary_prompt, task_type="simple")
            except:
                briefing_text = "Morning briefing generated from agent data."

            briefing = {
                "org_id": org_id,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "generated_at": datetime.utcnow().isoformat(),
                "summary": briefing_text,
                "finance": finance_result,
                "compliance": compliance_result,
                "collections": collections_result,
                "growth": growth_result,
                "forecast": forecast,
            }

            self._morning_briefings[org_id] = briefing
            agent_memory.store_business(org_id, f"morning_briefing_{briefing['date']}", briefing)

            await activity_stream.publish(
                ActivityType.MORNING_BRIEFING, agent="ceo", org_id=org_id,
                title="Morning Briefing Ready", message=briefing_text[:200],
                priority=Priority.MEDIUM, data={"date": briefing["date"]},
            )

            logger.info("ceo_morning_briefing_complete", org_id=org_id)
            return briefing

        except Exception as e:
            logger.error("ceo_morning_briefing_error", org_id=org_id, error=str(e))
            return {"success": False, "error": str(e)}

    async def generate_evening_summary(self, org_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info("ceo_evening_summary_started", org_id=org_id)

        try:
            state = ExecutionState(user_request="evening summary and tasks completed today", org_id=org_id, user_id=user_id)
            finance = FinanceExecutor()
            state = await finance.execute(state)
            finance_result = state.agent_outputs.get("finance_executor", {})

            morning = self._morning_briefings.get(org_id, {})
            action_items = morning.get("summary", "")

            summary_prompt = f"""You are the CEO agent. Generate an end-of-day summary.
Morning plan: {action_items}
End of day finance status: {finance_result.get('response', 'No data')}
Summarize:
1. What was accomplished today
2. What's still pending
3. Revenue and collections summary
4. Tomorrow's focus"""

            try:
                summary_text = await self.llm.simple_completion(prompt=summary_prompt, task_type="simple")
            except:
                summary_text = "Evening summary generated."

            summary = {
                "org_id": org_id,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "generated_at": datetime.utcnow().isoformat(),
                "summary": summary_text,
                "finance_end_of_day": finance_result,
            }

            self._evening_summaries[org_id] = summary
            agent_memory.store_business(org_id, f"evening_summary_{summary['date']}", summary)

            await activity_stream.publish(
                ActivityType.EVENING_SUMMARY, agent="ceo", org_id=org_id,
                title="Evening Summary", message=summary_text[:200],
                priority=Priority.LOW,
            )

            return summary

        except Exception as e:
            logger.error("ceo_evening_summary_error", org_id=org_id, error=str(e))
            return {"success": False, "error": str(e)}

    async def coordinate_agents(self, org_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info("ceo_agent_coordination_started", org_id=org_id)

        agents = [
            ("finance_executor", "financial summary"),
            ("compliance_executor", "compliance status"),
            ("collections_executor", "collections dashboard"),
            ("growth_executor", "growth dashboard"),
        ]

        tasks = []
        for executor_name, request in agents:
            executor = self.executors.get(
                next((role for role, ex in self.executors.items() if ex.name == executor_name), None)
            )
            if executor:
                state = ExecutionState(user_request=request, org_id=org_id, user_id=user_id)
                tasks.append(executor.execute(state))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        synthesized = {}
        for i, (executor_name, _) in enumerate(agents):
            result = results[i]
            if isinstance(result, Exception):
                synthesized[executor_name] = {"error": str(result)}
            else:
                synthesized[executor_name] = result.agent_outputs.get(executor_name, {})

        synthesis_prompt = f"""You are the CEO agent. Synthesize these agent reports into a unified organizational health summary:
{json.dumps({k: v.get('response', '') for k, v in synthesized.items()}, indent=2)}
Provide:
1. Overall health score (1-10)
2. Top concern
3. Top opportunity
4. Recommended next action"""

        try:
            synthesis = await self.llm.simple_completion(prompt=synthesis_prompt, task_type="simple")
        except:
            synthesis = "Coordination complete. Review individual agent reports."

        return {
            "org_id": org_id,
            "generated_at": datetime.utcnow().isoformat(),
            "synthesis": synthesis,
            "agent_results": synthesized,
        }

    def get_briefing_history(self, org_id: str) -> Dict[str, Any]:
        return {
            "morning_briefing": self._morning_briefings.get(org_id),
            "evening_summary": self._evening_summaries.get(org_id),
        }


master_orchestrator = MasterOrchestrator()
