import time
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field

from app.copilot.engine import CopilotEngine
from app.copilot.conversational import ConversationalAssistant
from app.copilot.prioritizer import AlertPrioritizer
from app.copilot.str_generator import generate_draft_str
from app.data.context_assembler import ContextAssembler
from app.data.audit_logger import AuditLogger
from app.data.feedback_store import FeedbackStore
from app.monitoring.drift_detector import ModelDriftDetector
from app.api.security import get_current_user, require_role

# FastAPI App Definition
app = FastAPI(
    title="AML Alert Triage Copilot — Enterprise Production API",
    description="Mission-critical GenAI compliance copilot with source citations, human-in-the-loop controls, and regulatory auditability.",
    version="1.0.0"
)

# Shared Singletons
context_assembler = ContextAssembler()
copilot_engine = CopilotEngine()
conversational_assistant = ConversationalAssistant()
alert_prioritizer = AlertPrioritizer()
audit_logger = AuditLogger()
feedback_store = FeedbackStore()
drift_detector = ModelDriftDetector()

# --- Request / Response Models ---
class IngestAlertRequest(BaseModel):
    alert_id: str
    customer_id: str
    rule_id: str
    rule_name: str
    trigger_date: str
    trigger_summary: str
    priority: Optional[str] = "Medium"
    archetype: Optional[str] = "Standard"

class AdjudicationRequest(BaseModel):
    disposition: str = Field(..., description="Close, Investigate, or Escalate")
    rationale: str
    override: Optional[bool] = False
    override_reason: Optional[str] = None
    str_final: Optional[str] = None
    decision_time_seconds: Optional[int] = 0

class ChatQueryRequest(BaseModel):
    alert_id: str
    query: str

class FeedbackRequest(BaseModel):
    alert_id: str
    helpfulness_rating: int
    recommendation_accuracy: str
    narrative_quality: str
    comments: Optional[str] = ""

# --- Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """Health check probe for container orchestrators (Kubernetes / Cloud Run)."""
    return {"status": "HEALTHY", "service": "AML Alert Triage Copilot API", "timestamp": time.time()}

@app.post("/api/v1/alerts/ingest", tags=["Integration Layer"])
def ingest_alert(alert_data: IngestAlertRequest, user: Dict[str, Any] = Depends(require_role(["compliance_manager", "analyst"]))):
    """Ingests a new monitoring alert from upstream transaction monitoring engines (Actimize, Oracle Mantas)."""
    alert_dict = alert_data.dict()
    # Check prioritization score immediately
    try:
        ctx = context_assembler.assemble_context(alert_dict["alert_id"])
        score_info = alert_prioritizer.score_alert(ctx)
        alert_dict["severity_score"] = score_info["severity_score"]
        alert_dict["priority_tier"] = score_info["priority_tier"]
    except Exception:
        alert_dict["severity_score"] = 50
        alert_dict["priority_tier"] = alert_dict.get("priority", "Medium")

    return {
        "status": "INGESTED",
        "alert_id": alert_dict["alert_id"],
        "assigned_priority": alert_dict["priority_tier"],
        "severity_score": alert_dict["severity_score"]
    }

@app.get("/api/v1/alerts/{alert_id}/context", tags=["Context Assembly"])
def get_alert_context(alert_id: str, user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves full assembled customer KYC, transaction ledger, and watchlist context."""
    try:
        ctx = context_assembler.assemble_context(alert_id)
        return ctx
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v1/alerts/{alert_id}/triage", tags=["Copilot Engine"])
def run_triage(alert_id: str, language: Optional[str] = "en", user: Dict[str, Any] = Depends(get_current_user)):
    """Executes the AI Copilot reasoning pipeline: context synthesis, grounded recommendation, and STR draft."""
    try:
        res = copilot_engine.triage_alert(alert_id)
        # If multi-language requested for STR draft
        if language != "en" and res["analysis"].get("recommendation") == "Escalate":
            reasons = [r["reason"] for r in res["analysis"].get("rationale", []) if isinstance(r, dict)]
            res["analysis"]["str_draft"] = generate_draft_str(res["context"], reasons, language=language)
            res["analysis"]["language"] = language

        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage execution failure: {str(e)}")

@app.post("/api/v1/alerts/{alert_id}/adjudicate", tags=["Adjudication & Audit"])
def adjudicate_alert(alert_id: str, adjudication: AdjudicationRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Captures human analyst disposition decision and commits to the immutable SHA-256 audit log."""
    ctx = context_assembler.assemble_context(alert_id)
    copilot_res = copilot_engine.triage_alert(alert_id)

    # Validate override
    ai_disp = copilot_res["analysis"].get("recommendation")
    is_override = (adjudication.disposition != ai_disp)

    if is_override and not (adjudication.override_reason or "").strip():
        raise HTTPException(status_code=400, detail="Override reason is mandatory when departing from AI recommendation.")

    entry = audit_logger.log_decision(
        alert_id=alert_id,
        customer_id=ctx.get("customer", {}).get("customer_id", "UNKNOWN"),
        ai_analysis=copilot_res["analysis"],
        analyst_decision=adjudication.dict(),
        analyst_id=user.get("sub", "ANALYST-DEFAULT")
    )
    return {"status": "COMMITTED_TO_AUDIT", "entry_id": entry["entry_id"], "audit_hash": entry["metadata"]["audit_entry_hash"]}

@app.post("/api/v1/chat/follow-up", tags=["Conversational Assistant"])
def chat_follow_up(request: ChatQueryRequest, user: Dict[str, Any] = Depends(get_current_user)):
    """Allows analysts to ask dynamic natural-language questions grounded in the alert evidence."""
    ctx = context_assembler.assemble_context(request.alert_id)
    answer_res = conversational_assistant.answer_query(request.query, ctx)
    return answer_res

@app.get("/api/v1/monitoring/telemetry", tags=["Production Monitoring"])
def get_monitoring_telemetry(user: Dict[str, Any] = Depends(require_role(["compliance_manager", "auditor"]))):
    """Returns rolling distribution drift, latency percentiles, and confidence calibration."""
    telemetry = drift_detector.compute_monitoring_telemetry()
    return telemetry
