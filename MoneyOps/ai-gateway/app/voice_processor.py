import uuid
import re
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from app.orchestration.intent_classifier import intent_classifier
from app.orchestration.entity_extractor import entity_extractor
from app.agents.finance_agent import finance_agent
from app.state.session_manager import session_manager
from app.schemas.intents import Intent
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class VoiceContext:
    session_id: str
    user_id: str
    org_uuid: str
    business_id: Optional[int] = 1
    clerk_org_id: Optional[str] = None
    extracted_entities: List[Dict[str, Any]] = field(default_factory=list)


class VoiceProcessor:
    def __init__(self):
        self.intent_classifier = intent_classifier
        self.entity_extractor = entity_extractor
        self.finance_agent = finance_agent
        self.state_manager = session_manager
        from app.adapters.backend_adapter import get_backend_adapter
        self.backend = get_backend_adapter()

    # ─────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────
    async def process(self, text: str, context: VoiceContext) -> dict:
        session = self.state_manager.get_session(
            context.session_id, context.user_id, context.org_uuid
        )

        # ── 1. IDENTITY RESOLUTION ──────────────────────────────────────────
        if context.org_uuid.startswith("org_") and (
            not session.org_id or session.org_id.startswith("org_")
        ):
            logger.info({"user": context.user_id, "event": "resolving_identity_per_session"})
            onboarding_resp = await self.backend.get_onboarding_status(context.user_id)
            if onboarding_resp and onboarding_resp.success and onboarding_resp.data:
                data = onboarding_resp.data
                resolved_uuid = (
                    data.get("orgId")
                    or data.get("orgUuid")
                    or data.get("organizationId")
                )
                if resolved_uuid:
                    context.org_uuid = resolved_uuid
                    session.org_id = resolved_uuid
                    session.business_id = data.get("businessId") or 1
                    self.state_manager.save_session(session)

        # ── 2. SESSION RESTORE ──────────────────────────────────────────────
        if session.org_id and not session.org_id.startswith("org_"):
            context.org_uuid = session.org_id
            context.business_id = session.business_id

        logger.info({
            "session_id": context.session_id,
            "resolved_org_uuid": context.org_uuid,
            "business_id": context.business_id,
            "event": "identity_persistence_check"
        })

        # ── 3. MARKET MONITOR (background, idempotent) ─────────────────────
        if context.org_uuid and not context.org_uuid.startswith("org_"):
            from app.agents.market_agent import market_agent_instance
            market_agent_instance.start_market_monitor(
                org_uuid=context.org_uuid,
                business_id=context.business_id or 1,
                industry="professional services"
            )

        # ── 4. INTENT LOCK — INVOICE_CREATE ────────────────────────────────
        if session.locked_intent == "INVOICE_CREATE" and session.invoice_draft is not None:
            cancel_words = {"cancel", "stop", "never mind", "forget it", "abort"}
            if any(w in text.lower() for w in cancel_words):
                session.locked_intent = None
                session.invoice_draft = None
                self.state_manager.save_session(session)
                return {"response_text": "Invoice cancelled.", "success": True, "intent": "CANCELLATION"}

            # Classify once for use in this block
            classification = await self.intent_classifier.classify(
                text, conversation_history=session.history
            )
            intent_val = (
                classification.intent.value
                if hasattr(classification.intent, "value")
                else str(classification.intent)
            )
            entities_result = await self.entity_extractor.extract(
                text, classification.intent, context
            )
            entities_list = getattr(entities_result, "entities", [])
            context.extracted_entities = [
                {"type": e.entity_type.value.lower(), "value": e.value}
                for e in entities_list
            ]

            draft = session.invoice_draft
            confirm_words = {
                "yes", "yeah", "yep", "sure", "ok", "okay", "correct",
                "proceed", "go ahead", "create it", "create",
            }
            if any(w in text.lower().strip() for w in confirm_words):
                if draft.gst_percent is None:
                    draft.gst_percent = 18.0
                    session.invoice_draft = draft
                    self.state_manager.save_session(session)
                elif draft.service_description and not draft.confirmed:
                    draft.confirmed = True
                    session.invoice_draft = draft
                    self.state_manager.save_session(session)

            if (
                draft.client_id
                and draft.amount is not None
                and draft.due_date
                and draft.gst_percent is not None
                and not draft.service_description
                and not any(w in text.lower().strip() for w in confirm_words)
            ):
                description = text.strip()
                filler_patterns = [
                    r"^this (one |invoice |bill )?is for\s*",
                    r"^it['s| is] for\s*",
                    r"^the service is\s*",
                    r"^the description is\s*",
                    r"^for\s+",
                    r"^invoice for\s*",
                    r"^the (description|service description) is\s*",
                ]
                for pattern in filler_patterns:
                    description = re.sub(pattern, "", description, flags=re.IGNORECASE).strip()
                draft.service_description = description.capitalize()
                session.invoice_draft = draft
                self.state_manager.save_session(session)
                context.extracted_entities = []

            result = await self.finance_agent.handle_invoice_create(context)
            if result.success:
                self.state_manager.add_turn(context.session_id, "user", text, "INVOICE_CREATE")
                self.state_manager.add_turn(context.session_id, "assistant", result.message, "INVOICE_CREATE")
            return {
                "response_text": result.message,
                "success": result.success,
                "intent": "INVOICE_CREATE",
                "ui_event": getattr(result, "ui_event", None),
            }

        # ── 5. INTENT LOCK — CLIENT_CREATE ─────────────────────────────────
        if session.locked_intent == "CLIENT_CREATE" and session.client_draft is not None:
            cancel_words = {"cancel", "stop", "never mind", "forget it", "abort"}
            if any(w in text.lower() for w in cancel_words):
                session.locked_intent = None
                session.client_draft = None
                self.state_manager.save_session(session)
                return {
                    "response_text": "Client creation cancelled.",
                    "success": True,
                    "intent": "CANCELLATION",
                }

            # Merge any new entities into draft
            entities_result = await self.entity_extractor.extract(
                text, Intent.CLIENT_CREATE, context
            )
            entities_list = getattr(entities_result, "entities", [])
            new_entities = {
                e.entity_type.value.lower(): e.value
                for e in entities_list
            }
            for k, v in new_entities.items():
                if v and k not in session.client_draft:
                    session.client_draft[k] = v
            self.state_manager.save_session(session)
            context.extracted_entities = [
                {"type": k, "value": v} for k, v in session.client_draft.items()
            ]

            result = await self._handle_client_create(text, context)
            if result.success:
                session_after = self.state_manager.get_session(context.session_id)
                if not getattr(session_after, "dialog_pending", False):
                    session_after.locked_intent = None
                    session_after.client_draft = None
                    self.state_manager.save_session(session_after)
                self.state_manager.add_turn(context.session_id, "user", text, "CLIENT_CREATE")
                self.state_manager.add_turn(context.session_id, "assistant", result.message, "CLIENT_CREATE")
            return {
                "response_text": result.message,
                "success": result.success,
                "intent": "CLIENT_CREATE",
                "ui_event": getattr(result, "ui_event", None),
            }

        # ── 6. NORMAL PATH — classify ONCE ─────────────────────────────────
        classification = await self.intent_classifier.classify(
            text,
            conversation_history=session.history,
            business_context={
                "business_id": context.business_id,
                "org_uuid": context.org_uuid,
            },
        )
        intent = (
            classification.intent.value
            if hasattr(classification.intent, "value")
            else str(classification.intent)
        )

        # Extract entities ONCE
        entities_result = await self.entity_extractor.extract(
            text, classification.intent, context
        )
        entities_list = getattr(entities_result, "entities", [])
        new_entities = {
            e.entity_type.value.lower(): e.value
            for e in entities_list
        }

        if intent == "CLIENT_CREATE":
            if session.client_draft is None:
                session.client_draft = {}
            for k, v in new_entities.items():
                if v:
                    session.client_draft[k] = v
            self.state_manager.save_session(session)
            context.extracted_entities = [
                {"type": k, "value": v} for k, v in session.client_draft.items()
            ]
        else:
            context.extracted_entities = [
                {"type": k, "value": v} for k, v in new_entities.items()
            ]

        # ── 7. ROUTE ────────────────────────────────────────────────────────
        MARKET_INTENTS = {
            "GROWTH_STRATEGY", "MARKET_EXPANSION", "SCALING_ADVICE",
            "COMPETITIVE_POSITIONING", "PARTNERSHIP_OPPORTUNITIES",
            "PRODUCT_STRATEGY", "RISK_ASSESSMENT", "SALES_STRATEGY",
            "CUSTOMER_ACQUISITION", "PRICING_STRATEGY", "PROBLEM_DIAGNOSIS",
            "SWOT_ANALYSIS", "TREND_ANALYSIS", "BENCHMARK_COMPARISON",
            "BUSINESS_HEALTH_CHECK", "FORECAST_REQUEST", "ANALYTICS_QUERY",
            "BUDGET_OPTIMIZATION", "CASH_FLOW_PLANNING", "PROFIT_OPTIMIZATION",
            "CUSTOMER_RETENTION",
        }
        MARKET_KEYWORDS = {
            "market", "sector", "industry", "economy", "world", "global",
            "india", "growth", "competitor", "business", "trend", "situation",
            "geopolitical", "policy", "rate", "inflation", "tariff",
            "opportunities", "intelligence", "revenue", "profit", "performance",
            "expenses", "how are we doing", "how is business",
        }

        if intent == "INVOICE_CREATE":
            session.locked_intent = "INVOICE_CREATE"
            session.dialog_pending = False
            self.state_manager.save_session(session)
            result = await self.finance_agent.handle_invoice_create(context)

        elif intent == "CLIENT_CREATE":
            session.locked_intent = "CLIENT_CREATE"
            session.dialog_pending = False
            self.state_manager.save_session(session)
            result = await self._handle_client_create(text, context)
            if result.success:
                session_after = self.state_manager.get_session(context.session_id)
                if not getattr(session_after, "dialog_pending", False):
                    session_after.locked_intent = None
                    session_after.client_draft = None
                    self.state_manager.save_session(session_after)

        elif intent == "CLIENT_QUERY":
            result = await self._handle_client_query(context)

        elif intent == "INVOICE_QUERY":
            result = await self._handle_invoice_query(context, text)

        elif intent == "INVOICE_STATUS_CHECK":
            result = await self._handle_invoice_query(context, text)

        elif intent == "PAYMENT_RECORD":
            result = await self._handle_payment_record(context, text, new_entities)

        elif intent == "BALANCE_CHECK":
            result = await self._handle_balance_check(context)

        elif intent in MARKET_INTENTS or (
            intent == "GENERAL_QUERY"
            and any(w in text.lower() for w in MARKET_KEYWORDS)
        ):
            from app.agents.market_agent import market_agent_instance
            result = await market_agent_instance.handle_market_query(
                text, context, conversation_history=session.history
            )

        else:
            from app.orchestration.agent_router import agent_router
            result = await agent_router.route(
                classification.intent,
                {e["type"]: e["value"] for e in context.extracted_entities},
                vars(context) if not isinstance(context, dict) else context,
            )

        if result.success:
            self.state_manager.add_turn(context.session_id, "user", text, intent)
            self.state_manager.add_turn(context.session_id, "assistant", result.message, intent)

        return {
            "response_text": result.message,
            "success": result.success,
            "intent": intent,
            "ui_event": getattr(result, "ui_event", None),
        }

    # ─────────────────────────────────────────────
    # CLIENT QUERY
    # ─────────────────────────────────────────────
    async def _handle_client_query(self, context: VoiceContext):
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        try:
            resp = await self.backend._request(
                "GET", "/api/clients",
                org_id=context.org_uuid,
                user_id=context.user_id,
                params={"limit": 100},
            )

            logger.info({
                "event": "client_query_backend_response",
                "org": context.org_uuid,
                "success": resp.success if resp else None,
                "raw_data_type": type(resp.data).__name__ if resp else "None",
                "raw_data_preview": str(resp.data)[:200] if resp else "None",
            })

            clients = []
            if resp and resp.success:
                # Handle both list response and wrapped response
                if isinstance(resp.data, list):
                    clients = resp.data
                elif isinstance(resp.data, dict) and "content" in resp.data:
                    clients = resp.data["content"]

            if not clients:
                return AgentResponse(
                    success=True,
                    message="You don't have any clients yet. Say 'add a client' to get started.",
                    agent_type=AgentType.FINANCE_AGENT,
                )

            names = [c.get("name", "Unknown") for c in clients[:5] if isinstance(c, dict)]
            count = len(clients)
            rest = f", and {count - 3} more" if count > 3 else ""
            return AgentResponse(
                success=True,
                message=f"You have {count} client{'s' if count > 1 else ''}: {', '.join(names[:3])}{rest}.",
                agent_type=AgentType.FINANCE_AGENT,
            )
        except Exception as e:
            logger.error({"event": "client_query_error", "error": str(e)})
            return AgentResponse(
                success=False,
                message="Couldn't fetch clients right now.",
                agent_type=AgentType.FINANCE_AGENT,
            )

    # ─────────────────────────────────────────────
    # INVOICE QUERY
    # ─────────────────────────────────────────────
    async def _handle_invoice_query(self, context: VoiceContext, text: str):
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        try:
            # Detect filter from text
            status_filter = None
            text_lower = text.lower()
            if any(w in text_lower for w in ["overdue", "pending", "unpaid", "late"]):
                status_filter = "OVERDUE"
            elif any(w in text_lower for w in ["paid", "completed", "settled"]):
                status_filter = "PAID"
            elif any(w in text_lower for w in ["sent", "outstanding"]):
                status_filter = "SENT"

            params: Dict[str, Any] = {"limit": 50}
            if status_filter:
                params["status"] = status_filter

            resp = await self.backend._request(
                "GET", "/api/invoices",
                org_id=context.org_uuid,
                user_id=context.user_id,
                params=params,
            )

            invoices = []
            if resp and resp.success:
                if isinstance(resp.data, list):
                    invoices = resp.data
                elif isinstance(resp.data, dict) and "content" in resp.data:
                    invoices = resp.data["content"]

            if not invoices:
                filter_text = f" {status_filter.lower()}" if status_filter else ""
                return AgentResponse(
                    success=True,
                    message=f"You have no{filter_text} invoices right now.",
                    agent_type=AgentType.FINANCE_AGENT,
                )

            count = len(invoices)
            total = sum(inv.get("amount", 0) or 0 for inv in invoices)
            filter_text = f" {status_filter.lower()}" if status_filter else ""
            sample = invoices[0]
            first_client = sample.get("clientName", "") or sample.get("client_name", "")
            first_amount = sample.get("amount", 0)

            return AgentResponse(
                success=True,
                message=f"You have {count}{filter_text} invoice{'s' if count > 1 else ''} totalling ₹{total:,.0f}. "
                        f"The latest is {'for ' + first_client if first_client else ''} — ₹{first_amount:,.0f}.",
                agent_type=AgentType.FINANCE_AGENT,
                ui_event={
                    "type": "navigate",
                    "path": f"/invoices{('?status=' + status_filter) if status_filter else ''}",
                } if status_filter else None,
            )
        except Exception as e:
            logger.error({"event": "invoice_query_error", "error": str(e)})
            return AgentResponse(
                success=False,
                message="Couldn't fetch invoices right now.",
                agent_type=AgentType.FINANCE_AGENT,
            )

    # ─────────────────────────────────────────────
    # PAYMENT RECORD
    # ─────────────────────────────────────────────
    async def _handle_payment_record(self, context: VoiceContext, text: str, entities: dict):
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        amount = entities.get("amount")
        invoice_id = entities.get("invoice_id")
        client_name = entities.get("client_name")

        if not amount:
            return AgentResponse(
                success=False,
                message="How much was the payment? Please say the amount.",
                agent_type=AgentType.FINANCE_AGENT,
            )

        # If no invoice_id, try to find by client name
        if not invoice_id and client_name:
            try:
                inv_resp = await self.backend._request(
                    "GET", "/api/invoices",
                    org_id=context.org_uuid,
                    user_id=context.user_id,
                    params={"status": "SENT", "limit": 50},
                )
                if inv_resp and inv_resp.success and isinstance(inv_resp.data, list):
                    for inv in inv_resp.data:
                        inv_client = (inv.get("clientName") or inv.get("client_name") or "").lower()
                        if client_name.lower() in inv_client:
                            invoice_id = inv.get("id")
                            break
            except Exception:
                pass

        if not invoice_id:
            return AgentResponse(
                success=False,
                message=f"I couldn't find an open invoice to record ₹{float(amount):,.0f} against. "
                        "Please tell me which client's invoice this payment is for.",
                agent_type=AgentType.FINANCE_AGENT,
            )

        try:
            resp = await self.backend._request(
                "POST", f"/api/invoices/{invoice_id}/payment",
                org_id=context.org_uuid,
                user_id=context.user_id,
                data={
                    "amount": float(amount),
                    "transactionType": "PAYMENT",
                    "description": f"Payment recorded via voice — ₹{float(amount):,.0f}",
                },
            )

            if resp and resp.success:
                return AgentResponse(
                    success=True,
                    message=f"Payment of ₹{float(amount):,.0f} recorded successfully.",
                    agent_type=AgentType.FINANCE_AGENT,
                    ui_event={
                        "type": "toast",
                        "variant": "success",
                        "title": "Payment Recorded",
                        "message": f"₹{float(amount):,.0f} marked as received.",
                        "duration": 5000,
                    },
                )
            else:
                return AgentResponse(
                    success=False,
                    message="Couldn't record the payment. Please check the invoice and try again.",
                    agent_type=AgentType.FINANCE_AGENT,
                )
        except Exception as e:
            logger.error({"event": "payment_record_error", "error": str(e)})
            return AgentResponse(
                success=False,
                message="Something went wrong recording the payment.",
                agent_type=AgentType.FINANCE_AGENT,
            )

    # ─────────────────────────────────────────────
    # BALANCE / METRICS CHECK
    # ─────────────────────────────────────────────
    async def _handle_balance_check(self, context: VoiceContext):
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        try:
            resp = await self.backend._request(
                "GET", "/api/finance-intelligence/metrics",
                org_id=context.org_uuid,
                user_id=context.user_id,
                params={"businessId": context.business_id or 1},
            )

            logger.info({
                "event": "balance_check_response",
                "org": context.org_uuid,
                "data": str(resp.data)[:200] if resp else "None",
            })

            if resp and resp.success and resp.data:
                d = resp.data
                revenue = d.get("revenue", 0) or 0
                expenses = d.get("expenses", 0) or 0
                profit = d.get("netProfit", 0) or 0
                overdue = d.get("overdueCount", 0) or 0
                overdue_amt = d.get("overdueAmount", 0) or 0

                msg = (
                    f"Your financials: revenue ₹{revenue:,.0f}, expenses ₹{expenses:,.0f}, "
                    f"net profit ₹{profit:,.0f}."
                )
                if overdue > 0:
                    msg += f" You have {overdue} overdue invoice{'s' if overdue > 1 else ''} worth ₹{overdue_amt:,.0f}."
                return AgentResponse(
                    success=True,
                    message=msg,
                    agent_type=AgentType.FINANCE_AGENT,
                )
            else:
                return AgentResponse(
                    success=True,
                    message="No financial data available yet. Add some invoices to get started.",
                    agent_type=AgentType.FINANCE_AGENT,
                )
        except Exception as e:
            logger.error({"event": "balance_check_error", "error": str(e)})
            return AgentResponse(
                success=False,
                message="Couldn't fetch your financial summary right now.",
                agent_type=AgentType.FINANCE_AGENT,
            )

    # ─────────────────────────────────────────────
    # CLIENT CREATE HELPERS
    # ─────────────────────────────────────────────
    def _infer_industry(self, text: str) -> str:
        text = text.lower()
        if any(w in text for w in ["real estate", "park", "builder", "property", "realty"]):
            return "Commercial Real Estate"
        if any(w in text for w in ["hotel", "resort", "hospitality"]):
            return "Hospitality"
        if any(w in text for w in ["logistics", "fleet", "transport"]):
            return "Fleet & Logistics"
        if any(w in text for w in ["tech", "it", "software"]):
            return "IT/Tech Campus"
        return "General Business"

    def _generate_smart_notes(self, name: str, city: str, industry: str) -> str:
        base = f"Potential B2B client in {city}. Industry: {industry}.\n"
        if "Real Estate" in industry or "tech" in industry.lower():
            base += "Likely needs EV charging due to ESG pressure. Pitch FAME III subsidy + fast deployment."
        elif "Logistics" in industry:
            base += "High utilization expected. Pitch bulk charging rates & depot infrastructure."
        else:
            base += "Initial contact to be established. Assess energy infrastructure needs."
        return base

    def _calculate_lead_score(self, text: str, city: str) -> int:
        score = 50
        text = text.lower()
        if any(w in text for w in ["real estate", "park", "campus"]):
            score += 20
        if city.lower() in ["pune", "mumbai", "bangalore", "bengaluru", "hyderabad"]:
            score += 15
        if any(w in text for w in ["private limited", "pvt ltd", "pvt. ltd"]):
            score += 15
        return min(score, 100)

    async def _handle_client_create(self, text: str, context: VoiceContext):
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        entities = {e["type"]: e["value"] for e in (context.extracted_entities or [])}
        name = entities.get("client_name") or entities.get("company_name")

        logger.info({
            "event": "client_create_attempt",
            "name": name,
            "entities": entities,
            "org_uuid": context.org_uuid,
        })

        if context.org_uuid.startswith("org_"):
            logger.warning({"event": "client_create_blocked_unresolved_org", "org_uuid": context.org_uuid})
            return AgentResponse(
                success=False,
                message="I'm having trouble identifying your account. Please try again in a moment.",
                agent_type=AgentType.FINANCE_AGENT,
            )

        if not name:
            session = self.state_manager.get_session(context.session_id)
            session.locked_intent = "CLIENT_CREATE"
            if not session.client_draft:
                session.client_draft = {}
            self.state_manager.save_session(session)
            return AgentResponse(
                success=False,
                message="What's the name of the business you'd like to add?",
                agent_type=AgentType.FINANCE_AGENT,
                needs_clarification=True,
            )

        raw_text = text if text else str(entities)
        city = entities.get("address", "")
        industry = self._infer_industry(raw_text)
        lead_score = self._calculate_lead_score(raw_text, city or "")
        smart_notes = self._generate_smart_notes(name, city or "unknown location", industry)

        # Open UI dialog for exact-input fields if missing
        dialog_fields = []
        if not entities.get("phone"):
            dialog_fields.append({"id": "phone", "label": "Phone Number", "type": "tel", "required": False})
        if not entities.get("email"):
            dialog_fields.append({"id": "email", "label": "Email Address", "type": "email", "required": False})
        if not entities.get("gst_number") and not entities.get("tax_id"):
            dialog_fields.append({"id": "gst_number", "label": "GST / Tax ID", "type": "text", "placeholder": "22AAAAA0000A1Z5", "required": False})
        if not entities.get("address"):
            dialog_fields.append({"id": "address", "label": "Address", "type": "textarea", "required": False})

        session = self.state_manager.get_session(context.session_id)
        if dialog_fields and not getattr(session, "dialog_pending", False):
            session.dialog_pending = True
            session.dialog_id = "client_details_form"
            if not session.client_draft:
                session.client_draft = {}
            session.client_draft.update(entities)
            self.state_manager.save_session(session)
            return AgentResponse(
                success=True,
                message=f"Got it — adding {name}. Please fill in the contact details on the form that just opened.",
                agent_type=AgentType.FINANCE_AGENT,
                ui_event={
                    "type": "open_input_dialog",
                    "dialog_id": "client_details_form",
                    "session_id": context.session_id,
                    "title": f"Add Details for {name}",
                    "message": "Type these in — much easier than speaking them!",
                    "fields": dialog_fields,
                    "submit_endpoint": "/api/v1/voice/dialog-response",
                },
            )

        # Direct save (dialog already submitted or all fields present)
        try:
            resp = await self.backend._request(
                "POST", "/api/clients",
                org_id=context.org_uuid,
                user_id=context.user_id,
                data={
                    "name": name,
                    "email": entities.get("email"),
                    "phoneNumber": entities.get("phone"),
                    "address": city or None,
                    "taxId": entities.get("gst_number") or entities.get("tax_id"),
                    "notes": smart_notes,
                },
            )

            logger.info({
                "event": "client_create_backend_response",
                "success": resp.success if resp else None,
                "data": str(resp.data)[:200] if resp else "None",
                "error": str(getattr(resp, "error", ""))[:200] if resp else "None",
            })

            if resp and resp.success:
                action = (
                    f"High-value lead — score {lead_score}/100 in {industry}. Smart notes saved to CRM."
                    if lead_score > 70
                    else f"Score {lead_score}/100 in {industry}."
                )
                return AgentResponse(
                    success=True,
                    message=f"Added {name}. {action}",
                    agent_type=AgentType.FINANCE_AGENT,
                    ui_event={
                        "type": "toast",
                        "variant": "success",
                        "title": "Client Added",
                        "message": f"{name} saved to CRM.",
                        "duration": 5000,
                    },
                )
            else:
                err = getattr(resp, "error", "") if resp else "Unknown error"
                return AgentResponse(
                    success=False,
                    message=f"Couldn't add {name}. {err}",
                    agent_type=AgentType.FINANCE_AGENT,
                )
        except Exception as e:
            logger.error({"event": "client_create_error", "error": str(e)})
            return AgentResponse(
                success=False,
                message="Something went wrong adding the client.",
                agent_type=AgentType.FINANCE_AGENT,
            )

    async def finalize_client_create(self, session) -> dict:
        """Called by the dialog-response endpoint after user fills the form."""
        from app.agents.base_agent import AgentResponse
        from app.schemas.intents import AgentType

        draft = session.client_draft or {}
        name = draft.get("client_name") or draft.get("company_name")
        city = draft.get("address", "")
        industry = self._infer_industry(str(draft))
        lead_score = self._calculate_lead_score(str(draft), city or "")
        smart_notes = self._generate_smart_notes(name, city or "unknown location", industry)

        try:
            resp = await self.backend._request(
                "POST", "/api/clients",
                org_id=session.org_id,
                user_id=getattr(session, "user_id", None),
                data={
                    "name": name,
                    "email": draft.get("email"),
                    "phoneNumber": draft.get("phone") or draft.get("phoneNumber"),
                    "address": draft.get("address"),
                    "taxId": draft.get("gst_number") or draft.get("taxId"),
                    "notes": smart_notes,
                },
            )

            logger.info({
                "event": "client_finalize_backend_response",
                "success": resp.success if resp else None,
                "data": str(resp.data)[:200] if resp else "None",
            })

            if resp and resp.success:
                return {
                    "success": True,
                    "response_text": f"Added {name} to your CRM.",
                    "ui_event": {
                        "type": "client_created",
                        "name": name,
                        "toast": {
                            "title": "Client Saved",
                            "variant": "success",
                            "message": f"{name} added successfully.",
                        },
                    },
                }
            return {
                "success": False,
                "response_text": f"Couldn't save {name}. Error: {getattr(resp, 'error', 'Unknown')}",
            }
        except Exception as e:
            logger.error({"event": "client_finalize_error", "error": str(e)})
            return {"success": False, "response_text": f"Error: {str(e)}"}


voice_processor = VoiceProcessor()
