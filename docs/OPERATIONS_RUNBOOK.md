# AML Alert Triage Copilot — Production Operations Runbook
**Document Version:** 1.0  
**Effective Date:** November 2026  
**Target Audience:** Compliance Operations, SRE / DevOps, Tier 1/2 Support Engineers  

---

## 1. System Overview & Architecture Summary

The AML Alert Triage Copilot is a mission-critical hybrid system running an API gateway, a context assembly pipeline, a dual-inference copilot engine (Live LLM + Offline Deterministic Rule Engine), and an immutable cryptographic audit logger.

```
Incoming Alert -> Ingest API -> Context Assembly -> Copilot Engine -> Validation -> Analyst Workspace -> Audit Logger
```

---

## 2. Standard Operational Workflows

### 2.1 Starting the Production API Service
```bash
uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2.2 Starting the Multi-Role Compliance Dashboard
```bash
py -m streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
```

### 2.3 Running Quarterly Model Revalidation & Regression Suite
```bash
py evaluation/run_evaluation.py
```
*Note: Any release or revalidation that yields `missed_escalations > 0` must block deployment immediately.*

---

## 3. Incident Response & Troubleshooting Playbooks

### Playbook A: External LLM API Outage / High Latency
- **Symptom:** `504 Gateway Timeout` or latency exceeding 10,000ms.
- **Automated Fallback:** The copilot automatically degrades to the **Deterministic AML Expert Engine** (`deterministic-aml-rule-engine-v1`).
- **Analyst Experience:** A banner appears: *"Inference running in Deterministic Engine Mode. All source citations verified."*
- **Action Required:**
  1. Check status of LLM provider (Google Gemini API / VPC endpoints).
  2. Verify API key quotas in Google Cloud Console.
  3. No analyst downtime is incurred due to deterministic offline fallback.

### Playbook B: Audit Hash Chain Integrity Breach
- **Symptom:** Dashboard or health check reports: `🚨 Audit Integrity Breach Detected`.
- **Root Cause:** Manual edit or retroactive alteration of the append-only `audit_log.jsonl` file.
- **Action Required:**
  1. Quarantine current log file immediately to `/quarantine/audit_log_corrupt_<timestamp>.jsonl`.
  2. Run integrity diagnostic script:
     ```bash
     py -c "from app.data.audit_logger import AuditLogger; ok, errs = AuditLogger().verify_chain_integrity(); print(errs)"
     ```
  3. Cross-reference entry hashes against backup write-once storage (WORM) or SIEM log forwarders (Splunk/Datadog).
  4. Escalate to Chief Information Security Officer (CISO) and Head of Compliance within 4 hours.

### Playbook C: Sudden Distribution Drift Alert
- **Symptom:** Drift telemetry flag `CRITICAL_DRIFT: Escalation rate dropped < 10%`.
- **Root Cause:** Upstream changes in monitoring rule thresholds (e.g. Mantas/Actimize rule logic altered) or data ingestion defect.
- **Action Required:**
  1. Review latest batch of ingested alerts in `app/monitoring/drift_detector.py`.
  2. Verify if upstream transaction monitoring system updated rule tuning without notifying compliance ops.
  3. Re-run 75-case golden evaluation suite to confirm copilot prompt integrity is intact.

---

## 4. Model Rollback Protocol

If a new prompt bundle or model version exhibits unexpected degradation in production:
1. Revert `PROMPT_BUNDLE_VERSION` in `app/utils/config.py` to the previous stable release (e.g. `PB-v1.0.0`).
2. Restart API workers:
   ```bash
   pkill -HUP uvicorn
   ```
3. Run evaluation verification:
   ```bash
   py evaluation/run_evaluation.py
   ```
4. Confirm audit records reflect the reverted `prompt_bundle_version`.

---

## 5. Maintenance & Retention Cadence

| Activity | Frequency | Responsible Team | Verification Artifact |
|---|---|---|---|
| **Golden Suite Regression** | Weekly (Automated CI/CD) | DevOps / Engineering | `eval_report_latest.json` |
| **Audit Log Hash Verification** | Daily (Automated cron) | Compliance Ops | `audit_verification.log` |
| **Fairness & Bias Evaluation** | Monthly | Compliance QA | Bias audit matrix |
| **Model Risk Revalidation** | Quarterly | Model Risk Management (MRM) | Formal MRM re-attestation |
| **Cryptographic Archive Backup**| Monthly | Infrastructure / SecOps | Cold WORM storage archive |
