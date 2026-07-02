"""
True Multi-Agent Orchestration API - Main brain endpoint
Provides unified access to all collaborative executor agents.
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio

from app.agents.master_orchestrator import master_orchestrator
from app.agents.heartbeat import heartbeat_scheduler
from app.agents.activity_stream import activity_stream
from app.agents.base_executor import FinanceExecutor, ComplianceExecutor, CollectionsExecutor, TReDSExecutor
from app.agents.growth import GrowthExecutor
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["True Multi-Agent"])


class AgentRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(
        default="default", description="Session ID for conversation continuity"
    )
    org_id: str = Field(..., description="Organization ID")
    user_id: Optional[str] = Field(None, description="User ID")
    business_id: Optional[str] = Field("1", description="Business ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class AgentResponseModel(BaseModel):
    message: str
    success: bool
    agent_type: str = "executor_orchestrator"
    executors_used: Optional[List[str]] = None
    iterations: Optional[int] = None
    ui_event: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    agents_involved: Optional[List[str]] = None
    delegation_chain: Optional[List[str]] = None
    business_goals: Optional[List[Dict[str, Any]]] = None
    goal_aligned: Optional[bool] = None
    goal_progress_pct: Optional[float] = None
    cross_agent_data: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=AgentResponseModel)
async def chat_with_agent(request: AgentRequest):
    """
    True agent-native execution endpoint.
    Executors make REAL API calls to complete financial operations.
    """
    result = await master_orchestrator.process(
        user_message=request.message,
        context={
            "org_id": request.org_id,
            "user_id": request.user_id,
            "business_id": request.business_id or "1",
            "session_id": request.session_id,
            **(request.context or {}),
        },
    )

    return AgentResponseModel(
        message=result["message"],
        success=result["success"],
        agent_type=result.get("agent_type") or "executor_orchestrator",
        executors_used=[result.get("executor")] if result.get("executor") else [],
        agents_involved=result.get("agents_involved"),
        delegation_chain=result.get("delegation_chain"),
        business_goals=result.get("business_goals"),
        goal_aligned=result.get("goal_aligned"),
        goal_progress_pct=result.get("goal_progress_pct"),
        cross_agent_data=result.get("cross_agent_data"),
        iterations=0,
        errors=result.get("errors", []),
        ui_event={
            "type": "execution_result",
            "operation": result.get("data", {}).get("operation") if isinstance(result.get("data"), dict) else None,
            "data": result.get("data"),
        },
    )


@router.get("/health")
async def health_check():
    """Check orchestrator health and list available executors"""
    return {
        "status": "healthy",
        "orchestrator": "executor_orchestrator",
        "executors": [role.value for role in master_orchestrator.executors.keys()],
        "llm_providers": ["groq", "cerebras", "gemini"],
    }


@router.post("/heartbeat/run")
async def run_heartbeat_now(org_id: str = Query(...), user_id: Optional[str] = Query(None)):
    """Run autonomous agent cycles for one organization on demand."""
    if not heartbeat_scheduler.executors:
        heartbeat_scheduler.register_executor("finance_executor", FinanceExecutor())
        heartbeat_scheduler.register_executor("compliance_executor", ComplianceExecutor())
        heartbeat_scheduler.register_executor("collections_executor", CollectionsExecutor())
        heartbeat_scheduler.register_executor("treds_executor", TReDSExecutor())
        heartbeat_scheduler.register_executor("growth_executor", GrowthExecutor())

    results = {}
    for name, executor in heartbeat_scheduler.executors.items():
        result = await executor.run_autonomous_cycle(org_id=org_id, user_id=user_id)
        results[name] = result.to_dict() if hasattr(result, "to_dict") else result

    return {"success": True, "org_id": org_id, "results": results}


@router.post("/briefing/morning")
async def generate_morning_briefing(org_id: str = Query(...), user_id: Optional[str] = Query(None)):
    """Generate CEO morning briefing for one organization."""
    return await master_orchestrator.generate_morning_briefing(org_id=org_id, user_id=user_id)


@router.post("/briefing/evening")
async def generate_evening_summary(org_id: str = Query(...), user_id: Optional[str] = Query(None)):
    """Generate CEO evening summary for one organization."""
    return await master_orchestrator.generate_evening_summary(org_id=org_id, user_id=user_id)


@router.get("/activity")
async def get_activity(org_id: Optional[str] = None, limit: int = 50):
    """Recent live agent activity for dashboard polling."""
    return {
        "events": await activity_stream.get_events(org_id=org_id, limit=limit),
        "summary": await activity_stream.get_summary(org_id=org_id),
    }


@router.websocket("/activity/ws")
async def activity_websocket(websocket: WebSocket, org_id: Optional[str] = None):
    """WebSocket stream for live agent activity."""
    await websocket.accept()
    await activity_stream.subscribe(websocket, org_id=org_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await activity_stream.unsubscribe(websocket, org_id=org_id)


@router.get("/activity/sse")
async def activity_sse(org_id: Optional[str] = None):
    """Server-sent events fallback for live agent activity."""

    async def stream():
        last_seen = 0
        while True:
            events = await activity_stream.get_events(org_id=org_id, limit=100)
            for event in events[last_seen:]:
                yield f"event: activity\ndata: {event}\n\n"
            last_seen = len(events)
            await asyncio.sleep(2)

    return StreamingResponse(stream(), media_type="text/event-stream")
