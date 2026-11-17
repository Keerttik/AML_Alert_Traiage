import json
import hashlib
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple
from app.utils.config import DATA_DIR

class AnonymisationPipeline:
    """ETL Pipeline that ingests raw/synthetic monitoring system data, applies consistent

    pseudonymisation to customer identifiers, and outputs sandboxed datasets for pilot testing.
    """
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.salt = "AML_PILOT_SALT_2026"
        self._name_mapping: Dict[str, str] = {}
        self._account_mapping: Dict[str, str] = {}

    def pseudonymise_id(self, original_id: str, prefix: str = "ANON") -> str:
        """Deterministically hashes an identifier to maintain consistency across tables."""
        raw = f"{original_id}_{self.salt}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()
        return f"{prefix}-{digest}"

    def generate_pilot_dataset(self, target_alert_count: int = 200) -> Dict[str, Any]:
        """Generates an expanded pilot sandbox dataset of 200+ alerts from archetypes,

        preserving financial topologies and generating realistic transaction ledgers.
        """
        # Load base seed archetypes
        with open(self.data_dir / "alerts.json", "r", encoding="utf-8") as f:
            base_alerts = json.load(f)
        with open(self.data_dir / "customers.json", "r", encoding="utf-8") as f:
            base_customers = json.load(f)
        with open(self.data_dir / "transactions.json", "r", encoding="utf-8") as f:
            base_txns = json.load(f)

        cust_lookup = {c["customer_id"]: c for c in base_customers}
        
        pilot_alerts = []
        pilot_customers = {}
        pilot_transactions = []

        branches = ["Midtown Hub", "Downtown Financial", "West End Commercial", "Airport Plaza", "Metro Express ATM", "Online Portal"]
        channels = ["Branch Teller", "Branch ATM", "Online Wire", "ACH Transfer", "International Wire"]

        for i in range(1, target_alert_count + 1):
            seed_alert = base_alerts[(i - 1) % len(base_alerts)]
            seed_cust = cust_lookup.get(seed_alert["customer_id"], base_customers[0])
            
            # Create synthetic pilot customer
            anon_cust_id = f"PILOT-CUST-{i:04d}"
            anon_acct_num = f"ACCT-88{i:05d}"
            
            # Subtle variation on declared income (+/- 15%)
            variance = 1.0 + random.uniform(-0.15, 0.15)
            monthly_inc = round((seed_cust.get("declared_monthly_income") or 5000) * variance, 2)
            annual_inc = round(monthly_inc * 12, 2)

            anon_cust = {
                "customer_id": anon_cust_id,
                "name": f"Pilot Subject {i:03d} ({seed_cust.get('nationality', 'US')})",
                "account_number": anon_acct_num,
                "account_type": seed_cust.get("account_type", "Personal Checking"),
                "occupation": seed_cust.get("occupation") if seed_alert["archetype"] != "Missing KYC Data" else None,
                "declared_annual_income": annual_inc if seed_alert["archetype"] != "Missing KYC Data" else None,
                "declared_monthly_income": monthly_inc if seed_alert["archetype"] != "Missing KYC Data" else None,
                "account_open_date": seed_cust.get("account_open_date", "2023-01-15"),
                "risk_rating": seed_cust.get("risk_rating", "Medium"),
                "nationality": seed_cust.get("nationality", "US"),
                "pep_status": seed_cust.get("pep_status", False),
                "expected_monthly_volume": {
                    "deposits": round(monthly_inc * 1.2, 2),
                    "withdrawals": round(monthly_inc * 1.1, 2)
                } if seed_alert["archetype"] != "Missing KYC Data" else None,
                "notes": f"Pilot dataset customer mapped from archetype '{seed_alert.get('archetype')}'."
            }
            pilot_customers[anon_cust_id] = anon_cust

            # Generate corresponding transactions
            alert_id = f"ALT-PILOT-{i:04d}"
            cust_txns = [t for t in base_txns if t.get("customer_id") == seed_alert["customer_id"]]
            flagged_ids = []

            for t_idx, t in enumerate(cust_txns):
                t_anon_id = f"TXN-P{i:04d}-{t_idx+1:02d}"
                amount_var = round(t["amount"] * variance, 2)
                is_flagged = t.get("flagged", False)
                if is_flagged:
                    flagged_ids.append(t_anon_id)

                pilot_transactions.append({
                    "txn_id": t_anon_id,
                    "customer_id": anon_cust_id,
                    "date": t.get("date", "2026-11-01"),
                    "amount": amount_var,
                    "type": t.get("type", "Transfer"),
                    "direction": t.get("direction", "Credit"),
                    "counterparty": t.get("counterparty"),
                    "channel": random.choice(branches) if "Teller" in t.get("channel", "") else t.get("channel", "Online"),
                    "memo": t.get("memo", ""),
                    "flagged": is_flagged
                })

            # Create pilot alert record
            pilot_alerts.append({
                "alert_id": alert_id,
                "customer_id": anon_cust_id,
                "rule_id": seed_alert["rule_id"],
                "rule_name": seed_alert["rule_name"],
                "rule_description": seed_alert.get("rule_description", ""),
                "trigger_date": seed_alert["trigger_date"],
                "trigger_summary": seed_alert["trigger_summary"].replace(seed_alert["customer_id"], anon_cust_id),
                "priority": seed_alert.get("priority", "Medium"),
                "status": "Open",
                "archetype": seed_alert.get("archetype", "Standard"),
                "ground_truth_disposition": seed_alert["ground_truth_disposition"],
                "ground_truth_rationale": seed_alert["ground_truth_rationale"],
                "flagged_txn_ids": flagged_ids
            })

        return {
            "alerts": pilot_alerts,
            "customers": list(pilot_customers.values()),
            "transactions": pilot_transactions
        }

    def save_pilot_sandbox(self, output_dir: Path = None):
        """Saves generated 200-alert pilot sandbox data to disk."""
        target_dir = output_dir or (self.data_dir / "pilot_sandbox")
        target_dir.mkdir(parents=True, exist_ok=True)
        
        data = self.generate_pilot_dataset(target_alert_count=200)

        with open(target_dir / "pilot_alerts.json", "w", encoding="utf-8") as f:
            json.dump(data["alerts"], f, indent=2)
        with open(target_dir / "pilot_customers.json", "w", encoding="utf-8") as f:
            json.dump(data["customers"], f, indent=2)
        with open(target_dir / "pilot_transactions.json", "w", encoding="utf-8") as f:
            json.dump(data["transactions"], f, indent=2)

        return target_dir, len(data["alerts"])
