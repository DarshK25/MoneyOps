from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time
import uuid


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    ALERT = "alert"
    ESCALATION = "escalation"
    NEGOTIATION = "negotiation"
    PROPOSAL = "proposal"
    DECISION = "decision"
    CONFIRMATION = "confirmation"
    REJECTION = "rejection"
    QUERY = "query"
    QUERY_RESULT = "query_result"
    DELEGATION = "delegation"
    DELEGATION_RESULT = "delegation_result"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class MessageStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    PROCESSED = "processed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DecisionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AgentRole(str, Enum):
    FINANCE_OPS = "finance_ops"
    COMPLIANCE = "compliance"
    COLLECTIONS = "collections"
    TREDS = "treds"
    GROWTH = "growth"
    CEO = "ceo"
    VOICE = "voice"


@dataclass
class AgentMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender: str = ""
    receiver: str = ""
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    requested_action: str = ""
    expected_response: str = ""
    priority: int = 3
    status: MessageStatus = MessageStatus.PENDING
    correlation_id: str = ""
    org_id: str = ""
    session_id: str = ""
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value if isinstance(self.message_type, MessageType) else self.message_type,
            "sender": self.sender,
            "receiver": self.receiver,
            "timestamp": self.timestamp,
            "context": self.context,
            "payload": self.payload,
            "reasoning": self.reasoning,
            "requested_action": self.requested_action,
            "expected_response": self.expected_response,
            "priority": self.priority,
            "status": self.status.value if isinstance(self.status, MessageStatus) else self.status,
            "correlation_id": self.correlation_id,
            "org_id": self.org_id,
            "session_id": self.session_id,
            "error": self.error,
        }


@dataclass
class Decision:
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    action: str = ""
    reasoning: str = ""
    score: float = 0.0
    status: DecisionStatus = DecisionStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    business_health: Dict[str, Any] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    expected_benefit: str = ""
    estimated_cost: str = ""
    confidence: float = 0.0
    org_id: str = ""
    timestamp: float = field(default_factory=time.time)
    outcome: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "reasoning": self.reasoning,
            "score": self.score,
            "status": self.status.value if isinstance(self.status, DecisionStatus) else self.status,
            "context": self.context,
            "business_health": self.business_health,
            "risks": self.risks,
            "alternatives": self.alternatives,
            "expected_benefit": self.expected_benefit,
            "estimated_cost": self.estimated_cost,
            "confidence": self.confidence,
            "org_id": self.org_id,
            "timestamp": self.timestamp,
            "outcome": self.outcome,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class AuditRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    action: str = ""
    decision_id: str = ""
    reasoning: str = ""
    data_used: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = ""
    actual_outcome: str = ""
    execution_duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    retries: int = 0
    agent_interactions: List[str] = field(default_factory=list)
    org_id: str = ""
    timestamp: float = field(default_factory=time.time)
    message_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "decision_id": self.decision_id,
            "reasoning": self.reasoning,
            "data_used": self.data_used,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "execution_duration_ms": self.execution_duration_ms,
            "success": self.success,
            "error": self.error,
            "retries": self.retries,
            "agent_interactions": self.agent_interactions,
            "org_id": self.org_id,
            "timestamp": self.timestamp,
            "message_ids": self.message_ids,
        }
