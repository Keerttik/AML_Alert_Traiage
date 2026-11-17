import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from app.utils.config import AUDIT_LOG_FILE, EVALUATION_DIR

class ModelDriftDetector:
    """Monitors live triage recommendations, confidence calibration, and latency telemetry

    to detect distribution drift, false negative risks, and performance degradation.
    """
    def __init__(self, audit_file: Path = AUDIT_LOG_FILE):
        self.audit_file = audit_file

    def get_audit_records(self) -> List[Dict[str, Any]]:
        if not self.audit_file.exists():
            return []
        records = []
        with open(self.audit_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        records.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return records

    def compute_monitoring_telemetry(self) -> Dict[str, Any]:
        """Calculates rolling distribution, confidence levels, latency quantiles, and drift alerts."""
        records = self.get_audit_records()
        total_records = len(records)
        
        if total_records == 0:
            return {
                "total_predictions": 0,
                "disposition_distribution": {"Close": 0, "Investigate": 0, "Escalate": 0},
                "confidence_calibration": {"High": 0, "Medium": 0, "Low": 0},
                "latency_metrics": {"p50_ms": 0, "p95_ms": 0, "avg_ms": 0},
                "drift_alerts": [],
                "status": "HEALTHY — NO_DATA"
            }

        # 1. Disposition Distribution
        disp_counts = {"Close": 0, "Investigate": 0, "Escalate": 0}
        conf_counts = {"High": 0, "Medium": 0, "Low": 0}
        latencies = []

        for r in records:
            ai_data = r.get("ai_analysis", {})
            rec = ai_data.get("recommendation", "Investigate")
            conf = ai_data.get("confidence", "Medium")
            ms = ai_data.get("response_time_ms", 120)

            disp_counts[rec] = disp_counts.get(rec, 0) + 1
            conf_counts[conf] = conf_counts.get(conf, 0) + 1
            latencies.append(ms)

        disp_pct = {k: round((v / total_records) * 100.0, 1) for k, v in disp_counts.items()}
        conf_pct = {k: round((v / total_records) * 100.0, 1) for k, v in conf_counts.items()}

        # 2. Latency percentiles
        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        avg_ms = round(sum(latencies) / len(latencies), 1) if latencies else 0

        # 3. Drift Analysis & Alerts
        drift_alerts = []

        # Baseline expected: Close ~35-50%, Investigate ~25-40%, Escalate ~20-35%
        if disp_pct.get("Escalate", 0) < 10.0 and total_records >= 20:
            drift_alerts.append({
                "severity": "CRITICAL",
                "message": f"Escalation rate dropped to {disp_pct.get('Escalate')}% (Historical baseline: 25-30%). Potential false-negative suppression drift!"
            })
        
        if conf_pct.get("Low", 0) > 25.0:
            drift_alerts.append({
                "severity": "WARNING",
                "message": f"High proportion of Low Confidence outputs ({conf_pct.get('Low')}%). Possible data quality decay or missing KYC baseline in ingested alerts."
            })

        if p95 > 10000:
            drift_alerts.append({
                "severity": "WARNING",
                "message": f"P95 latency exceeded SLA threshold ({p95}ms > 10,000ms)."
            })

        status = "CRITICAL_DRIFT" if any(a["severity"] == "CRITICAL" for a in drift_alerts) else ("DRIFT_WARNING" if drift_alerts else "HEALTHY")

        return {
            "total_predictions": total_records,
            "disposition_distribution": disp_pct,
            "confidence_calibration": conf_pct,
            "latency_metrics": {
                "p50_ms": p50,
                "p95_ms": p95,
                "avg_ms": avg_ms
            },
            "drift_alerts": drift_alerts,
            "system_health": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
