import json
import sys
from pathlib import Path

def validate_gate():
    report_file = Path("evaluation/eval_report_latest.json")
    if not report_file.exists():
        print("ERROR: Evaluation report not found!")
        sys.exit(1)

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = data.get("metrics", {})
    missed = metrics.get("missed_escalations_count", 999)
    citation_acc = metrics.get("citation_accuracy_percent", 0.0)
    hallucination_rate = metrics.get("hallucination_rate_percent", 100.0)

    print("==================================================")
    print("REGULATORY GUARDRAIL CI GATE VERIFICATION")
    print("==================================================")
    print(f"Missed Escalations (Target: 0):   {missed}")
    print(f"Citation Accuracy (Target: >=95%): {citation_acc}%")
    print(f"Hallucination Rate (Target: <2%): {hallucination_rate}%")
    print("==================================================")

    if missed > 0:
        print(f"FATAL REGULATORY BREACH: Missed escalations must be exactly 0, got {missed}!")
        sys.exit(1)

    if citation_acc < 95.0:
        print(f"CITATION ACCURACY BREACH: Expected >= 95%, got {citation_acc}%!")
        sys.exit(1)

    if hallucination_rate > 2.0:
        print(f"HALLUCINATION BREACH: Expected < 2%, got {hallucination_rate}%!")
        sys.exit(1)

    print("SUCCESS: ALL REGULATORY COMPLIANCE GATES PASSED.")
    sys.exit(0)

if __name__ == "__main__":
    validate_gate()
