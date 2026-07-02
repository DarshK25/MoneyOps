"""
BusinessContextProvider — gives agents real-time awareness of business health.
Every executor uses this to evaluate decisions against the current state of the business.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time

from app.adapters.backend_adapter import get_backend_adapter
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BusinessHealth:
    """Real-time snapshot of business health."""
    org_id: str
    revenue: float = 0.0
    expenses: float = 0.0
    profit: float = 0.0
    profit_margin: float = 0.0
    cash_balance: float = 0.0
    total_invoices: int = 0
    pending_invoices: int = 0
    overdue_invoices: int = 0
    overdue_amount: float = 0.0
    overdue_rate: float = 0.0
    collection_rate: float = 0.0
    growth_rate: float = 0.0
    compliance_health: str = "unknown"  # healthy, warning, critical
    compliance_issues: int = 0
    upcoming_deadlines: int = 0
    churn_risk_clients: int = 0
    tin: float = 0.0  # Total Income (Net) = revenue - expenses
    health_score: float = 0.0  # 0-100 composite score
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "org_id": self.org_id,
            "revenue": self.revenue,
            "expenses": self.expenses,
            "profit": self.profit,
            "profit_margin": self.profit_margin,
            "cash_balance": self.cash_balance,
            "total_invoices": self.total_invoices,
            "pending_invoices": self.pending_invoices,
            "overdue_invoices": self.overdue_invoices,
            "overdue_amount": self.overdue_amount,
            "overdue_rate": self.overdue_rate,
            "collection_rate": self.collection_rate,
            "growth_rate": self.growth_rate,
            "compliance_health": self.compliance_health,
            "compliance_issues": self.compliance_issues,
            "upcoming_deadlines": self.upcoming_deadlines,
            "churn_risk_clients": self.churn_risk_clients,
            "health_score": self.health_score,
            "risks": self.risks,
            "opportunities": self.opportunities,
        }


class BusinessContextProvider:
    """
    Provides real-time business health context for agent decision-making.
    Fetches live data from the backend, computes health scores, identifies risks.
    """

    def __init__(self):
        self.backend = get_backend_adapter()
        self._cache: Dict[str, BusinessHealth] = {}
        self._cache_ttl: float = 60.0  # 1 minute cache

    async def get_health(self, org_id: str) -> BusinessHealth:
        """Get current business health, with caching."""
        cached = self._cache.get(org_id)
        if cached and (time.time() - cached.timestamp) < self._cache_ttl:
            return cached

        health = await self._fetch_health(org_id)
        self._cache[org_id] = health
        return health

    async def _fetch_health(self, org_id: str) -> BusinessHealth:
        """Fetch and compute business health from live backend data."""
        health = BusinessHealth(org_id=org_id)

        try:
            # Fetch finance metrics
            metrics = await self.backend.get_finance_metrics("1", org_id, None)
            if metrics and metrics.success and metrics.data:
                m = metrics.data
                health.revenue = float(m.get("revenue", 0))
                health.expenses = float(m.get("expenses", 0))
                health.profit = float(m.get("netProfit", 0))
                health.profit_margin = (health.profit / max(health.revenue, 1)) * 100
                health.cash_balance = float(m.get("cashBalance", 0))
        except Exception as e:
            logger.warning("health_metrics_fetch_failed", org_id=org_id, error=str(e))

        try:
            # Fetch invoices for overdue analysis
            invoices_resp = await self.backend._request(
                "GET", "/api/invoices", org_id=org_id
            )
            if invoices_resp and invoices_resp.success and invoices_resp.data:
                from app.agents.base_executor import BaseExecutor
                invoices = BaseExecutor._items(invoices_resp.data)
                health.total_invoices = len(invoices)
                overdue = [i for i in invoices if i.get("status") == "OVERDUE"]
                pending = [i for i in invoices if i.get("status") in ("DRAFT", "SENT")]
                health.overdue_invoices = len(overdue)
                health.pending_invoices = len(pending)
                health.overdue_amount = sum(float(i.get("totalAmount", 0)) for i in overdue)
                health.overdue_rate = (health.overdue_invoices / max(health.total_invoices, 1)) * 100
                total_paid = sum(float(i.get("totalAmount", 0)) for i in invoices if i.get("status") == "PAID")
                total_billed = health.revenue + health.overdue_amount
                health.collection_rate = (total_paid / max(total_billed, 1)) * 100
        except Exception as e:
            logger.warning("health_invoices_fetch_failed", org_id=org_id, error=str(e))

        try:
            # Fetch compliance status
            compliance = await self.backend._request(
                "GET", "/api/compliance/status", org_id=org_id
            )
            if compliance and compliance.success and compliance.data:
                issues = compliance.data.get("issues", [])
                health.compliance_issues = len(issues)
                deadlines = compliance.data.get("upcomingDeadlines", [])
                health.upcoming_deadlines = len(deadlines) if isinstance(deadlines, list) else 0
                if health.compliance_issues > 3:
                    health.compliance_health = "critical"
                elif health.compliance_issues > 0:
                    health.compliance_health = "warning"
                else:
                    health.compliance_health = "healthy"
        except Exception as e:
            logger.warning("health_compliance_fetch_failed", org_id=org_id, error=str(e))

        # Compute health score (0-100)
        score = 50.0  # Start neutral

        # Profitability (up to 20 points)
        if health.profit_margin > 30:
            score += 20
        elif health.profit_margin > 15:
            score += 15
        elif health.profit_margin > 5:
            score += 10
        elif health.profit_margin > 0:
            score += 5
        else:
            score -= 10

        # Overdue rate (up to 20 points)
        if health.overdue_rate < 5:
            score += 20
        elif health.overdue_rate < 15:
            score += 15
        elif health.overdue_rate < 30:
            score += 5
        else:
            score -= 15

        # Collection rate (up to 20 points)
        if health.collection_rate > 90:
            score += 20
        elif health.collection_rate > 75:
            score += 15
        elif health.collection_rate > 50:
            score += 5
        else:
            score -= 10

        # Compliance health (up to 20 points)
        if health.compliance_health == "healthy":
            score += 20
        elif health.compliance_health == "warning":
            score += 5
        else:
            score -= 20

        # Cash balance (up to 20 points)
        if health.cash_balance > health.expenses * 3:
            score += 20
        elif health.cash_balance > health.expenses:
            score += 10
        elif health.cash_balance > 0:
            score += 5
        else:
            score -= 10

        health.health_score = max(0, min(100, score))

        # Identify risks
        if health.overdue_rate > 30:
            health.risks.append(f"CRITICAL: {health.overdue_rate:.0f}% of invoices are overdue")
        if health.compliance_health == "critical":
            health.risks.append(f"CRITICAL: {health.compliance_issues} compliance issues need immediate attention")
        if health.profit_margin < 0:
            health.risks.append(f"WARNING: Business is operating at a loss ({health.profit_margin:.1f}% margin)")
        if health.cash_balance <= 0:
            health.risks.append("CRITICAL: No cash balance - immediate liquidity crisis")
        if health.upcoming_deadlines > 5:
            health.risks.append(f"WARNING: {health.upcoming_deadlines} compliance deadlines approaching")

        # Identify opportunities
        if health.overdue_rate > 20:
            health.opportunities.append("High overdue rate — active collections can quickly improve cash flow")
        if health.profit_margin > 20:
            health.opportunities.append("Strong margins — consider reinvesting in growth or TReDS discounting")
        if health.cash_balance > health.expenses * 6:
            health.opportunities.append("Excess cash — consider TReDS to earn returns on surplus")
        if health.collection_rate < 70:
            health.opportunities.append("Low collection rate — automated reminders can improve cash flow")

        return health


# Singleton
business_context_provider = BusinessContextProvider()
