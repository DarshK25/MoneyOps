from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import time
import json
import math

from app.agentos.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LearningRecord:
    agent: str
    action: str
    context: Dict[str, Any]
    outcome_score: float
    success: bool
    execution_time_ms: float
    decision_score: float
    timestamp: float = field(default_factory=time.time)


class AgentLearning:
    """Outcome-based learning system that improves agent decision-making over time.

    Tracks every action's outcome and builds pattern models per agent.
    """

    def __init__(self):
        self._cache: Dict[str, List[LearningRecord]] = {}

    def record_outcome(self, agent: str, action: str,
                        context: Dict[str, Any],
                        outcome_score: float, success: bool,
                        execution_time_ms: float,
                        decision_score: float):
        record = LearningRecord(
            agent=agent,
            action=action,
            context=context,
            outcome_score=outcome_score,
            success=success,
            execution_time_ms=execution_time_ms,
            decision_score=decision_score,
        )
        if agent not in self._cache:
            self._cache[agent] = []
        self._cache[agent].append(record)
        if len(self._cache[agent]) > 500:
            self._cache[agent] = self._cache[agent][-500:]
        agent_memory.store_long_term(agent, f"learning:{action}:{record.timestamp}", record.__dict__)

    def get_agent_performance(self, agent: str) -> Dict[str, Any]:
        records = self._cache.get(agent, [])
        if not records:
            stored = agent_memory.get_long_term(agent, "learning:stats")
            return stored or {"agent": agent, "total_actions": 0, "avg_success_rate": 0}
        total = len(records)
        successes = sum(1 for r in records if r.success)
        avg_outcome = sum(r.outcome_score for r in records) / total
        avg_decision_score = sum(r.decision_score for r in records) / total
        avg_exec_time = sum(r.execution_time_ms for r in records) / total
        return {
            "agent": agent,
            "total_actions": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": (successes / total) * 100,
            "avg_outcome_score": round(avg_outcome, 2),
            "avg_decision_score": round(avg_decision_score, 2),
            "avg_execution_time_ms": round(avg_exec_time, 2),
        }

    def get_action_recommendation(self, agent: str, action: str) -> Dict[str, Any]:
        records = [r for r in self._cache.get(agent, []) if r.action == action]
        if not records:
            # Try from MongoDB
            stored = agent_memory.get_long_term(agent, f"learning:rec:{action}")
            return stored or {
                "action": action,
                "confidence": 0,
                "sample_size": 0,
                "recommended": True,
            }
        total = len(records)
        successes = sum(1 for r in records if r.success)
        avg_outcome = sum(r.outcome_score for r in records) / total
        avg_exec_time = sum(r.execution_time_ms for r in records) / total
        confidence = min(1.0, (successes / total) * (1 - 1 / math.sqrt(total + 1)))
        rec = {
            "action": action,
            "success_rate": (successes / total) * 100,
            "avg_outcome_score": round(avg_outcome, 2),
            "avg_execution_time_ms": round(avg_exec_time, 2),
            "sample_size": total,
            "confidence": round(confidence, 3),
            "recommended": confidence > 0.5,
        }
        agent_memory.store_long_term(agent, f"learning:rec:{action}", rec)
        return rec

    def get_action_patterns(self, agent: str) -> Dict[str, Any]:
        records = self._cache.get(agent, [])
        if not records:
            return {"agent": agent, "patterns": []}
        action_groups: Dict[str, List[LearningRecord]] = {}
        for r in records:
            if r.action not in action_groups:
                action_groups[r.action] = []
            action_groups[r.action].append(r)
        patterns = []
        for action, group in action_groups.items():
            total = len(group)
            successes = sum(1 for r in group if r.success)
            avg_outcome = sum(r.outcome_score for r in group) / total
            avg_decision = sum(r.decision_score for r in group) / total
            patterns.append({
                "action": action,
                "frequency": total,
                "success_rate": round((successes / total) * 100, 1),
                "avg_outcome": round(avg_outcome, 2),
                "avg_decision_score": round(avg_decision, 2),
                "trend": "improving" if avg_outcome > avg_decision else "declining",
            })
        patterns.sort(key=lambda p: p["frequency"], reverse=True)
        result = {"agent": agent, "patterns": patterns}
        agent_memory.store_long_term(agent, "learning:patterns", result)
        return result

    def get_learning_summary(self) -> Dict[str, Any]:
        agents = list(self._cache.keys())
        return {
            "agents_tracked": agents,
            "total_records": sum(len(v) for v in self._cache.values()),
            "agent_performances": {a: self.get_agent_performance(a) for a in agents},
        }


agent_learning = AgentLearning()
