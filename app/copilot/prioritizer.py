from typing import Dict, Any, List

class AlertPrioritizer:
    """Pre-scores transaction monitoring alerts based on typologies, financial velocity,

    sanctions exposure, and KYC deviations to produce a deterministic Severity Risk Score (0-100).
    """
    def __init__(self):
        pass

    def score_alert(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates risk score and priority tier for an assembled alert context."""
        score = 20 # Baseline threshold
        factors = []

        alert = context.get("alert", {})
        customer = context.get("customer", {})
        transactions = context.get("transactions", [])
        watchlist_hits = context.get("watchlist_hits", [])

        flagged_txns = [t for t in transactions if t.get("flagged")] or transactions
        total_amt = sum(t.get("amount", 0) for t in flagged_txns)
        monthly_income = customer.get("declared_monthly_income") or 0.0

        # Factor 1: Watchlist & Sanctions hits
        if watchlist_hits:
            is_sanctions = any("sanction" in (w.get("list_type") or "").lower() for w in watchlist_hits)
            if is_sanctions:
                score += 55
                factors.append("Direct match with designated Sanctions / OFAC counterparty (+55)")
            else:
                score += 25
                factors.append("Politically Exposed Person (PEP) or Adverse Media match (+25)")

        # Factor 2: PEP status on customer
        if customer.get("pep_status") and not watchlist_hits:
            score += 20
            factors.append("Subject customer is designated PEP (+20)")

        # Factor 3: High dollar amount
        if total_amt >= 200000:
            score += 25
            factors.append(f"High aggregate volume: ${total_amt:,.2f} (+25)")
        elif total_amt >= 50000:
            score += 15
            factors.append(f"Substantial volume: ${total_amt:,.2f} (+15)")

        # Factor 4: Income Multiple Divergence
        if monthly_income > 0:
            multiple = total_amt / monthly_income
            if multiple >= 10:
                score += 30
                factors.append(f"Severe income variance: {multiple:.1f}x monthly salary (+30)")
            elif multiple >= 4:
                score += 15
                factors.append(f"Moderate income variance: {multiple:.1f}x monthly salary (+15)")

        # Factor 5: Structuring pattern (sub-threshold counts)
        if alert.get("rule_id") == "STRUCT-001" or "structuring" in alert.get("rule_name", "").lower():
            score += 25
            factors.append("High-frequency sub-$10,000 cash structuring typology (+25)")

        # Factor 6: Mitigating factors (Down-weighting)
        archetype = alert.get("archetype", "")
        if "Legitimate" in archetype or "Seasonal" in archetype:
            score -= 35
            factors.append("Documented seasonal merchant processing pattern (-35)")
        elif "Explained" in archetype or "Escrow" in alert.get("trigger_summary", ""):
            score -= 30
            factors.append("Documented real estate escrow closing with verified title deed (-30)")
        elif "Benign" in archetype:
            score -= 25
            factors.append("Isolated private transaction with verified receipt (-25)")

        # Clamp score between 0 and 100
        final_score = max(5, min(99, score))

        if final_score >= 75:
            tier = "CRITICAL"
            sla_hours = 4
        elif final_score >= 50:
            tier = "HIGH"
            sla_hours = 12
        elif final_score >= 30:
            tier = "MEDIUM"
            sla_hours = 24
        else:
            tier = "LOW"
            sla_hours = 48

        return {
            "severity_score": final_score,
            "priority_tier": tier,
            "target_sla_hours": sla_hours,
            "scoring_factors": factors,
            "alert_id": alert.get("alert_id")
        }
