import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.data.context_assembler import ContextAssembler
from app.data.audit_logger import AuditLogger
from app.copilot.engine import CopilotEngine
from app.copilot.citations import CitationEngine
from app.copilot.validator import OutputValidator

def test_context_assembler_completeness():
    assembler = ContextAssembler()
    # Normal alert with full KYC
    ctx_normal = assembler.assemble_context("ALT-2026-001042")
    assert ctx_normal["_metadata"]["is_complete"] is True
    assert len(ctx_normal["_metadata"]["missing_fields"]) == 0

    # Incomplete KYC alert
    ctx_incomplete = assembler.assemble_context("ALT-2026-001050")
    assert ctx_incomplete["_metadata"]["is_complete"] is False
    assert "Customer Declared Occupation" in ctx_incomplete["_metadata"]["missing_fields"]

def test_citations_engine():
    engine = CitationEngine()
    text = "Activity deviates from baseline [KYC Profile] and matches rule [Rule: STRUCT-001] for txn [Txn: TXN-101001]."
    citations = engine.extract_citations(text)
    assert "[KYC Profile]" in citations
    assert "[Rule: STRUCT-001]" in citations
    assert "[Txn: TXN-101001]" in citations

def test_audit_logger_hash_chain(tmp_path):
    test_log_file = tmp_path / "test_audit.jsonl"
    logger = AuditLogger(log_file=test_log_file)

    entry1 = logger.log_decision(
        alert_id="ALT-2026-001042",
        customer_id="CUST-88401",
        ai_analysis={"recommendation": "Escalate"},
        analyst_decision={"disposition": "Escalate", "rationale": "Agreed"}
    )
    assert entry1["entry_id"] == "AUD-2026-00001"

    entry2 = logger.log_decision(
        alert_id="ALT-2026-001047",
        customer_id="CUST-65412",
        ai_analysis={"recommendation": "Close"},
        analyst_decision={"disposition": "Close", "rationale": "False positive verified"}
    )
    assert entry2["entry_id"] == "AUD-2026-00002"

    is_valid, msgs = logger.verify_chain_integrity()
    assert is_valid is True
    assert len(logger.get_all_entries()) == 2

def test_copilot_engine_triage():
    copilot = CopilotEngine()

    # Test 1: Structuring -> Must Escalate
    res_structuring = copilot.triage_alert("ALT-2026-001042")
    assert res_structuring["analysis"]["recommendation"] == "Escalate"
    assert res_structuring["analysis"]["confidence"] == "High"
    assert res_structuring["analysis"]["str_draft"] is not None
    assert res_structuring["validation"]["status"] == "PASSED"

    # Test 2: Legitimate seasonal business -> Must Close (False Positive)
    res_seasonal = copilot.triage_alert("ALT-2026-001047")
    assert res_seasonal["analysis"]["recommendation"] == "Close"
    assert res_seasonal["analysis"]["confidence"] == "High"
    assert res_seasonal["validation"]["status"] == "PASSED"

    # Test 3: Missing KYC -> Must say Insufficient Evidence & Investigate
    res_missing_kyc = copilot.triage_alert("ALT-2026-001050")
    assert res_missing_kyc["analysis"]["recommendation"] == "Investigate"
    assert res_missing_kyc["analysis"]["confidence"] == "Low"
    assert res_missing_kyc["analysis"]["missing_data"] is not None
