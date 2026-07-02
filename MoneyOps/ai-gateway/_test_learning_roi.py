"""Test learning layer and ROI tracker"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Learning Layer ===")
from app.agentos.learning import agent_learning

agent_learning.record_outcome("collections", "send_reminder", {"overdue_days": 45}, 85.0, True, 1200, 75.0)
agent_learning.record_outcome("collections", "send_reminder", {"overdue_days": 90}, 60.0, False, 3500, 50.0)
agent_learning.record_outcome("collections", "send_reminder", {"overdue_days": 30}, 95.0, True, 800, 90.0)
agent_learning.record_outcome("finance", "cash_flow_analysis", {}, 88.0, True, 500, 82.0)

perf = agent_learning.get_agent_performance("collections")
print("Collections perf: {:.0f}% success ({} actions)".format(perf["success_rate"], perf["total_actions"]))

rec = agent_learning.get_action_recommendation("collections", "send_reminder")
print("Send reminder rec: confidence={}, recommended={}".format(rec["confidence"], rec["recommended"]))

patterns = agent_learning.get_action_patterns("collections")
print("Patterns found: {}".format(len(patterns["patterns"])))

summary = agent_learning.get_learning_summary()
print("Agents tracked: {}".format(summary["agents_tracked"]))
print("Total records: {}".format(summary["total_records"]))

print()
print("=== ROI Tracker ===")
from app.agentos.roi import roi_tracker

roi_tracker.record_metric("collections", "amount_recovered", 150000, previous_value=120000)
roi_tracker.record_metric("collections", "dso_days", 38, previous_value=45)
roi_tracker.record_metric("compliance", "late_fees_avoided", 25000)
roi_tracker.record_metric("treds", "working_capital_generated", 500000)
roi_tracker.record_metric("growth", "revenue_growth_pct", 12.5, previous_value=8.2)

col_roi = roi_tracker.get_agent_roi("collections")
print("Collections ROI: {} INR recovered".format(col_roi["total_value_generated"]))

all_roi = roi_tracker.get_all_roi()
print("Total agents tracked: {}".format(all_roi["total_agents"]))
print("Total value generated: {} INR".format(all_roi["total_value_generated"]))

roi_tracker.auto_collect_from_observation()

print()
print("ALL LEARNING + ROI TESTS PASSED!")
