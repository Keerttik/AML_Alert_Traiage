import re
from typing import Dict, Any, List, Tuple
from app.copilot.citations import CitationEngine

PROHIBITED_LEGAL_TERMS = [
    r"(?i)\bis\s+(guilty\s+of|committing)\s+money\s+laundering\b",
    r"(?i)\bis\s+a\s+criminal\b",
    r"(?i)\bthis\s+proves\s+fraud\b",
    r"(?i)\billegal\s+drug\s+proceeds\b",
]

class OutputValidator:
    def __init__(self):
        self.citation_engine = CitationEngine()

    def validate(self, ai_output: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the multi-stage output validation pipeline on the copilot output."""
        issues: List[str] = []
        status = "PASSED"

        # 1. Schema check
        required_keys = ["summary", "recommendation", "confidence", "rationale", "risk_factors", "mitigating_factors"]
        for k in required_keys:
            if k not in ai_output:
                issues.append(f"Missing required field in output schema: '{k}'")

        if issues:
            return {
                "status": "FAILED",
                "issues": issues,
                "sanitised_output": ai_output,
                "hallucinations_detected": 0
            }

        # 2. Recommendation value check
        valid_recs = ["Close", "Investigate", "Escalate"]
        if ai_output.get("recommendation") not in valid_recs:
            issues.append(f"Invalid recommendation '{ai_output.get('recommendation')}'. Must be one of {valid_recs}.")
            ai_output["recommendation"] = "Investigate"
            ai_output["confidence"] = "Low"

        # 3. Citation check
        citation_results = self.citation_engine.validate_citations_against_context(ai_output, context)
        if citation_results["invalid_citations"]:
            issues.append(f"Invalid or ungrounded citations detected: {', '.join(citation_results['invalid_citations'])}")

        # 4. Hallucination check on transaction IDs
        all_text = (
            ai_output.get("summary", "") + " " +
            str(ai_output.get("rationale", "")) + " " +
            (ai_output.get("str_draft") or "")
        )
        mentioned_txns = re.findall(r"TXN-\d+", all_text)
        valid_txns = {t["txn_id"] for t in context.get("transactions", [])}
        hallucinated_txns = [t for t in mentioned_txns if t not in valid_txns]

        if hallucinated_txns:
            issues.append(f"Hallucinated transaction IDs detected: {', '.join(set(hallucinated_txns))}")

        # 5. Prohibited legal claims scan
        for term_regex in PROHIBITED_LEGAL_TERMS:
            if re.search(term_regex, all_text):
                issues.append(f"Prohibited definitive legal phrasing detected: '{term_regex}'")

        # 6. Overall status determination
        hallucination_count = len(hallucinated_txns) + len(citation_results["invalid_citations"])
        if hallucination_count > 0:
            status = "WARNING" if hallucination_count <= 2 else "FAILED"
        elif issues:
            status = "WARNING"

        return {
            "status": status,
            "issues": issues,
            "citation_stats": citation_results,
            "hallucinations_detected": hallucination_count,
            "sanitised_output": ai_output
        }
