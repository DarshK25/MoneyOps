"""
Growth Agent - Evidence-based revenue intelligence.
Replaces spreadsheet-level logic with proper pattern detection, trend analysis,
customer segmentation, and outcome tracking.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import statistics

from app.agents.base_executor import BaseExecutor, AgentRole, CycleResult
from app.agentos.memory import agent_memory
from app.agentos.observation import audit_registry
from app.agentos.identity import GROWTH_AGENT_IDENTITY
from app.llm.multi_provider import llm_client
from app.adapters.backend_adapter import get_backend_adapter
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _items(data):
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return data["data"]
        if isinstance(data.get("data"), dict):
            return _items(data["data"])
        if isinstance(data.get("content"), list):
            return data["content"]
        for key in ("clients", "invoices", "transactions", "items", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


class GrowthExecutor(BaseExecutor):
    """
    Growth Agent: Evidence-based revenue intelligence.
    - Revenue trend analysis with confidence intervals
    - Customer segmentation by spending patterns
    - Upsell opportunity scoring with evidence
    - Churn risk detection with behavioral indicators
    - TReDS optimization recommendations
    """

    def __init__(self):
        super().__init__("growth_executor", AgentRole.GROWTH)
        self.identity = GROWTH_AGENT_IDENTITY
        self.backend = get_backend_adapter()
        self.llm = llm_client

    async def execute(self, state) -> "ExecutionState":
        user_request = state.user_request.lower()
        self._start_time = 0.0

        try:
            if any(w in user_request for w in ["forecast", "predict", "revenue projection"]):
                result = await self._forecast_revenue(state)
            elif any(w in user_request for w in ["upsell", "cross-sell", "expand"]):
                result = await self._identify_upsell(state)
            elif any(w in user_request for w in ["churn", "retention", "at risk"]):
                result = await self._churn_risk(state)
            elif any(w in user_request for w in ["optimize", "treds strategy", "best rate"]):
                result = await self._optimize_treds(state)
            elif any(w in user_request for w in ["dashboard", "overview", "summary", "growth"]):
                result = await self._growth_dashboard(state)
            else:
                result = await self._fallback_response(user_request)

            state.agent_outputs[self.name] = result
            state.completed_steps.append(self.name)
        except Exception as e:
            state.errors.append(f"{self.name}: {str(e)}")
            logger.error("growth_executor_error", error=str(e))

        return state

    async def run_autonomous_cycle(self, org_id: str, user_id: Optional[str] = None) -> CycleResult:
        try:
            opportunities = await self._find_growth_opportunities(org_id, user_id)
            forecast = await self._calculate_forecast(org_id, user_id)

            actions = []
            alerts = []

            if opportunities.get("treds_optimization"):
                savings = opportunities["treds_optimization"].get("potential_savings", 0)
                if savings > 0:
                    actions.append(f"TReDS optimization: Potential savings Rs.{savings:,.0f}")

            if opportunities.get("upsell_targets"):
                for target in opportunities["upsell_targets"][:3]:
                    actions.append(f"Upsell: {target.get('client')} - potential Rs.{target.get('potential_uplift', 0):,.0f}")

            if forecast.get("cash_flow_risk"):
                alerts.append({"type": "cash_flow_risk", "severity": "high", "message": forecast["cash_flow_risk"]})

            result = CycleResult(
                agent=self.name,
                org_id=org_id,
                success=True,
                summary=f"Found {len(opportunities.get('upsell_targets', []))} upsell opportunities, "
                       f"TReDS savings: Rs.{opportunities.get('treds_optimization', {}).get('potential_savings', 0):,.0f}",
                actions_taken=actions,
                alerts=alerts,
                metrics={
                    "upsell_count": len(opportunities.get("upsell_targets", [])),
                    "forecast_revenue": forecast.get("next_month_revenue", 0),
                    "forecast_confidence": forecast.get("confidence", 0),
                    "treds_potential": opportunities.get("treds_optimization", {}).get("potential_savings", 0),
                }
            )

            await audit_registry.record(
                agent_name=self.name,
                action="autonomous_cycle",
                reasoning=f"Growth analysis for {org_id}",
                success=True,
                org_id=org_id,
                actual_outcome=result.summary,
            )

            return result
        except Exception as e:
            logger.error("growth_cycle_error", error=str(e), org_id=org_id)
            return CycleResult(agent=self.name, org_id=org_id, success=False, summary="Growth cycle failed", error=str(e))

    async def _forecast_revenue(self, state) -> Dict[str, Any]:
        try:
            invoices = self.read_shared_context("invoices", state, namespace="finance_executor")
            if not invoices:
                invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id)
                invoices = _items(invoices_resp.data) if invoices_resp.success else []

            if not invoices:
                return {"success": True, "response": "Insufficient data for forecasting."}

            monthly_revenue = {}
            for inv in invoices:
                if inv.get("createdAt"):
                    try:
                        month = inv["createdAt"][:7]
                        amount = float(inv.get("totalAmount", 0))
                        monthly_revenue[month] = monthly_revenue.get(month, 0) + amount
                    except:
                        pass

            sorted_months = sorted(monthly_revenue.keys())
            if len(sorted_months) < 2:
                return {"success": True, "response": "Need at least 2 months of data for forecasting."}

            monthly_values = [monthly_revenue[m] for m in sorted_months]

            recent_3 = monthly_values[-3:] if len(monthly_values) >= 3 else monthly_values
            avg = statistics.mean(recent_3) if len(recent_3) > 1 else recent_3[0]

            growth_rates = []
            for i in range(1, len(monthly_values)):
                prev = monthly_values[i-1]
                if prev > 0:
                    growth_rates.append((monthly_values[i] - prev) / prev)

            avg_growth = statistics.mean(growth_rates) if growth_rates else 0.1
            growth_volatility = statistics.stdev(growth_rates) if len(growth_rates) > 1 else 0.1

            next_month_point = monthly_values[-1] * (1 + avg_growth)
            next_month_lower = next_month_point * (1 - growth_volatility)
            next_month_upper = next_month_point * (1 + growth_volatility)

            confidence = max(0, min(100, 80 - (growth_volatility * 100)))
            trend = "upward" if avg_growth > 0.02 else "downward" if avg_growth < -0.02 else "stable"

            result = {
                "success": True,
                "operation": "revenue_forecast",
                "monthly_revenue": monthly_revenue,
                "sorted_months": sorted_months,
                "next_month_forecast": next_month_point,
                "forecast_lower_bound": next_month_lower,
                "forecast_upper_bound": next_month_upper,
                "avg_growth_rate": avg_growth * 100,
                "growth_volatility": growth_volatility * 100,
                "confidence": confidence,
                "trend": trend,
                "total_data_points": len(sorted_months),
                "response": f"Next month forecast: Rs.{next_month_point:,.0f} "
                           f"(range: Rs.{next_month_lower:,.0f} - Rs.{next_month_upper:,.0f}). "
                           f"Trend: {trend}. Confidence: {confidence:.0f}%. "
                           f"Average growth: {avg_growth*100:.1f}%",
            }

            self.share_context_with("forecast", result, state)
            agent_memory.store_business(state.org_id, f"forecast_{datetime.now().strftime('%Y%m')}", result)
            return result

        except Exception as e:
            return {"success": False, "response": f"Forecast error: {str(e)}"}

    async def _identify_upsell(self, state) -> Dict[str, Any]:
        try:
            clients = await self.backend.get_clients(state.org_id, user_id=state.user_id) or []
            invoices = self.read_shared_context("invoices", state, namespace="finance_executor")
            if not invoices:
                invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id)
                invoices = _items(invoices_resp.data) if invoices_resp.success else []

            client_revenue = {}
            client_invoice_count = {}
            client_recency = {}

            for inv in invoices:
                client = inv.get("clientName", "Unknown")
                amount = float(inv.get("totalAmount", 0))
                client_revenue[client] = client_revenue.get(client, 0) + amount
                client_invoice_count[client] = client_invoice_count.get(client, 0) + 1
                inv_date = inv.get("createdAt", "")
                if inv_date > client_recency.get(client, ""):
                    client_recency[client] = inv_date

            all_revenues = list(client_revenue.values()) if client_revenue else [0]
            median_revenue = statistics.median(all_revenues) if len(all_revenues) > 1 else all_revenues[0] if all_revenues else 0
            std_revenue = statistics.stdev(all_revenues) if len(all_revenues) > 1 else median_revenue * 0.3

            upsell_targets = []
            for client in clients:
                name = client.get("name", "Unknown")
                revenue = client_revenue.get(name, 0)
                invoice_count = client_invoice_count.get(name, 0)

                if revenue <= 0:
                    continue

                revenue_z_score = (revenue - median_revenue) / max(std_revenue, 1)

                if revenue_z_score > 1.5:
                    tier = "premium"
                    opportunity_desc = "Premium tier upgrade with priority support"
                    uplift_rate = 0.25
                elif revenue_z_score > 0.5:
                    tier = "growth"
                    opportunity_desc = "Growth tier - additional services bundle"
                    uplift_rate = 0.20
                elif invoice_count >= 5:
                    tier = "engaged"
                    opportunity_desc = "Volume discount plan with committed usage"
                    uplift_rate = 0.15
                else:
                    tier = "standard"
                    opportunity_desc = "Standard tier - increase service adoption"
                    uplift_rate = 0.10

                potential_uplift = revenue * uplift_rate
                confidence = min(90, 50 + (revenue_z_score * 10)) if revenue_z_score > 0 else 40

                upsell_targets.append({
                    "client": name,
                    "current_revenue": revenue,
                    "invoice_count": invoice_count,
                    "tier": tier,
                    "opportunity": opportunity_desc,
                    "potential_uplift": potential_uplift,
                    "confidence": confidence,
                    "evidence": f"Revenue Rs.{revenue:,.0f} across {invoice_count} invoices",
                })

            upsell_targets.sort(key=lambda x: x["potential_uplift"], reverse=True)
            total_potential = sum(t["potential_uplift"] for t in upsell_targets)

            result = {
                "success": True,
                "operation": "upsell_identified",
                "targets": upsell_targets[:10],
                "total_potential": total_potential,
                "total_targets": len(upsell_targets),
                "segments": {
                    "premium": len([t for t in upsell_targets if t["tier"] == "premium"]),
                    "growth": len([t for t in upsell_targets if t["tier"] == "growth"]),
                    "engaged": len([t for t in upsell_targets if t["tier"] == "engaged"]),
                    "standard": len([t for t in upsell_targets if t["tier"] == "standard"]),
                },
                "response": f"Found {len(upsell_targets)} upsell opportunities across "
                           f"{len([t for t in upsell_targets if t['tier'] in ('premium', 'growth')])} high-value clients. "
                           f"Total potential uplift: Rs.{total_potential:,.0f}",
            }

            agent_memory.store_business(state.org_id, f"upsell_{datetime.now().strftime('%Y%m%d')}", result)
            return result

        except Exception as e:
            return {"success": False, "response": f"Upsell analysis error: {str(e)}"}

    async def _churn_risk(self, state) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id)
            invoices = _items(invoices_resp.data) if invoices_resp.success else []

            client_last_invoice = {}
            client_invoice_count = {}
            client_total_revenue = {}

            for inv in invoices:
                client = inv.get("clientName", "Unknown")
                date = inv.get("createdAt", "")
                amount = float(inv.get("totalAmount", 0))
                if date > client_last_invoice.get(client, ""):
                    client_last_invoice[client] = date
                client_invoice_count[client] = client_invoice_count.get(client, 0) + 1
                client_total_revenue[client] = client_total_revenue.get(client, 0) + amount

            at_risk = []
            now = datetime.now()
            for client, last_date in client_last_invoice.items():
                try:
                    parsed = datetime.fromisoformat(last_date.replace("Z", "+00:00").replace("+00:00", "") if last_date else "2000-01-01")
                    days_inactive = (now - parsed).days
                except:
                    days_inactive = 365

                invoice_count = client_invoice_count.get(client, 0)
                total_revenue = client_total_revenue.get(client, 0)

                if days_inactive > 90:
                    if days_inactive > 180:
                        risk_level = "critical"
                        risk_score = 90
                    elif days_inactive > 120:
                        risk_level = "high"
                        risk_score = 75
                    else:
                        risk_level = "medium"
                        risk_score = 60

                    churn_impact = total_revenue * (risk_score / 100)

                    at_risk.append({
                        "client": client,
                        "last_invoice": last_date,
                        "days_inactive": days_inactive,
                        "invoice_count": invoice_count,
                        "total_revenue": total_revenue,
                        "risk_level": risk_level,
                        "risk_score": risk_score,
                        "estimated_churn_impact": churn_impact,
                    })

            at_risk.sort(key=lambda x: x["estimated_churn_impact"], reverse=True)
            total_churn_impact = sum(c["estimated_churn_impact"] for c in at_risk)

            result = {
                "success": True,
                "operation": "churn_risk",
                "at_risk_clients": at_risk[:10],
                "total_at_risk": len(at_risk),
                "total_churn_impact": total_churn_impact,
                "risk_distribution": {
                    "critical": len([c for c in at_risk if c["risk_level"] == "critical"]),
                    "high": len([c for c in at_risk if c["risk_level"] == "high"]),
                    "medium": len([c for c in at_risk if c["risk_level"] == "medium"]),
                },
                "response": f"{len(at_risk)} clients at churn risk. "
                           f"Critical: {len([c for c in at_risk if c['risk_level'] == 'critical'])}, "
                           f"High: {len([c for c in at_risk if c['risk_level'] == 'high'])}. "
                           f"Potential revenue impact: Rs.{total_churn_impact:,.0f}",
            }

            agent_memory.store_business(state.org_id, f"churn_{datetime.now().strftime('%Y%m%d')}", result)
            return result

        except Exception as e:
            return {"success": False, "response": f"Churn analysis error: {str(e)}"}

    async def _fetch_discount_rate(self) -> float:
        try:
            resp = await self.backend._request("GET", "/api/treds/rates")
            if resp.success and resp.data:
                rate = float(resp.data.get("discount_rate_pct", 0))
                if rate > 0:
                    return rate
        except Exception:
            logger.warning("treds_rates_unavailable_using_fallback")
        return max(2.0, 6.5 * 1.5)

    async def _optimize_treds(self, state) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=state.org_id, user_id=state.user_id)
            invoices = _items(invoices_resp.data) if invoices_resp.success else []

            eligible = []
            for inv in invoices:
                if inv.get("status") == "SENT":
                    try:
                        due = datetime.strptime(inv.get("dueDate", ""), "%Y-%m-%d")
                        days_until_due = (due - datetime.now()).days
                        if 7 < days_until_due < 60:
                            eligible.append({
                                "invoice_id": inv.get("id"),
                                "client": inv.get("clientName"),
                                "amount": float(inv.get("totalAmount", 0)),
                                "days_until_due": days_until_due,
                                "urgency": "high" if days_until_due < 15 else "medium" if days_until_due < 30 else "low",
                            })
                    except:
                        pass

            total_eligible = sum(e["amount"] for e in eligible)
            discount_rate = await self._fetch_discount_rate()
            optimal_discount = total_eligible * (discount_rate / 100)

            result = {
                "success": True,
                "operation": "treds_optimization",
                "eligible_invoices": eligible[:10],
                "total_eligible": total_eligible,
                "optimal_discount_rate": discount_rate,
                "estimated_cost": optimal_discount,
                "urgency_breakdown": {
                    "high": len([e for e in eligible if e["urgency"] == "high"]),
                    "medium": len([e for e in eligible if e["urgency"] == "medium"]),
                    "low": len([e for e in eligible if e["urgency"] == "low"]),
                },
                "response": f"{len(eligible)} invoices optimal for TReDS. "
                           f"Urgent: {len([e for e in eligible if e['urgency'] == 'high'])}, "
                           f"Total: Rs.{total_eligible:,.0f}. Est. cost: Rs.{optimal_discount:,.0f} at {discount_rate}%",
            }

            agent_memory.store_business(state.org_id, f"treds_opt_{datetime.now().strftime('%Y%m%d')}", result)
            return result

        except Exception as e:
            return {"success": False, "response": f"TReDS optimization error: {str(e)}"}

    async def _growth_dashboard(self, state) -> Dict[str, Any]:
        try:
            forecast = await self._forecast_revenue(state)
            upsell = await self._identify_upsell(state)
            churn = await self._churn_risk(state)

            data_quality = "Based on available data, " if forecast.get("confidence", 100) < 70 or not upsell.get("total_targets") else ""
            result = {
                "success": True,
                "operation": "growth_dashboard",
                "forecast": forecast,
                "upsell": upsell,
                "churn_risk": churn,
                "response": f"{data_quality}forecast: Rs.{forecast.get('next_month_forecast', 0):,.0f} "
                           f"(confidence: {forecast.get('confidence', 0):.0f}%), "
                           f"{upsell.get('total_targets', 0)} upsell targets (Rs.{upsell.get('total_potential', 0):,.0f}), "
                           f"{churn.get('total_at_risk', 0)} churn risks (Rs.{churn.get('total_churn_impact', 0):,.0f})",
            }
            return result

        except Exception as e:
            return {"success": False, "response": f"Growth dashboard error: {str(e)}"}

    async def _find_growth_opportunities(self, org_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=org_id, user_id=user_id)
            invoices = _items(invoices_resp.data) if invoices_resp.success else []

            client_revenue = {}
            for inv in invoices:
                client = inv.get("clientName", "Unknown")
                client_revenue[client] = client_revenue.get(client, 0) + float(inv.get("totalAmount", 0))

            all_rev = list(client_revenue.values()) if client_revenue else [0]
            median_rev = statistics.median(all_rev) if len(all_rev) > 1 else all_rev[0] if all_rev else 0
            std_rev = statistics.stdev(all_rev) if len(all_rev) > 1 else median_rev * 0.3

            upsell_targets = []
            for client, revenue in client_revenue.items():
                if revenue > max(median_rev + std_rev, 50000):
                    upsell_targets.append({
                        "client": client,
                        "revenue": revenue,
                        "potential_uplift": revenue * 0.20,
                        "opportunity": "Premium tier",
                    })

            eligible_treds = [i for i in invoices if i.get("status") == "SENT"]
            treds_savings = sum(float(i.get("totalAmount", 0)) for i in eligible_treds) * 0.03

            return {
                "upsell_targets": upsell_targets,
                "treds_optimization": {"potential_savings": treds_savings},
            }
        except Exception as e:
            logger.error("find_opportunities_error", error=str(e))
            return {"upsell_targets": [], "treds_optimization": {"potential_savings": 0}}

    async def _calculate_forecast(self, org_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            invoices_resp = await self.backend._request("GET", "/api/invoices", org_id=org_id, user_id=user_id)
            invoices = _items(invoices_resp.data) if invoices_resp.success else []

            monthly = {}
            for inv in invoices:
                if inv.get("createdAt"):
                    month = inv["createdAt"][:7]
                    monthly[month] = monthly.get(month, 0) + float(inv.get("totalAmount", 0))

            sorted_months = sorted(monthly.keys())
            if len(sorted_months) >= 2:
                recent = [monthly[m] for m in sorted_months[-3:]]
                avg_revenue = sum(recent) / len(recent)
                growth_rates = []
                for i in range(1, len(sorted_months)):
                    prev = monthly[sorted_months[i-1]]
                    if prev > 0:
                        growth_rates.append((monthly[sorted_months[i]] - prev) / prev)
                avg_growth = statistics.mean(growth_rates) if growth_rates else 0.05
                forecast_next = recent[-1] * (1 + avg_growth)

                cash_risk = None
                if avg_growth < -0.1:
                    cash_risk = f"Revenue declining {abs(avg_growth)*100:.0f}% month-over-month"

                return {"next_month_revenue": forecast_next, "confidence": 60 + len(sorted_months) * 5, "cash_flow_risk": cash_risk}

            return {"next_month_revenue": 0, "confidence": 0, "cash_flow_risk": "Insufficient data for forecast"}
        except Exception as e:
            logger.error("forecast_error", error=str(e))
            return {"next_month_revenue": 0, "confidence": 0, "cash_flow_risk": str(e)}


growth_executor = GrowthExecutor()
