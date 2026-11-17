import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.data.anonymiser_pipeline import AnonymisationPipeline
from app.data.feedback_store import FeedbackStore
from app.data.context_assembler import ContextAssembler
from evaluation.pilot_simulator import PilotSimulator

def test_anonymisation_pipeline(tmp_path):
    pipeline = AnonymisationPipeline()
    # Test deterministic pseudonymisation
    id1 = pipeline.pseudonymise_id("CUST-88401", "ANON")
    id2 = pipeline.pseudonymise_id("CUST-88401", "ANON")
    assert id1 == id2
    assert id1.startswith("ANON-")

    # Test dataset generation
    data = pipeline.generate_pilot_dataset(target_alert_count=20)
    assert len(data["alerts"]) == 20
    assert len(data["customers"]) == 20
    assert len(data["transactions"]) > 0

def test_feedback_store(tmp_path):
    fb_file = tmp_path / "test_feedback.jsonl"
    store = FeedbackStore(file_path=fb_file)

    entry = store.record_feedback(
        alert_id="ALT-2026-001042",
        analyst_id="ANALYST-01",
        helpfulness_rating=5,
        recommendation_accuracy="Accurate & Appropriate",
        narrative_quality="High - minimal edits",
        comments="Great summary and citations."
    )
    assert entry["helpfulness_rating"] == 5

    metrics = store.get_summary_metrics()
    assert metrics["total_responses"] == 1
    assert metrics["avg_rating"] == 5.0
    assert metrics["nps_satisfaction_percent"] == 100.0

def test_pilot_sandbox_context_assembly():
    assembler = ContextAssembler(use_pilot_sandbox=True)
    all_alerts = assembler.get_all_alerts()
    assert len(all_alerts) > 0
    first_alert = all_alerts[0]
    ctx = assembler.assemble_context(first_alert["alert_id"])
    assert ctx["alert"]["alert_id"] == first_alert["alert_id"]
    assert "customer" in ctx
    assert len(ctx["transactions"]) > 0

def test_pilot_simulator_metrics():
    simulator = PilotSimulator()
    res = simulator.run_simulation(alert_count=20)
    assert res["ab_comparison"]["time_reduction_percent"] > 40.0
    assert res["quality_metrics"]["missed_escalations"] == 0
    assert len(res["weekly_trends"]) == 4
