from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import time

from app.agentos.types import AgentRole, Decision, DecisionStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentRules:
    max_iterations: int = 5
    max_execution_time_ms: int = 30000
    max_concurrent_actions: int = 3
    required_approval_roles: List[str] = field(default_factory=list)
    blocked_actions: List[str] = field(default_factory=list)
    always_log: bool = True
    require_health_check: bool = True


DEFAULT_RULES: Dict[AgentRole, AgentRules] = {
    AgentRole.FINANCE_OPS: AgentRules(
        max_iterations=5,
        max_execution_time_ms=30000,
        blocked_actions=[],
        required_approval_roles=["ceo"],
    ),
    AgentRole.COMPLIANCE: AgentRules(
        max_iterations=3,
        max_execution_time_ms=15000,
        blocked_actions=["file_gst_return", "submit_tax_filing"],
        required_approval_roles=["ceo"],
    ),
    AgentRole.COLLECTIONS: AgentRules(
        max_iterations=10,
        max_execution_time_ms=20000,
        blocked_actions=[],
        required_approval_roles=[],
    ),
    AgentRole.TREDS: AgentRules(
        max_iterations=5,
        max_execution_time_ms=60000,
        blocked_actions=[],
        required_approval_roles=["ceo"],
    ),
    AgentRole.GROWTH: AgentRules(
        max_iterations=5,
        max_execution_time_ms=20000,
        blocked_actions=[],
        required_approval_roles=[],
    ),
    AgentRole.CEO: AgentRules(
        max_iterations=10,
        max_execution_time_ms=60000,
        blocked_actions=[],
        required_approval_roles=[],
    ),
}


class Governance:
    def __init__(self):
        self._rules: Dict[str, AgentRules] = {}
        self._custom_validators: Dict[str, List[Callable]] = {}
        self._denied_actions: List[Dict[str, Any]] = []

    def register_agent(self, agent_name: str, role: AgentRole,
                       custom_rules: Optional[AgentRules] = None):
        rules = custom_rules or DEFAULT_RULES.get(role, AgentRules())
        self._rules[agent_name] = rules
        logger.info("governance_agent_registered", agent=agent_name, role=role.value)

    def add_validator(self, agent_name: str, validator: Callable):
        if agent_name not in self._custom_validators:
            self._custom_validators[agent_name] = []
        self._custom_validators[agent_name].append(validator)

    async def approve(self, agent_name: str, action: str,
                      context: Dict[str, Any],
                      decision: Decision) -> bool:
        rules = self._rules.get(agent_name)
        if rules is None:
            logger.warning("governance_no_rules", agent=agent_name)
            return True

        action_lower = action.lower()
        for blocked in rules.blocked_actions:
            if blocked in action_lower:
                decision.status = DecisionStatus.BLOCKED
                decision.reasoning += f" | BLOCKED by governance: action '{blocked}' is not permitted for {agent_name}"
                self._denied_actions.append({
                    "agent": agent_name, "action": action,
                    "reason": f"Blocked action: {blocked}", "timestamp": time.time(),
                })
                logger.warning("governance_action_blocked", agent=agent_name, action=action, blocked_rule=blocked)
                return False

        custom_validators = self._custom_validators.get(agent_name, [])
        for validator in custom_validators:
            try:
                result = validator(agent_name, action, context, decision)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    return False
            except Exception as e:
                logger.error("governance_validator_error", agent=agent_name, error=str(e))
                decision.status = DecisionStatus.FAILED
                decision.reasoning += f" | Validator error: {str(e)}"
                return False

        if rules.require_health_check:
            if decision.score < 40:
                logger.info("governance_health_check_failed", agent=agent_name, action=action, score=decision.score)
                if rules.required_approval_roles:
                    decision.status = DecisionStatus.ESCALATED
                    decision.reasoning += " | Health check failed - escalated for CEO approval"
                    return False

        return True

    def get_rules(self, agent_name: str) -> Optional[AgentRules]:
        return self._rules.get(agent_name)

    def get_denied_actions(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._denied_actions[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "registered_agents": list(self._rules.keys()),
            "total_denied": len(self._denied_actions),
            "rules_summary": {
                name: {
                    "max_iterations": rules.max_iterations,
                    "max_execution_time_ms": rules.max_execution_time_ms,
                    "blocked_actions": rules.blocked_actions,
                    "required_approval_roles": rules.required_approval_roles,
                }
                for name, rules in self._rules.items()
            },
        }


import asyncio
governance = Governance()
