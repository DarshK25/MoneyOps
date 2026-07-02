from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentResult:
    success: bool
    message: str


class EnhancedFinanceAgent:
    async def _generate_financial_summary(self, org_id, user_id=None):
        return f"summary for {org_id} / {user_id}"

    async def handle_balance_check(self, context):
        org_id = getattr(context, "org_uuid", None) or getattr(context, "org_id", None)
        user_id = getattr(context, "user_id", None)
        message = await self._generate_financial_summary(org_id, user_id=user_id)
        return AgentResult(success=True, message=message)