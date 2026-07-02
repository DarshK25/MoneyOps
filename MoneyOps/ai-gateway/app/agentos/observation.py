from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import time
import uuid
import json

from app.agentos.types import AuditRecord
from app.agentos.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ObservationRegistry:
    def __init__(self):
        self._records: List[AuditRecord] = []
        self._max_records = 1000

    async def record(self, agent_name: str, action: str,
                     decision_id: str = "", reasoning: str = "",
                     data_used: Optional[Dict[str, Any]] = None,
                     expected_outcome: str = "", actual_outcome: str = "",
                     execution_duration_ms: float = 0.0,
                     success: bool = True, error: Optional[str] = None,
                     retries: int = 0,
                     agent_interactions: Optional[List[str]] = None,
                     org_id: str = "",
                     message_ids: Optional[List[str]] = None) -> str:
        record = AuditRecord(
            agent_name=agent_name,
            action=action,
            decision_id=decision_id,
            reasoning=reasoning,
            data_used=data_used or {},
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            execution_duration_ms=execution_duration_ms,
            success=success,
            error=error,
            retries=retries,
            agent_interactions=agent_interactions or [],
            org_id=org_id,
            message_ids=message_ids or [],
        )
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

        agent_memory.store_outcome(agent_name, record.record_id, record.to_dict())

        from app.agents.activity_stream import activity_stream, ActivityType, Priority
        event_type = ActivityType.AGENT_CYCLE if success else ActivityType.ALERT
        priority = Priority.LOW if success else Priority.HIGH
        await activity_stream.publish(
            event_type=event_type,
            agent=agent_name,
            org_id=org_id or "system",
            title=f"{agent_name}: {action}",
            message=actual_outcome or expected_outcome,
            priority=priority,
            data={
                "record_id": record.record_id,
                "action": action,
                "success": success,
                "duration_ms": execution_duration_ms,
                "error": error,
            },
        )
        return record.record_id

    def get_records(self, agent_name: Optional[str] = None,
                    limit: int = 50,
                    success_only: Optional[bool] = None) -> List[Dict[str, Any]]:
        records = list(self._records)
        if agent_name:
            records = [r for r in records if r.agent_name == agent_name]
        if success_only is not None:
            records = [r for r in records if r.success == success_only]
        return [r.to_dict() for r in records[-limit:]]

    def get_agent_summary(self, agent_name: str) -> Dict[str, Any]:
        records = [r for r in self._records if r.agent_name == agent_name]
        if not records:
            return {"agent": agent_name, "total_actions": 0}
        total = len(records)
        successes = sum(1 for r in records if r.success)
        failures = total - successes
        avg_duration = sum(r.execution_duration_ms for r in records) / max(total, 1)
        return {
            "agent": agent_name,
            "total_actions": total,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / max(total, 1)) * 100,
            "avg_duration_ms": avg_duration,
            "last_action": records[-1].to_dict() if records else None,
        }

    def get_system_summary(self) -> Dict[str, Any]:
        agents = set(r.agent_name for r in self._records)
        return {
            "total_records": len(self._records),
            "active_agents": list(agents),
            "agent_summaries": {agent: self.get_agent_summary(agent) for agent in agents},
            "total_successes": sum(1 for r in self._records if r.success),
            "total_failures": sum(1 for r in self._records if not r.success),
            "total_errors": sum(1 for r in self._records if r.error),
        }


audit_registry = ObservationRegistry()
