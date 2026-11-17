# Implementation Plan
# AML Alert Triage Copilot — Phase-wise Roadmap

**Document Version:** 1.0  
**Author:** Product Manager  
**Date:** November 2026  
**Companion to:** PRD_AML_Copilot.md, AI_SYSTEM_DESIGN.md

---

## Overview

This document breaks the AML Alert Triage Copilot from concept to production into **three phases**, each with defined goals, milestones, deliverables, timelines, team requirements, and exit criteria. The phases are designed so that each one delivers standalone value and de-risks the next.

```
 PHASE 1                    PHASE 2                     PHASE 3
 Prototype                  Pilot                       Production
 (Weeks 1–6)                (Weeks 7–14)                (Weeks 15–24)
 ─────────────────────────  ──────────────────────────  ──────────────────────────
 Prove the concept          Validate with real users     Scale and harden
 Synthetic data             Sandboxed real data          Full integration
 Solo / small team          + Analysts + Compliance      + Eng + Infra + Legal
 Portfolio-ready demo       Internal pilot program       Production deployment
```

---

## Phase 1: Prototype (Weeks 1–6)

### Goal
Build a functional, demo-ready prototype using synthetic data that demonstrates product thinking, AI guardrails, evaluation rigour, and user-centred design.

### Who is this for?
- **Primary:** Portfolio showcase for PM interviews and hiring panels
- **Secondary:** Internal stakeholder buy-in for a pilot programme

---

### Sprint 1 (Weeks 1–2): Foundation & Data

#### Objectives
- Set up project infrastructure
- Create synthetic alert dataset
- Build data models and context assembly service

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 1.1 | **Project setup** | Repository, folder structure (per AI_SYSTEM_DESIGN §13.1), virtual environment, dependencies | `requirements.txt` installs cleanly; app skeleton runs |
| 1.2 | **Synthetic data: Customers** | 12–15 fictional customer KYC profiles covering diverse occupations, income levels, risk ratings, PEP status, nationalities | `customers.json` validated against schema |
| 1.3 | **Synthetic data: Transactions** | Transaction ledgers for each customer — normal baseline + flagged activity | `transactions.json` with ≥100 transactions across all customers |
| 1.4 | **Synthetic data: Alerts** | 12+ alert scenarios covering all archetypes (PRD §8.2): structuring, layering, income spike, dormant, round-trip, FPs, missing KYC, mixed signals, PEP, watchlist | `alerts.json` with ground-truth labels |
| 1.5 | **Synthetic data: Watchlists** | Fictional watchlist entries for counterparty-match scenarios | `watchlists.json` |
| 1.6 | **Context Assembly Service** | Python module that takes an `alert_id` and assembles the full context payload (customer + transactions + prior alerts + counterparties + watchlist hits) | Unit tests pass; output matches schema in AI_SYSTEM_DESIGN §2.2 |
| 1.7 | **Input completeness checker** | Validates assembled context; returns "Insufficient Evidence" payload if critical fields are missing | Unit tests cover all missing-data scenarios |

#### Key Decisions in Sprint 1

| Decision | Options | Recommendation |
|---|---|---|
| Data format | JSON files vs. SQLite | **JSON files** — simpler for prototype, easier to inspect and version-control |
| Number of alert scenarios | 10 vs. 15 vs. 20+ | **12–15** — covers all archetypes with manageable effort |
| Customer diversity | Homogeneous vs. diverse demographics | **Diverse** — necessary for bias evaluation later |

---

### Sprint 2 (Weeks 3–4): Copilot Engine & Guardrails

#### Objectives
- Implement the core AI analysis engine
- Build the prompt architecture
- Implement output validation and guardrails
- Create the STR narrative generator

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 2.1 | **Prompt templates** | System prompt, context injection template, user prompt + output schema — all versioned (AI_SYSTEM_DESIGN §3) | Prompt bundle PB-v1.0.0 defined and tested manually against 3 alert scenarios |
| 2.2 | **LLM integration** | API integration with chosen LLM (Gemini / OpenAI / Claude); configurable model, temperature, max tokens | API call returns valid JSON for a sample alert |
| 2.3 | **Citation engine** | Extraction of citations from AI output; validation against input context (AI_SYSTEM_DESIGN §4) | Unit tests: valid citations pass, invalid citations flagged, hallucinated references caught |
| 2.4 | **Output validation pipeline** | JSON schema validation → recommendation value check → citation validation → hallucination detection → prohibited content scan (AI_SYSTEM_DESIGN §8) | End-to-end pipeline tested with valid, invalid, and adversarial outputs |
| 2.5 | **Input sanitisation** | Strip/escape potential injection patterns from free-text fields (transaction memos) | Test with 5 adversarial memo strings; all neutralised |
| 2.6 | **STR narrative generator** | 5W1H structured draft generation for "Escalate" recommendations (AI_SYSTEM_DESIGN §6) | Generated narrative for 3 escalation scenarios reviewed for quality |
| 2.7 | **Copilot engine (integrated)** | End-to-end: `alert_id` → context assembly → input check → LLM call → output validation → structured response | All 12 alert scenarios produce valid, cited, schema-compliant outputs |
| 2.8 | **"Insufficient Evidence" logic** | When input completeness check fails, return structured "insufficient evidence" response without calling LLM | Missing-KYC scenario triggers correct response |

#### Key Decisions in Sprint 2

| Decision | Options | Recommendation |
|---|---|---|
| LLM provider | Gemini 2.5 Pro / GPT-4o / Claude Sonnet 4 | **Evaluate all three** on 5 scenarios; select based on accuracy, citation compliance, and cost. Gemini recommended for portfolio alignment with Google ecosystem |
| Prompt strategy | Zero-shot vs. few-shot | **Few-shot** (2–3 examples) for consistent output format; keep examples in separate config for easy iteration |
| Temperature | 0.0 vs. 0.1 vs. 0.3 | **0.1** — near-deterministic but allows natural language variation |
| JSON enforcement | Prompt-only vs. JSON mode | **JSON mode** where available (Gemini, OpenAI); fallback to prompt-only with retry on parse failure |

---

### Sprint 3 (Weeks 5–6): UI, Audit Log & Evaluation

#### Objectives
- Build the analyst-facing UI (dashboard + triage workspace + audit log viewer)
- Implement the audit logging system
- Build and run the evaluation harness
- Polish for demo-readiness

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 3.1 | **Alert queue dashboard** | Sortable, filterable list of alerts with AI-suggested priority tier, rule type, status, and summary stats | Dashboard loads, filters work, clicking an alert navigates to triage workspace |
| 3.2 | **Triage workspace** | Split view: left = alert data (KYC, transactions, rule details); right = copilot panel (summary, recommendation, STR draft, decision capture) | Analyst can view full context + AI analysis side by side |
| 3.3 | **Citation interactivity** | Clickable citations in copilot panel that highlight corresponding data in the alert data panel | Clicking `[Txn: TXN-990101]` highlights the row in the transaction table |
| 3.4 | **Decision capture form** | Disposition selector (Close / Investigate / Escalate) + rationale text area (pre-filled from AI, editable) + override detection + Submit button | Cannot submit without rationale; override flag auto-detected |
| 3.5 | **STR draft editor** | Editable text area for STR narrative with `[DRAFT]` label; diff view available | Analyst can edit draft; original AI version preserved |
| 3.6 | **Audit log writer** | Append-only JSONL writer capturing full audit entry (AI_SYSTEM_DESIGN §9) with hash chain | Each submission creates a new audit entry; entries are immutable |
| 3.7 | **Audit log viewer** | Searchable, filterable table of all audit entries; expandable rows showing full detail | Filter by date, customer, disposition, override status; export to CSV |
| 3.8 | **Golden evaluation dataset** | 50+ labelled scenarios with expert ground-truth dispositions and rationales | Dataset covers all archetypes, edge cases, and demographic diversity |
| 3.9 | **Automated evaluation script** | Runs all golden scenarios through copilot engine; computes metrics (AI_SYSTEM_DESIGN §10) | Script runs end-to-end; generates report with all metrics |
| 3.10 | **Evaluation dashboard** | UI page showing latest eval metrics: missed escalation rate, agreement rate, FP precision, citation accuracy, hallucination rate | Dashboard renders all metrics with pass/fail indicators |
| 3.11 | **README & documentation** | Executive summary, setup instructions, architecture overview, demo walkthrough, PM case study framing | A reviewer can clone the repo, install deps, and run the demo in <5 minutes |

#### Key Decisions in Sprint 3

| Decision | Options | Recommendation |
|---|---|---|
| Frontend framework | Streamlit vs. React + FastAPI | **Streamlit** for speed-to-demo; consider React if richer interactivity needed |
| Audit log format | JSONL file vs. SQLite | **JSONL** — human-readable, append-only semantics, easy to inspect |
| Evaluation set size | 20 vs. 50 vs. 100 | **50** — sufficient for meaningful metrics; manageable to curate with expert labels |
| Hosting for demo | Local vs. Streamlit Cloud vs. Vercel | **Streamlit Cloud** (free tier) for shareable link in portfolio |

---

### Phase 1 Exit Criteria

| Criterion | Measurement |
|---|---|
| ✅ Prototype runs end-to-end | Analyst can open alert → view AI analysis → make decision → audit entry created |
| ✅ All 12 alert archetypes covered | Synthetic data includes every archetype from PRD §8.2 |
| ✅ Missed escalation rate = 0% | Evaluation suite confirms zero false negatives |
| ✅ Citation accuracy ≥ 95% | Evaluation suite confirms |
| ✅ Hallucination rate < 2% | Evaluation suite confirms |
| ✅ Overall agreement rate ≥ 85% | Evaluation suite confirms |
| ✅ Audit log captures every decision | 100% of submissions have complete audit entries |
| ✅ "Insufficient evidence" works | Missing-KYC scenarios correctly handled |
| ✅ STR draft quality acceptable | 3+ escalation narratives reviewed and deemed reasonable |
| ✅ Demo-ready | README, setup instructions, and walkthrough complete |

---

## Phase 2: Pilot (Weeks 7–14)

### Goal
Validate the copilot with real AML analysts using anonymised/sandboxed data, gather feedback, and refine the system for production viability.

### Prerequisites
- Phase 1 exit criteria met
- Stakeholder approval from Compliance leadership
- Access to anonymised historical alert data (sandboxed environment)
- 3–5 analyst volunteers for pilot participation

---

### Sprint 4 (Weeks 7–9): Data Integration & Analyst Onboarding

#### Objectives
- Replace synthetic data with anonymised real data (sandbox)
- Integrate with sandboxed monitoring system export
- Onboard pilot analysts with training

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 4.1 | **Data pipeline: anonymised alerts** | ETL pipeline to ingest anonymised historical alerts from monitoring system export (CSV/JSON); map to copilot data schema | 200+ real (anonymised) alerts ingested and queryable |
| 4.2 | **Data pipeline: anonymised KYC** | Map anonymised customer profiles to copilot KYC schema | Customer profiles linked to alerts |
| 4.3 | **Data pipeline: transactions** | Map anonymised transaction ledgers | Transactions linked to customers and alerts |
| 4.4 | **Role-based access (basic)** | Simple login with role selection: Analyst, Manager, Auditor | Different roles see different views (Analyst: triage; Manager: audit + metrics; Auditor: audit read-only) |
| 4.5 | **Analyst training materials** | User guide, 15-min walkthrough video, FAQ, "What the copilot can and cannot do" one-pager | Materials reviewed by Compliance; analysts confirm understanding |
| 4.6 | **Feedback mechanism** | Per-alert feedback form: "Was the AI analysis helpful? (1–5)", "Was the recommendation appropriate?", free-text comments | Feedback captured and queryable |
| 4.7 | **Analyst onboarding sessions** | 2× 1-hour training sessions with pilot analysts; hands-on practice with prototype | All pilot analysts complete training; questions documented |

#### Key Decisions in Sprint 4

| Decision | Options | Recommendation |
|---|---|---|
| Anonymisation method | Pseudonymisation vs. synthetic replacement vs. differential privacy | **Pseudonymisation** (consistent fake names/IDs; real patterns preserved) — balances utility and privacy |
| Number of pilot analysts | 3 vs. 5 vs. 10 | **5** — enough for statistical significance on feedback; manageable for support |
| Pilot duration | 2 weeks vs. 4 weeks | **4 weeks** (Sprints 5–6) — sufficient to observe behaviour change and gather meaningful data |

---

### Sprint 5–6 (Weeks 10–14): Live Pilot & Iteration

#### Objectives
- Run the live pilot with real analysts triaging real (anonymised) alerts
- Collect metrics: time per alert, agreement rate, override rate, analyst satisfaction
- Iterate on prompts, UI, and guardrails based on feedback

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 5.1 | **Live pilot execution** | 5 analysts use copilot for daily triage over 4 weeks; parallel to (not replacing) existing workflow | Analysts complete ≥50 alert triages each using the copilot |
| 5.2 | **A/B comparison data** | Compare analyst disposition and time-per-alert with copilot vs. without (historical baseline or same analyst on alternating days) | Statistical comparison report generated |
| 5.3 | **Weekly analyst check-ins** | 30-min weekly sessions with pilot analysts to gather qualitative feedback, pain points, feature requests | Check-in notes documented; themes identified |
| 5.4 | **Prompt iteration (2–3 rounds)** | Refine prompts based on analyst feedback and error analysis; re-run evaluation suite after each change | Each iteration passes all evaluation thresholds |
| 5.5 | **UI refinements** | Address analyst feedback on layout, information density, interaction flow | Top 5 UI feedback items addressed |
| 5.6 | **Expanded evaluation set** | Add 20+ new scenarios based on real alert patterns encountered during pilot | Golden dataset grows to 70+ scenarios |
| 5.7 | **Bias audit report** | Analyse disposition patterns across customer demographics in pilot data | Report shows no statistically significant demographic bias |
| 5.8 | **Pilot results report** | Comprehensive report: quantitative metrics, qualitative feedback, risk assessment, go/no-go recommendation for production | Report reviewed by Compliance leadership |

#### Pilot Success Criteria

| Metric | Target |
|---|---|
| **Time per alert reduction** | ≥ 30% vs. baseline (manual triage) |
| **Missed escalation rate** | 0% (zero tolerance) |
| **AI-analyst agreement rate** | ≥ 80% (lower bar than eval set due to real-world complexity) |
| **Analyst satisfaction (NPS)** | ≥ 3.5 / 5.0 average |
| **Audit completeness** | 100% of pilot decisions have full audit entries |
| **No regulatory concerns raised** | Compliance review signs off |

---

### Phase 2 Exit Criteria

| Criterion | Measurement |
|---|---|
| ✅ Pilot completed with ≥5 analysts over ≥4 weeks | Participation records confirm |
| ✅ Quantitative metrics meet targets | Pilot results report confirms |
| ✅ No missed escalations in pilot | Audit log + expert review confirms |
| ✅ Analyst feedback is net positive | NPS ≥ 3.5; qualitative themes are constructive |
| ✅ Compliance leadership approves production path | Sign-off documented |
| ✅ Prompt and model stabilised | ≤1 prompt change in final 2 weeks of pilot |
| ✅ Bias audit clean | No demographic bias detected |

---

## Phase 3: Production (Weeks 15–24)

### Goal
Harden the system for production deployment: full integration with bank systems, enterprise security, scalability, monitoring, and regulatory compliance.

### Prerequisites
- Phase 2 exit criteria met
- Compliance and Legal sign-off on production deployment
- Infrastructure budget approved
- Security and architecture review completed

---

### Sprint 7–8 (Weeks 15–18): Integration & Security Hardening

#### Objectives
- Integrate with production monitoring and case management systems
- Implement enterprise security controls
- Deploy LLM inference in private cloud / on-premise

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 7.1 | **Monitoring system integration** | Real-time or near-real-time ingestion of alerts from production monitoring system (Actimize / Norkom / in-house) via API or message queue | Alerts flow into copilot within 5 minutes of creation |
| 7.2 | **KYC / CDD system integration** | Real-time query of customer KYC data from core systems | Context assembly fetches live KYC for any alert |
| 7.3 | **Core banking integration** | Transaction ledger retrieval from core banking system | Context assembly fetches relevant transaction window |
| 7.4 | **Case management write-back** | Disposition decisions write back to case management system (analyst-initiated, never AI-initiated) | Analyst "Submit" in copilot updates case status in monitoring system |
| 7.5 | **Private LLM deployment** | LLM inference deployed in bank's private cloud (GCP VPC / Azure Private Link / on-premise GPU cluster) | No customer data leaves bank network boundary |
| 7.6 | **IAM / SSO integration** | SAML/OIDC integration with bank's identity provider; role-based access enforced | Analysts, managers, and auditors see appropriate views |
| 7.7 | **Encryption** | TLS 1.3 in transit; AES-256 at rest for all data stores; HSM for audit log signing | Security audit confirms compliance |
| 7.8 | **Penetration testing** | External pen test of the application; focus on prompt injection, data leakage, privilege escalation | All critical and high findings remediated |

---

### Sprint 9–10 (Weeks 19–22): Scalability, Monitoring & Advanced Features

#### Objectives
- Scale for full analyst team (not just pilot group)
- Implement production monitoring and alerting
- Add advanced features based on pilot feedback

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 9.1 | **Load testing** | Simulate full analyst team (20–50 concurrent users); LLM inference under load | p95 response time < 10 seconds under full load |
| 9.2 | **Model monitoring dashboard** | Track: output distribution drift, latency, error rates, confidence calibration, citation accuracy over time | Dashboard live; alerting configured for threshold breaches |
| 9.3 | **Automated evaluation CI/CD** | Evaluation suite runs automatically on every prompt or model change; blocks deployment if thresholds breached | Pipeline integrated with deployment workflow |
| 9.4 | **Tamper-evident audit log** | Cryptographic hash chain (or integration with tamper-evident ledger) for audit entries; compliant with regulatory retention requirements | Audit team confirms tamper-evidence; retention policy enforced |
| 9.5 | **Advanced: Analyst feedback loop** | Structured feedback from analyst overrides feeds into prompt refinement pipeline and evaluation set expansion | Feedback pipeline active; ≥10 new eval scenarios added per month |
| 9.6 | **Advanced: Conversational follow-up** | Analyst can ask follow-up questions about an alert ("What other counterparties has this customer transacted with?") | Follow-up maintains alert context; citations still required |
| 9.7 | **Advanced: Alert prioritisation** | ML-based pre-scoring to rank alerts by likely severity; copilot analyses highest-priority alerts first | Priority ranking visible in alert queue; analysts report improved workflow |
| 9.8 | **Advanced: Multi-language STR** | STR narrative generation in multiple languages (English + relevant local language) | Narratives generated in 2+ languages; quality reviewed by native speakers |

---

### Sprint 11–12 (Weeks 23–24): Rollout, Training & Handoff

#### Objectives
- Roll out to full analyst team
- Comprehensive training programme
- Operational handoff and documentation

#### Deliverables

| # | Deliverable | Description | Done When |
|---|---|---|---|
| 11.1 | **Phased rollout plan** | Rollout to analyst team in 3 waves (33% each) over 2 weeks; monitoring between waves | Each wave has go/no-go checkpoint based on metrics |
| 11.2 | **Full training programme** | Instructor-led training (2 hours) + self-paced e-learning module + reference guide + FAQ | All analysts complete training before access is granted |
| 11.3 | **Champion network** | 2–3 analyst "champions" trained as power users and first-line support | Champions identified and trained |
| 11.4 | **Operations runbook** | Incident response procedures, escalation paths, model rollback process, evaluation schedule | Runbook reviewed by operations team |
| 11.5 | **Regulatory documentation** | Model risk management (MRM) documentation per SR 11-7; human-in-the-loop evidence package; bias testing results | Compliance and Legal sign off |
| 11.6 | **Post-launch monitoring plan** | Weekly metrics review for first 8 weeks; monthly thereafter; quarterly model revalidation | Monitoring cadence agreed with Compliance |
| 11.7 | **Retrospective & roadmap** | Post-launch retro with all stakeholders; updated roadmap for next 6 months | Retro documented; roadmap approved |

---

### Phase 3 Exit Criteria (Production Launch)

| Criterion | Measurement |
|---|---|
| ✅ Full integration with monitoring, KYC, and case management systems | Integration tests pass; data flows confirmed |
| ✅ Private LLM deployment operational | No customer data leaves bank network |
| ✅ Security audit passed | Pen test + security review — all critical/high findings resolved |
| ✅ Missed escalation rate = 0% on production evaluation set | Automated eval confirms |
| ✅ p95 response time < 10 seconds under full load | Load test confirms |
| ✅ Tamper-evident audit log operational | Audit team confirms |
| ✅ All analysts trained and onboarded | Training completion records |
| ✅ Regulatory documentation complete | Compliance + Legal sign-off |
| ✅ Monitoring and alerting operational | Dashboard live; test alerts fire correctly |
| ✅ Rollback procedure tested | Successful rollback drill completed |

---

## Resource Requirements

### Phase 1 (Prototype)

| Role | Effort | Notes |
|---|---|---|
| Product Manager | 1 person, full-time | Owns scope, data design, evaluation criteria, documentation |
| Full-Stack Developer | 1 person, full-time (or PM with coding skills) | Builds prototype; can be the same person as PM for portfolio projects |
| Subject Matter Expert (AML) | Advisory (2–3 hours/week) | Reviews scenarios, labels evaluation set, validates STR narrative quality |

### Phase 2 (Pilot)

| Role | Effort | Notes |
|---|---|---|
| Product Manager | 1 person, full-time | Runs pilot, analyses feedback, iterates |
| Full-Stack Developer | 1 person, full-time | Data pipeline, UI refinements, prompt iteration |
| AML Analysts (pilot) | 5 people, part-time (2–3 hrs/day) | Use copilot for daily triage during pilot |
| Compliance Manager | Advisory (2 hrs/week) | Reviews pilot design, results, and go/no-go |
| Data Engineer | 0.5 person | Anonymisation pipeline, data integration |

### Phase 3 (Production)

| Role | Effort | Notes |
|---|---|---|
| Product Manager | 1 person, full-time | Rollout management, stakeholder coordination |
| Backend Engineers | 2 people, full-time | System integration, API development, scaling |
| Frontend Engineer | 1 person, full-time | Production UI, accessibility, performance |
| ML / AI Engineer | 1 person, full-time | LLM deployment, monitoring, evaluation pipeline |
| DevOps / SRE | 1 person, full-time | Infrastructure, CI/CD, security hardening |
| Data Engineer | 1 person, full-time | Data pipelines, ETL, data quality |
| Compliance Officer | 0.5 person | Regulatory documentation, MRM, sign-off |
| Security Engineer | 0.5 person | Pen testing, security review, encryption |

---

## Risk-Gated Progression

Each phase transition is gated by a **Go / No-Go decision** based on exit criteria:

```
┌───────────┐    Exit criteria met?    ┌───────────┐    Exit criteria met?    ┌────────────┐
│           │    ┌───┐                 │           │    ┌───┐                 │            │
│  PHASE 1  │───▶│GO │────────────────▶│  PHASE 2  │───▶│GO │────────────────▶│  PHASE 3   │
│ Prototype │    └───┘                 │  Pilot    │    └───┘                 │ Production │
│           │    ┌──────┐              │           │    ┌──────┐              │            │
│           │───▶│NO-GO │──▶ Fix gaps  │           │───▶│NO-GO │──▶ Fix gaps  │            │
│           │    └──────┘   & re-eval  │           │    └──────┘   & re-eval  │            │
└───────────┘                          └───────────┘                          └────────────┘

Go/No-Go Decision Makers:
  Phase 1→2: Product Manager + Compliance Manager
  Phase 2→3: Compliance Leadership + CTO / Head of Engineering + Legal
```

---

## Summary Timeline

| Week | Phase | Sprint | Key Milestone |
|---|---|---|---|
| 1–2 | Phase 1 | Sprint 1 | Synthetic data complete; context assembly working |
| 3–4 | Phase 1 | Sprint 2 | Copilot engine working end-to-end with guardrails |
| 5–6 | Phase 1 | Sprint 3 | UI complete; evaluation suite passes; demo-ready ✅ |
| 7–9 | Phase 2 | Sprint 4 | Real data integrated; analysts onboarded |
| 10–14 | Phase 2 | Sprint 5–6 | 4-week live pilot; iteration; pilot report ✅ |
| 15–18 | Phase 3 | Sprint 7–8 | System integration; security hardening; private LLM |
| 19–22 | Phase 3 | Sprint 9–10 | Scalability; monitoring; advanced features |
| 23–24 | Phase 3 | Sprint 11–12 | Full rollout; training; production launch ✅ |

---

## Appendix: Decision Log Template

Track all significant decisions made during implementation:

| Date | Decision | Options Considered | Choice | Rationale | Decided By |
|---|---|---|---|---|---|
| Week 1 | LLM provider for prototype | Gemini / GPT-4o / Claude | TBD | TBD | PM |
| Week 1 | Frontend framework | Streamlit / React | TBD | TBD | PM + Dev |
| Week 2 | Evaluation set size | 20 / 50 / 100 | TBD | TBD | PM + SME |
| Week 4 | Prompt strategy | Zero-shot / Few-shot | TBD | TBD | PM + AI Eng |
| Week 7 | Anonymisation method | Pseudonymisation / Synthetic / DP | TBD | TBD | PM + Data Eng + Legal |

---

*End of Implementation Plan — Version 1.0*
