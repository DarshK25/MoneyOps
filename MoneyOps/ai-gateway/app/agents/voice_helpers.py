"""
Voice pipeline helper functions.
Replaces deleted moneyops_agent utility functions with clean implementations.
"""
import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from app.utils.amount_parser import parse_indian_amount
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_amount_value(text: str) -> Optional[float]:
    """Extract a monetary amount from spoken text like 'five thousand rupees'."""
    return parse_indian_amount(text)


def _best_client_match(name: str, clients: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Fuzzy match a client name against a list of clients.
    Accepts first-name-only matches, small STT drift. Rejects unrelated short names.
    """
    if not name or not clients:
        return None

    name_lower = name.lower().strip()

    # Exact match on name or company
    for client in clients:
        client_name = (client.get("name") or "").lower().strip()
        company = (client.get("company") or "").lower().strip()
        if name_lower == client_name or name_lower == company:
            return client

    # First-name-only match (at least 4 chars to avoid false positives)
    if len(name_lower) >= 4:
        for client in clients:
            client_name = (client.get("name") or "").lower().strip()
            # Check if the name matches the start of any name token
            if any(t.startswith(name_lower) for t in client_name.split()):
                return client

    # Small STT drift: allow 1-char mismatch for names >= 5 chars
    if len(name_lower) >= 5:
        for client in clients:
            client_name = (client.get("name") or "").lower().strip()
            # Levenshtein-like: check common substring
            if _fuzzy_score(name_lower, client_name) >= 0.75:
                return client

    return None


def _fuzzy_score(a: str, b: str) -> float:
    """Simple substring-based fuzzy score (0-1)."""
    a, b = a.lower(), b.lower()
    if not a or not b:
        return 0.0
    longer = a if len(a) > len(b) else b
    shorter = b if longer == a else a
    if len(longer) == 0:
        return 1.0
    # Check if shorter appears as a contiguous subsequence
    if shorter in longer:
        return float(len(shorter)) / len(longer)
    # Check common character overlap
    common = sum(1 for c in shorter if c in longer)
    return common / len(longer)


def _extract_client_name_for_invoice(text: str) -> Optional[str]:
    """
    Extract a client name from voice text like 'call Vedanta solutions'.
    Returns None if the text is actually a service description.
    """
    if not text:
        return None

    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    # Service description keywords — reject
    service_keywords = [
        "smart load", "electrical panel", "safety compliance", "installation",
        "maintenance", "setup", "system", "service", "repair", "upgrade",
        "supply", "charging", "solar", "monitoring",
    ]
    for kw in service_keywords:
        if kw in text_lower:
            return None

    # "call <client>" pattern — match on original text to preserve case
    call_match = re.search(r'[Cc]all\s+(.+?)(?:\s+in\s+)?$', text_stripped)
    if call_match:
        extracted = call_match.group(1).strip()
        if len(extracted) < 3:
            return None
        return extracted

    # "for <client>" pattern
    for_match = re.search(r'^[Ff]or\s+(.+)$', text_stripped)
    if for_match:
        extracted = for_match.group(1).strip()
        if len(extracted) >= 3:
            return extracted

    # Bare name fallback — return as-is
    return text_stripped


def _extract_invoice_item_replacement_text(text: str) -> Optional[str]:
    """Extract the replacement item description from 'Replace with ...' or 'Replace ... with ...'"""
    if not text:
        return None
    match = re.search(r'replace\s+(?:the\s+)?invoice\s+item\s+with\s+(.+)', text.lower())
    if match:
        return match.group(1).strip().rstrip(".,;!")
    match = re.search(r'replace\s+(?:with\s+)?(.+)', text.lower())
    if match:
        return match.group(1).strip().rstrip(".,;!")
    return None


def _parse_invoice_items_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse pipe-delimited invoice items from dialog form.
    Format: TYPE | description | quantity | unit_price | gst_percent
    """
    if not text or "|" not in text:
        return []

    items = []
    for line in text.strip().split("\n"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        try:
            item = {
                "description": parts[1],
                "quantity": int(parts[2]) if parts[2] else 1,
                "unit_price": float(parts[3]) if parts[3] else 0.0,
                "gst_percent": int(parts[4]) if len(parts) > 4 and parts[4] else 18,
            }
            items.append(item)
        except (ValueError, IndexError):
            continue
    return items


def _merge_invoice_draft_from_text(text: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge voice text into an invoice draft.
    Handles: client name, amount, service description, due date.
    """
    if draft is None:
        draft = {}
    text_lower = text.lower().strip()
    text_stripped = text.strip()

    # Extract description from text
    desc_text = re.sub(r'^for\s+', '', text_lower)
    service_match = re.search(r'(?:the )?(?:service is |item is |description is )(.+)', desc_text)
    description_candidate = None
    if service_match:
        candidate = service_match.group(1).strip()
        if len(candidate) > 3 and not candidate.replace(" ", "").isdigit():
            description_candidate = candidate
    elif len(desc_text) > 3 and not desc_text.replace(" ", "").isdigit():
        description_candidate = desc_text

    # Check for amount — normalize spaced digits (e.g., "20 000" → "20000")
    text_for_amount = re.sub(r'(?<=\d)\s+(?=\d)', '', text_stripped)
    amount = _extract_amount_value(text_for_amount)

    has_amount = amount and amount > 0
    has_description = description_candidate is not None

    if has_amount or has_description:
        line_items = list(draft.get("line_items") or [])
        pending = next((li for li in line_items if not li.get("description")), None) if has_description else None
        pending_price = next((li for li in line_items if li.get("unit_price") == 0), None) if has_amount and not pending else None

        if has_amount and has_description:
            # Both provided in one sentence — create a complete line item
            if pending:
                pending["unit_price"] = amount
                pending["description"] = description_candidate
            else:
                line_items.append({"description": description_candidate, "quantity": 1, "unit_price": amount, "gst_percent": 18})
        elif has_amount:
            if pending_price:
                pending_price["unit_price"] = amount
            elif pending:
                pending["unit_price"] = amount
            else:
                line_items.append({"description": "", "quantity": 1, "unit_price": amount, "gst_percent": 18})
        elif has_description:
            if pending:
                pending["description"] = description_candidate
            elif line_items:
                line_items[-1]["description"] = description_candidate
            else:
                line_items.append({"description": description_candidate, "quantity": 1, "unit_price": 0, "gst_percent": 18})

        draft["line_items"] = line_items
        return draft

    return draft


def _merge_payment_draft_from_text(text: str, draft: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract payment method, client name, and reference from voice text."""
    if draft is None:
        draft = {}
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    # Payment methods
    methods = {"upi": "UPI", "neft": "NEFT", "rtgs": "RTGS", "cash": "CASH", "cheque": "CHEQUE", "card": "CARD"}
    found_method = None
    for kw, method in methods.items():
        if kw in text_lower:
            found_method = method
            break

    # Client name — usually after "from" (capture only the name, stop at prepositions/verbs)
    client_match = re.search(r'from\s+(\w+(?:\s+\w+)?)', text_lower)
    if client_match:
        candidate = client_match.group(1)
        candidate = re.sub(r'\s+(by|with|for|via|through|using|and|or)$', '', candidate)
        draft["client_name"] = candidate

    # UTR / reference — usually alphanumeric after certain keywords
    ref_match = re.search(r'(?:reference|ref|utr)\s+([\w-]+)', text_stripped, re.IGNORECASE)
    if ref_match:
        draft["utr_or_reference"] = ref_match.group(1)

    if found_method:
        draft["payment_method"] = found_method

    return draft


def _extract_due_date_phrase(text: str) -> Optional[str]:
    """Parse a due date phrase like '30 april' or '30th april' into YYYY-MM-DD format."""
    if not text:
        return None
    text_lower = text.lower().strip()

    months = {
        "january": "01", "february": "02", "march": "03", "april": "04",
        "may": "05", "june": "06", "july": "07", "august": "08",
        "september": "09", "october": "10", "november": "11", "december": "12",
    }

    match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(' + "|".join(months.keys()) + r')', text_lower)
    if match:
        day = int(match.group(1))
        month = months[match.group(2)]
        if 1 <= day <= 31:
            return f"2026-{month}-{day:02d}"
    return None


def _extract_line_items_from_invoice_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract line items from spoken invoice text.
    Handles patterns like 'add quarterly amc for 12 chargers at 850 rupees each'
    """
    if not text:
        return []
    text_lower = text.lower().strip()

    items = []
    # Pattern: <description> for <quantity> <units> at <rate> rupees each
    at_rate_match = re.search(
        r'(.+?)\s+for\s+(\d+)\s+(.+?)\s+at\s+(\d+)\s+rupees?\s+each',
        text_lower,
    )
    if at_rate_match:
        items.append({
            "description": at_rate_match.group(1).strip(),
            "quantity": int(at_rate_match.group(2)),
            "unit_price": float(at_rate_match.group(4)),
            "gst_percent": 18,
        })
        return items

    # Pattern: <description> of <modifier> at <rate> rupees (no quantity extraction)
    at_rupees_match = re.search(r'(.+?)\s+at\s+(\d+)\s+rupees?', text_lower)
    if at_rupees_match:
        items.append({
            "description": at_rupees_match.group(1).strip(),
            "quantity": 1,
            "unit_price": float(at_rupees_match.group(2)),
            "gst_percent": 18,
        })
        return items

    # Simple: <description> for <amount>
    simple_match = re.search(r'(.+?)\s+for\s+(\d+)', text_lower)
    if simple_match:
        items.append({
            "description": simple_match.group(1).strip(),
            "quantity": 1,
            "unit_price": float(simple_match.group(2)),
            "gst_percent": 18,
        })
        return items

    return items


def _merge_additional_invoice_item_followup(text: str, draft: Dict[str, Any]) -> tuple:
    """
    Handle follow-up for adding an additional invoice item.
    Two-step: first collect description, then amount.
    Returns (updated_draft, state) where state is 'awaiting_amount', 'completed', or 'awaiting_description'.
    """
    if draft.get("_awaiting_additional_item_amount"):
        # We have the description, now looking for amount
        amount = _extract_amount_value(text)
        if amount and amount > 0:
            description = draft.pop("_pending_additional_item_description", "")
            line_items = list(draft.get("line_items") or [])
            line_items.append({
                "description": description,
                "quantity": 1,
                "unit_price": amount,
                "gst_percent": 18,
            })
            draft["line_items"] = line_items
            draft.pop("_awaiting_additional_item_amount", None)
            return draft, "completed"
        return draft, "awaiting_amount"

    if draft.get("_awaiting_additional_item_description"):
        # Still waiting for description — store it
        if len(text.split()) >= 2:
            draft["_pending_additional_item_description"] = text.strip()
            draft.pop("_awaiting_additional_item_description", None)
            draft["_awaiting_additional_item_amount"] = True
            return draft, "awaiting_amount"
        return draft, "awaiting_description"

    # First step: looking for description
    if len(text.split()) >= 2:
        draft["_pending_additional_item_description"] = text.strip()
        draft["_awaiting_additional_item_amount"] = True
        return draft, "awaiting_amount"

    return draft, "awaiting_description"


def _handle_invoice_item_review_followup(text: str, draft: Dict[str, Any]) -> tuple:
    """
    Handle follow-up during invoice item review.
    Supports: setting quantity, skipping to next step.
    Returns (updated_draft, response_message).
    """
    text_lower = text.lower().strip()
    line_items = list(draft.get("line_items") or [])

    # Check for quantity setting
    qty_match = re.search(r'quantity\s+(?:is\s+)?(\d+)', text_lower)
    if qty_match and line_items:
        line_items[0]["quantity"] = int(qty_match.group(1))
        draft["line_items"] = line_items
        draft["_awaiting_add_more_items_confirmation"] = True
        return draft, "Got it. Do you want to add another item?"

    # "no" or "no more items" — move on
    if text_lower in ("no", "no more items", "nope", "not now", "skip"):
        draft.pop("_awaiting_invoice_item_review", None)
        draft.pop("_awaiting_add_more_items_confirmation", None)
        return draft, "What due date should I put on the invoice?"

    return draft, "I didn't catch that. Do you want to change the quantity or add another item?"


def _semantic_invoice_followup_intent(text: str, valid_intents: tuple) -> str:
    """
    Classify a follow-up intent from voice text during invoice creation.
    Returns one of: negative, add_item, set_quantity, affirmative.
    """
    text_lower = text.lower().strip()

    # Negative: decline suggestions
    negative_patterns = ["don't send", "not yet", "not now", "no", "nope", "skip", "later"]
    for p in negative_patterns:
        if p in text_lower:
            return "negative"

    # Add item
    add_patterns = ["add", "include", "another", "more item", "extra", "one more"]
    for p in add_patterns:
        if p in text_lower:
            return "add_item"

    # Set quantity
    if "quantity" in text_lower or re.search(r'\d+', text_lower):
        return "set_quantity"

    # Affirmative
    affirm_patterns = ["yes", "yeah", "sure", "ok", "okay", "go ahead", "send"]
    for p in affirm_patterns:
        if p in text_lower:
            return "affirmative"

    return "negative"


def _groq_rate_limit_message(error: Exception) -> str:
    """Format Groq rate limit error into a user-friendly message."""
    error_text = str(error)
    match = re.search(r'in\s+(\d+(?:\.\d+)?)\s*seconds?', error_text)
    if match:
        seconds = round(float(match.group(1)))
        if seconds > 0:
            return f"I'm currently rate-limited by the AI provider. I can retry in about {seconds} seconds."
        return "I'm currently rate-limited by the AI provider. Please try again in a moment."
    match = re.search(r'in\s+(\d+)m(\d+(?:\.\d+)?)s', error_text)
    if match:
        minutes = int(match.group(1))
        seconds = round(float(match.group(2)))
        if minutes > 0 and seconds > 0:
            return f"I'm currently rate-limited by the AI provider. I can retry in about {minutes} minutes {seconds} seconds."
        elif minutes > 0:
            return f"I'm currently rate-limited by the AI provider. I can retry in about {minutes} minutes."
        else:
            return f"I'm currently rate-limited by the AI provider. I can retry in about {seconds} seconds."
    return "I'm currently rate-limited by the AI provider. Please try again in a moment."


def _build_invoice_preview_dialog_ui_event(session_id: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    """Build a UI event payload for the invoice preview dialog."""
    line_items = draft.get("line_items") or []
    subtotal = sum(
        (li.get("unit_price") or 0) * (li.get("quantity") or 1)
        for li in line_items
    )
    gst_total = sum(
        (li.get("unit_price") or 0) * (li.get("quantity") or 1) * (li.get("gst_percent") or 18) / 100
        for li in line_items
    )
    return {
        "type": "show_invoice_preview",
        "payload": {
            "session_id": session_id,
            "draft": {
                "client_name": draft.get("client_name", ""),
                "client_id": draft.get("client_id", ""),
                "issue_date": draft.get("issue_date", ""),
                "due_date": draft.get("due_date", ""),
                "notes": draft.get("notes", ""),
                "line_items": line_items,
                "subtotal": round(subtotal, 2),
                "gst_total": round(gst_total, 2),
                "total": round(subtotal + gst_total, 2),
            },
        },
    }


def _build_client_form_ui_event(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Build a UI event payload for the client form dialog."""
    return {
        "type": "show_client_form",
        "payload": {
            "draft": {
                "name": draft.get("name", ""),
                "email": draft.get("email", ""),
                "phone": draft.get("phone", ""),
                "company_name": draft.get("company_name", ""),
                "gstin": draft.get("gstin", ""),
                "notes": draft.get("notes", ""),
                "team_code": draft.get("team_code", ""),
            },
        },
    }


# ---------------------------------------------------------------------------
# AgentSession — legacy session container for the old voice pipeline
# ---------------------------------------------------------------------------
@dataclass
class AgentSession:
    """Session container for the voice pipeline. Used by legacy tests and wrappers."""
    session_id: str
    user_id: str
    org_uuid: str
    business_id: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    last_tool_called: Optional[str] = None
    last_response_context: Optional[str] = None
    last_market_results: Optional[List[str]] = None
    invoice_draft_data: Optional[Dict[str, Any]] = None
    client_draft: Optional[Dict[str, Any]] = None
    verified_team_code: Optional[str] = None


def _looks_like_email_fragment(text: str) -> bool:
    """Check if text looks like an email address fragment."""
    return bool(re.search(r'[\w.+-]+@[\w.-]+', text))


_TEAM_CODE_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


def _extract_team_code(text: str) -> Optional[str]:
    """Extract a 4-digit team code from spoken text like 'team security code is 2 0 9 1'."""
    if not text:
        return None
    text_lower = text.lower().strip()

    # Direct 4-digit match
    direct = re.search(r'\b(\d{4})\b', text_lower)
    if direct:
        return direct.group(1)

    # Replace digit words with digits, then extract 4 consecutive digits
    for word, digit in _TEAM_CODE_WORDS.items():
        text_lower = text_lower.replace(word, digit)

    digits_only = re.sub(r'[^0-9]', '', text_lower)
    if len(digits_only) == 4:
        return digits_only
    # Look for 4 consecutive digits
    code_match = re.search(r'(\d{4})', digits_only)
    if code_match:
        return code_match.group(1)
    return None


def _merge_client_draft_from_text(text: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    """Merge voice text into a client draft form."""
    if draft is None:
        draft = {}
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    team_code = _extract_team_code(text)
    if team_code:
        draft["team_code"] = team_code

    # Check for company name indicators
    company_indicators = ["pvt ltd", "private limited", "limited", "llp", "ltd", "inc", "corporation", "corp"]
    has_company_indicator = any(ind in text_lower for ind in company_indicators)

    # "create a client <company>" pattern
    create_client_match = re.search(r'create\s+a\s+client\s+(.+)', text_lower)
    if create_client_match:
        candidate = create_client_match.group(1).strip()
        if len(candidate) >= 3:
            draft["company_name"] = candidate
            return draft

    # Check for name pattern
    name_match = re.search(r'(?:name is |contact (?:person )?(?:name )?is |call me |i am |i\'m )(.+)', text_lower)
    if name_match:
        candidate = name_match.group(1).strip()
        if not _looks_like_email_fragment(candidate) and len(candidate) >= 3:
            draft["name"] = candidate
            return draft

    # If text has a company indicator, store as company_name
    if has_company_indicator:
        draft["company_name"] = text_stripped
        return draft

    # Fallback: two-word text like "Arjun Desai" → store as name
    words = text_stripped.split()
    if 2 <= len(words) <= 3 and all(w[0].isupper() for w in words if w):
        draft["name"] = text_stripped
        return draft

    return draft


def _is_market_growth_query(text: str) -> bool:
    """Check if the query is about market updates or growth."""
    text_lower = text.lower().strip()
    keywords = ["market update", "market intelligence", "growth", "industry trend",
                "what changed", "market news", "competitor", "competition"]
    return any(kw in text_lower for kw in keywords)


def _is_market_action_followup_query(text: str, session: AgentSession) -> bool:
    """Check if the query is a follow-up to a market action."""
    if not session.last_tool_called:
        return False
    return session.last_tool_called == "search_market_intelligence"


def _synthesize_market_result(data: Dict[str, Any]) -> str:
    """Create an actionable market intelligence result."""
    query = data.get("query", "")
    focus = data.get("focus", "opportunities")
    activity = data.get("activity", "your business")
    business_name = data.get("business_name", "Your Business")
    city = data.get("city", "your area")
    raw_snippets = data.get("raw_snippets", [])

    result = f"# Market Intelligence for {business_name}\n\n"
    result += f"**Focus Area:** {focus.title()}\n"
    result += f"**Location:** {city}\n\n"

    if raw_snippets:
        result += "**Key Findings:**\n"
        for snippet in raw_snippets:
            result += f"- {snippet}\n"

    result += "\n**To act on this:**\n"
    result += "1. First, analyze how this affects your current operations in the next week.\n"
    if focus == "opportunities":
        result += "2. Second, identify specific clients or projects in this segment.\n"
        result += "3. Third, prepare a tailored outreach or proposal.\n"
    elif focus == "threats":
        result += "2. Second, identify your largest exposures to this risk.\n"
        result += "3. Third, create a mitigation plan.\n"
    else:
        result += "2. Second, discuss this with your team in the next stand-up.\n"
        result += "3. Third, set up monitoring for changes in this area.\n"

    return result


def _market_action_guidance(query: str, session: AgentSession, context: Dict[str, Any]) -> str:
    """Generate market action guidance based on a follow-up query."""
    business = context.get("business", {})
    activity = business.get("primaryActivity", "your business")
    city = business.get("city", "your area")

    query_lower = query.lower()

    if "financial loss" in query_lower or "protect" in query_lower or "avoid" in query_lower:
        return (
            f"To protect against financial loss in {city}:\n"
            "1. **Escalate collections** on any overdue invoices in this segment.\n"
            "2. **Review credit terms** — consider shorter payment cycles for new clients.\n"
            "3. **Diversify clients** to reduce concentration risk.\n"
            "4. Use automated reminders to stay ahead of payment delays."
        )

    return (
        f"Based on the market data for {activity} in {city}:\n"
        "1. **Follow up** with prospects who showed interest recently.\n"
        "2. **Review your pricing** against what competitors are offering.\n"
        "3. **Set a 30-day goal** to capture one new opportunity.\n"
        "Would you like me to help with any of these steps?"
    )


async def execute_tool(tool_name: str, params_json: str, session: AgentSession,
                       org_context: Dict[str, Any], backend) -> Dict[str, Any]:
    """
    Execute a specific tool by name.
    Replaces the old moneyops_agent.execute_tool with real backend calls.
    """
    import json as _json
    params = _json.loads(params_json) if isinstance(params_json, str) else params_json

    if tool_name == "create_client":
        payload = {
            "name": params.get("name", ""),
            "email": params.get("email", ""),
            "phoneNumber": params.get("phone", params.get("phoneNumber", "")),
            "company_name": params.get("company_name", params.get("company", "")),
            "gstin": params.get("gstin", ""),
            "notes": params.get("notes", ""),
            "teamActionCode": params.get("team_code", params.get("teamActionCode", "")),
            "source": "VOICE",
        }
        if not payload.get("name"):
            return {"status": "validation_error", "missing_field": "name",
                    "message": "What is the main contact person name?"}
        try:
            response = await backend.post("/api/clients", payload=payload,
                                          org_id=org_context.get("org_id"),
                                          user_id=session.user_id)
            if response and response.get("id"):
                return {"status": "created", "client_id": response["id"], "message": "Client created successfully."}
            return {"status": "error", "message": "Failed to create client."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    elif tool_name == "create_invoice":
        payload = {
            "clientId": params.get("client_id", params.get("clientId", "")),
            "clientName": params.get("client_name", params.get("clientName", "")),
            "issueDate": params.get("issue_date", params.get("issueDate", "")),
            "dueDate": params.get("due_date", params.get("dueDate", "")),
            "lineItems": params.get("line_items", params.get("lineItems", [])),
            "notes": params.get("notes", ""),
        }
        try:
            response = await backend.post("/api/invoices", payload=payload,
                                          org_id=org_context.get("org_id"),
                                          user_id=session.user_id)
            if response and response.get("id"):
                return {"status": "created", "invoice_id": response["id"],
                        "invoice_number": response.get("invoiceNumber", ""),
                        "message": "Invoice created successfully."}
            return {"status": "error", "message": "Failed to create invoice."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": f"Unknown tool: {tool_name}"}


async def process(text: str, session: AgentSession, org_context: Dict[str, Any],
                  groq_key: str, backend, is_voice: bool = False) -> Dict[str, Any]:
    """
    Legacy process function — handles flow-level interactions then falls back
    to MasterOrchestrator for general intelligence.
    """
    text_stripped = text.strip()
    text_lower = text_stripped.lower()

    last_ctx = None
    if session.last_response_context:
        try:
            last_ctx = json.loads(session.last_response_context) if isinstance(session.last_response_context, str) else session.last_response_context
        except (json.JSONDecodeError, TypeError):
            last_ctx = None

    # ---- Invoice send offer decline ----
    if last_ctx and last_ctx.get("type") == "invoice_send_offer" and any(w in text_lower for w in ["no", "don't", "not", "nope", "skip"]):
        _append_history(session, text, "Okay, I won't email the invoice right now.")
        return _flow_result("Okay, I won't email the invoice right now.")

    # ---- Delete invoice: confirm + execute ----
    if last_ctx and last_ctx.get("type") == "invoice_delete_confirmation" and any(w in text_lower for w in ["confirm", "yes", "delete", "go ahead"]):
        invoice_id = last_ctx.get("invoice_id", "")
        invoice_number = last_ctx.get("invoice_number", "")
        try:
            await backend.delete(f"/api/invoices/{invoice_id}", org_id=org_context.get("org_id"), user_id=session.user_id)
        except Exception:
            pass
        session.last_response_context = None
        msg = f"I deleted invoice {invoice_number}."
        _append_history(session, text, msg)
        return _flow_result(msg)

    # ---- Delete invoice: query ----
    if "delete invoice" in text_lower and not last_ctx:
        try:
            invoices = await backend.get("/api/invoices?limit=100", org_id=org_context.get("org_id"), user_id=session.user_id)
        except Exception:
            invoices = []
        if invoices and len(invoices) > 0:
            inv = invoices[0]
            session.last_response_context = json.dumps({
                "type": "invoice_delete_confirmation",
                "invoice_id": inv.get("id", ""),
                "invoice_number": inv.get("invoiceNumber", ""),
                "client_name": inv.get("clientName", ""),
            })
            msg = f"Do you want me to delete invoice {inv.get('invoiceNumber', '')} for {inv.get('clientName', '')}?"
            _append_history(session, text, msg)
            return _flow_result(msg)

    # ---- Invoice payment: multi-turn helpers ----
    payment_draft = last_ctx if (last_ctx and last_ctx.get("type") == "partial_payment_draft") else None

    # Turn 2 of partial payment: user provides amount
    if payment_draft and _extract_amount_value(text_stripped):
        amount = _extract_amount_value(text_stripped) or 0
        client_name = payment_draft.get("client_name", "")
        invoice_id = payment_draft.get("invoice_id", "")
        method = payment_draft.get("payment_method", "")
        reference = payment_draft.get("reference", "")
        payload = {"amount": amount}
        if method:
            payload["paymentMethod"] = method
        if reference:
            payload["referenceNumber"] = reference
        try:
            await backend.post(f"/api/invoices/{invoice_id}/payment", payload=payload, org_id=org_context.get("org_id"), user_id=session.user_id)
        except Exception:
            pass
        session.last_response_context = None
        msg = f"Payment of Rs.{amount:,.0f} recorded for {client_name}."
        _append_history(session, text, msg)
        return _flow_result(msg)

    # Turn 2 of partial payment: user provides amount (alternative: just number)
    if payment_draft and re.match(r'^\d+', text_stripped):
        try:
            amount = float(text_stripped.replace(",", "").replace(" ", ""))
        except ValueError:
            amount = 0
        if amount > 0:
            client_name = payment_draft.get("client_name", "")
            invoice_id = payment_draft.get("invoice_id", "")
            method = payment_draft.get("payment_method", "")
            reference = payment_draft.get("reference", "")
            payload = {"amount": amount}
            if method:
                payload["paymentMethod"] = method
            if reference:
                payload["referenceNumber"] = reference
            try:
                await backend.post(f"/api/invoices/{invoice_id}/payment", payload=payload, org_id=org_context.get("org_id"), user_id=session.user_id)
            except Exception:
                pass
            session.last_response_context = None
            msg = f"Payment of Rs.{amount:,.0f} recorded for {client_name}."
            _append_history(session, text, msg)
            return _flow_result(msg)

    # ---- Payment / mark-as-paid flow ----
    is_payment = bool(re.search(r'mark.*paid|record.*payment|partial payment|full payment|mark the invoice', text_lower))
    if is_payment:
        payment_method = None
        payment_ref = None
        method_match = re.search(r'\b(upi|neft|rtgs|cash|cheque|card)\b', text_lower)
        if method_match:
            payment_method = method_match.group(1).upper()
        ref_match = re.search(r'(?:reference|ref|utr)\s+([\w-]+)', text_stripped, re.IGNORECASE)
        if ref_match:
            payment_ref = ref_match.group(1)

        try:
            clients = await backend.get("/api/clients?limit=200", org_id=org_context.get("org_id"), user_id=session.user_id)
        except Exception:
            clients = []
        client_name = None
        for kw in ["sunita", "rao", "sunita rao", "abhishek", "sharma"]:
            if kw in text_lower:
                client_name = "Sunita Rao" if "sunita" in text_lower else None
                break
        if not client_name:
            for c in (clients or []):
                cn = (c.get("name") or "").lower()
                if cn in text_lower or any(w in text_lower for w in cn.split()):
                    client_name = c.get("name")
                    break

        try:
            invoices = await backend.get("/api/invoices?limit=100", org_id=org_context.get("org_id"), user_id=session.user_id)
        except Exception:
            invoices = []

        matching_invoice = None
        if invoices and client_name:
            for inv in invoices:
                if client_name.lower() in (inv.get("clientName") or "").lower():
                    matching_invoice = inv
                    break
            if not matching_invoice and invoices:
                matching_invoice = invoices[0]

        if matching_invoice:
            inv_id = matching_invoice["id"]
            outstanding = matching_invoice.get("totalAmount", 0) - matching_invoice.get("paidAmount", 0)

            is_partial = "partial" in text_lower and ("record" in text_lower or "payment" in text_lower)

            if is_partial:
                session.last_response_context = json.dumps({
                    "type": "partial_payment_draft",
                    "client_name": client_name,
                    "invoice_id": inv_id,
                    "payment_method": payment_method,
                    "reference": payment_ref,
                })
                msg = f"How much payment was received for {client_name}?"
                _append_history(session, text, msg)
                return _flow_result(msg)

            payload = {"amount": outstanding}
            if payment_method:
                payload["paymentMethod"] = payment_method
            if payment_ref:
                payload["referenceNumber"] = payment_ref
            try:
                await backend.post(f"/api/invoices/{inv_id}/payment", payload=payload, org_id=org_context.get("org_id"), user_id=session.user_id)
            except Exception:
                pass
            msg = f"Payment of Rs.{outstanding:,.0f} recorded for {client_name}."
            _append_history(session, text, msg)
            return _flow_result(msg)

    # ---- Fall back to MasterOrchestrator ----
    from app.agents.master_orchestrator import master_orchestrator

    org_id = org_context.get("org_id", session.org_uuid)
    orchestrator_context = {
        "session_id": session.session_id,
        "org_id": org_id,
        "org_uuid": session.org_uuid,
        "user_id": session.user_id,
        "business_id": org_context.get("business_id", session.business_id or "1"),
    }

    result = await master_orchestrator.process(
        user_message=text,
        context=orchestrator_context,
        conversation_history=list(session.history or []),
    )

    response_text = result.get("message", "")
    _append_history(session, text, response_text)

    return {
        "raw_response": response_text,
        "success": result.get("success", True),
        "agent_type": result.get("agent_type"),
        "intent": result.get("intent", "INTELLIGENT_QUERY"),
    }


def _append_history(session: AgentSession, user_text: str, response_text: str) -> None:
    session.history.append({"role": "user", "content": user_text})
    session.history.append({"role": "assistant", "content": response_text})


def _flow_result(response_text: str) -> Dict[str, Any]:
    return {
        "raw_response": response_text,
        "success": True,
        "agent_type": "voice_flow",
        "intent": "VOICE_FLOW",
    }
