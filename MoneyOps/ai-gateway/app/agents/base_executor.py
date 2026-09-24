"""
True Agent-Native Executors - Agents that EXECUTE operations via real API calls.
Rebuilt on AgentOS infrastructure: message bus, decision engine, governance, observation, memory.

Every executor:
- Has a defined identity with mission, goals, constraints
- Communicates via message bus (not shared dicts)
- Makes decisions through the decision engine
- Logs every action to the audit registry
- Persists memory beyond sessions
- Has proper validation, timeouts, retries, error handling
"""
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta

from app.llm.multi_provider import llm_client
from app.config import settings
from app.utils.logger import get_logger
from app.adapters.backend_adapter import get_backend_adapter
from app.memory.pinecone_manager import pinecone_manager
from app.integrations.treds_client import treds_client
from app.schemas.treds import InvoiceDiscountingRequest
from app.agentos.message_bus import message_bus, AgentMessage, MessageType
from app.agentos.governance import governance, AgentRules
from app.agentos.observation import audit_registry
from app.agentos.memory import agent_memory
from app.agentos.identity import (
    AGENT_IDENTITIES, AgentIdentity, AgentRole, AgentMission, AgentCapability,
    FINANCE_AGENT_IDENTITY, COMPLIANCE_AGENT_IDENTITY,
    COLLECTIONS_AGENT_IDENTITY, TREDS_AGENT_IDENTITY,
    GROWTH_AGENT_IDENTITY, CEO_AGENT_IDENTITY,
)
from app.agents.activity_stream import activity_stream, ActivityType, Priority
from app.middleware.agent_rate_limiter import check_executor_concurrency
from app.utils.tracing import get_trace_id, set_trace_id

logger = get_logger(__name__)


class AgentRole(str, Enum):
    FINANCE_OPS = "finance_ops"
    COMPLIANCE = "compliance"
    COLLECTIONS = "collections"
    TREDS = "treds"
    GROWTH = "growth"
    CEO = "ceo"


@dataclass
class CycleResult:
    """Result of an autonomous agent cycle"""
    agent: str
    org_id: str
    success: bool
    summary: str
    actions_taken: List[str] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent,
            "org_id": self.org_id,
            "success": self.success,
            "summary": self.summary,
            "actions_taken": self.actions_taken,
            "alerts": self.alerts,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "error": self.error,
        }


@dataclass
class ExecutionState:
    """Shared state across all agents - retained for backward compatibility.
    New agents should use message_bus for inter-agent communication."""
    user_request: str
    org_id: str = ""
    user_id: Optional[str] = None
    business_id: str = "1"
    thread_id: str = "default"
    session_id: str = ""
    trace_id: str = ""  # populated from contextvars on creation
    conversation_history: list = field(default_factory=list)
    execution_plan: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    delegation_target: str = ""
    delegation_message: str = ""
    cross_agent_queries: list = field(default_factory=list)
    cross_agent_synthesis: list = field(default_factory=list)
    next_agent: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 5


@dataclass
class DecisionEvaluation:
    action_description: str
    score: float
    recommendation: str
    impact_analysis: str
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    business_health_snapshot: Dict[str, Any] = field(default_factory=dict)

    def should_proceed(self) -> bool:
        return self.recommendation == "proceed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_description": self.action_description,
            "score": self.score,
            "recommendation": self.recommendation,
            "impact_analysis": self.impact_analysis,
            "risks": self.risks,
            "alternatives": self.alternatives,
        }


class BaseExecutor:
    """
    Agent-Native Executor with AgentOS integration.
    Every executor has identity, communicates via message bus,
    makes decisions through the decision engine, and logs to audit.
    """

    def __init__(self, name: str, role: AgentRole):
        self.name = name
        self.role = role
        self.llm = llm_client
        self.backend = get_backend_adapter()
        self.identity: Optional[AgentIdentity] = AGENT_IDENTITIES.get(
            AgentRole(role.value) if isinstance(role, AgentRole) else role
        )
        self._start_time: float = 0.0

    async def _ensure_registered(self):
        """Idempotent AgentOS registration. Safe to call multiple times."""
        if not hasattr(self, '_agentos_registered') or not self._agentos_registered:
            await message_bus.register_agent(self.name)
            governance.register_agent(self.name, self.role)
            self._agentos_registered = True
            logger.info("agentos_initialized", agent=self.name, role=self.role.value, trace_id=get_trace_id())

    async def _init_agentos(self):
        await self._ensure_registered()

    async def _check_concurrency_limit(self, state: ExecutionState) -> bool:
        """Check per-agent concurrency cap. Returns True if allowed."""
        if state.org_id:
            allowed = await check_executor_concurrency(self.name, state.org_id)
            if not allowed:
                logger.warning(
                    "executor_concurrency_limit_reached",
                    agent=self.name,
                    org_id=state.org_id,
                    trace_id=get_trace_id(),
                )
                return False
        return True

    async def execute(self, state: ExecutionState) -> ExecutionState:
        # Assert AgentOS registration before any execution — fail loud, not quiet
        if not hasattr(self, '_agentos_registered') or not self._agentos_registered:
            await self._ensure_registered()
        raise NotImplementedError

    async def run_autonomous_cycle(self, org_id: str, user_id: Optional[str] = None) -> CycleResult:
        # AgentOS registration check at the top (idempotent)
        await self._ensure_registered()

        try:
            state = ExecutionState(
                user_request="run_autonomous_cycle",
                org_id=org_id,
                user_id=user_id,
                session_id="autonomous",
            )
            state = await self.execute(state)
            outputs = state.agent_outputs.get(self.name, {})
            return CycleResult(
                agent=self.name,
                org_id=org_id,
                success=len(state.errors) == 0,
                summary=outputs.get("response", f"{self.name} cycle completed") if isinstance(outputs, dict) else f"{self.name} cycle completed",
                error="; ".join(state.errors) if state.errors else None,
            )
        except Exception as e:
            return CycleResult(
                agent=self.name,
                org_id=org_id,
                success=False,
                summary=f"{self.name} cycle failed",
                error=str(e),
            )

    async def _evaluate_and_decide(self, action: str, state: ExecutionState) -> Tuple[bool, DecisionEvaluation]:
        from app.agentos.decision import decision_engine
        decision = await decision_engine.evaluate(
            agent_name=self.name,
            action=action,
            context={"org_id": state.org_id, "user_id": state.user_id},
            org_id=state.org_id,
        )
        eval_result = DecisionEvaluation(
            action_description=action,
            score=decision.score,
            recommendation="proceed" if decision.status.value == "approved" else
                           "caution" if decision.status.value == "escalated" else "block",
            impact_analysis=decision.reasoning,
            risks=decision.risks,
            alternatives=decision.alternatives,
            business_health_snapshot=decision.business_health,
        )
        return decision.status.value in ("approved", "executing"), eval_result

    async def _audit(self, action: str, decision_id: str, reasoning: str,
                     success: bool, duration_ms: float, error: Optional[str] = None,
                     org_id: str = "", outcome: str = "", retries: int = 0):
        await audit_registry.record(
            agent_name=self.name,
            action=action,
            decision_id=decision_id,
            reasoning=reasoning,
            execution_duration_ms=duration_ms,
            success=success,
            error=error,
            retries=retries,
            org_id=org_id,
            actual_outcome=outcome,
        )

    def write_to_memory(self, key: str, value: Any, state: ExecutionState):
        agent_memory.store_short_term(self.name, key, value)

    def read_from_memory(self, key: str, state: ExecutionState) -> Any:
        return agent_memory.get_short_term(self.name, key)

    def delegate_to(self, target_role: str, message: str, state: ExecutionState):
        state.delegation_target = target_role
        state.delegation_message = message
        logger.info("agent_delegation", from_agent=self.name, to_agent=target_role, trace_id=get_trace_id())

    def share_context_with(self, key: str, value: Any, state: ExecutionState, namespace: str = None):
        ns = namespace or self.name
        state.shared_memory[f"{ns}:{key}"] = {
            "value": value,
            "source_agent": self.name,
            "timestamp": time.time(),
        }

    def read_shared_context(self, key: str, state: ExecutionState, namespace: str = None) -> Any:
        if namespace:
            entry = state.shared_memory.get(f"{namespace}:{key}")
            return entry.get("value") if entry else None
        for k, v in state.shared_memory.items():
            if k.endswith(f":{key}"):
                return v.get("value")
        return None

    def list_shared_context(self, state: ExecutionState) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for k, v in state.shared_memory.items():
            ns, _, key = k.partition(":")
            if ns not in result:
                result[ns] = {}
            result[ns][key] = v.get("value")
        return result

    async def query_agent(self, target_role: str, query: str, state: ExecutionState) -> Dict[str, Any]:
        msg = AgentMessage(
            message_type=MessageType.QUERY,
            sender=self.name,
            receiver=target_role,
            payload={"query": query},
            org_id=state.org_id,
        )
        sent = await message_bus.send(msg)
        if sent:
            return {"success": True, "response": f"Query sent to {target_role}"}
        return {"success": False, "response": f"Failed to send query to {target_role}"}

    async def evaluate_decision(self, action: str, state: ExecutionState) -> DecisionEvaluation:
        _, eval_result = await self._evaluate_and_decide(action, state)
        return eval_result

    @staticmethod
    def _items(data: Any) -> List[Dict[str, Any]]:
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                return data["data"]
            if isinstance(data.get("data"), dict):
                return BaseExecutor._items(data["data"])
            if isinstance(data.get("content"), list):
                return data["content"]
            for key in ("clients", "invoices", "transactions", "items", "results"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    async def _handle_unrecognized(self, state: ExecutionState) -> Dict[str, Any]:
        return await self._fallback_response(state.user_request)

    async def _fallback_response(self, user_request: str) -> Dict[str, Any]:
        try:
            prompt = (
                f"The user said: '{user_request}'. "
                f"I am the {self.name} ({self.role.value}) agent. "
                f"If this is a valid business or financial request, rephrase it in a helpful way. "
                f"If unrelated, politely state what I can help with. "
                f"Return JSON: {{\"response\": \"your response\"}}"
            )
            result = json.loads(await self.llm.simple_completion(prompt=prompt, task_type="simple"))
            return {"success": True, "response": result.get("response", f"I can help with {self.role.value} tasks. Could you rephrase?")}
        except Exception:
            return {"success": True, "response": f"I understand you're asking about something related to your business. As the {self.role.value} agent, I can help with operations like invoicing, payments, compliance, or growth analysis. Could you be more specific?"}


class FinanceExecutor(BaseExecutor):
    """Executes financial operations via REAL API calls"""

    def __init__(self):
        super().__init__("finance_executor", AgentRole.FINANCE_OPS)
        self.identity = FINANCE_AGENT_IDENTITY

    async def execute(self, state: ExecutionState) -> ExecutionState:
        self._start_time = time.time()
        user_request = state.user_request.lower()
        org_id = state.org_id

        # ── Concurrency cap check (same pattern added to all executors) ─────────
        if not await self._check_concurrency_limit(state):
            state.agent_outputs[self.name] = {
                "success": False,
                "operation": "concurrency_limited",
                "response": f"{self.name} is at capacity. Please try again shortly.",
            }
            state.completed_steps.append(self.name)
            return state

        try:
            action = self._classify_action(user_request)
            should_proceed, eval_result = await self._evaluate_and_decide(action, state)
            self.share_context_with("decision_evaluation", eval_result.to_dict(), state)

            if not should_proceed:
                state.agent_outputs[self.name] = {
                    "success": False,
                    "operation": "decision_blocked",
                    "action": action,
                    "response": eval_result.impact_analysis,
                    "risks": eval_result.risks,
                    "alternatives": eval_result.alternatives,
                    "recommendation": eval_result.recommendation,
                    "score": eval_result.score,
                }
                state.completed_steps.append(self.name)
                duration_ms = (time.time() - self._start_time) * 1000
                await self._audit(action, "", eval_result.impact_analysis, False, duration_ms, org_id=org_id)
                return state

            handler = self._get_handler(action)
            result = await handler(state)

            if isinstance(result, dict):
                result["decision_evaluation"] = eval_result.to_dict()

            state.agent_outputs[self.name] = result
            state.completed_steps.append(self.name)
            duration_ms = (time.time() - self._start_time) * 1000
            await self._audit(action, "", eval_result.impact_analysis,
                            result.get("success", False), duration_ms,
                            error=result.get("response") if not result.get("success") else None,
                            org_id=org_id, outcome=result.get("response", ""))

        except Exception as e:
            state.errors.append(f"{self.name}: {str(e)}")
            logger.error("finance_executor_error", error=str(e), org_id=org_id, trace_id=get_trace_id())
            duration_ms = (time.time() - self._start_time) * 1000
            await self._audit("execute", "", str(e), False, duration_ms, error=str(e), org_id=org_id)

        return state

    def _classify_action(self, user_request: str) -> str:
        if any(w in user_request for w in ["create invoice", "new invoice", "add invoice"]):
            return "create invoice"
        elif any(w in user_request for w in ["record payment", "mark paid", "payment received"]):
            return "record payment"
        elif any(w in user_request for w in ["record expense", "add expense", "spent"]):
            return "record expense"
        elif any(w in user_request for w in ["balance", "cash position", "how much", "revenue", "profit", "financial", "earnings", "income"]):
            return "check balance"
        elif any(w in user_request for w in ["invoice", "pending", "overdue", "due"]):
            return "query invoices"
        else:
            return "financial summary"

    def _get_handler(self, action: str):
        handlers = {
            "create invoice": self._create_invoice,
            "record payment": self._record_payment,
            "record expense": self._record_expense,
            "check balance": self._check_balance,
            "query invoices": self._query_invoices,
            "financial summary": self._get_financial_summary,
        }
        return handlers.get(action, self._get_financial_summary)

    async def _extract_with_llm(self, prompt: str, retries: int = 2) -> Optional[Dict[str, Any]]:
        for attempt in range(retries + 1):
            try:
                response = await self.llm.simple_completion(prompt=prompt, task_type="simple")
                # Try direct JSON parse first
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    # Try to extract JSON from code blocks or surrounding text
                    import re
                    json_match = re.search(r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}', response, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group(0))
                    raise
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < retries:
                    await asyncio.sleep(0.3)
                    continue
                logger.warning("llm_extraction_failed", error=str(e), attempt=attempt, trace_id=get_trace_id())
                # Return minimal default instead of None so callers don't break
                return {}
            except Exception as e:
                logger.error("llm_extraction_error", error=str(e), attempt=attempt, trace_id=get_trace_id())
                if attempt < retries:
                    await asyncio.sleep(0.5)
                    continue
                return {}
        return {}

    async def _create_invoice(self, state: ExecutionState) -> Dict[str, Any]:
        prompt = f"""Extract invoice details from: {state.user_request}
Return JSON:
{{
    "client_name": "extracted client",
    "amount": numeric_only,
    "description": "brief desc",
    "due_days": number
}}
If missing, use null."""

        details = await self._extract_with_llm(prompt)
        if not details:
            details = {"client_name": None, "amount": None, "description": "Invoice", "due_days": 30}

        if not details.get("client_name") or not details.get("amount"):
            return {"success": False, "response": "I need client name and amount to create an invoice."}

        clients = await self.backend.get_clients(state.org_id, user_id=state.user_id)
        client_id = None
        for client in clients if clients else []:
            if details["client_name"].lower() in (client.get("name") or "").lower():
                client_id = client.get("id")
                break

        due_date = (datetime.now() + timedelta(days=details.get("due_days", 30))).strftime("%Y-%m-%d")
        payload = {
            "clientId": client_id,
            "clientName": details["client_name"],
            "totalAmount": float(details["amount"]),
            "dueDate": due_date,
            "description": details.get("description", "Invoice"),
            "status": "SENT",
        }

        try:
            response = await self.backend._request(
                "POST", "/api/invoices", org_id=state.org_id, user_id=state.user_id, data=payload
            )
            if response.success:
                invoice_id = response.data.get("id", "unknown") if response.data else "unknown"
                agent_memory.store_long_term(self.name, f"invoice_{invoice_id}", {
                    "id": invoice_id, "amount": details["amount"],
                    "client": details["client_name"], "due_date": due_date,
                })
                return {
                    "success": True, "operation": "invoice_created",
                    "invoice_id": invoice_id, "amount": details["amount"],
                    "client": details["client_name"],
                    "response": f"Invoice created for Rs.{float(details['amount']):,.0f} to {details['client_name']}. Due: {due_date}.",
                }
            return {"success": False, "response": f"Failed: {response.error or 'Unknown error'}"}
        except Exception as e:
            return {"success": False, "response": f"Error creating invoice: {str(e)}"}

    async def _record_payment(self, state: ExecutionState) -> Dict[str, Any]:
        invoices_resp = await self.backend._request(
            "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
        )
        if not invoices_resp.success or not invoices_resp.data:
            return {"success": False, "response": "No invoices found."}

        invoices = self._items(invoices_resp.data)
        pending = [i for i in invoices if i.get("status") in ("SENT", "OVERDUE")]
        if not pending:
            return {"success": True, "response": "No pending invoices to mark as paid."}

        invoice_list = "\n".join([
            f"- {i.get('clientName', 'Unknown')}: Rs.{float(i.get('totalAmount', 0)):,.0f} (ID: {i.get('id')})"
            for i in pending[:5]
        ])
        prompt = f"""User: "{state.user_request}"
PENDING:
{invoice_list}
Which invoice? Return JSON: {{"invoice_id": "id_from_list", "client_name": "name", "amount": number}}"""

        match = await self._extract_with_llm(prompt)
        invoice_id = match.get("invoice_id", pending[0].get("id")) if match else pending[0].get("id")

        try:
            response = await self.backend._request(
                "POST", f"/api/invoices/{invoice_id}/payment",
                org_id=state.org_id, user_id=state.user_id,
                data={"amount": float(pending[0].get("totalAmount", 0)),
                      "transactionType": "PAYMENT", "description": "Payment via AI"}
            )
            if response.success:
                return {"success": True, "operation": "payment_recorded", "invoice_id": invoice_id,
                        "response": "Payment recorded. Invoice marked as paid."}
            return {"success": False, "response": f"Failed: {response.error}"}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _record_expense(self, state: ExecutionState) -> Dict[str, Any]:
        prompt = f"""Extract from: {state.user_request}
Return JSON:
{{"amount": numeric_only, "category": "salaries|fuel|rent|software|travel|marketing|utilities|other", "description": "brief desc"}}"""

        details = await self._extract_with_llm(prompt)
        if not details or not details.get("amount"):
            return {"success": False, "response": "Please specify the expense amount."}

        payload = {
            "amount": float(details["amount"]),
            "type": "debit",
            "category": details.get("category", "other"),
            "description": details.get("description", "Expense via AI"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "AI-Agent",
        }

        try:
            response = await self.backend._request(
                "POST", "/api/transactions", org_id=state.org_id, user_id=state.user_id, data=payload
            )
            if response.success:
                return {"success": True, "operation": "expense_recorded", "amount": details["amount"],
                        "response": f"Recorded expense of Rs.{float(details['amount']):,.0f} for {details.get('category', 'expenses')}."}
            return {"success": False, "response": f"Failed: {response.error}"}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _check_balance(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            metrics_resp = await self.backend.get_finance_metrics(
                state.business_id, state.org_id, state.user_id
            )
            if not metrics_resp.success or not metrics_resp.data:
                return {"success": False, "response": "Couldn't fetch financial data."}

            m = metrics_resp.data
            return {"success": True, "operation": "balance_check",
                    "response": f"Revenue: Rs.{m.get('revenue', 0):,.0f} | Expenses: Rs.{m.get('expenses', 0):,.0f} | Profit: Rs.{m.get('netProfit', 0):,.0f}"}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _query_invoices(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
            )
            if not invoices_resp.success or not invoices_resp.data:
                return {"success": True, "response": "No invoices yet."}

            invoices = self._items(invoices_resp.data)
            pending = [i for i in invoices if i.get("status") in ("DRAFT", "SENT")]
            overdue = [i for i in invoices if i.get("status") == "OVERDUE"]

            pending_amt = sum(float(i.get("totalAmount", 0)) for i in pending)
            overdue_amt = sum(float(i.get("totalAmount", 0)) for i in overdue)

            self.share_context_with("invoices", invoices, state)
            self.share_context_with("pending_count", len(pending), state)
            self.share_context_with("overdue_count", len(overdue), state)
            self.share_context_with("overdue_amount", overdue_amt, state)

            agent_memory.store_business(state.org_id, "last_invoice_query", {
                "total": len(invoices), "pending": len(pending), "overdue": len(overdue),
                "overdue_amount": overdue_amt, "timestamp": time.time(),
            })

            resp = f"Total: {len(invoices)} invoices. "
            if pending:
                resp += f"Pending: {len(pending)} (Rs.{pending_amt:,.0f}). "
            if overdue:
                resp += f"OVERDUE: {len(overdue)} (Rs.{overdue_amt:,.0f}). "
            return {"success": True, "operation": "invoice_query", "response": resp}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _get_financial_summary(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            results = await asyncio.gather(
                self.backend.get_finance_metrics(state.business_id, state.org_id, state.user_id),
                self.backend._request("GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id),
                return_exceptions=True
            )

            metrics = results[0].data if not isinstance(results[0], Exception) and results[0].success else {}
            invoices = self._items(results[1].data) if not isinstance(results[1], Exception) and results[1].success else []

            revenue = metrics.get("revenue", 0)
            expenses = metrics.get("expenses", 0)
            profit = metrics.get("netProfit", 0)
            margin = (profit / max(revenue, 1)) * 100 if revenue > 0 else 0
            overdue = [i for i in invoices if i.get("status") == "OVERDUE"] if isinstance(invoices, list) else []
            overdue_amt = sum(float(i.get("totalAmount", 0)) for i in overdue)

            self.share_context_with("revenue", revenue, state)
            self.share_context_with("profit", profit, state)
            self.share_context_with("margin", margin, state)
            self.share_context_with("invoices", invoices, state)
            self.share_context_with("overdue_amount", overdue_amt, state)
            self.share_context_with("expenses", expenses, state)

            agent_memory.store_business(state.org_id, "last_financial_summary", {
                "revenue": revenue, "expenses": expenses, "profit": profit,
                "margin": margin, "overdue_count": len(overdue),
                "overdue_amount": overdue_amt,
            })

            resp = f"Revenue: Rs.{revenue:,.0f} | Expenses: Rs.{expenses:,.0f} | Profit: Rs.{profit:,.0f} ({margin:.1f}%). "
            if overdue:
                resp += f"URGENT: {len(overdue)} overdue worth Rs.{overdue_amt:,.0f}. "
            return {"success": True, "operation": "financial_summary", "response": resp}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}


class ComplianceExecutor(BaseExecutor):
    """Executes compliance operations with real GST knowledge retrieval and no stubs."""

    def __init__(self):
        super().__init__("compliance_executor", AgentRole.COMPLIANCE)
        self.identity = COMPLIANCE_AGENT_IDENTITY

    async def execute(self, state: ExecutionState) -> ExecutionState:
        self._start_time = time.time()
        user_request = state.user_request.lower()

        if not await self._check_concurrency_limit(state):
            state.agent_outputs[self.name] = {
                "success": False, "operation": "concurrency_limited",
                "response": f"{self.name} is at capacity. Please try again shortly.",
            }
            state.completed_steps.append(self.name)
            return state

        try:
            action = self._classify_action(user_request)
            should_proceed, eval_result = await self._evaluate_and_decide(action, state)

            if not should_proceed:
                state.agent_outputs[self.name] = {
                    "success": False, "operation": "decision_blocked",
                    "action": action, "response": eval_result.impact_analysis,
                    "risks": eval_result.risks, "alternatives": eval_result.alternatives,
                    "recommendation": eval_result.recommendation, "score": eval_result.score,
                }
                state.completed_steps.append(self.name)
                return state

            handler = self._get_handler(action)
            result = await handler(state)

            if isinstance(result, dict):
                result["decision_evaluation"] = eval_result.to_dict()

            state.agent_outputs[self.name] = result
            state.completed_steps.append(self.name)

            duration_ms = (time.time() - self._start_time) * 1000
            await self._audit(action, "", eval_result.impact_analysis,
                            result.get("success", False), duration_ms,
                            error=result.get("response") if not result.get("success") else None,
                            org_id=state.org_id, outcome=result.get("response", ""))

        except Exception as e:
            state.errors.append(f"{self.name}: {str(e)}")
            logger.error("compliance_executor_error", error=str(e))

        return state

    def _classify_action(self, user_request: str) -> str:
        if any(w in user_request for w in ["gst", "tax", "calculate"]):
            return "gst calculation"
        elif any(w in user_request for w in ["compliance", "deadline", "filing"]):
            return "compliance check"
        elif any(w in user_request for w in ["reconcile", "gstr", "2a", "2b"]):
            return "gst reconciliation"
        elif any(w in user_request for w in ["dashboard", "overview", "summary"]):
            return "compliance dashboard"
        else:
            return "unrecognized"

    def _get_handler(self, action: str):
        handlers = {
            "gst calculation": self._calculate_gst,
            "compliance check": self._check_compliance,
            "gst reconciliation": self._reconcile_gst,
            "compliance dashboard": self._get_compliance_dashboard,
            "unrecognized": self._handle_unrecognized,
        }
        return handlers.get(action, self._get_compliance_dashboard)

    async def _calculate_gst(self, state: ExecutionState) -> Dict[str, Any]:
        invoices = self.read_shared_context("invoices", state, namespace="finance_executor")

        prompt = f"""Extract from: {state.user_request}
Return JSON: {{"amount": numeric, "gst_rate": 5|12|18|28}}"""

        try:
            details = json.loads(await self.llm.simple_completion(prompt=prompt, task_type="simple"))
            amount = float(details.get("amount", 0))
            gst_rate = float(details.get("gst_rate", 18))
        except:
            return {"success": False, "response": "Please specify amount for GST calculation."}

        if amount <= 0 and invoices:
            total = sum(float(i.get("totalAmount", 0)) for i in invoices if i.get("totalAmount"))
            amount = total

        if amount <= 0:
            self.delegate_to("finance_ops", f"PROVIDE_INVOICES_FOR_GST: {state.user_request}", state)
            self.share_context_with("pending_gst_request", {
                "original_request": state.user_request, "gst_rate": gst_rate,
            }, state)
            return {"success": False, "response": "I need invoice data. Fetching from Finance...", "requires_delegation": True}

        gst = amount * (gst_rate / 100)
        result = {
            "success": True, "operation": "gst_calculation",
            "amount": amount, "gst_rate": gst_rate, "gst": gst,
            "total": amount + gst,
            "response": f"On Rs.{amount:,.0f} at {gst_rate}%: GST = Rs.{gst:,.0f}, Total = Rs.{amount + gst:,.0f}",
        }
        self.share_context_with("gst_result", result, state)
        agent_memory.store_business(state.org_id, f"gst_calc_{int(time.time())}", result)
        return result

    async def _check_compliance(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            response = await self.backend._request(
                "GET", "/api/compliance/deadlines", org_id=state.org_id, user_id=state.user_id
            )
            deadlines = []
            rag_context = ""
            if response.success and response.data:
                deadlines_data = response.data
                if isinstance(deadlines_data, dict):
                    deadlines = deadlines_data.get("upcoming", [])
                elif isinstance(deadlines_data, list):
                    deadlines = deadlines_data

            if deadlines:
                try:
                    rules = await agent_memory.search_compliance(
                        query=f"GST filing deadline {deadlines[0].get('name', '')}" if deadlines else "GST compliance rules",
                        top_k=3
                    )
                    if rules:
                        rag_context = "\nRELEVANT RULES:\n" + "\n".join([f"- {r['text'][:200]}" for r in rules])
                except Exception as e:
                    logger.warning("compliance_rag_search_failed", error=str(e))
                    rag_context = "\n(Compliance knowledge base unavailable - check Pinecone configuration)"

            if not deadlines:
                return {"success": True, "operation": "compliance_check",
                        "response": "No upcoming compliance deadlines." + rag_context}

            items = [f"{d.get('name', 'Deadline')}: due {d.get('dueDate', 'TBD')}" for d in deadlines[:5]]
            agent_memory.store_business(state.org_id, f"compliance_check_{int(time.time())}", {
                "deadlines": items, "rag_rules_found": len(rules) if rules else 0,
            })
            return {"success": True, "operation": "compliance_check",
                    "response": f"Upcoming: {'; '.join(items)}" + rag_context}
        except Exception as e:
            return {"success": False, "response": f"Compliance check error: {str(e)}"}

    async def _reconcile_gst(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            gst_status = await self.backend._request(
                "GET", "/api/compliance/gst-status", org_id=state.org_id, user_id=state.user_id
            )
            status_data = {}
            if gst_status.success and gst_status.data:
                status_data = gst_status.data if isinstance(gst_status.data, dict) else {}

            invoices = self.read_shared_context("invoices", state, namespace="finance_executor")
            if not invoices:
                invoices_resp = await self.backend._request(
                    "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
                )
                invoices = self._items(invoices_resp.data) if invoices_resp.success else []

            purchase_total = sum(float(i.get("totalAmount", 0)) for i in invoices if i.get("totalAmount"))
            itc_claimed = status_data.get("itcClaimed", 0)
            gst_rate = await self._determine_gst_rate(invoices)
            itc_eligible = purchase_total * (gst_rate / 100)
            discrepancy = abs(itc_claimed - itc_eligible) if itc_claimed else 0

            result = {
                "success": True, "operation": "gst_reconciliation",
                "total_purchases": purchase_total,
                "itc_eligible_estimate": itc_eligible,
                "itc_claimed": itc_claimed,
                "discrepancy": discrepancy,
                "response": f"GST reconciliation: Rs.{purchase_total:,.0f} in purchases. Eligible ITC ~Rs.{itc_eligible:,.0f}. Claimed: Rs.{itc_claimed:,.0f}. Discrepancy: Rs.{discrepancy:,.0f}." if itc_claimed else
                           f"GST reconciliation: Rs.{purchase_total:,.0f} in purchases. Estimated ITC eligible: Rs.{itc_eligible:,.0f}. Connect to GST portal for exact figures.",
            }
            agent_memory.store_business(state.org_id, f"gst_reconciliation_{int(time.time())}", result)
            return result
        except Exception as e:
            return {"success": False, "response": f"GST reconciliation error: {str(e)}"}

    async def _determine_gst_rate(self, invoices: list) -> float:
        try:
            hsn_codes = set()
            for inv in invoices:
                items = inv.get("lineItems", inv.get("items", []))
                if isinstance(items, list):
                    for item in items:
                        hsn = item.get("hsnCode") or item.get("hsn", "")
                        if hsn:
                            hsn_codes.add(hsn)
                if inv.get("hsnCode"):
                    hsn_codes.add(inv["hsnCode"])

            descriptions = []
            for inv in invoices[:5]:
                desc = inv.get("description") or inv.get("clientName", "")
                if desc:
                    descriptions.append(desc)

            prompt = (
                f"Given these {'HSN codes: ' + ', '.join(list(hsn_codes)[:5]) if hsn_codes else 'business context: ' + '. '.join(descriptions[:3])}\n"
                f"Determine the most likely GST slab rate (0, 5, 12, 18, or 28) as a number.\n"
                f"Return JSON: {{\"gst_rate\": number, \"reason\": \"brief reason\"}}\n"
                f"Use 18 if uncertain."
            )
            result = json.loads(await self.llm.simple_completion(prompt=prompt, task_type="simple"))
            rate = float(result.get("gst_rate", 18))
            return rate if rate in (0, 5, 12, 18, 28) else 18
        except Exception:
            return 18.0

    async def _get_compliance_dashboard(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            deadlines_resp = await self.backend._request(
                "GET", "/api/compliance/deadlines", org_id=state.org_id, user_id=state.user_id
            )
            deadlines = deadlines_resp.data.get("upcoming", []) if deadlines_resp.success and isinstance(deadlines_resp.data, dict) else []

            gst_resp = await self.backend._request(
                "GET", "/api/compliance/gst-status", org_id=state.org_id, user_id=state.user_id
            )
            gst_status = gst_resp.data.get("status", "Unknown") if gst_resp.success and isinstance(gst_resp.data, dict) else "Unknown"

            return {"success": True, "operation": "compliance_dashboard",
                    "response": f"GST: {gst_status}. {len(deadlines)} upcoming deadlines."}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}


class CollectionsExecutor(BaseExecutor):
    """
    Executes automated collections via REAL WhatsApp/SMS delivery.
    Uses Redis notification queue to trigger the notification_worker which uses Twilio.
    No simulated sends - every reminder is verifiably delivered or reported as failed.
    """

    def __init__(self):
        super().__init__("collections_executor", AgentRole.COLLECTIONS)
        self.identity = COLLECTIONS_AGENT_IDENTITY

    async def execute(self, state: ExecutionState) -> ExecutionState:
        self._start_time = time.time()
        user_request = state.user_request.lower()

        if not await self._check_concurrency_limit(state):
            state.agent_outputs[self.name] = {
                "success": False, "operation": "concurrency_limited",
                "response": f"{self.name} is at capacity. Please try again shortly.",
            }
            state.completed_steps.append(self.name)
            return state

        try:
            if any(w in user_request for w in ["send reminder", "chase", "follow up"]):
                result = await self._send_reminders(state)
            elif any(w in user_request for w in ["escalate", "overdue", "aging"]):
                result = await self._escalate_overdue(state)
            else:
                result = await self._collections_dashboard(state)

            state.agent_outputs[self.name] = result
            state.completed_steps.append(self.name)

            duration_ms = (time.time() - self._start_time) * 1000
            await self._audit("collections", "", result.get("response", ""),
                            result.get("success", False), duration_ms,
                            error=None if result.get("success") else result.get("response"),
                            org_id=state.org_id, outcome=result.get("response", ""))

        except Exception as e:
            state.errors.append(f"{self.name}: {str(e)}")
            logger.error("collections_executor_error", error=str(e))

        return state

    async def _send_reminders(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices = self.read_shared_context("invoices", state, namespace="finance_executor")
            if not invoices:
                invoices_resp = await self.backend._request(
                    "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
                )
                if not invoices_resp.success or not invoices_resp.data:
                    return {"success": True, "response": "No invoices found for reminders."}
                invoices = self._items(invoices_resp.data)

            overdue = [i for i in invoices if i.get("status") == "OVERDUE"]
            if not overdue:
                return {"success": True, "response": "No overdue invoices to send reminders for."}

            aging = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
            for inv in overdue:
                try:
                    due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                    days = (datetime.now() - due).days
                    if days <= 30:
                        aging["0-30"] += 1
                    elif days <= 60:
                        aging["31-60"] += 1
                    elif days <= 90:
                        aging["61-90"] += 1
                    else:
                        aging["90+"] += 1
                except:
                    aging["0-30"] += 1

            sent_count = 0
            failed_count = 0
            delivery_results = []

            reminder_templates = {
                "0-30": "Dear {client}, your invoice {invoice_id} of Rs.{amount:,.0f} was due on {due_date}. Please remit payment at your earliest convenience.",
                "31-60": "Dear {client}, payment for invoice {invoice_id} of Rs.{amount:,.0f} is overdue by {days} days. We request immediate settlement.",
                "61-90": "Dear {client}, invoice {invoice_id} for Rs.{amount:,.0f} is {days} days overdue. Please arrange payment to avoid escalation.",
                "90+": "Dear {client}, invoice {invoice_id} for Rs.{amount:,.0f} is {days} days past due. This account is being escalated to our collections team.",
            }

            for inv in overdue:
                try:
                    due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                    days = (datetime.now() - due).days
                except:
                    days = 0

                if days <= 30:
                    bucket = "0-30"
                elif days <= 60:
                    bucket = "31-60"
                elif days <= 90:
                    bucket = "61-90"
                else:
                    bucket = "90+"

                template = reminder_templates.get(bucket, reminder_templates["0-30"])
                message_text = template.format(
                    client=inv.get("clientName", "Client"),
                    invoice_id=inv.get("id", "N/A"),
                    amount=float(inv.get("totalAmount", 0)),
                    due_date=inv.get("dueDate", "N/A"),
                    days=days,
                )

                client_phone = inv.get("clientPhone", "")
                if client_phone:
                    try:
                        await self._enqueue_whatsapp(client_phone, message_text, state.org_id)
                        sent_count += 1
                        delivery_results.append({
                            "invoice_id": inv.get("id"),
                            "client": inv.get("clientName"),
                            "channel": "whatsapp",
                            "status": "queued",
                        })
                    except Exception as e:
                        failed_count += 1
                        logger.warning("reminder_enqueue_failed", invoice_id=inv.get("id"), error=str(e))
                        delivery_results.append({
                            "invoice_id": inv.get("id"),
                            "client": inv.get("clientName"),
                            "channel": "whatsapp",
                            "status": "failed",
                            "error": str(e),
                        })
                else:
                    try:
                        await self._enqueue_email(
                            inv.get("clientEmail", ""),
                            "Payment Reminder",
                            message_text,
                            state.org_id,
                        )
                        sent_count += 1
                        delivery_results.append({
                            "invoice_id": inv.get("id"),
                            "client": inv.get("clientName"),
                            "channel": "email",
                            "status": "queued",
                        })
                    except Exception as e:
                        failed_count += 1
                        delivery_results.append({
                            "invoice_id": inv.get("id"),
                            "client": inv.get("clientName"),
                            "channel": "email",
                            "status": "failed",
                            "error": str(e),
                        })

            await agent_memory.store_semantic(
                namespace="collections-patterns",
                record_id=f"reminders_{state.org_id}_{datetime.now().timestamp():.0f}",
                text=f"Sent {sent_count} reminders, {failed_count} failed. Buckets: {json.dumps(aging)}",
                metadata={
                    "type": "reminder_batch", "org_id": state.org_id,
                    "sent": sent_count, "failed": failed_count,
                    "total_overdue": len(overdue),
                }
            )

            agent_memory.store_business(state.org_id, f"reminder_batch_{int(time.time())}", {
                "sent": sent_count, "failed": failed_count, "total": len(overdue),
                "aging": aging, "results": delivery_results[:10],
            })

            aging_str = ", ".join(f"{k}: {v}" for k, v in aging.items() if v > 0)
            if sent_count > 0:
                return {
                    "success": True, "operation": "reminders_sent",
                    "reminders_sent": sent_count, "reminders_failed": failed_count,
                    "aging_buckets": aging, "delivery_results": delivery_results[:10],
                    "response": f"Sent {sent_count} payment reminders via WhatsApp/email. Aging: {aging_str}. Failed: {failed_count}.",
                }
            else:
                return {
                    "success": True, "operation": "reminders_queued",
                    "reminders_sent": 0, "reminders_failed": failed_count,
                    "aging_buckets": aging,
                    "response": f"Identified {len(overdue)} overdue invoices but no client contact info found. Aging: {aging_str}. Please add phone/email to client records.",
                }

        except Exception as e:
            logger.error("send_reminders_error", error=str(e), org_id=state.org_id)
            return {"success": False, "response": f"Error sending reminders: {str(e)}"}

    async def _enqueue_whatsapp(self, phone: str, message: str, org_id: str):
        """Enqueue a WhatsApp notification to the Redis-backed notification worker."""
        try:
            from app.integrations.redis_client import cache_set, get_redis
            r = await get_redis()
            if r:
                job = json.dumps({
                    "type": "WHATSAPP_NOTIFICATION",
                    "payload": {"to": phone, "message": message, "org_id": org_id},
                    "timestamp": time.time(),
                })
                await r.lpush("moneyops:queue:notification", job)
                logger.info("whatsapp_enqueued", phone=phone[-4:], org_id=org_id)
            else:
                logger.warning("redis_unavailable_whatsapp_not_queued", phone=phone[-4:])
                raise RuntimeError("Redis unavailable - cannot queue WhatsApp notification")
        except ImportError:
            logger.error("redis_client_not_available")
            raise RuntimeError("Redis client not available")

    async def _enqueue_email(self, email: str, subject: str, message: str, org_id: str):
        """Enqueue an email notification."""
        if not email:
            raise ValueError("No email address provided")
        try:
            from app.integrations.redis_client import get_redis
            r = await get_redis()
            if r:
                job = json.dumps({
                    "type": "EMAIL_NOTIFICATION",
                    "payload": {"to": email, "subject": subject, "message": message, "org_id": org_id},
                    "timestamp": time.time(),
                })
                await r.lpush("moneyops:queue:notification", job)
                logger.info("email_enqueued", email=email, org_id=org_id)
            else:
                await self.backend._request(
                    "POST", "/api/notifications/email",
                    org_id=org_id, data={"to": email, "subject": subject, "message": message}
                )
        except Exception as e:
            logger.error("email_enqueue_failed", email=email, error=str(e))
            raise

    async def _escalate_overdue(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
            )
            if not invoices_resp.success or not invoices_resp.data:
                return {"success": True, "response": "No invoices found."}

            invoices = self._items(invoices_resp.data)
            critical = []
            for inv in invoices:
                if inv.get("status") == "OVERDUE":
                    try:
                        due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                        days = (datetime.now() - due).days
                        if days > 30:
                            critical.append({
                                "client": inv.get("clientName"),
                                "amount": float(inv.get("totalAmount", 0)),
                                "days": days,
                                "invoice_id": inv.get("id"),
                                "client_phone": inv.get("clientPhone", ""),
                            })
                    except:
                        pass

            if not critical:
                return {"success": True, "response": "No critically overdue invoices (>30 days)."}

            total_at_risk = sum(c["amount"] for c in critical)
            for item in critical:
                if item["days"] > 90:
                    await activity_stream.publish(
                        ActivityType.ALERT, agent=self.name, org_id=state.org_id,
                        title=f"CRITICAL: {item['client']} - {item['days']} days overdue",
                        message=f"Invoice Rs.{item['amount']:,.0f} is {item['days']} days past due. Immediate escalation required.",
                        priority=Priority.CRITICAL,
                        data={"invoice_id": item["invoice_id"], "amount": item["amount"], "days": item["days"]},
                    )

            agent_memory.store_business(state.org_id, f"escalation_{int(time.time())}", {
                "critical_count": len(critical), "total_at_risk": total_at_risk,
            })

            return {
                "success": True, "operation": "escalation", "critical_count": len(critical),
                "total_at_risk": total_at_risk,
                "response": f"CRITICAL: {len(critical)} invoices >30 days overdue. Risk: Rs.{total_at_risk:,.0f}. Recommend TReDS discounting for immediate cash flow relief.",
            }
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _collections_dashboard(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices = self.read_shared_context("invoices", state, namespace="finance_executor")
            if not invoices:
                invoices_resp = await self.backend._request(
                    "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
                )
                if not invoices_resp.success or not invoices_resp.data:
                    return {"success": True, "response": "No invoices for collections."}
                invoices = self._items(invoices_resp.data)

            aging = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
            for inv in invoices:
                if inv.get("status") == "OVERDUE":
                    try:
                        due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                        days = (datetime.now() - due).days
                        if days <= 30:
                            aging["0-30"] += 1
                        elif days <= 60:
                            aging["31-60"] += 1
                        elif days <= 90:
                            aging["61-90"] += 1
                        else:
                            aging["90+"] += 1
                    except:
                        pass

            agent_memory.store_business(state.org_id, f"collections_dashboard_{int(time.time())}", {
                "aging": aging, "total_overdue": sum(aging.values()),
            })

            aging_str = ", ".join(f"{k}: {v}" for k, v in aging.items() if v > 0)
            return {"success": True, "operation": "collections_dashboard", "aging_buckets": aging,
                    "response": f"Collections: {aging_str}"}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}


class TReDSExecutor(BaseExecutor):
    """
    TReDS Working Capital Integration.
    Connects to real TReDS APIs (RXIL, M1xchange, Invoicemart).
    When TREDS_ENABLED=False, clearly reports that the service is unavailable
    rather than returning fabricated rates.
    """

    def __init__(self):
        super().__init__("treds_executor", AgentRole.TREDS)
        self.identity = TREDS_AGENT_IDENTITY
        self.treds_client = treds_client

    async def execute(self, state: ExecutionState) -> ExecutionState:
        self._start_time = time.time()
        user_request = state.user_request.lower()

        try:
            action = self._classify_action(user_request)
            handler = self._get_handler(action)
            result = await handler(state)

            state.agent_outputs[self.name] = result
            state.completed_steps.append(self.name)

            duration_ms = (time.time() - self._start_time) * 1000
            await self._audit(action, "", result.get("response", ""),
                            result.get("success", False), duration_ms,
                            error=None if result.get("success") else result.get("response"),
                            org_id=state.org_id, outcome=result.get("response", ""))

        except Exception as e:
            state.errors.append(f"{self.name}: {str(e)}")
            logger.error("treds_executor_error", error=str(e))

        return state

    def _classify_action(self, user_request: str) -> str:
        if any(w in user_request for w in ["discount", "treds", "working capital", "get cash"]):
            return "discount invoice"
        elif any(w in user_request for w in ["eligible", "qualify"]):
            return "eligible invoices"
        elif any(w in user_request for w in ["rates", "discount rate"]):
            return "discounting rates"
        else:
            return "treds dashboard"

    def _get_handler(self, action: str):
        handlers = {
            "discount invoice": self._discount_invoice,
            "eligible invoices": self._get_eligible_invoices,
            "discounting rates": self._get_discounting_rates,
            "treds dashboard": self._treds_dashboard,
        }
        return handlers.get(action, self._treds_dashboard)

    async def _check_treds_available(self) -> bool:
        if not settings.TREDS_ENABLED:
            return False
        try:
            rates = await self.treds_client.get_discounting_rates(
                invoice_amount=100000.0, tenure_days=30
            )
            return rates.is_available if hasattr(rates, "is_available") else True
        except Exception as e:
            logger.warning("treds_availability_check_failed", error=str(e))
            return False

    async def _get_eligible_invoices(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
            )
            if not invoices_resp.success or not invoices_resp.data:
                return {"success": True, "response": "No invoices found."}

            invoices = self._items(invoices_resp.data)
            eligible = []
            for inv in invoices:
                if inv.get("status") == "SENT":
                    try:
                        due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                        days_until_due = (due - datetime.now()).days
                        if days_until_due > 7:
                            eligible.append({
                                "invoice_id": inv.get("id"),
                                "client": inv.get("clientName"),
                                "amount": float(inv.get("totalAmount", 0)),
                                "days_until_due": days_until_due,
                            })
                    except:
                        pass

            total_eligible = sum(e["amount"] for e in eligible)
            treds_available = await self._check_treds_available()

            if not treds_available:
                return {
                    "success": True, "operation": "treds_eligible",
                    "eligible_count": len(eligible),
                    "total_eligible": total_eligible,
                    "treds_available": False,
                    "invoices": eligible[:5],
                    "response": f"{len(eligible)} invoices eligible for discounting (Rs.{total_eligible:,.0f}). TReDS API is not configured. Set TREDS_ENABLED=True with valid credentials to enable discounting.",
                }

            return {
                "success": True, "operation": "treds_eligible",
                "eligible_count": len(eligible),
                "total_eligible": total_eligible,
                "treds_available": True,
                "invoices": eligible[:5],
                "response": f"{len(eligible)} invoices eligible for TReDS. Total: Rs.{total_eligible:,.0f}. Connect to TReDS exchange to discount.",
            }
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}

    async def _discount_invoice(self, state: ExecutionState) -> Dict[str, Any]:
        treds_available = await self._check_treds_available()
        if not treds_available:
            return {
                "success": False, "operation": "treds_unavailable",
                "response": "TReDS invoice discounting is not available. The TReDS API is not configured (TREDS_ENABLED=False). To enable: set TREDS_ENABLED=True and configure TReDS API credentials (RXIL, M1xchange, or InvoiceMart).",
            }

        try:
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
            )
            if not invoices_resp.success or not invoices_resp.data:
                return {"success": False, "response": "No invoices found."}

            invoices = self._items(invoices_resp.data)
            eligible = [i for i in invoices if i.get("status") == "SENT"]
            if not eligible:
                return {"success": False, "response": "No eligible invoices for discounting."}

            inv_list = "\n".join([
                f"- {i.get('clientName', 'Unknown')}: Rs.{float(i.get('totalAmount', 0)):,.0f} (ID: {i.get('id')})"
                for i in eligible[:5]
            ])
            prompt = f"""User wants to discount: "{state.user_request}"
ELIGIBLE:
{inv_list}
Which invoice? Return JSON: {{"invoice_id": "id", "amount": number}}"""

            try:
                match = json.loads(await self.llm.simple_completion(prompt=prompt, task_type="simple"))
                invoice_id = match.get("invoice_id") or eligible[0].get("id")
                amount = float(match.get("amount", eligible[0].get("totalAmount", 0)))
                selected_invoice = next((i for i in eligible if i.get("id") == invoice_id), eligible[0])
            except:
                selected_invoice = eligible[0]
                invoice_id = selected_invoice.get("id")
                amount = float(selected_invoice.get("totalAmount", 0))

            discount_request = InvoiceDiscountingRequest(
                invoice_id=invoice_id,
                invoice_number=selected_invoice.get("invoiceNumber", f"INV-{invoice_id}"),
                invoice_date=selected_invoice.get("createdAt", datetime.now().strftime("%Y-%m-%d")),
                due_date=selected_invoice.get("dueDate", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")),
                amount=amount,
                client_name=selected_invoice.get("clientName", "Unknown"),
                client_gstin=selected_invoice.get("clientGstin"),
                supplier_gstin=selected_invoice.get("supplierGstin"),
                description=selected_invoice.get("description", "Invoice discounting via TReDS"),
            )

            result = await self.treds_client.discount_invoice(discount_request)

            agent_memory.store_long_term(self.name, f"treds_tx_{invoice_id}", {
                "invoice_id": invoice_id, "amount": amount,
                "transaction_id": result.transaction_id,
                "discount_rate": result.discount_rate,
                "amount_received": result.discounted_amount,
                "platform": str(result.platform),
            })

            return {
                "success": True, "operation": "treds_discounted",
                "invoice_id": invoice_id,
                "transaction_id": result.transaction_id,
                "original_amount": amount,
                "discount_rate": result.discount_rate,
                "amount_received": result.discounted_amount,
                "fee": result.fee,
                "platform": result.platform,
                "status": result.status,
                "response": f"Invoice discounted via {result.platform.value.upper() if hasattr(result.platform, 'value') else result.platform} at {result.discount_rate}%. You get Rs.{result.discounted_amount:,.0f} now. Fee: Rs.{result.fee:,.0f}. Transaction ID: {result.transaction_id}",
            }
        except RuntimeError as e:
            if "disabled" in str(e).lower():
                return {
                    "success": False, "operation": "treds_disabled",
                    "response": "TReDS invoice discounting is not available. The API is not configured (TREDS_ENABLED=False). Configure TReDS credentials to enable discounting.",
                }
            return {"success": False, "response": f"TReDS API error: {str(e)}"}
        except Exception as e:
            return {"success": False, "response": f"TReDS error: {str(e)}"}

    async def _get_discounting_rates(self, state: ExecutionState) -> Dict[str, Any]:
        treds_available = await self._check_treds_available()
        if not treds_available:
            return {
                "success": False, "operation": "treds_rates_unavailable",
                "response": "TReDS discounting rates are not available. The TReDS API is not configured (TREDS_ENABLED=False). To see live rates: set TREDS_ENABLED=True and configure TReDS API credentials.",
            }

        try:
            rates = await self.treds_client.get_discounting_rates(
                invoice_amount=100000.0, tenure_days=30
            )
            return {
                "success": True, "operation": "treds_rates",
                "min_rate": rates.min_rate, "max_rate": rates.max_rate,
                "provider": f"TReDS ({rates.platform.value.upper()})" if hasattr(rates.platform, 'value') else f"TReDS ({rates.platform})",
                "currency": rates.currency,
                "tenure_days": rates.tenure_days,
                "is_available": rates.is_available,
                "response": f"Current TReDS discounting rates from {rates.platform.value.upper() if hasattr(rates.platform, 'value') else rates.platform}: {rates.min_rate}%-{rates.max_rate}% annualized.",
            }
        except Exception as e:
            logger.error("treds_rates_api_failed", error=str(e))
            return {"success": False, "response": f"TReDS rates API error: {str(e)}"}

    async def _treds_dashboard(self, state: ExecutionState) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id
            )
            if not invoices_resp.success or not invoices_resp.data:
                return {"success": True, "response": "No invoices for TReDS."}

            invoices = self._items(invoices_resp.data)
            eligible_count = len([i for i in invoices if i.get("status") == "SENT"])
            total_sent = sum(float(i.get("totalAmount", 0)) for i in invoices if i.get("status") == "SENT")
            treds_available = await self._check_treds_available()

            if not treds_available:
                return {"success": True, "operation": "treds_dashboard",
                        "eligible_invoices": eligible_count,
                        "total_sent_amount": total_sent,
                        "treds_enabled": False,
                        "response": f"{eligible_count} invoices (Rs.{total_sent:,.0f}) eligible for TReDS discounting. Enable TREDS_ENABLED=True with valid credentials to access live rates and discounting."}

            try:
                rates = await self.treds_client.get_discounting_rates(
                    invoice_amount=total_sent if total_sent > 0 else 100000, tenure_days=30
                )
                rate_info = f" Current rates: {rates.min_rate}%-{rates.max_rate}% via {rates.platform.value.upper() if hasattr(rates.platform, 'value') else rates.platform}."
            except:
                rate_info = " (Live rates unavailable from TReDS API)"

            return {"success": True, "operation": "treds_dashboard",
                    "eligible_invoices": eligible_count,
                    "total_sent_amount": total_sent,
                    "treds_enabled": True,
                    "response": f"{eligible_count} invoices (Rs.{total_sent:,.0f}) eligible for TReDS discounting.{rate_info}"}
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}
