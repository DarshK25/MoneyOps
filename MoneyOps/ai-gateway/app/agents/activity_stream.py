"""
Activity Stream - WebSocket/SSE publisher for real-time agent monitoring.
Publishes agent activities, alerts, and system events to connected dashboard clients.

Supports both WebSocket (primary) and Server-Sent Events (fallback).
"""
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import asyncio
import json

from app.schemas.heartbeat import ActivityEvent, ActivityType, Priority
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ActivityStream:
    """
    Manages real-time activity streaming to dashboard clients.
    - Maintains connected WebSocket connections
    - Publishes events to all subscribers
    - Maintains event history for new connections
    - Supports filtering by org_id, agent, event type
    """

    def __init__(self):
        self._subscribers: Dict[str, Set[Any]] = {}  # org_id -> set of WebSocket connections
        self._broadcast_subscribers: Set[Any] = set()  # global subscribers
        self._event_history: List[ActivityEvent] = []
        self._max_history = 100
        self._lock = asyncio.Lock()

    async def subscribe(self, websocket, org_id: Optional[str] = None):
        """Subscribe a WebSocket connection to events"""
        async with self._lock:
            if org_id:
                if org_id not in self._subscribers:
                    self._subscribers[org_id] = set()
                self._subscribers[org_id].add(websocket)
            else:
                self._broadcast_subscribers.add(websocket)

        # Send recent history to new subscriber
        recent = self._event_history[-20:]
        for event in recent:
            if not org_id or event.org_id == org_id:
                try:
                    await websocket.send_json(event.model_dump(mode="json"))
                except Exception:
                    pass

        logger.info("activity_stream_subscribed", org_id=org_id)

    async def unsubscribe(self, websocket, org_id: Optional[str] = None):
        """Unsubscribe a WebSocket connection"""
        async with self._lock:
            if org_id and org_id in self._subscribers:
                self._subscribers[org_id].discard(websocket)
                if not self._subscribers[org_id]:
                    del self._subscribers[org_id]
            else:
                self._broadcast_subscribers.discard(websocket)

    async def publish(
        self,
        event_type: ActivityType,
        agent: str,
        org_id: str,
        title: str,
        message: str,
        priority: Priority = Priority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Publish an activity event to all relevant subscribers"""
        event = ActivityEvent(
            type=event_type,
            agent=agent,
            org_id=org_id,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
        )

        async with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]

        await self._send_event(event)

    async def _send_event(self, event: ActivityEvent):
        """Send event to all matching subscribers"""
        event_json = event.model_dump(mode="json")

        # Send to org-specific subscribers
        org_subscribers = self._subscribers.get(event.org_id, set())
        disconnected = set()
        for ws in org_subscribers:
            try:
                await ws.send_json(event_json)
            except Exception:
                disconnected.add(ws)

        # Clean up disconnected subscribers
        if disconnected:
            async with self._lock:
                self._subscribers[event.org_id] -= disconnected

        # Send to broadcast subscribers
        disconnected = set()
        for ws in self._broadcast_subscribers:
            try:
                await ws.send_json(event_json)
            except Exception:
                disconnected.add(ws)

        if disconnected:
            async with self._lock:
                self._broadcast_subscribers -= disconnected

    async def get_events(
        self,
        org_id: Optional[str] = None,
        agent: Optional[str] = None,
        event_type: Optional[ActivityType] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get recent events with optional filtering"""
        events = self._event_history

        if org_id:
            events = [e for e in events if e.org_id == org_id]
        if agent:
            events = [e for e in events if e.agent == agent]
        if event_type:
            events = [e for e in events if e.type == event_type]

        return [e.model_dump(mode="json") for e in events[-limit:]]

    async def get_active_agents(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of agents that have recently published events"""
        events = self._event_history
        if org_id:
            events = [e for e in events if e.org_id == org_id]

        agent_activity = {}
        for event in events[-50:]:
            if event.agent not in agent_activity:
                agent_activity[event.agent] = {
                    "agent": event.agent,
                    "last_event": event.timestamp,
                    "event_count": 0,
                    "last_event_type": event.type,
                }
            agent_activity[event.agent]["event_count"] += 1
            agent_activity[event.agent]["last_event"] = event.timestamp
            agent_activity[event.agent]["last_event_type"] = event.type

        return list(agent_activity.values())

    async def get_summary(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of recent activity"""
        events = self._event_history
        if org_id:
            events = [e for e in events if e.org_id == org_id]

        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_events = [e for e in events if e.timestamp.strftime("%Y-%m-%d") == today]

        return {
            "total_events": len(events),
            "today_events": len(today_events),
            "active_agents": len(set(e.agent for e in today_events)),
            "critical_alerts": len([e for e in today_events if e.priority == Priority.CRITICAL]),
            "subscribers": sum(len(s) for s in self._subscribers.values()) + len(self._broadcast_subscribers),
        }

    def generate_sse_event(self, event: ActivityEvent) -> str:
        """Format event as Server-Sent Event data"""
        data = json.dumps(event.model_dump(mode="json"), default=str)
        return f"event: activity\ndata: {data}\n\n"


activity_stream = ActivityStream()
