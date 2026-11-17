# Product Requirements Document (PRD)
# AML Alert Triage Copilot

**Document Version:** 1.0  
**Author:** Product Manager  
**Date:** November 2026  
**Status:** Draft — For Review  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Users & Personas](#3-users--personas)
4. [Goals & Success Metrics](#4-goals--success-metrics)
5. [User Journey & Workflow](#5-user-journey--workflow)
6. [Functional Requirements](#6-functional-requirements)
7. [AI Behaviour & Guardrails](#7-ai-behaviour--guardrails)
8. [Information Architecture & Data Model](#8-information-architecture--data-model)
9. [Non-Functional Requirements](#9-non-functional-requirements)
10. [Evaluation Framework](#10-evaluation-framework)
11. [Risks & Mitigations](#11-risks--mitigations)
12. [Scope & Phasing](#12-scope--phasing)
13. [Open Questions](#13-open-questions)
14. [Appendix](#14-appendix)

---

## 1. Executive Summary

Financial institutions are required by law to detect and report money laundering. Their transaction monitoring systems cast a deliberately wide net, generating thousands of alerts daily — the vast majority of which are false positives. AML analysts spend most of their time manually gathering context from scattered systems rather than applying their expertise to make judgments.

The **AML Alert Triage Copilot** is a GenAI-powered assistant that sits alongside the analyst in the triage workflow. For every alert, the copilot:

- Synthesises the relevant customer profile, transaction history, and rule-trigger context into a single view.
- Recommends a disposition (**Close**, **Investigate**, or **Escalate**) grounded in cited source data.
- Drafts a regulatory STR narrative for escalations.
- Logs every AI recommendation and analyst decision into an immutable audit trail.

**Design axiom:** The AI prepares and recommends. The analyst decides. The copilot never acts autonomously on an alert.

**Target outcome:** Cut average triage time by 40-60% while maintaining zero missed escalations and full audit completeness.

---

## 2. Problem Statement

### 2.1 Current State

| Dimension | Today's Reality |
|---|---|
| **False positive rate** | Industry benchmarks: 90-95% of alerts are not truly suspicious |
| **Context gathering** | Analysts manually query 3-5 separate systems (KYC, core banking, transaction ledger, watchlists, prior SARs/STRs) per alert |
| **Time per alert** | 30-45 minutes average for a Level 1 review, significantly longer for complex cases |
| **Decision consistency** | Same alert pattern reviewed by different analysts can produce different dispositions |
| **Documentation quality** | Rationales vary widely in depth; some lack sufficient detail for regulatory examination |
| **Analyst capacity** | Teams are chronically understaffed relative to alert volume |

### 2.2 Core Pain Points

1. **Slow triage:** ~70% of analyst time is spent on information retrieval, not judgment.
2. **Alert fatigue:** Constant exposure to benign alerts dulls vigilance for the genuinely suspicious ones.
3. **Inconsistent decisions:** Without standardised reasoning frameworks, similar alerts get different outcomes depending on who reviews them and when.
4. **Audit exposure:** Gaps in documented rationale create regulatory risk during examinations.

### 2.3 Why Now

- Generative AI capabilities (reasoning, summarisation, citation) have reached the maturity needed for high-stakes advisory use cases.
- Regulatory bodies (FinCEN, FCA, AUSTRAC) are signalling openness to AI-assisted compliance, provided human accountability is preserved.
- Competitors and fintechs are moving: first-mover advantage in compliant AI tooling is narrowing.

---

## 3. Users & Personas

### 3.1 Primary: AML Analyst (Level 1 / Level 2)

| Attribute | Detail |
|---|---|
| **Role** | Reviews alerts daily, decides disposition, drafts STR narratives for escalations |
| **Daily volume** | 20-40 alerts per shift |
| **Core need** | Faster access to contextual information; consistent reasoning framework |
| **Pain** | Repetitive context gathering across systems; pressure to clear backlog without missing real cases |
| **Trust posture** | Sceptical of AI making compliance decisions; open to AI doing the prep work |
| **Key quote** | *"I don't need AI to decide for me. I need it to stop making me open six tabs to figure out what's going on."* |

### 3.2 Secondary: Compliance Manager / BSA Officer

| Attribute | Detail |
|---|---|
| **Role** | Oversees analyst team; reviews escalation quality; represents the bank to regulators |
| **Core need** | Decision consistency, audit trail completeness, STR narrative quality |
| **Pain** | Cannot easily compare how different analysts handled similar patterns; exam prep is manual |
| **Trust posture** | Cautious — needs clear evidence that AI improves outcomes without introducing new regulatory risk |
| **Key quote** | *"If the examiner asks why we closed an alert, I need to pull up a clear, source-cited rationale in under a minute."* |

### 3.3 Tertiary: Internal Audit / Regulatory Examiner

| Attribute | Detail |
|---|---|
| **Role** | Reviews triage decisions retrospectively for quality, bias, and compliance |
| **Core need** | Complete, tamper-evident decision records; ability to assess whether AI influence introduced bias |
| **Pain** | Inconsistent documentation; no visibility into AI-assisted vs. purely manual decisions |

---

## 4. Goals & Success Metrics

### 4.1 Objective Hierarchy

```
North Star: Reduce time-to-disposition per alert while maintaining (or improving) detection quality.

├── Efficiency: Analysts spend less time on context gathering
├── Quality: Decisions are more consistent and better documented
├── Safety: No true positives are missed due to AI influence
└── Governance: Full auditability of AI involvement in every decision
```

### 4.2 Key Metrics

| Metric | Type | Target | Measurement Method |
|---|---|---|---|
| **Average time per alert** | Primary / Efficiency | ≥40% reduction from baseline | Timestamp: alert-opened → disposition-submitted |
| **Missed escalation rate** | Guardrail / Safety | 0% (zero tolerance) | Comparison against expert-labelled evaluation set |
| **AI-analyst agreement rate** | Quality | ≥85% on the evaluation set | AI suggestion vs. analyst final decision |
| **False positive screening accuracy** | Efficiency | ≥90% of FP alerts correctly suggested for closure | Precision on "Close" suggestions vs. expert labels |
| **Audit completeness** | Governance | 100% | Every disposition has: AI suggestion + analyst decision + rationale |
| **STR narrative acceptance rate** | Quality | ≥70% of drafts accepted with minor edits only | Analyst edit distance on AI-drafted narratives |
| **Analyst trust / NPS** | Sentiment | Positive trend over 4 weeks | Post-session survey (1-5 scale) |

### 4.3 Guardrail Constraints

> **Hard rule:** If the guardrail metric (missed escalation rate) degrades from zero on any evaluation batch, the copilot's "Close" suggestions are suspended pending investigation. "Investigate" and "Escalate" suggestions continue.

---

## 5. User Journey & Workflow

### 5.1 Current Workflow (Without Copilot)

```
Alert fires → Analyst opens alert → Manually queries KYC system → Manually
queries transaction ledger → Manually checks watchlists → Manually reviews
prior SARs → Mentally synthesises → Makes disposition → Writes rationale
(free text, variable quality) → Submits → Next alert
```

**Pain points are concentrated in Steps 3-6 (manual context gathering) and Step 9 (documentation).**

### 5.2 Proposed Workflow (With Copilot)

```
┌─────────────────────────────────────────────────────────────────┐
│                     ALERT TRIAGE WORKSPACE                      │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐   │
│  │  ALERT QUEUE  │    │         COPILOT PANEL                │   │
│  │              │    │                                      │   │
│  │  Alert #1042 │───▶│  1. CONTEXT SUMMARY                  │   │
│  │  Alert #1043 │    │     Why the alert fired, what is     │   │
│  │  Alert #1044 │    │     unusual vs. KYC baseline.        │   │
│  │  ...         │    │     [Source citations inline]        │   │
│  │              │    │                                      │   │
│  │  Filters:    │    │  2. RECOMMENDATION                   │   │
│  │  - Priority  │    │     ▶ Escalate (STR)                 │   │
│  │  - Rule type │    │     Reason: 12 sub-threshold cash    │   │
│  │  - Status    │    │     deposits in 9 days totalling     │   │
│  │              │    │     $94,800 [Txn Ledger]             │   │
│  │              │    │     Customer declared income:        │   │
│  │              │    │     $4,200/mo [KYC Profile]          │   │
│  │              │    │                                      │   │
│  │              │    │  3. STR DRAFT (if Escalate)          │   │
│  │              │    │     [DRAFT - REQUIRES REVIEW]        │   │
│  │              │    │     "On or about Nov 1-9, 2026..."   │   │
│  │              │    │                                      │   │
│  │              │    │  4. ANALYST DECISION                  │   │
│  │              │    │     [Close] [Investigate] [Escalate] │   │
│  │              │    │     Rationale: [pre-filled, editable]│   │
│  │              │    │     [Submit Decision]                │   │
│  └──────────────┘    └──────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Step-by-Step User Flow

| Step | Actor | Action | System Response |
|---|---|---|---|
| 1 | Analyst | Opens the alert queue dashboard | Queue loads with alerts sorted by priority (AI-suggested risk tier) |
| 2 | Analyst | Selects an alert | Workspace loads alert metadata + copilot begins analysis |
| 3 | Copilot | Retrieves KYC profile, transaction history, rule metadata, prior alerts | Displays a structured context summary with inline source citations |
| 4 | Copilot | Analyses patterns against KYC baseline | Presents recommendation (Close / Investigate / Escalate) with cited reasoning |
| 5 | Copilot | If recommendation = Escalate | Generates a draft STR narrative in 5W1H format, marked as DRAFT |
| 6 | Copilot | If critical data is missing | Displays "Insufficient evidence to recommend disposition" with list of what is missing |
| 7 | Analyst | Reviews summary, recommendation, and (if applicable) STR draft | — |
| 8 | Analyst | Accepts, modifies, or overrides the recommendation | Decision panel captures final disposition + rationale |
| 9 | Analyst | Edits STR narrative if needed | Track-changes view shows AI draft vs. analyst edits |
| 10 | Analyst | Clicks "Submit Decision" | Audit log entry created (immutable); alert moves to resolved queue |
| 11 | System | Logs full record | AI suggestion, analyst decision, rationale, timestamp, alert data snapshot all persisted |

---

## 6. Functional Requirements

### 6.1 Alert Queue & Dashboard

| ID | Requirement | Priority |
|---|---|---|
| F-01 | Display a sortable, filterable queue of open alerts | P0 |
| F-02 | Each alert row shows: Alert ID, customer name, triggering rule, date, AI-suggested priority tier (High / Medium / Low) | P0 |
| F-03 | Clicking an alert opens the triage workspace (split view: alert data + copilot panel) | P0 |
| F-04 | Filter alerts by: status (Open / In Review / Resolved), rule type, priority tier, date range | P1 |
| F-05 | Show alert volume and disposition breakdown summary (cards/charts) at top of dashboard | P1 |

### 6.2 Copilot Context Summary

| ID | Requirement | Priority |
|---|---|---|
| F-10 | For each alert, generate a plain-language summary explaining: (a) which monitoring rule fired, (b) the specific transactions or patterns that triggered it, (c) how these deviate from the customer's KYC baseline | P0 |
| F-11 | Every factual claim in the summary must include an inline source citation (e.g., `[KYC Profile]`, `[Txn #1042]`, `[Rule: Structuring-001]`) | P0 |
| F-12 | Display the customer's KYC snapshot: name, account type, occupation, declared income, account age, expected transaction profile | P0 |
| F-13 | Display a transaction ledger for the relevant period, highlighting the flagged transactions | P0 |
| F-14 | Show counterparty information where available; flag if a counterparty appears on any watchlist | P1 |
| F-15 | Show prior alert history for this customer (count, dispositions, dates) | P1 |

### 6.3 AI Recommendation Engine

| ID | Requirement | Priority |
|---|---|---|
| F-20 | Generate a disposition recommendation: **Close**, **Investigate**, or **Escalate (STR)** | P0 |
| F-21 | Each recommendation must include a structured rationale with ≥2 cited reasons | P0 |
| F-22 | If the copilot cannot form a recommendation due to missing or contradictory data, it must output **"Insufficient evidence"** with a list of what data is missing or ambiguous | P0 |
| F-23 | The copilot must never auto-select a disposition or submit a decision without explicit analyst action | P0 |
| F-24 | Display a confidence indicator (High / Medium / Low) alongside the recommendation | P1 |
| F-25 | Allow the analyst to ask follow-up questions to the copilot about the alert context (conversational) | P2 |

### 6.4 STR Narrative Drafter

| ID | Requirement | Priority |
|---|---|---|
| F-30 | When the recommendation is "Escalate", auto-generate a draft STR narrative | P0 |
| F-31 | The narrative must follow the 5W1H structure: Who (subject), What (activity), When (dates), Where (accounts/jurisdictions), Why (suspicion basis), How (method/pattern) | P0 |
| F-32 | The draft must be clearly labelled: `[DRAFT — REQUIRES ANALYST REVIEW BEFORE SUBMISSION]` | P0 |
| F-33 | Every factual claim in the narrative must cite its source data | P0 |
| F-34 | The analyst can edit the narrative in-place; edits are tracked (diff view available) | P1 |
| F-35 | Provide a "Regenerate" button if the analyst wants a fresh draft after providing feedback | P2 |

### 6.5 Analyst Decision & Submission

| ID | Requirement | Priority |
|---|---|---|
| F-40 | Analyst must explicitly select a final disposition: Close, Investigate, or Escalate | P0 |
| F-41 | Analyst must provide or confirm a rationale (pre-filled from AI reasoning, fully editable) | P0 |
| F-42 | If the analyst's decision differs from the AI recommendation, prompt (not require) the analyst to note why they overrode | P0 |
| F-43 | "Submit Decision" button finalises the disposition and creates the audit log entry | P0 |
| F-44 | Prevent submission without a rationale (validation) | P0 |

### 6.6 Audit Log

| ID | Requirement | Priority |
|---|---|---|
| F-50 | Every submitted decision creates an immutable audit log entry containing: alert ID, timestamp, AI recommendation, AI rationale, AI confidence, analyst decision, analyst rationale, override flag (yes/no), override reason (if applicable), STR draft (if applicable), analyst-edited STR (if applicable) | P0 |
| F-51 | Audit log is append-only; entries cannot be modified or deleted | P0 |
| F-52 | Audit log is viewable in a searchable, filterable table | P0 |
| F-53 | Each audit entry is exportable (JSON / CSV) for regulatory examination | P1 |
| F-54 | Audit log tracks the model version / prompt version used for each AI recommendation | P1 |

---

## 7. AI Behaviour & Guardrails

### 7.1 Core Behavioural Rules

| Rule | Description | Enforcement |
|---|---|---|
| **Human-in-the-loop** | The copilot NEVER closes an alert, files an STR, or takes any action autonomously | System architecture: no write-path from AI to case management without analyst confirmation |
| **Grounded citations** | Every factual claim must cite a specific data source | Prompt engineering + output validation; uncited claims are flagged |
| **Epistemic honesty** | If data is missing, contradictory, or insufficient, the copilot must say so explicitly rather than guess | "Insufficient evidence" fallback logic with enumeration of missing data |
| **No fabrication** | The copilot must not invent transactions, counterparties, dates, or amounts not present in the source data | Output validation against input data; hallucination detection in evaluation |
| **Regulatory neutrality** | The copilot does not make legal conclusions (e.g., "this is money laundering"); it describes patterns and deviations | Prompt guardrails + output review |
| **Bias awareness** | Recommendations must be based on behavioural patterns and data, not customer demographics | Evaluation set includes demographic controls; bias audit in metrics |

### 7.2 Prompt Architecture

```
┌───────────────────────────────────────────────┐
│              SYSTEM PROMPT                     │
│  Role definition, behavioural rules,           │
│  output format specification,                  │
│  citation requirements, "insufficient          │
│  evidence" fallback instructions               │
├───────────────────────────────────────────────┤
│              CONTEXT INJECTION                 │
│  Structured data payload:                      │
│  - Alert metadata & rule details               │
│  - Customer KYC profile                        │
│  - Transaction ledger (relevant window)        │
│  - Prior alert history                         │
│  - Counterparty & watchlist data               │
├───────────────────────────────────────────────┤
│              USER PROMPT                       │
│  "Analyse this alert and provide your          │
│   recommendation with cited reasoning."        │
├───────────────────────────────────────────────┤
│              OUTPUT SCHEMA                     │
│  Structured JSON:                              │
│  {                                             │
│    summary: string (with citations),           │
│    recommendation: Close|Investigate|Escalate, │
│    confidence: High|Medium|Low,                │
│    rationale: [{ reason, source_citation }],   │
│    missing_data: [string] | null,              │
│    str_draft: string | null                    │
│  }                                             │
└───────────────────────────────────────────────┘
```

### 7.3 Failure Modes & Fallbacks

| Failure Mode | Detection | Fallback |
|---|---|---|
| AI service unavailable | API timeout / error | Show alert data without copilot panel; analyst proceeds manually |
| Hallucinated data | Output validation against input payload | Suppress recommendation; show "Copilot could not generate a reliable analysis" |
| Missing critical input data (no KYC on file) | Input completeness check | "Insufficient evidence" output with missing data enumerated |
| Contradictory signals | Confidence scoring | Low-confidence flag; recommend "Investigate" as safe default |
| Prompt injection via transaction memo fields | Input sanitisation | Sanitise free-text fields before injection; reject anomalous outputs |

---

## 8. Information Architecture & Data Model

### 8.1 Core Entities

```
┌─────────────┐       ┌─────────────────┐       ┌──────────────┐
│   Customer   │──1:N──│   Account       │──1:N──│ Transaction  │
│              │       │                 │       │              │
│  customer_id │       │  account_id     │       │  txn_id      │
│  name        │       │  account_type   │       │  date        │
│  occupation  │       │  open_date      │       │  amount      │
│  income      │       │  status         │       │  type        │
│  risk_rating │       │  currency       │       │  direction   │
│  onboard_date│       │                 │       │  counterparty│
│  nationality │       │                 │       │  memo        │
│  pep_status  │       │                 │       │  channel     │
└─────────────┘       └─────────────────┘       └──────────────┘
        │
        │ 1:N
        ▼
┌─────────────┐       ┌─────────────────┐       ┌──────────────┐
│    Alert     │──1:1──│ AI_Analysis     │──1:1──│ Audit_Entry  │
│              │       │                 │       │              │
│  alert_id    │       │  analysis_id    │       │  entry_id    │
│  customer_id │       │  alert_id       │       │  alert_id    │
│  rule_id     │       │  summary        │       │  ai_rec      │
│  rule_name   │       │  recommendation │       │  ai_rationale│
│  trigger_date│       │  confidence     │       │  analyst_dec │
│  status      │       │  rationale[]    │       │  analyst_rat │
│  priority    │       │  missing_data[] │       │  override    │
│  assigned_to │       │  str_draft      │       │  override_rsn│
│              │       │  model_version  │       │  str_final   │
│              │       │  prompt_version │       │  timestamp   │
│              │       │  created_at     │       │  model_ver   │
└─────────────┘       └─────────────────┘       └──────────────┘
```

### 8.2 Synthetic Data Requirements (Prototype)

The prototype uses fictional data covering these alert archetypes:

| # | Archetype | Expected Disposition | Purpose |
|---|---|---|---|
| 1 | **Classic structuring** — multiple sub-threshold cash deposits | Escalate | Test structuring detection |
| 2 | **Pass-through / layering** — large inflow immediately wired out | Escalate | Test rapid movement detection |
| 3 | **Income inconsistency** — activity far exceeds declared income | Investigate / Escalate | Test KYC deviation logic |
| 4 | **Dormant account spike** — long-inactive account suddenly active | Investigate | Test dormancy pattern |
| 5 | **Round-trip** — funds sent and returned from same counterparty | Investigate | Test circular flow detection |
| 6 | **Legitimate business spike** — seasonal business with expected Q4 surge | Close (FP) | Test false positive recognition |
| 7 | **Salary + rent pattern** — regular predictable activity | Close (FP) | Test benign pattern recognition |
| 8 | **Large but explained** — one-time real estate transaction with documentation | Close (FP) | Test contextual explanation |
| 9 | **Missing KYC** — alert with incomplete customer profile | Insufficient Evidence | Test "I don't know" guardrail |
| 10 | **Mixed signals** — some suspicious, some explainable patterns | Investigate | Test nuanced reasoning |
| 11 | **PEP with minor deviation** — politically exposed person, small anomaly | Investigate (heightened scrutiny) | Test PEP-aware logic |
| 12 | **Watchlist counterparty** — transaction with a flagged entity | Escalate | Test watchlist integration |

---

## 9. Non-Functional Requirements

| Category | Requirement | Target |
|---|---|---|
| **Response time** | Copilot analysis generation | < 8 seconds for summary + recommendation |
| **Availability** | Copilot service uptime | 99.5% during business hours (graceful degradation: analyst can work without copilot) |
| **Data privacy** | No customer data sent to external AI services in production | All inference on-premise or in bank's private cloud (prototype: synthetic data, external API acceptable) |
| **Audit integrity** | Audit log entries | Append-only, tamper-evident (hash chain or equivalent in production) |
| **Accessibility** | WCAG 2.1 AA compliance | Keyboard navigation, screen reader support, sufficient contrast |
| **Browser support** | Chrome, Edge (latest 2 versions) | Prototype: Chrome only |

---

## 10. Evaluation Framework

### 10.1 Evaluation Set Design

A curated set of **50+ alert scenarios** with **expert-labelled ground truth dispositions** and rationales, covering:
- All 12 archetypes from Section 8.2
- Edge cases and boundary conditions
- Demographic diversity in customer profiles (to test for bias)

### 10.2 Evaluation Metrics

| Metric | Formula | Threshold |
|---|---|---|
| **Missed escalation rate (False Negative)** | Alerts labelled "Escalate" by experts but suggested "Close" by AI / Total expert "Escalate" labels | **0%** (hard gate) |
| **False positive screening precision** | AI "Close" suggestions that match expert "Close" label / Total AI "Close" suggestions | ≥ 90% |
| **Overall agreement** | AI suggestion matches expert label / Total alerts | ≥ 85% |
| **Citation accuracy** | Claims with valid source citations / Total factual claims | ≥ 95% |
| **Hallucination rate** | Outputs containing fabricated data points / Total outputs | 0% target, < 2% tolerance |
| **"Insufficient evidence" appropriateness** | Correct "insufficient evidence" outputs / Total cases with genuinely missing data | ≥ 90% |

### 10.3 Evaluation Cadence

- **Pre-launch:** Full evaluation suite must pass all thresholds
- **Weekly (post-launch):** Random sample of 20 analyst-decided alerts reviewed by senior analyst for quality
- **Monthly:** Full evaluation suite re-run against current model/prompt version
- **On every prompt or model change:** Full evaluation suite re-run before deployment

---

## 11. Risks & Mitigations

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Analyst over-reliance (automation bias)** — analysts rubber-stamp AI recommendations without critical review | High | Medium | Random "challenge" alerts where AI deliberately withholds recommendation; track override rates; training programme |
| **AI hallucination** — copilot fabricates transactions or facts | Critical | Low | Output validation against input data; citation requirements; hallucination detection in eval; "insufficient evidence" fallback |
| **Missed true positive** — AI suggests "Close" on a genuinely suspicious alert | Critical | Low | Zero-tolerance guardrail metric; conservative bias toward "Investigate" in ambiguous cases; human always decides |
| **Regulatory rejection** — regulator views AI-assisted triage as insufficient human oversight | High | Medium | Clear human-in-the-loop design; full audit trail showing AI ≠ decision-maker; regulatory engagement plan |
| **Prompt injection** — malicious transaction memo manipulates AI output | Medium | Low | Input sanitisation; output schema validation; anomaly detection on AI outputs |
| **Model drift** — AI quality degrades over time with model updates | Medium | Medium | Pinned model versions; evaluation suite re-run on every change; rollback capability |
| **Analyst distrust / low adoption** — analysts don't use or trust the tool | High | Medium | Analyst involvement in design; transparency in AI reasoning; gradual rollout; feedback mechanism |

---

## 12. Scope & Phasing

### 12.1 Phase 1 — Prototype (Current Scope)

**Goal:** Demonstrate product thinking, AI guardrail design, and evaluation rigour with a working prototype.

| In Scope | Out of Scope |
|---|---|
| Synthetic/fictional alert data (12+ scenarios) | Real customer or bank data |
| Alert queue dashboard with filters and summary stats | Production IAM/SSO, role-based access |
| Copilot analysis: summary, recommendation, citations | Integration with real monitoring systems |
| STR narrative drafting (for escalations) | Automatic STR filing |
| Analyst decision capture with rationale | Automatic alert closure |
| Immutable audit log (append-only, in-app) | Tamper-evident hash chains |
| Evaluation dashboard with key metrics | Real-time model monitoring |
| AI guardrails: "insufficient evidence", citation validation | On-premise / private cloud inference |

### 12.2 Phase 2 — Pilot (Future)

- Integration with one monitoring system (sandbox environment)
- Real (anonymised) historical alerts for evaluation
- Role-based access (analyst, manager, auditor views)
- Analyst feedback loop → prompt refinement
- Regulatory review and approval process

### 12.3 Phase 3 — Production (Future)

- Full integration with bank's monitoring and case management systems
- On-premise / private cloud AI inference
- Tamper-evident audit log (blockchain or hash chain)
- Multi-language STR support
- Advanced analytics: pattern clustering, alert prioritisation ML model
- Continuous learning from analyst feedback (with human oversight)

---

## 13. Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| 1 | Which LLM provider and model to use for the prototype? (e.g., Gemini, GPT-4, Claude) | PM / Engineering | Open |
| 2 | Should the prototype be a web app (Streamlit/React) or a clickable prototype (Figma)? | PM | Open |
| 3 | How should we handle the edge case where an analyst repeatedly overrides AI recommendations — is this a training signal or a performance flag? | PM / Compliance | Open |
| 4 | What is the right level of AI confidence granularity? (Binary: confident/not vs. three-tier: High/Med/Low vs. numeric score) | PM / Design | Open |
| 5 | Should the copilot have a conversational follow-up capability in Phase 1, or is it purely one-shot analysis? | PM / Engineering | Open |
| 6 | What regulatory body guidance (if any) should be cited in the PRD or prototype to demonstrate awareness? | PM / Compliance | Open |

---

## 14. Appendix

### 14.1 Glossary

| Term | Definition |
|---|---|
| **AML** | Anti-Money Laundering — laws, regulations, and procedures to prevent criminals from disguising illegally obtained funds as legitimate income |
| **STR / SAR** | Suspicious Transaction Report / Suspicious Activity Report — formal report filed with financial intelligence unit when suspicious activity is identified |
| **KYC** | Know Your Customer — the process of verifying a customer's identity, risk profile, and expected account behaviour |
| **False Positive** | An alert that, upon investigation, turns out to be non-suspicious (legitimate activity) |
| **False Negative** | A genuinely suspicious case that was NOT flagged or was incorrectly closed — the worst outcome in AML compliance |
| **Structuring** | Deliberately breaking large transactions into smaller ones to avoid reporting thresholds |
| **Layering / Pass-through** | Moving money through accounts rapidly to obscure its origin |
| **PEP** | Politically Exposed Person — individual in a prominent public function, requiring enhanced due diligence |
| **5W1H** | Who, What, When, Where, Why, How — standard structure for STR narratives |

### 14.2 Regulatory References

- **FinCEN (US):** Bank Secrecy Act / Anti-Money Laundering requirements
- **FCA (UK):** Financial Conduct Authority — Senior Managers and Certification Regime
- **FATF:** Financial Action Task Force — 40 Recommendations on Money Laundering
- **AUSTRAC (Australia):** Anti-Money Laundering and Counter-Terrorism Financing Act 2006

### 14.3 Competitive Landscape (Illustrative)

| Player | Approach | Differentiation of Our Copilot |
|---|---|---|
| Traditional case management (Actimize, Norkom) | Rule-based; no AI summarisation or recommendation | AI-powered context synthesis + recommendation |
| Emerging AML AI vendors (e.g., Lucinity, ThetaRay) | Full-stack platforms; model + UI | Lightweight copilot overlay; human-centred; transparent reasoning |
| Internal bank data science teams | Custom ML scoring models | Not a replacement for scoring — augments analyst workflow downstream of scoring |

---

*End of PRD — Version 1.0*
