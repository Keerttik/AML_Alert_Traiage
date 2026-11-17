import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.utils.config import AUDIT_LOG_FILE

class AuditLogger:
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or AUDIT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

    def _get_last_entry_hash(self) -> str:
        """Reads the last line of the JSONL log file to retrieve the previous entry's hash."""
        if not self.log_file.exists() or self.log_file.stat().st_size == 0:
            return "0000000000000000000000000000000000000000000000000000000000000000"

        last_line = ""
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()

        if not last_line:
            return "0000000000000000000000000000000000000000000000000000000000000000"

        try:
            data = json.loads(last_line)
            return data.get("metadata", {}).get("audit_entry_hash", "")
        except Exception:
            return "0000000000000000000000000000000000000000000000000000000000000000"

    def _compute_hash(self, content_dict: Dict[str, Any]) -> str:
        """Computes deterministic SHA-256 hash of a JSON-serializable dictionary."""
        serialised = json.dumps(content_dict, sort_keys=True, default=str)
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()

    def log_decision(
        self,
        alert_id: str,
        customer_id: str,
        ai_analysis: Dict[str, Any],
        analyst_decision: Dict[str, Any],
        analyst_id: str = "ANALYST-DEFAULT"
    ) -> Dict[str, Any]:
        """Appends an immutable audit log record to the JSONL log file with cryptographic chaining."""
        prev_hash = self._get_last_entry_hash()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Count existing entries to generate ID
        existing_count = len(self.get_all_entries())
        entry_id = f"AUD-2026-{existing_count + 1:05d}"

        # Detect override
        ai_rec = (ai_analysis.get("recommendation") or "").strip().lower()
        analyst_disp = (analyst_decision.get("disposition") or "").strip().lower()
        is_override = ai_rec != analyst_disp if (ai_rec and analyst_disp) else False

        entry_core = {
            "entry_id": entry_id,
            "timestamp": timestamp,
            "alert_id": alert_id,
            "customer_id": customer_id,
            "ai_analysis": {
                "prompt_bundle_version": ai_analysis.get("prompt_bundle_version", "PB-v1.0.0"),
                "model_id": ai_analysis.get("model_id", "unknown"),
                "summary": ai_analysis.get("summary", ""),
                "recommendation": ai_analysis.get("recommendation", ""),
                "confidence": ai_analysis.get("confidence", "Medium"),
                "rationale": ai_analysis.get("rationale", []),
                "missing_data": ai_analysis.get("missing_data"),
                "str_draft": ai_analysis.get("str_draft"),
                "validation_result": ai_analysis.get("validation_result", "PASSED"),
                "validation_issues": ai_analysis.get("validation_issues", [])
            },
            "analyst_decision": {
                "analyst_id": analyst_id,
                "disposition": analyst_decision.get("disposition", ""),
                "rationale": analyst_decision.get("rationale", ""),
                "override": is_override,
                "override_reason": analyst_decision.get("override_reason") if is_override else None,
                "str_final": analyst_decision.get("str_final"),
                "decision_time_seconds": analyst_decision.get("decision_time_seconds", 0)
            }
        }

        # Cryptographic link
        entry_hash = self._compute_hash({**entry_core, "previous_entry_hash": prev_hash})
        full_entry = {
            **entry_core,
            "metadata": {
                "audit_entry_hash": entry_hash,
                "previous_entry_hash": prev_hash
            }
        }

        # Atomic append to audit file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_entry, default=str) + "\n")

        return full_entry

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Reads all audit log records from the JSONL log file."""
        entries = []
        if not self.log_file.exists():
            return entries

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return entries

    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Verifies the SHA-256 cryptographic chain across all audit log entries."""
        entries = self.get_all_entries()
        if not entries:
            return True, ["Audit log is empty; chain is intact."]

        errors = []
        expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"

        for idx, entry in enumerate(entries):
            metadata = entry.get("metadata", {})
            recorded_hash = metadata.get("audit_entry_hash", "")
            recorded_prev = metadata.get("previous_entry_hash", "")

            if recorded_prev != expected_prev_hash:
                errors.append(
                    f"Entry {entry.get('entry_id')} (index {idx}) broken chain: "
                    f"expected previous {expected_prev_hash[:10]}..., got {recorded_prev[:10]}..."
                )

            # Recompute
            core = {k: v for k, v in entry.items() if k != "metadata"}
            recomputed = self._compute_hash({**core, "previous_entry_hash": recorded_prev})

            if recomputed != recorded_hash:
                errors.append(
                    f"Entry {entry.get('entry_id')} (index {idx}) tampering detected: "
                    f"recorded {recorded_hash[:10]}..., recomputed {recomputed[:10]}..."
                )

            expected_prev_hash = recorded_hash

        is_valid = len(errors) == 0
        return is_valid, errors
