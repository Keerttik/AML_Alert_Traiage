import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.utils.config import AUDIT_LOG_DIR

FEEDBACK_FILE = AUDIT_LOG_DIR / "pilot_feedback.jsonl"

class FeedbackStore:
    """Stores per-alert qualitative and quantitative feedback from AML analysts during the pilot."""
    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or FEEDBACK_FILE
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.touch()

    def record_feedback(
        self,
        alert_id: str,
        analyst_id: str,
        helpfulness_rating: int, # 1 to 5
        recommendation_accuracy: str, # "Accurate & Appropriate", "Too Aggressive / Over-flagged", "Too Lenient"
        narrative_quality: str, # "High - minimal edits", "Adequate", "Poor - extensive edits"
        comments: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Appends a new feedback record to the pilot feedback store."""
        entry = {
            "feedback_id": f"FB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{alert_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_id": alert_id,
            "analyst_id": analyst_id,
            "helpfulness_rating": helpfulness_rating,
            "recommendation_accuracy": recommendation_accuracy,
            "narrative_quality": narrative_quality,
            "comments": comments,
            "tags": tags or []
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Retrieves all feedback entries."""
        if not self.file_path.exists():
            return []
        entries = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        pass
        return entries

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Computes aggregate pilot feedback KPIs (Average Rating, Accuracy Distribution)."""
        entries = self.get_all_feedback()
        if not entries:
            return {
                "total_responses": 0,
                "avg_rating": 0.0,
                "nps_satisfaction_percent": 0.0,
                "accuracy_breakdown": {},
                "narrative_quality_breakdown": {}
            }

        total = len(entries)
        ratings = [e.get("helpfulness_rating", 0) for e in entries]
        avg_rating = sum(ratings) / total if total > 0 else 0.0
        
        # High satisfaction count (rating 4 or 5)
        high_satisfaction = sum(1 for r in ratings if r >= 4)
        nps_satisfaction_percent = (high_satisfaction / total) * 100.0

        accuracy_counts = {}
        for e in entries:
            acc = e.get("recommendation_accuracy", "Unknown")
            accuracy_counts[acc] = accuracy_counts.get(acc, 0) + 1

        narrative_counts = {}
        for e in entries:
            nq = e.get("narrative_quality", "Unknown")
            narrative_counts[nq] = narrative_counts.get(nq, 0) + 1

        return {
            "total_responses": total,
            "avg_rating": round(avg_rating, 2),
            "nps_satisfaction_percent": round(nps_satisfaction_percent, 1),
            "accuracy_breakdown": accuracy_counts,
            "narrative_quality_breakdown": narrative_counts
        }
