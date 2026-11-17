from typing import Dict, Any, List

def generate_draft_str(context: Dict[str, Any], rationale_reasons: List[str]) -> str:
    """Generates a standard regulatory 5W1H Suspicious Transaction Report (STR) narrative draft

    with strict source citations and required audit disclaimers.
    """
    customer = context.get("customer", {})
    alert = context.get("alert", {})
    transactions = context.get("transactions", [])
    flagged_txns = [t for t in transactions if t.get("flagged")] or transactions

    total_amount = sum(t.get("amount", 0) for t in flagged_txns)
    dates = sorted([t.get("date", "") for t in flagged_txns if t.get("date")])
    date_start = dates[0] if dates else "N/A"
    date_end = dates[-1] if dates else "N/A"

    channels = list({t.get("channel", "Unknown") for t in flagged_txns})
    counterparties = list({t.get("counterparty") for t in flagged_txns if t.get("counterparty")})

    reasons_text = "\n".join([f"  - {r}" for r in rationale_reasons]) if rationale_reasons else "  - Unexplained deviation from profile"

    narrative = f"""[DRAFT — REQUIRES ANALYST REVIEW BEFORE SUBMISSION]
================================================================================
SUSPICIOUS TRANSACTION REPORT (STR) NARRATIVE DRAFT
Alert Reference: {alert.get('alert_id', 'N/A')} [Rule: {alert.get('rule_id', 'N/A')}]
================================================================================

1. WHO (Subject Information):
The subject of this report is {customer.get('name', 'Unknown')} [KYC: Name], account #{customer.get('account_number', 'N/A')} [KYC: Account], an individual whose declared occupation is '{customer.get('occupation', 'Unspecified')}' [KYC: Occupation] with a declared monthly income of ${customer.get('declared_monthly_income', 0):,.2f} [KYC: Income]. Account risk rating: {customer.get('risk_rating', 'Medium')} [KYC: Risk].

2. WHAT (Suspicious Activity):
During the period under review, the account exhibited unusual activity consisting of {len(flagged_txns)} flagged transaction(s) aggregating to ${total_amount:,.2f} [Txn Records]. The triggering activity is categorized under monitoring rule: {alert.get('rule_name', 'Rule')} [Rule: {alert.get('rule_id', 'N/A')}].

3. WHEN (Timeframe):
The activity occurred between {date_start} and {date_end} [Txn Records], representing a concentrated burst of transactions over an abbreviated window.

4. WHERE (Jurisdiction & Channels):
Transactions originated/settled across channels including: {', '.join(channels)} [Txn Channels].
Counterparties identified: {', '.join(counterparties) if counterparties else 'None / Cash Deposits'} [Counterparty Data].

5. WHY (Basis for Suspicion):
The activity warrants escalation due to the following specific deviations from the subject's customer profile and standard AML typologies:
{reasons_text}
The aggregated volume of ${total_amount:,.2f} significantly exceeds the subject's expected monthly volume of ${customer.get('expected_monthly_volume', {}).get('deposits', 0):,.2f} [KYC: Baseline] with no verified economic or commercial justification on file.

6. HOW (Methodology / Typology):
The pattern reflects characteristics of {alert.get('archetype', 'Suspicious Activity')}, specifically executed via {', '.join(channels[:3])}.

SUPPORTING EVIDENCE SUMMARY:
- Primary Trigger: {alert.get('trigger_summary', 'N/A')} [Rule: {alert.get('rule_id', 'N/A')}]
- Referenced Flagged Transactions: {', '.join([t.get('txn_id', '') for t in flagged_txns[:6]])} [Txn Records]

================================================================================
[DRAFT — PREPARED BY AML COPILOT. MUST BE VERIFIED AND APPROVED BY ANALYST]
"""
    return narrative
