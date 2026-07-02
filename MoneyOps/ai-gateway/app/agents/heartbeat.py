"""
Heartbeat Scheduler - APScheduler-based autonomous agent cycles.
Triggers real agent execution on schedule.
All cycles execute actual agent work, not just event publishing.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.agents.base_executor import (
    FinanceExecutor, ComplianceExecutor, CollectionsExecutor, TReDSExecutor, CycleResult, ExecutionState
)
from app.adapters.backend_adapter import get_backend_adapter
from app.agents.growth import GrowthExecutor
from app.agents.master_orchestrator import master_orchestrator
from app.agents.activity_stream import activity_stream, ActivityType, Priority
from app.agentos.observation import audit_registry
from app.agentos.memory import agent_memory
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


class HeartbeatScheduler:
    """
    Manages autonomous agent cycles with REAL execution:
    - Nightly heartbeat (2 AM): All agents run autonomous cycles
    - Morning briefing (7 AM): CEO agent generates daily plan
    - Collections reminders (9 AM, 2 PM): Automated payment reminders via WhatsApp
    - Evening summary (6 PM): End-of-day wrap-up
    - Continuous monitoring (every 30 min): Alert scanning
    - Growth analysis (4 PM): Daily growth opportunity analysis
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.executors: Dict[str, Any] = {}
        self._cycle_history: List[Dict[str, Any]] = []
        self._initialized = False
        self._orgs: List[str] = ["system"]
        self._orgs_last_fetch: float = 0
        self._orgs_cache_ttl: int = 300

    def register_executor(self, name: str, executor):
        self.executors[name] = executor
        logger.info("heartbeat_executor_registered", executor=name)

    def start(self):
        if self._initialized:
            logger.warning("heartbeat_scheduler_already_started")
            return
        self._setup_jobs()
        self.scheduler.start()
        self._initialized = True
        asyncio.create_task(self._load_orgs())
        logger.info("heartbeat_scheduler_started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self._initialized = False
            logger.info("heartbeat_scheduler_stopped")

    async def _load_orgs(self):
        try:
            now = datetime.utcnow().timestamp()
            if now - self._orgs_last_fetch < self._orgs_cache_ttl:
                return
            backend = get_backend_adapter()
            resp = await backend._request("GET", "/api/orgs")
            if resp.success and resp.data:
                orgs_data = resp.data
                if isinstance(orgs_data, list):
                    self._orgs = [o.get("id", o) if isinstance(o, dict) else str(o) for o in orgs_data]
                elif isinstance(orgs_data, dict):
                    orgs_list = orgs_data.get("orgs", orgs_data.get("data", []))
                    self._orgs = [o.get("id", o) if isinstance(o, dict) else str(o) for o in orgs_list]
                if self._orgs:
                    self._orgs_last_fetch = now
                    logger.info("heartbeat_orgs_loaded", count=len(self._orgs), orgs=self._orgs[:5])
                    return
            logger.warning("heartbeat_orgs_fallback_to_system")
            self._orgs = ["system"]
        except Exception as e:
            logger.error("heartbeat_orgs_load_error", error=str(e))
            self._orgs = ["system"]

    def _setup_jobs(self):
        self.scheduler.add_job(
            self._run_nightly_heartbeat,
            CronTrigger(hour=2, minute=0, timezone="Asia/Kolkata"),
            id="nightly_heartbeat", name="Nightly Agent Heartbeat",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_morning_briefing,
            CronTrigger(hour=7, minute=0, timezone="Asia/Kolkata"),
            id="morning_briefing", name="Morning Briefing",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_collections_reminder,
            CronTrigger(hour=9, minute=0, timezone="Asia/Kolkata"),
            id="collections_morning", name="Morning Collections Reminder",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_collections_reminder,
            CronTrigger(hour=14, minute=0, timezone="Asia/Kolkata"),
            id="collections_afternoon", name="Afternoon Collections Reminder",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_evening_summary,
            CronTrigger(hour=18, minute=0, timezone="Asia/Kolkata"),
            id="evening_summary", name="Evening Summary",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._scan_for_alerts,
            IntervalTrigger(minutes=30),
            id="alert_scanning", name="Alert Scanning",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self._run_growth_analysis,
            CronTrigger(hour=16, minute=0, timezone="Asia/Kolkata"),
            id="growth_analysis", name="Daily Growth Analysis",
            replace_existing=True,
        )

    async def _run_nightly_heartbeat(self):
        logger.info("nightly_heartbeat_started")
        await activity_stream.publish(
            ActivityType.HEARTBEAT, agent="heartbeat", org_id="system",
            title="Nightly Heartbeat Started",
            message="Running autonomous cycles for all agents",
            priority=Priority.LOW,
        )

        results = {}
        for org_id in self._orgs:
            for name, executor in self.executors.items():
                if hasattr(executor, "run_autonomous_cycle"):
                    try:
                        result = await executor.run_autonomous_cycle(org_id=org_id)
                        results[f"{org_id}:{name}"] = result.to_dict() if hasattr(result, "to_dict") else result

                        await activity_stream.publish(
                            ActivityType.AGENT_CYCLE, agent=name, org_id=org_id,
                            title=f"{name} cycle complete",
                            message=result.summary if hasattr(result, "summary") else "Cycle completed",
                            priority=Priority.MEDIUM if getattr(result, "success", False) else Priority.HIGH,
                            data={"actions": getattr(result, "actions_taken", []),
                                  "alerts": getattr(result, "alerts", [])},
                        )
                    except Exception as e:
                        logger.error("heartbeat_executor_error", executor=name, error=str(e))
                        results[f"{org_id}:{name}"] = {"success": False, "error": str(e)}

        self._cycle_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "nightly_heartbeat",
            "results": results,
        })

        await activity_stream.publish(
            ActivityType.HEARTBEAT, agent="heartbeat", org_id="system",
            title="Nightly Heartbeat Complete",
            message=f"Ran {len(results)} agent cycles across {len(self._orgs)} orgs",
            priority=Priority.LOW,
        )
        logger.info("nightly_heartbeat_completed", cycle_count=len(results))

    async def _run_morning_briefing(self):
        logger.info("morning_briefing_started")
        for org_id in self._orgs:
            try:
                await master_orchestrator.generate_morning_briefing(org_id=org_id)
            except Exception as e:
                logger.error("morning_briefing_error", org_id=org_id, error=str(e))

    async def _run_collections_reminder(self):
        logger.info("collections_reminder_started")
        for org_id in self._orgs:
            try:
                if "collections_executor" in self.executors:
                    executor = self.executors["collections_executor"]
                    state = ExecutionState(
                        user_request="send reminders to overdue clients",
                        org_id=org_id, user_id=None,
                        business_id="1", session_id="heartbeat",
                    )
                    result = await executor._send_reminders(state)
                    logger.info("collections_reminder_result", org_id=org_id, result=result.get("response", ""))
            except Exception as e:
                logger.error("collections_reminder_error", org_id=org_id, error=str(e))

    async def _run_evening_summary(self):
        logger.info("evening_summary_started")
        for org_id in self._orgs:
            try:
                await master_orchestrator.generate_evening_summary(org_id=org_id)
            except Exception as e:
                logger.error("evening_summary_error", org_id=org_id, error=str(e))

        today_cycles = [c for c in self._cycle_history
                       if c["timestamp"].startswith(datetime.utcnow().strftime("%Y-%m-%d"))]

        await activity_stream.publish(
            ActivityType.EVENING_SUMMARY, agent="ceo", org_id="system",
            title="Evening Summary Complete",
            message=f"{len(today_cycles)} agent cycles ran today",
            priority=Priority.LOW, data={"cycles_today": len(today_cycles)},
        )

    async def _scan_for_alerts(self):
        for org_id in self._orgs:
            try:
                if "collections_executor" in self.executors:
                    executor = self.executors["collections_executor"]
                    state = ExecutionState(
                        user_request="collections dashboard",
                        org_id=org_id, user_id=None,
                        business_id="1", session_id="heartbeat",
                    )
                    result = await executor._collections_dashboard(state)

                    if result.get("aging_buckets"):
                        critical = result["aging_buckets"].get("90+", 0)
                        if critical > 0:
                            await activity_stream.publish(
                                ActivityType.ALERT, agent="collections_executor",
                                org_id=org_id,
                                title=f"{critical} invoices 90+ days overdue",
                                message="Critical collection risk detected",
                                priority=Priority.CRITICAL,
                                data={"aging": result["aging_buckets"]},
                            )
                            logger.warning("alert_critical_overdue", org_id=org_id, count=critical)
            except Exception as e:
                logger.error("alert_scan_error", org_id=org_id, error=str(e))

    async def _run_growth_analysis(self):
        logger.info("growth_analysis_started")
        if "growth_executor" in self.executors:
            growth = self.executors["growth_executor"]
            for org_id in self._orgs:
                try:
                    result = await growth.run_autonomous_cycle(org_id=org_id)
                    await activity_stream.publish(
                        ActivityType.GROWTH_INSIGHT, agent="growth_executor",
                        org_id=org_id, title="Growth Analysis Complete",
                        message=result.summary,
                        priority=Priority.MEDIUM,
                        data={"metrics": getattr(result, "metrics", {})},
                    )
                except Exception as e:
                    logger.error("growth_analysis_error", org_id=org_id, error=str(e))

    def get_cycle_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._cycle_history[-limit:]

    def get_status(self) -> Dict[str, Any]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            })
        return {
            "running": self.scheduler.running,
            "initialized": self._initialized,
            "executors": list(self.executors.keys()),
            "scheduled_jobs": jobs,
            "cycles_run": len(self._cycle_history),
        }


heartbeat_scheduler = HeartbeatScheduler()
