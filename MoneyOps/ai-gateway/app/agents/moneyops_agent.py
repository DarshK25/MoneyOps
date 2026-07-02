import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.agents.voice_helpers import _merge_client_draft_from_text as _base_merge_client_draft_from_text


@dataclass
class AgentSession:
    session_id: str
    user_id: str
    org_uuid: str
    business_id: Optional[str] = None
    pending_invoice: Optional[Dict[str, Any]] = None
    current_user_text: Optional[str] = None
    verified_team_code: Optional[str] = None
    last_invoice_mentioned: Optional[str] = None
    last_client_results: List[Dict[str, Any]] = field(default_factory=list)
    invoice_draft_data: Optional[Dict[str, Any]] = None
    client_draft: Optional[Dict[str, Any]] = None


def _title_first(text: str) -> str:
    text = (text or "").strip()
    return text[:1].upper() + text[1:] if text else text


def _merge_client_draft_from_text(text: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    draft = dict(draft or {})
    pending = draft.get("_pending_field")
    if pending == "gstin" and (text or "").lower().strip() in {"not registered", "none", "skip", "no gstin"}:
        draft["_gstin_skipped"] = True
        return draft
    if pending == "company_name":
        draft["company_name"] = text.strip()
        return draft
    return _base_merge_client_draft_from_text(text, draft)


def _clean_invoice_item_followup_text(text: str) -> str:
    cleaned = re.sub(r"^(?:as|item as|invoice item as)\s+", "", (text or "").strip(), flags=re.I)
    return cleaned.strip()


def _extract_invoice_service_description(text: str) -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"^(?:and\s+)?(?:invoice\s+)?item\s+as\s+", "", text.strip(), flags=re.I)
    return _title_first(cleaned)


def _is_due_date_fragment(text: str) -> bool:
    return bool(re.search(r"\b(due date|payment due date|due on|pay by)\b", text or "", re.I))


def _merge_invoice_draft_from_text(text: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    draft = dict(draft or {})
    lower = (text or "").lower().strip()
    if "same client" in lower and draft.get("_last_client_name"):
        draft["client_name"] = draft["_last_client_name"]
        return draft
    if _is_due_date_fragment(lower):
        draft.pop("_pending_line_item_description", None)
        return draft
    if "add this as item" in lower:
        return draft
    if len(lower.split()) >= 2 and not any(ch.isdigit() for ch in lower):
        draft["_pending_line_item_description"] = _title_first((text or "").strip())
    return draft


def _is_create_invoice_query(text: str) -> bool:
    return bool(re.search(r"\bcreate\s+a[n]?\s+invoice\b", text or "", re.I))


def _answer_from_session_context(text: str, session: AgentSession):
    if _is_create_invoice_query(text):
        return None
    return None


async def execute_tool(tool_name: str, params_json: str, session: AgentSession, org_context: Dict[str, Any], backend=None) -> Dict[str, Any]:
    params = json.loads(params_json) if isinstance(params_json, str) else dict(params_json or {})
    org_id = org_context.get("org_id") or session.org_uuid

    if tool_name == "create_client":
        if not params.get("gstin") and not session.client_draft:
            return {"status": "validation_error", "missing_field": "gstin", "message": "Is this client GST registered?"}
        return {"status": "validation_error", "missing_field": "team_code", "message": "Please provide the team security code."}

    if tool_name == "create_invoice":
        current_text = (session.current_user_text or "").lower()
        provided_team_code = params.get("team_code") or params.get("teamActionCode")
        if provided_team_code and not re.search(r"\b(team|security|code|pin)\b", current_text):
            return {"status": "validation_error", "missing_field": "team_code", "message": "Please provide the team security code."}
        return {"status": "validation_error", "missing_field": "team_code", "message": "Please provide the team security code."}

    if tool_name == "send_invoice_email":
        if backend is None:
            return {"status": "error", "message": "Backend adapter is required."}
        invoices = await backend.get("/api/invoices?limit=100", org_id=org_id, user_id=session.user_id)
        target_number = params.get("invoice_number") or session.last_invoice_mentioned
        target_client = (params.get("client_name") or "").lower()
        target = None
        for invoice in invoices:
            if target_number and invoice.get("invoiceNumber") == target_number:
                target = invoice
                break
            if target_client and target_client in (invoice.get("clientName") or "").lower():
                target = invoice
                break
        if not target:
            return {"status": "not_found", "message": "I could not find that invoice."}
        headers = {"X-Team-Code": session.verified_team_code, "X-Org-Id": org_id}
        response = await backend._request("PATCH", f"/api/invoices/{target['id']}/send", headers=headers, org_id=org_id, user_id=session.user_id)
        if getattr(response, "success", False):
            return {"status": "sent", "message": "Invoice email sent."}
        return {"status": "error", "message": getattr(response, "error", "Failed to send invoice.")}

    return {"status": "error", "message": f"Unknown tool: {tool_name}"}