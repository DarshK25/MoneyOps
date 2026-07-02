"""
Agent Router - Routes voice intents to the agent system.
Voice Agent uses this as its bridge into the agent ecosystem.
All business logic lives in the agent system, not in the voice layer.
"""
from typing import Dict, Any, Optional, Set
import json

from app.agents.master_orchestrator import master_orchestrator
from app.agents.compliance_agent import compliance_agent
from app.agents.general_agent import general_agent
from app.schemas.intents import Intent, AgentType
from app.utils.logger import get_logger

logger = get_logger(__name__)

_COMPLIANCE_INTENTS: Set[Intent] = {
    Intent.GST_QUERY, Intent.COMPLIANCE_QUERY, Intent.COMPLIANCE_CHECK,
    Intent.COMPLIANCE_REPORT, Intent.TAX_OPTIMIZATION, Intent.TAX_CALCULATION,
    Intent.AUDIT_READINESS,
}

_CONVERSATIONAL_INTENTS: Set[Intent] = {
    Intent.GREETING, Intent.HELP, Intent.GENERAL_QUERY,
}


class AgentRouter:
    """
    Routes classified intents to the appropriate agent.
    Three paths:
      1. Compliance intents → ComplianceAgent (tool-based, backend calls)
      2. Conversational intents → GeneralAgent (rule/LLM-based)
      3. Business intents → MasterOrchestrator → domain executor
    """

    INTENT_TO_EXECUTOR = {
        Intent.INVOICE_CREATE: "finance_ops",
        Intent.INVOICE_QUERY: "finance_ops",
        Intent.INVOICE_STATUS_CHECK: "finance_ops",
        Intent.PAYMENT_RECORD: "finance_ops",
        Intent.BALANCE_CHECK: "finance_ops",
        Intent.TRANSACTION_EXPENSE: "finance_ops",
        Intent.CLIENT_CREATE: "finance_ops",
        Intent.CLIENT_QUERY: "finance_ops",
        Intent.REMINDER_CREATE: "collections",
        Intent.REMINDER_LIST: "collections",
        Intent.INVOICE_PAYMENT: "finance_ops",
        Intent.FORECAST_REQUEST: "growth",
        Intent.ANALYTICS_QUERY: "growth",
        Intent.CHURN_PREDICTION: "growth",
        Intent.CUSTOMER_SEGMENTATION: "growth",
        Intent.BUSINESS_HEALTH_CHECK: "ceo",
    }

    async def route(
        self,
        intent: Intent,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> "AgentResponse":
        ctx = context or {}
        org_id = ctx.get("org_id", "")
        user_id = ctx.get("user_id")
        session_id = ctx.get("session_id", "voice_default")

        agent_context = {
            "org_id": org_id,
            "user_id": user_id,
            "session_id": session_id,
            "business_id": ctx.get("business_id", "1"),
            "channel": "voice",
        }

        if intent in _COMPLIANCE_INTENTS:
            return await compliance_agent.process(intent, entities, agent_context)

        if intent in _CONVERSATIONAL_INTENTS:
            return await general_agent.process(intent, entities, agent_context)

        executor_type = self.INTENT_TO_EXECUTOR.get(intent, "finance_ops")
        user_message = self._build_message(intent, entities)

        result = await master_orchestrator.process(
            user_message=user_message,
            context=agent_context,
        )

        from app.agents.base_agent import AgentResponse
        return AgentResponse(
            success=result.get("success", False),
            message=result.get("message", "Completed"),
            data=result.get("data"),
            agent_type=AgentType.GENERAL_AGENT,
            tool_used=executor_type,
        )

    def _build_message(self, intent: Intent, entities: Dict[str, Any]) -> str:
        intent_to_phrase = {
            Intent.INVOICE_CREATE: f"create invoice for {entities.get('client_name', 'client')} for {entities.get('total', entities.get('amount', 0))}",
            Intent.INVOICE_QUERY: "show my invoices",
            Intent.INVOICE_STATUS_CHECK: "check invoice status",
            Intent.PAYMENT_RECORD: f"record payment for invoice {entities.get('invoice_id', '')}",
            Intent.BALANCE_CHECK: "what is my current balance",
            Intent.TRANSACTION_EXPENSE: f"record expense of {entities.get('amount', 0)} for {entities.get('description', 'expenses')}",
            Intent.CLIENT_CREATE: f"create client {entities.get('name', '')}",
            Intent.CLIENT_QUERY: "show my clients",
            Intent.GST_QUERY: f"calculate GST on {entities.get('amount', 0)}",
            Intent.COMPLIANCE_QUERY: "check compliance status",
            Intent.COMPLIANCE_CHECK: "check compliance status",
            Intent.TAX_CALCULATION: f"calculate tax on {entities.get('amount', 0)}",
            Intent.AUDIT_READINESS: "check audit readiness",
            Intent.REMINDER_CREATE: "send reminders to overdue clients",
            Intent.REMINDER_LIST: "show collections status",
            Intent.INVOICE_PAYMENT: f"process payment for invoice {entities.get('invoice_id', '')}",
            Intent.FORECAST_REQUEST: "forecast revenue",
            Intent.ANALYTICS_QUERY: "show growth dashboard",
            Intent.CHURN_PREDICTION: "check churn risk",
            Intent.CUSTOMER_SEGMENTATION: "segment my customers",
            Intent.BUSINESS_HEALTH_CHECK: "how is my business doing",
            Intent.HELP: "what can you do",
        }
        return intent_to_phrase.get(intent, f"process {intent.value}")


agent_router = AgentRouter()
