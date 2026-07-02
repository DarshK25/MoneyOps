from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import time
import json

from app.agentos.types import Decision, DecisionStatus
from app.agentos.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DecisionEngine:
    def __init__(self):
        self._decision_cache: Dict[str, Decision] = {}

    async def evaluate(self, agent_name: str, action: str,
                       context: Dict[str, Any],
                       org_id: str = "") -> Decision:
        decision = Decision(
            agent_name=agent_name,
            action=action,
            context=context,
            org_id=org_id,
        )

        try:
            from app.agents.business_context import business_context_provider
            health = await business_context_provider.get_health(org_id) if org_id else None
            if health:
                decision.business_health = health.to_dict()

            score, reasoning, risks, alternatives = self._score_action(
                action, decision.business_health
            )
            decision.score = score
            decision.reasoning = reasoning
            decision.risks = risks
            decision.alternatives = alternatives

            if score >= 70:
                decision.status = DecisionStatus.APPROVED
                decision.confidence = score / 100.0
            elif score >= 40:
                decision.status = DecisionStatus.ESCALATED
                decision.confidence = score / 100.0
            else:
                decision.status = DecisionStatus.BLOCKED
                decision.confidence = score / 100.0

            self._decision_cache[decision.decision_id] = decision
            agent_memory.store_decision(agent_name, decision.decision_id, decision.to_dict())

            logger.info("decision_evaluated",
                       agent=agent_name, action=action,
                       score=score, status=decision.status.value,
                       org_id=org_id)

        except Exception as e:
            logger.error("decision_evaluation_failed", agent=agent_name, action=action, error=str(e))
            decision.status = DecisionStatus.FAILED
            decision.reasoning = f"Evaluation error: {str(e)}"
            decision.score = 50.0

        return decision

    def _score_action(self, action: str,
                      business_health: Dict[str, Any]) -> Tuple[float, str, List[str], List[str]]:
        action_lower = action.lower()
        risks: List[str] = []
        alternatives: List[str] = []
        score = 75.0
        analysis_parts = []

        if not business_health:
            analysis_parts.append("No business health data available - using default score")
            return score, " | ".join(analysis_parts), risks, alternatives

        overdue_rate = float(business_health.get("overdue_rate", 0))
        profit_margin = float(business_health.get("profit_margin", 0))
        cash_balance = float(business_health.get("cash_balance", 0))
        expenses = float(business_health.get("expenses", 0))
        collection_rate = float(business_health.get("collection_rate", 0))
        compliance_health = str(business_health.get("compliance_health", "unknown"))
        health_score = float(business_health.get("health_score", 50))

        if any(w in action_lower for w in ["create invoice", "new invoice", "add invoice"]):
            if overdue_rate > 30:
                risks.append(f"Overdue rate is {overdue_rate:.0f}% — new invoices increase exposure")
                score -= 25
                alternatives.append("Send collection reminders to recover overdue amount first")
            elif overdue_rate > 15:
                risks.append(f"Overdue rate is {overdue_rate:.0f}% — consider including payment terms")
                score -= 10
            if collection_rate < 50:
                risks.append(f"Collection rate is only {collection_rate:.0f}% — new invoices may not be paid")
                score -= 15
                alternatives.append("Improve collection process before adding new receivables")
            if cash_balance < 0:
                risks.append("Negative cash balance — invoice will help but collections should be prioritized")
                score -= 5
            analysis_parts.append(f"Business has {business_health.get('overdue_invoices', 0)} overdue invoices worth Rs.{business_health.get('overdue_amount', 0):,.0f}")

        elif any(w in action_lower for w in ["send reminder", "chase", "collect"]):
            if overdue_rate > 30:
                score += 15
                analysis_parts.append("Collections will directly improve cash flow")
            if overdue_rate < 5:
                score -= 5
                risks.append("Overdue rate is low — reminders may damage client relationships")
                alternatives.append("Focus on growth or compliance instead")

        elif any(w in action_lower for w in ["discount", "treds"]):
            if cash_balance < expenses:
                score += 20
                analysis_parts.append("TReDS discounting will improve liquidity")
            elif cash_balance > expenses * 6:
                score -= 10
                risks.append("Sufficient cash reserves — discounting reduces margin unnecessarily")
                alternatives.append("Invest surplus cash in growth initiatives")
            if profit_margin < 5:
                score -= 10
                risks.append(f"Thin profit margin ({profit_margin:.1f}%) — discounting will reduce profitability")

        elif any(w in action_lower for w in ["gst", "tax", "file", "compliance"]):
            if compliance_health == "critical":
                score += 20
                analysis_parts.append(f"Critical — {business_health.get('compliance_issues', 0)} issues need resolution")
            if business_health.get("upcoming_deadlines", 0) > 3:
                score += 10
                analysis_parts.append(f"{business_health.get('upcoming_deadlines', 0)} deadlines approaching")

        elif any(w in action_lower for w in ["record expense", "add expense", "spent"]):
            if profit_margin < 0:
                score -= 20
                risks.append(f"Business is already at a loss ({profit_margin:.1f}% margin)")
                alternatives.append("Review existing expenses before adding new ones")
            if cash_balance < expenses:
                score -= 15
                risks.append("Cash reserves are insufficient to cover current expenses")

        elif any(w in action_lower for w in ["forecast", "growth", "upsell"]):
            if profit_margin > 15:
                score += 10
                analysis_parts.append("Strong margins make growth initiatives viable")
            if overdue_rate > 25:
                score -= 10
                risks.append("High overdue rate should be addressed before pursuing growth")
                alternatives.append("Focus on collections to stabilize cash flow first")

        score = max(0, min(100, score))
        if not analysis_parts:
            analysis_parts.append("No specific health conflicts detected for this action.")

        return score, " | ".join(analysis_parts), risks, alternatives

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        cached = self._decision_cache.get(decision_id)
        if cached:
            return cached.to_dict()
        stored = agent_memory.get_decision("", decision_id)
        return stored

    def get_agent_decisions(self, agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        decision_ids = agent_memory.list_decisions(agent_name)
        decisions = []
        for did in decision_ids[-limit:]:
            d = agent_memory.get_decision(agent_name, did)
            if d:
                decisions.append(d)
        return decisions


decision_engine = DecisionEngine()
