import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.api.server import app
from app.copilot.prioritizer import AlertPrioritizer
from app.copilot.conversational import ConversationalAssistant
from app.copilot.str_generator import generate_draft_str
from app.monitoring.drift_detector import ModelDriftDetector
from app.data.context_assembler import ContextAssembler

client = TestClient(app)

def test_fastapi_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_fastapi_context_and_triage():
    # Context endpoint
    ctx_res = client.get("/api/v1/alerts/ALT-2026-001042/context")
    assert ctx_res.status_code == 200
    assert ctx_res.json()["alert"]["alert_id"] == "ALT-2026-001042"

    # Triage endpoint
    triage_res = client.post("/api/v1/alerts/ALT-2026-001042/triage")
    assert triage_res.status_code == 200
    data = triage_res.json()
    assert data["analysis"]["recommendation"] == "Escalate"
    assert data["validation"]["status"] == "PASSED"

def test_fastapi_chat_follow_up():
    chat_res = client.post(
        "/api/v1/chat/follow-up",
        json={"alert_id": "ALT-2026-001042", "query": "What is the customer declared income?"}
    )
    assert chat_res.status_code == 200
    ans_data = chat_res.json()
    assert "income" in ans_data["answer"].lower()
    assert len(ans_data["source_citations"]) > 0

def test_alert_prioritizer():
    assembler = ContextAssembler()
    prioritizer = AlertPrioritizer()

    # Sanctions hit should be CRITICAL
    ctx_sanctions = assembler.assemble_context("ALT-2026-001053")
    score_sanctions = prioritizer.score_alert(ctx_sanctions)
    assert score_sanctions["priority_tier"] in ["CRITICAL", "HIGH"]
    assert score_sanctions["severity_score"] >= 70

    # Benign false positive should be LOW/MEDIUM
    ctx_benign = assembler.assemble_context("ALT-2026-001048")
    score_benign = prioritizer.score_alert(ctx_benign)
    assert score_benign["severity_score"] < score_sanctions["severity_score"]

def test_multi_language_str():
    assembler = ContextAssembler()
    ctx = assembler.assemble_context("ALT-2026-001042")
    reasons = ["Structuring pattern identified", "Sub-threshold transactions"]

    str_es = generate_draft_str(ctx, reasons, language="es")
    assert "REPORTE DE OPERACIONES SOSPECHOSAS" in str_es

    str_fr = generate_draft_str(ctx, reasons, language="fr")
    assert "DÉCLARATION DE SOUPÇON" in str_fr

    str_ar = generate_draft_str(ctx, reasons, language="ar")
    assert "تقرير المعاملات المشبوهة" in str_ar

def test_model_drift_detector():
    detector = ModelDriftDetector()
    telemetry = detector.compute_monitoring_telemetry()
    assert "disposition_distribution" in telemetry
    assert "confidence_calibration" in telemetry
    assert "latency_metrics" in telemetry
    assert telemetry["system_health"] in ["HEALTHY", "DRIFT_WARNING", "CRITICAL_DRIFT", "HEALTHY — NO_DATA"]
