import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.copilot.engine import CopilotEngine
from app.utils.config import EVALUATION_DIR
from evaluation.metrics import compute_evaluation_metrics

def run_evaluation(api_key: str = None) -> dict:
    golden_path = EVALUATION_DIR / "golden_dataset.json"
    with open(golden_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = CopilotEngine(api_key=api_key)
    eval_results = []

    print(f"\n=======================================================")
    print(f"AML ALERT TRIAGE COPILOT — EVALUATION HARNESS")
    print(f"Evaluating {len(cases)} Golden Test Scenarios...")
    print(f"=======================================================\n")

    for idx, case in enumerate(cases):
        alert_id = case["alert_id"]
        exp_disp = case["expected_disposition"]
        archetype = case.get("archetype", "Standard")

        res = engine.triage_alert(alert_id)
        pred_disp = res["analysis"]["recommendation"]
        confidence = res["analysis"]["confidence"]
        val_status = res["validation"]["status"]
        hallucinations = res["validation"]["hallucinations_detected"]
        citation_stats = res["validation"]["citation_stats"]

        is_match = (exp_disp == pred_disp)
        status_symbol = "✓" if is_match else "✗"

        print(f"[{status_symbol}] Case {case['case_id']}: {archetype:<30} | Expected: {exp_disp:<11} | Pred: {pred_disp:<11} | Conf: {confidence:<6}")

        eval_results.append({
            "case_id": case["case_id"],
            "alert_id": alert_id,
            "archetype": archetype,
            "expected_disposition": exp_disp,
            "predicted_disposition": pred_disp,
            "confidence": confidence,
            "validation_status": val_status,
            "hallucinations_detected": hallucinations,
            "citation_stats": citation_stats,
            "response_time_ms": res["metadata"]["response_time_ms"],
            "customer_demographics": case.get("customer_demographics", {})
        })

    metrics = compute_evaluation_metrics(eval_results)

    # Save report
    report_output = {
        "metrics": metrics,
        "results": eval_results
    }
    report_file = EVALUATION_DIR / "eval_report_latest.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_output, f, indent=2)

    print("\n=======================================================")
    print("EVALUATION SUMMARY & GUARDRAIL CHECKS")
    print("=======================================================")
    print(f"Total Cases Evaluated:           {metrics['total_cases_evaluated']}")
    print(f"Agreement Rate:                  {metrics['agreement_rate_percent']}%  [{metrics['thresholds_summary']['agreement_rate']}]")
    print(f"Missed Escalations (Guardrail):  {metrics['missed_escalations_count']}  [{metrics['thresholds_summary']['missed_escalations']}]")
    print(f"FP Screening Precision:          {metrics['fp_screening_precision_percent']}%  [{metrics['thresholds_summary']['fp_precision']}]")
    print(f"Citation Accuracy:               {metrics['citation_accuracy_percent']}%  [{metrics['thresholds_summary']['citation_accuracy']}]")
    print(f"Hallucination Rate:              {metrics['hallucination_rate_percent']}%  [{metrics['thresholds_summary']['hallucination_rate']}]")
    print(f"Average Response Time:           {metrics['avg_response_time_ms']} ms")
    print(f"\nReport saved to: {report_file}")
    print("=======================================================\n")

    return report_output

if __name__ == "__main__":
    run_evaluation()
