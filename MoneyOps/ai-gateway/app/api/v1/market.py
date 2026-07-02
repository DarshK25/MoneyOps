from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(tags=["Market"])


@router.get("/market/intelligence")
async def market_intelligence(
    org_uuid: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    return {
        "success": True,
        "cached": False,
        "data": [],
        "highlights": [],
        "message": "Market intelligence is available through the AI agent. Ask your agent for market insights.",
    }
