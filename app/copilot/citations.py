import re
from typing import Dict, Any, List, Tuple

CITATION_REGEX = re.compile(r"\[(KYC(?:[:\s][^\]]+)?|Txn:\s*[^\]]+|Rule:\s*[^\]]+|Prior Alert:\s*[^\]]+|Counterparty:\s*[^\]]+|Watchlist(?::\s*[^\]]+)?)\]", re.IGNORECASE)

class CitationEngine:
    def __init__(self):
        pass

    def extract_citations(self, text: str) -> List[str]:
        """Finds all square-bracketed citations matching valid formats in a text block."""
        if not text:
            return []
        matches = CITATION_REGEX.findall(text)
        # Normalize brackets
        return [f"[{m.strip()}]" for m in matches]

    def validate_citations_against_context(
        self,
        ai_output: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extracts and verifies every citation against the raw context payload.

        Returns validity stats and flags invalid or ungrounded citations.
        """
        all_text_blocks = []
        if ai_output.get("summary"):
            all_text_blocks.append(ai_output["summary"])
        for r in ai_output.get("rationale", []):
            if isinstance(r, dict):
                all_text_blocks.append(r.get("reason", ""))
                for c in r.get("source_citations", []):
                    all_text_blocks.append(c)
        for rf in ai_output.get("risk_factors", []):
            all_text_blocks.append(rf)
        for mf in ai_output.get("mitigating_factors", []):
            all_text_blocks.append(mf)
        if ai_output.get("str_draft"):
            all_text_blocks.append(ai_output["str_draft"])

        combined_text = " ".join(all_text_blocks)
        found_citations = self.extract_citations(combined_text)

        # Context lookups
        valid_txn_ids = {t["txn_id"].upper() for t in context.get("transactions", [])}
        alert_rule_id = (context.get("alert", {}).get("rule_id") or "").upper()
        customer = context.get("customer", {})
        watchlist_hits = context.get("watchlist_hits", [])
        counterparties = {c.upper() for c in context.get("counterparties", [])}
        prior_alerts = {a["alert_id"].upper() for a in context.get("prior_alerts", [])}

        valid_citations = []
        invalid_citations = []
        valid_occurrence_count = 0
        invalid_occurrence_count = 0

        for cit in found_citations:
            content = cit[1:-1].strip()
            is_valid = False

            if content.upper().startswith("KYC"):
                # Valid if customer object has data
                is_valid = bool(customer.get("name") or customer.get("customer_id"))

            elif content.upper().startswith("TXN:"):
                txn_val = content.split(":", 1)[1].strip().upper()
                is_valid = txn_val in valid_txn_ids

            elif content.upper().startswith("RULE:"):
                rule_val = content.split(":", 1)[1].strip().upper()
                is_valid = (rule_val == alert_rule_id) or (rule_val in alert_rule_id)

            elif content.upper().startswith("PRIOR ALERT:"):
                pa_val = content.split(":", 1)[1].strip().upper()
                is_valid = pa_val in prior_alerts

            elif content.upper().startswith("COUNTERPARTY:"):
                cp_val = content.split(":", 1)[1].strip().upper()
                is_valid = any(cp_val in cp or cp in cp_val for cp in counterparties)

            elif content.upper().startswith("WATCHLIST"):
                is_valid = len(watchlist_hits) > 0 or customer.get("pep_status")

            if is_valid:
                valid_citations.append(cit)
                valid_occurrence_count += 1
            else:
                invalid_citations.append(cit)
                invalid_occurrence_count += 1

        total_citations = len(found_citations)
        accuracy = (valid_occurrence_count / total_citations * 100.0) if total_citations > 0 else 100.0

        return {
            "total_citations": total_citations,
            "valid_count": valid_occurrence_count,
            "invalid_count": invalid_occurrence_count,
            "valid_citations": list(set(valid_citations)),
            "invalid_citations": list(set(invalid_citations)),
            "accuracy_percent": round(accuracy, 1),
            "passed_threshold": accuracy >= 95.0
        }
