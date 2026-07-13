from typing import Any, Dict, Tuple

from app.state.session_manager import session_manager


class _BackendPlaceholder:
    async def get_onboarding_status(self, user_id):
        return None

    async def get_my_organization(self, user_id):
        return None


class IntelligentAgent:
    def __init__(self):
        self.backend = _BackendPlaceholder()

    def _route_query(self, query: str, session=None) -> Tuple[str, Dict[str, Any]]:
        text = (query or "").lower().strip()
        args: Dict[str, Any] = {}
        if session is not None and getattr(session, "locked_intent", None) == "INVOICE_CREATE" and getattr(session, "invoice_draft", None) is not None:
            return "create_invoice", args
        if session is not None and getattr(session, "last_tool", None) == "get_business_context":
            return "get_business_context", args
        if session is not None and getattr(session, "last_tool", None) == "search_market":
            return "search_market", {"followup": True}
        if session is not None and getattr(session, "last_tool", None) == "get_all_invoices" and len(text.split()) <= 3:
            return "get_all_invoices", {"metric": "count"}
        if "paid" in text and "invoice" in text and "revenue" in text:
            return "get_all_invoices", {"status": "PAID", "metric": "revenue"}
        if any(word in text for word in ["market", "competitor", "trend", "affect my business"]):
            return "search_market", args
        if any(word in text for word in ["business", "sector", "industry"]):
            return "get_business_context", args
        return "general", args

    async def _tool_get_business_context(self, args: Dict[str, Any]) -> str:
        session_id = args.get("session_id")
        raw_text = (args.get("raw_text") or "").lower()
        if session_id:
            session = await session_manager.get_session(session_id, args.get("user_id", "unknown"), args.get("org_id", "unknown"))
            profile = session.last_business_profile or {}
            if profile and "sector" in raw_text:
                return f"{profile.get('name', 'Your business')} sits in {profile.get('sector')}."

        org_response = None
        if hasattr(self.backend, "get_my_organization"):
            org_response = await self.backend.get_my_organization(args.get("user_id"))
        data = getattr(org_response, "data", None) if getattr(org_response, "success", False) else None
        if data:
            parts = [data.get("legalName") or data.get("businessName") or data.get("name"), data.get("industry"), data.get("targetMarket"), data.get("primaryActivity")]
            return " | ".join([p for p in parts if p])

        status_response = None
        if hasattr(self.backend, "get_onboarding_status"):
            status_response = await self.backend.get_onboarding_status(args.get("user_id"))
        status_data = getattr(status_response, "data", None) if getattr(status_response, "success", False) else None
        if status_data:
            name = status_data.get("businessName") or status_data.get("legalName") or "Your business"
            return f"{name}: detailed business profile is still missing."
        return "Your detailed business profile is still missing."

    async def _tool_search_market(self, args: Dict[str, Any]) -> str:
        session = await session_manager.get_session(args.get("session_id", "default"), args.get("user_id", "unknown"), args.get("org_id", "unknown"))
        profile = session.last_business_profile or {}
        results = session.last_market_results or []
        if args.get("followup") and results:
            return f"For {profile.get('name', 'your business')}: " + " ".join(results)
        return "No cached market results are available yet."