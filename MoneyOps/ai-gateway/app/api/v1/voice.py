"""
Voice API endpoint.
Processes voice input via moneyops_agent — no classify, no route, no entity extraction.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import time
import uuid

from app.voice_processor import voice_processor, VoiceContext
from app.utils.logger import get_logger
from app.config import settings
from app.adapters.backend_adapter import normalize_business_id
from app.state.session_manager import session_manager

try:
    from livekit.api.access_token import AccessToken, VideoGrants

    _LIVEKIT_AVAILABLE = True
except ImportError:
    _LIVEKIT_AVAILABLE = False

router = APIRouter()
logger = get_logger(__name__)


class VoiceProcessRequest(BaseModel):
    text: str
    user_id: str
    org_id: str
    session_id: str
    business_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)


class VoiceDialogResponseRequest(BaseModel):
    session_id: str
    dialog_id: str
    fields: Dict[str, Any] = Field(default_factory=dict)


@router.get("/voice/token")
async def get_voice_token(
    user_id: str = "user",
    org_id: Optional[str] = None,
    room_name: Optional[str] = None,
):
    """Generate a LiveKit access token for voice chat."""
    try:
        if not _LIVEKIT_AVAILABLE:
            raise HTTPException(status_code=503, detail="LiveKit SDK not installed")

        if not settings.LIVEKIT_API_KEY or not settings.LIVEKIT_API_SECRET:
            raise HTTPException(status_code=500, detail="LiveKit credentials missing")

        actual_room = room_name or f"voice-{user_id}-{str(uuid.uuid4())[:8]}"

        token = (
            AccessToken(settings.LIVEKIT_API_KEY, settings.LIVEKIT_API_SECRET)
            .with_identity(user_id)
            .with_metadata(
                f'{{"user_id":"{user_id}","org_id":"{org_id or "default"}","room":"{actual_room}"}}'
            )
            .with_grants(VideoGrants(room_join=True, room=actual_room))
        )

        return {
            "token": token.to_jwt(),
            "url": settings.LIVEKIT_URL,
            "room_name": actual_room,
        }
    except Exception as e:
        logger.error("token_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice/process")
async def process_voice(request: VoiceProcessRequest, fastapi_request: Request):
    """
    Main voice processing pipeline.
    Routes directly to moneyops_agent via voice_processor — no classify/extract/route.
    """
    try:
        logger.info("voice_process_start", 
                    session_id=request.session_id, 
                    user_id=request.user_id,
                    text_preview=request.text[:50])

        # Fragment guard - single words that are meaningless
        fragment_words = {"and", "or", "the", "a", "is", "to", "of", "in", "it", "i", "you", "we"}
        if len(request.text.split()) <= 1 and request.text.lower().strip() in fragment_words:
            logger.info("fragment_ignored", text=request.text)
            return {
                "response_text": "",
                "intent": "FRAGMENT",
                "success": True,
                "stage": "COLLECTING",
            }

        resolved_business_id = normalize_business_id(
            request.business_id or request.context.get("business_id") or request.context.get("businessId") or "1"
        )

        context = VoiceContext(
            session_id=request.session_id,
            user_id=request.user_id,
            org_uuid=request.org_id,
            business_id=str(resolved_business_id),
            user_org_id=request.org_id,
            raw_text=request.text,
            history=request.conversation_history,
        )

        result = await voice_processor.process(request.text, context)

        # Extract info from result
        response_text = result.get("response_text", "")
        tool_called = result.get("tool_called", "")
        
        # Determine stage based on result
        stage = "EXECUTED"
        if not result.get("success", True):
            stage = "FAILED"
        
        # Map tool to intent
        TOOL_TO_INTENT = {
            "create_invoice": "INVOICE_CREATE",
            "get_invoices": "INVOICE_QUERY",
            "record_payment": "PAYMENT_RECORD",
            "create_client": "CLIENT_CREATE",
            "get_clients": "CLIENT_QUERY",
            "check_compliance": "COMPLIANCE",
            "get_business_health_score": "BUSINESS_HEALTH",
            "get_daily_briefing": "DAILY_BRIEFING",
            "get_cash_flow_forecast": "CASH_FLOW",
            "send_collection_reminder": "COLLECTION",
            "send_invoice_email": "INVOICE_SEND",
            "search_market_intelligence": "MARKET_INTEL",
            "record_expense": "EXPENSE_RECORD",
            "get_overdue_action_plan": "OVERDUE_PLAN",
            "get_financial_summary": "FINANCIAL_SUMMARY",
        }
        intent = TOOL_TO_INTENT.get(tool_called, "INTELLIGENT_QUERY")

        logger.info("voice_process_complete",
                    session_id=request.session_id,
                    tool_called=tool_called,
                    intent=intent,
                    success=result.get("success", True))

        # Always return 200 to prevent voice service retries
        return {
            "response_text": response_text if response_text is not None else "I've processed that.",
            "intent": intent,
            "confidence": 0.9,
            "success": result.get("success", True),
            "stage": stage,
            "tool_called": tool_called,
            "needs_more_info": False,
            "raw_response": result.get("raw_response", ""),
            "ui_event": result.get("ui_event"),
        }

    except Exception as e:
        logger.error("voice_process_failed", error=str(e), exc_info=True)
        # Always return 200 even on errors — returning 500 causes voice service to retry
        return {
            "response_text": "I hit a snag on that request. Please try again.",
            "success": False,
            "intent": "ERROR",
            "confidence": 0.0,
            "stage": "FAILED",
            "needs_more_info": False,
        }


@router.post("/voice/dialog-response")
async def process_voice_dialog_response(request: VoiceDialogResponseRequest):
    try:
        session = session_manager.get_session(request.session_id)
        fields = dict(request.fields or {})

        if request.dialog_id == "invoice_preview_form":
            draft = dict(session.invoice_draft_data or {})
            if fields.get("client_name"):
                draft["client_name"] = str(fields.get("client_name")).strip()
            if fields.get("client_id"):
                draft["client_id"] = str(fields.get("client_id")).strip()
            if fields.get("issue_date"):
                draft["issue_date"] = str(fields.get("issue_date")).strip()
            if fields.get("due_date"):
                draft["due_date"] = str(fields.get("due_date")).strip()
            if fields.get("notes") is not None:
                draft["notes"] = str(fields.get("notes")).strip()
            if fields.get("invoice_items_text") is not None:
                from app.agents.voice_helpers import _parse_invoice_items_text
                parsed_items = _parse_invoice_items_text(str(fields.get("invoice_items_text") or ""))
                if parsed_items:
                    draft["line_items"] = parsed_items

            session.invoice_draft_data = draft
            session_manager.save_session(session)
            from app.agents.voice_helpers import _build_invoice_preview_dialog_ui_event
            return {
                "success": True,
                "message": "Invoice draft updated. You can keep editing it or continue by voice.",
                "ui_event": _build_invoice_preview_dialog_ui_event(request.session_id, draft),
            }

        if request.dialog_id == "client_preview_form":
            draft = dict(session.client_draft or {})
            if fields.get("name") is not None:
                draft["name"] = str(fields.get("name") or "").strip()
            if fields.get("email") is not None:
                draft["email"] = str(fields.get("email") or "").strip()
            phone_value = fields.get("phoneNumber", fields.get("phone"))
            if phone_value is not None:
                draft["phone"] = str(phone_value or "").strip()
            company_value = fields.get("company_name", fields.get("company"))
            if company_value is not None:
                draft["company_name"] = str(company_value or "").strip()
            if fields.get("gstin") is not None:
                gstin = str(fields.get("gstin") or "").strip().upper()
                if gstin:
                    draft["gstin"] = gstin
                    draft.pop("_gstin_skipped", None)
                else:
                    draft.pop("gstin", None)
            if fields.get("notes") is not None:
                draft["notes"] = str(fields.get("notes") or "").strip()
            team_code_value = fields.get("team_code", fields.get("teamActionCode"))
            if team_code_value is not None:
                draft["team_code"] = str(team_code_value or "").strip()

            session.client_draft = draft
            session_manager.save_session(session)
            from app.agents.voice_helpers import _build_client_form_ui_event
            return {
                "success": True,
                "message": "Client draft updated. Your typed corrections will be used for the next voice step.",
                "ui_event": _build_client_form_ui_event(draft),
            }

        return {
            "success": False,
            "message": f"Unsupported dialog: {request.dialog_id}",
        }
    except Exception as e:
        logger.error("voice_dialog_response_failed", error=str(e), exc_info=True)
        return {
            "success": False,
            "message": "I couldn't update that draft right now.",
        }


class InvoiceStage(str, Enum):
    COLLECT_CLIENT = "COLLECT_CLIENT"
    COLLECT_AMOUNT = "COLLECT_AMOUNT"
    COLLECT_DUE_DATE = "COLLECT_DUE_DATE"
    CONFIRMATION = "CONFIRMATION"
    EXECUTED = "EXECUTED"


@dataclass
class BaseDraftContext:
    intent_value: str
    stage_attempt_count: int = 0
    last_question_asked: Optional[str] = None
    failed_turn_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class InvoiceDraft(BaseDraftContext):
    stage: InvoiceStage = InvoiceStage.COLLECT_CLIENT
    eager_validation_done: bool = False
    client_name: Optional[str] = None
    client_id: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    gst_percent: Optional[float] = None
    line_items: list = field(default_factory=list)

    def update(self, data: dict):
        if "client_name" in data:
            self.client_name = data["client_name"]
        if "client_id" in data:
            self.client_id = data["client_id"]
        if "amount" in data:
            self.amount = data["amount"]
        if "due_date" in data:
            self.due_date = data["due_date"]
        if "gst_percent" in data:
            self.gst_percent = data["gst_percent"]
        if "line_items" in data:
            self.line_items = data["line_items"]
        self._advance_stage()
        self.updated_at = time.time()

    def _advance_stage(self):
        if self.stage == InvoiceStage.COLLECT_CLIENT and self.client_name:
            self.stage = InvoiceStage.COLLECT_AMOUNT
        if self.stage == InvoiceStage.COLLECT_AMOUNT and self.amount is not None:
            self.stage = InvoiceStage.COLLECT_DUE_DATE
        if self.stage == InvoiceStage.COLLECT_DUE_DATE and self.due_date:
            self.stage = InvoiceStage.CONFIRMATION

    def is_complete_for_execution(self) -> bool:
        return all([self.client_name, self.amount is not None, self.due_date])


@dataclass
class ClientDraft(BaseDraftContext):
    onboarding_verified: bool = False
    presented_client_list: list = field(default_factory=list)


def sanitize_history(history: list) -> list:
    clean = []
    for turn in history:
        if isinstance(turn, dict):
            if turn.get("intent") == "ERROR":
                continue
            content = str(turn.get("content", turn.get("message", "")))
            if "trouble" in content.lower():
                continue
        clean.append(turn)
    return clean[-10:]


def should_break_multi_turn_lock(current_intent: str, new_intent: str, new_confidence: float, current_stage: str) -> bool:
    if current_stage in ("CONFIRMATION", "EXECUTED"):
        return False
    if new_confidence < 0.85:
        return False
    break_pairs = {
        "INVOICE_CREATE": "BALANCE_CHECK",
        "CLIENT_CREATE": "INVOICE_CREATE",
    }
    expected = break_pairs.get(current_intent)
    if expected and new_intent == expected:
        return True
    return False
