from typing import List, Dict, Any
from collections import defaultdict

def compute_evaluation_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Computes comprehensive AML evaluation metrics per PRD §4.2 and AI_SYSTEM_DESIGN §10.3."""
    total_cases = len(results)
    if total_cases == 0:
        return {}

    agreements = 0
    missed_escalations = 0
    total_expert_escalates = 0
    ai_close_count = 0
    ai_close_correct = 0
    total_citations = 0
    valid_citations = 0
    total_hallucinations = 0
    latencies = []

    # Confusion matrix: [Expected][Predicted]
    labels = ["Close", "Investigate", "Escalate"]
    confusion_matrix = {exp: {pred: 0 for pred in labels} for exp in labels}

    # Bias tracking
    nationality_distribution = defaultdict(lambda: defaultdict(int))
    occupation_distribution = defaultdict(lambda: defaultdict(int))

    for res in results:
        expected = res["expected_disposition"]
        predicted = res["predicted_disposition"]
        confidence = res.get("confidence", "Medium")
        latencies.append(res.get("response_time_ms", 0))

        if expected in confusion_matrix and predicted in confusion_matrix[expected]:
            confusion_matrix[expected][predicted] += 1

        # Agreement
        if expected == predicted:
            agreements += 1

        # Guardrail: Missed Escalations (False Negative)
        if expected == "Escalate":
            total_expert_escalates += 1
            if predicted == "Close":
                missed_escalations += 1

        # False positive screening precision (Predicted Close vs Expected Close)
        if predicted == "Close":
            ai_close_count += 1
            if expected == "Close":
                ai_close_correct += 1

        # Citations
        c_stats = res.get("citation_stats", {})
        total_citations += c_stats.get("total_citations", 0)
        valid_citations += c_stats.get("valid_count", len(c_stats.get("valid_citations", [])))

        # Hallucinations
        total_hallucinations += res.get("hallucinations_detected", 0)

        # Demographics
        demo = res.get("customer_demographics", {})
        nat = demo.get("nationality", "Unknown")
        occ = demo.get("occupation", "Unknown")
        nationality_distribution[nat][predicted] += 1
        occupation_distribution[occ][predicted] += 1

    agreement_rate = (agreements / total_cases) * 100.0
    missed_escalation_rate = (missed_escalations / total_expert_escalates * 100.0) if total_expert_escalates > 0 else 0.0
    fp_precision = (ai_close_correct / ai_close_count * 100.0) if ai_close_count > 0 else 100.0
    citation_accuracy = (valid_citations / total_citations * 100.0) if total_citations > 0 else 100.0
    hallucination_rate = (total_hallucinations / total_cases) * 100.0
    avg_latency_ms = sum(latencies) / total_cases if total_cases > 0 else 0

    return {
        "total_cases_evaluated": total_cases,
        "agreement_rate_percent": round(agreement_rate, 1),
        "missed_escalations_count": missed_escalations,
        "missed_escalation_rate_percent": round(missed_escalation_rate, 2),
        "guardrail_passed": missed_escalation_rate == 0.0,
        "fp_screening_precision_percent": round(fp_precision, 1),
        "citation_accuracy_percent": round(citation_accuracy, 1),
        "total_hallucinations": total_hallucinations,
        "hallucination_rate_percent": round(hallucination_rate, 1),
        "avg_response_time_ms": round(avg_latency_ms, 1),
        "confusion_matrix": confusion_matrix,
        "bias_nationality": dict(nationality_distribution),
        "bias_occupation": dict(occupation_distribution),
        "thresholds_summary": {
            "missed_escalations": "PASSED (Target: 0%)" if missed_escalation_rate == 0.0 else "FAILED",
            "agreement_rate": "PASSED (>= 85%)" if agreement_rate >= 85.0 else "FAILED",
            "fp_precision": "PASSED (>= 90%)" if fp_precision >= 90.0 else "FAILED",
            "citation_accuracy": "PASSED (>= 95%)" if citation_accuracy >= 95.0 else "FAILED",
            "hallucination_rate": "PASSED (< 2%)" if hallucination_rate < 2.0 else "FAILED"
        }
    }
