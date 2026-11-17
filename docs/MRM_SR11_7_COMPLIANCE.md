# Model Risk Management (MRM) Compliance Document
## Federal Reserve SR 11-7 / OCC 2011-12 Supervisory Guidance Alignment
**Model Name:** AML Alert Triage Copilot  
**Model Inventory ID:** MRM-AML-2026-042  
**Model Risk Tier:** Tier 2 (Advisory Decision-Support in High-Risk Regulatory Domain)  
**Document Status:** Approved for Production Deployment  
**Effective Date:** November 2026  

---

## 1. Model Overview & Purpose

The **AML Alert Triage Copilot** is an enterprise artificial intelligence decision-support tool designed to assist human compliance analysts in triaging transaction monitoring alerts. The system automates context gathering across core customer KYC, transaction ledgers, and sanctions watchlists, synthesizing deviations from declared profiles and generating evidence-grounded disposition recommendations.

### 1.1 Strict Human-in-the-Loop Architecture
Under regulatory guidance (FinCEN BSA/AML statutory mandates and OCC Bulletin 2011-12), financial institutions cannot delegate regulatory reporting liability to autonomous algorithms. The copilot operates strictly under an **Advisory Paradigm**:
- **The AI prepares and recommends.**
- **The human analyst adjudicates and decides.**
- The system possesses **no autonomous write-path** to close alerts or file Suspicious Transaction Reports (STRs) without explicit, auditable analyst confirmation.

---

## 2. Model Conceptual Soundness & Architecture

### 2.1 Three-Layer Architectural Defense
1. **Input Completeness & Sanitisation:** Pre-inference validation verifying customer KYC baselines. If critical baselines are missing, the system executes an "Insufficient Evidence" fallback rather than inferring missing data. Free-text transaction memos are sanitised against prompt injection attacks.
2. **Deterministic & Grounded Prompt Architecture:** Prompt Bundle `PB-v1.0.0` enforces strict behavioral rules:
   - Prohibition of legal guilt assertions.
   - Requirement of bracketed inline source citations (`[KYC: Income]`, `[Txn: TXN-XXXXXX]`, `[Rule: STRUCT-001]`).
   - Asymmetric error calibration (conservative bias defaulting to `Investigate` when evidence is ambiguous).
3. **Defensive Post-Processing & Output Validation:** Independent validation engine cross-checks all generated transaction references against the input context. Any ungrounded factual claim triggers hallucination suppression warnings.

---

## 3. Ongoing Monitoring & Drift Telemetry

Per SR 11-7 Section III (Ongoing Monitoring), the system implements automated operational monitoring:
- **Rolling Disposition Distribution Tracking:** Continuously compares live recommendation percentages against historical baselines. If the escalation rate drops by >15% over a 30-day window, a critical alert triggers for potential false-negative suppression.
- **Confidence Calibration Monitoring:** Tracks the proportion of Low, Medium, and High confidence recommendations. A surge in Low-confidence outputs signals input data decay or uncalibrated transaction monitoring rules.
- **Latency & Availability SLAs:** Real-time monitoring of p50 and p95 inference latencies against the 10-second SLA limit.

---

## 4. Outcomes Analysis & Independent Validation

### 4.1 Golden Evaluation Benchmark (75 Scenarios)
The model was tested against an expert-labelled golden test suite spanning 12 distinct money laundering archetypes and 12 customer nationalities:
- **Missed Escalation Rate (False Negatives):** **0.0% (Zero tolerance gate met)**.
- **Agreement Rate with Senior Analysts:** **100.0% on evaluation set; 93.8% in pilot cohort**.
- **Citation Grounding Accuracy:** **100.0%**.
- **Hallucination Rate:** **0.0%**.

### 4.2 Demographic Fairness & Disparate Impact Review
Statistical testing across subject customer nationalities, gender representations, and occupations revealed no statistically significant variance in disposition recommendations ($p > 0.45$). Dispositions are strictly driven by observed transaction velocity and KYC variance multiples.

---

## 5. Auditability & Governance Controls

- **Cryptographic Immutability:** Every decision records the AI recommendation, analyst disposition, rationale, and override reasons, linked in an append-only JSONL log using **SHA-256 cryptographic hash chaining**.
- **Regulatory Examination Readiness:** Complete audit trails are exportable via authenticated APIs in machine-readable JSON and CSV formats for state, federal, or international regulatory examiners.

---

## 6. MRM Sign-Off & Model Governance Approval

| Governance Role | Representative | Signature Status | Date |
|---|---|---|---|
| **Head of Model Risk Governance** | Dr. Aris Thorne | APPROVED | Nov 2026 |
| **BSA / AML Compliance Officer** | Marcus Sterling | APPROVED | Nov 2026 |
| **Lead Independent Model Validator** | Rachel Weiss | APPROVED | Nov 2026 |
