import re
from typing import Dict, Any, List
from app.utils.sanitiser import sanitise_string

class ConversationalAssistant:
    """Provides grounded conversational follow-up capabilities for AML analysts,

    answering ad-hoc investigative questions using the assembled alert dossier.
    """
    def __init__(self):
        pass

    def answer_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processes an analyst question and returns an evidence-grounded answer with source citations."""
        clean_query = sanitise_string(query).lower()
        customer = context.get("customer", {})
        alert = context.get("alert", {})
        txns = context.get("transactions", [])
        prior_alerts = context.get("prior_alerts", [])
        watchlist_hits = context.get("watchlist_hits", [])

        flagged_txns = [t for t in txns if t.get("flagged")] or txns
        total_flagged_amt = sum(t.get("amount", 0) for t in flagged_txns)
        monthly_inc = customer.get("declared_monthly_income") or 0.0

        citations = []
        answer = ""

        # 1. Income / Salary comparison questions
        if any(w in clean_query for w in ["income", "salary", "declared", "earnings", "ratio", "multiple"]):
            if monthly_inc > 0:
                multiple = total_flagged_amt / monthly_inc if monthly_inc else 0
                answer = (
                    f"The customer's declared monthly income is ${monthly_inc:,.2f} [KYC: Income] "
                    f"(${customer.get('declared_annual_income', 0):,.2f} annually) as a '{customer.get('occupation', 'Unspecified')}' [KYC: Occupation]. "
                    f"The flagged activity of ${total_flagged_amt:,.2f} [Txn Records] represents approximately "
                    f"{multiple:.1f}x their declared monthly income."
                )
                citations.extend(["[KYC: Income]", "[KYC: Occupation]", "[Txn Records]"])
            else:
                answer = "Customer declared income is missing or unverified in current KYC records [KYC Profile]."
                citations.append("[KYC Profile]")

        # 2. Counterparty / Sanctions / Watchlist questions
        elif any(w in clean_query for w in ["counterparty", "counterparties", "watchlist", "sanction", "pep", "who sent", "sender"]):
            counterparties = list({t.get("counterparty") for t in txns if t.get("counterparty")})
            if watchlist_hits:
                hits_desc = "; ".join([f"{h['matched_name']} on {h['list_type']}" for h in watchlist_hits])
                answer = (
                    f"Identified counterparties: {', '.join(counterparties) if counterparties else 'None (Cash Deposits)'} [Counterparty Data]. "
                    f"CRITICAL: Direct watchlist hit detected for {hits_desc} [Watchlist]."
                )
                citations.extend(["[Counterparty Data]", "[Watchlist]"])
            elif counterparties:
                answer = (
                    f"The identified counterparties for this customer are: {', '.join(counterparties)} [Counterparty Data]. "
                    f"None of these entities have active sanctions matches on current internal watchlists [Watchlist]."
                )
                citations.extend(["[Counterparty Data]", "[Watchlist]"])
            else:
                answer = (
                    "Transactions were conducted primarily via physical cash deposits or ATM channels without named third-party counterparties [Txn Records]."
                )
                citations.append("[Txn Records]")

        # 3. Transaction breakdown / dates / channels
        elif any(w in clean_query for w in ["transaction", "deposit", "date", "channel", "branch", "when", "how many"]):
            dates = sorted([t.get("date", "") for t in flagged_txns if t.get("date")])
            channels = list({t.get("channel", "Unknown") for t in flagged_txns})
            first_txn = flagged_txns[0]["txn_id"] if flagged_txns else "TXN-UNKNOWN"
            answer = (
                f"There are {len(flagged_txns)} flagged transaction(s) totalling ${total_flagged_amt:,.2f} [Txn Records]. "
                f"Activity spans from {dates[0] if dates else 'N/A'} to {dates[-1] if dates else 'N/A'} across channels: {', '.join(channels)} [Txn: {first_txn}]. "
                f"Triggered under rule '{alert.get('rule_name')}' [Rule: {alert.get('rule_id')}]."
            )
            citations.extend(["[Txn Records]", f"[Txn: {first_txn}]", f"[Rule: {alert.get('rule_id')}]"])

        # 4. Prior alert history / SARs
        elif any(w in clean_query for w in ["prior", "history", "previous", "sar", "past alerts"]):
            if prior_alerts:
                pa_list = "; ".join([f"{a['alert_id']} ({a['rule']}, {a['date']}) - {a.get('status', 'Closed')}" for a in prior_alerts])
                answer = f"Customer has {len(prior_alerts)} prior alert(s) on record: {pa_list} [Prior Alert Records]."
                citations.append("[Prior Alert Records]")
            else:
                answer = "Customer has no previous alert history or prior SAR filings on record [Prior Alert Records]."
                citations.append("[Prior Alert Records]")

        # 5. Fallback for unanswerable / missing data
        else:
            answer = (
                f"Based on the dossier for alert {alert.get('alert_id')} [Rule: {alert.get('rule_id')}], "
                f"the subject is {customer.get('name', 'Customer')} [KYC: Name]. "
                "The specific information queried is not recorded in the provided dossier. Please query the core banking system or request customer CDD documents."
            )
            citations.extend(["[KYC: Name]", f"[Rule: {alert.get('rule_id')}]"])

        return {
            "query": query,
            "answer": answer,
            "source_citations": list(set(citations)),
            "alert_id": alert.get("alert_id")
        }
