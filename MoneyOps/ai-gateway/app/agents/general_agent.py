from typing import List, Dict, Any, Optional

from app.agents.base_agent import BaseAgent, AgentResponse, ToolDefinition
from app.schemas.intents import AgentType, Intent


_GREETING_RESPONSE = (
    "Hello! I'm your MoneyOps financial assistant. "
    "I can help you create invoices, check balances, manage payments, "
    "and provide insights about your business finances. How can I help you today?"
)

_HELP_RESPONSE = (
    "I can help you with:\n"
    "- Creating and managing invoices\n"
    "- Checking account balances and cash flow\n"
    "- Recording payments and expenses\n"
    "- Compliance and GST calculations\n"
    "- Business growth insights and forecasts\n\n"
    "Just tell me what you need and I'll take care of it!"
)


class GeneralAgent(BaseAgent):
    def get_agent_type(self) -> AgentType:
        return AgentType.GENERAL_AGENT

    def get_supported_intents(self) -> List[Intent]:
        return [Intent.GREETING, Intent.HELP, Intent.GENERAL_QUERY]

    def get_tools(self) -> List[ToolDefinition]:
        return []

    async def process(self, intent: Intent, entities: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        if intent == Intent.GREETING:
            return self._build_success_response(_GREETING_RESPONSE)
        if intent == Intent.HELP:
            return self._build_success_response(_HELP_RESPONSE)
        result = self._rule_based_redirect(entities.get("query", ""))
        return self._build_success_response(result)

    def _rule_based_redirect(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["tax", "gst", "compliance", "deadline", "file"]):
            return "I can help with GST calculations and compliance tracking. Would you like me to check your compliance status or calculate GST on an invoice?"
        if any(w in q for w in ["invoice", "bill", "payment", "paid"]):
            return "I can help you create invoices, record payments, and track overdue amounts. What would you like to do?"
        if any(w in q for w in ["balance", "cash", "money", "account"]):
            return "I can check your account balance and cash position. Would you like a financial summary?"
        return (
            "I understand you're asking about something related to your business. "
            "I can help with invoicing, payments, compliance, and financial insights. "
            "Could you be more specific about what you need?"
        )


general_agent = GeneralAgent()
