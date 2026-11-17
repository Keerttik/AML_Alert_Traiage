import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from app.utils.config import DATA_DIR
from app.utils.sanitiser import sanitise_payload

class ContextAssembler:
    def __init__(self, data_dir: Optional[Path] = None, use_pilot_sandbox: bool = False):
        self.data_dir = data_dir or DATA_DIR
        self.use_pilot_sandbox = use_pilot_sandbox
        self._load_data()

    def set_dataset_mode(self, use_pilot_sandbox: bool):
        self.use_pilot_sandbox = use_pilot_sandbox
        self._load_data()

    def _load_data(self):
        if self.use_pilot_sandbox and (self.data_dir / "pilot_sandbox" / "pilot_alerts.json").exists():
            sandbox_dir = self.data_dir / "pilot_sandbox"
            with open(sandbox_dir / "pilot_alerts.json", "r", encoding="utf-8") as f:
                self.alerts: List[Dict[str, Any]] = json.load(f)
            with open(sandbox_dir / "pilot_customers.json", "r", encoding="utf-8") as f:
                self.customers: List[Dict[str, Any]] = json.load(f)
            with open(sandbox_dir / "pilot_transactions.json", "r", encoding="utf-8") as f:
                self.transactions: List[Dict[str, Any]] = json.load(f)
        else:
            with open(self.data_dir / "alerts.json", "r", encoding="utf-8") as f:
                self.alerts: List[Dict[str, Any]] = json.load(f)
            with open(self.data_dir / "customers.json", "r", encoding="utf-8") as f:
                self.customers: List[Dict[str, Any]] = json.load(f)
            with open(self.data_dir / "transactions.json", "r", encoding="utf-8") as f:
                self.transactions: List[Dict[str, Any]] = json.load(f)

        with open(self.data_dir / "watchlists.json", "r", encoding="utf-8") as f:
            self.watchlists: List[Dict[str, Any]] = json.load(f)

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        return self.alerts

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        for alert in self.alerts:
            if alert["alert_id"] == alert_id:
                return alert
        return None

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        for customer in self.customers:
            if customer["customer_id"] == customer_id:
                return customer
        return None

    def check_input_completeness(self, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validates whether required context fields are present per AI_SYSTEM_DESIGN §2.3.

        Returns (is_complete, missing_fields).
        """
        missing_fields = []
        customer = context.get("customer") or {}
        alert = context.get("alert") or {}
        transactions = context.get("transactions") or []

        if not alert.get("rule_name") or not alert.get("trigger_summary"):
            missing_fields.append("Alert Rule Definition & Trigger Summary")

        if not customer.get("name"):
            missing_fields.append("Customer Legal Name")
        if not customer.get("occupation"):
            missing_fields.append("Customer Declared Occupation")
        if customer.get("declared_annual_income") is None:
            missing_fields.append("Customer Declared Annual Income")
        if not customer.get("expected_monthly_volume"):
            missing_fields.append("Customer Expected Monthly Volume Baseline")

        if not transactions:
            missing_fields.append("Transaction Ledger Records")

        is_complete = len(missing_fields) == 0
        return is_complete, missing_fields

    def assemble_context(self, alert_id: str) -> Dict[str, Any]:
        """Assembles a structured context payload for an alert, checking watchlists

        and prior alert history.
        """
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found.")

        customer_id = alert["customer_id"]
        customer = self.get_customer_by_id(customer_id) or {}

        # Get transactions for customer
        customer_txns = [
            txn for txn in self.transactions if txn.get("customer_id") == customer_id
        ]
        # Sort chronologically
        customer_txns.sort(key=lambda x: x.get("date", ""))

        # Check counterparties against watchlists
        counterparties = set()
        watchlist_hits = []
        for txn in customer_txns:
            cp = txn.get("counterparty")
            if cp:
                counterparties.add(cp)
                for wl in self.watchlists:
                    if wl["name"].lower() in cp.lower() or cp.lower() in wl["name"].lower():
                        watchlist_hits.append({
                            "entity_id": wl["entity_id"],
                            "matched_name": wl["name"],
                            "txn_id": txn["txn_id"],
                            "list_type": wl["list_type"],
                            "designation": wl["designation"]
                        })

        # Check if customer himself is on watchlist (e.g. PEP)
        if customer.get("name"):
            for wl in self.watchlists:
                if wl["name"].lower() == customer["name"].lower():
                    watchlist_hits.append({
                        "entity_id": wl["entity_id"],
                        "matched_name": wl["name"],
                        "entity_type": "Subject Customer",
                        "list_type": wl["list_type"],
                        "designation": wl["designation"]
                    })

        # Construct raw payload
        context_payload = {
            "alert": {
                "alert_id": alert["alert_id"],
                "rule_id": alert["rule_id"],
                "rule_name": alert["rule_name"],
                "rule_description": alert.get("rule_description", ""),
                "trigger_date": alert["trigger_date"],
                "trigger_summary": alert["trigger_summary"],
                "priority": alert.get("priority", "Medium"),
                "archetype": alert.get("archetype", "")
            },
            "customer": {
                "customer_id": customer.get("customer_id", customer_id),
                "name": customer.get("name"),
                "account_number": customer.get("account_number"),
                "account_type": customer.get("account_type"),
                "occupation": customer.get("occupation"),
                "declared_annual_income": customer.get("declared_annual_income"),
                "declared_monthly_income": customer.get("declared_monthly_income"),
                "account_open_date": customer.get("account_open_date"),
                "risk_rating": customer.get("risk_rating"),
                "nationality": customer.get("nationality"),
                "pep_status": customer.get("pep_status", False),
                "expected_monthly_volume": customer.get("expected_monthly_volume"),
                "notes": customer.get("notes", "")
            },
            "transactions": customer_txns,
            "counterparties": list(counterparties),
            "watchlist_hits": watchlist_hits,
            "prior_alerts": [
                {
                    "alert_id": a["alert_id"],
                    "date": a["trigger_date"],
                    "rule": a["rule_name"],
                    "status": a.get("status", "Closed")
                }
                for a in self.alerts
                if a.get("customer_id") == customer_id and a["alert_id"] != alert_id
            ]
        }

        # Apply sanitisation to neutralise prompt injection in free-text fields
        sanitised_payload = sanitise_payload(context_payload)

        # Check completeness
        is_complete, missing_fields = self.check_input_completeness(sanitised_payload)
        sanitised_payload["_metadata"] = {
            "is_complete": is_complete,
            "missing_fields": missing_fields
        }

        return sanitised_payload
