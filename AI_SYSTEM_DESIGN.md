# AI System Design Document
# AML Alert Triage Copilot

**Document Version:** 1.0  
**Author:** Product Manager  
**Date:** November 2026  
**Status:** Draft  
**Companion to:** PRD_AML_Copilot.md

---

## Table of Contents

1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Data Pipeline & Context Assembly](#2-data-pipeline--context-assembly)
3. [Prompt Engineering Architecture](#3-prompt-engineering-architecture)
4. [Citation Engine](#4-citation-engine)
5. [Recommendation Logic & Confidence Scoring](#5-recommendation-logic--confidence-scoring)
6. [STR Narrative Generation](#6-str-narrative-generation)
7. [Guardrail System](#7-guardrail-system)
8. [Output Validation & Post-Processing](#8-output-validation--post-processing)
9. [Audit Logging Architecture](#9-audit-logging-architecture)
10. [Evaluation & Testing Harness](#10-evaluation--testing-harness)
11. [Failure Modes & Resilience](#11-failure-modes--resilience)
12. [Security & Privacy Considerations](#12-security--privacy-considerations)
13. [Technology Stack (Prototype)](#13-technology-stack-prototype)
14. [Future Architecture (Production)](#14-future-architecture-production)

---

## 1. System Overview & Architecture

### 1.1 Design Philosophy

The system follows three architectural principles:

| Principle | Implication |
|---|---|
| **Advisory, never autonomous** | No write-path from AI to case management without explicit analyst confirmation |
| **Transparent reasoning** | Every AI output is traceable to source data via citations; no black-box recommendations |
| **Fail safe, not fail silent** | When the system cannot produce a reliable output, it says so explicitly rather than guessing |

### 1.2 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           ANALYST BROWSER                                  │
│  ┌──────────────┐  ┌───────────────────────────────────────────────────┐   │
│  │  Alert Queue  │  │              Triage Workspace                    │   │
│  │  Dashboard    │  │  ┌─────────────┐  ┌──────────────────────────┐  │   │
│  │              │  │  │ Alert Data   │  │   Copilot Panel          │  │   │
│  │              │  │  │ Panel        │  │   • Context Summary      │  │   │
│  │              │  │  │             │  │   • Recommendation       │  │   │
│  │              │  │  │             │  │   • STR Draft             │  │   │
│  │              │  │  │             │  │   • Decision Capture      │  │   │
│  │              │  │  └─────────────┘  └──────────────────────────┘  │   │
│  └──────────────┘  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────┬─────────────────────────────────────┘
                                       │ HTTPS / REST API
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION SERVER (Backend)                        │
│                                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │   API       │  │  Context     │  │  Copilot     │  │  Audit         │   │
│  │   Gateway   │──│  Assembly    │──│  Engine      │──│  Logger        │   │
│  │             │  │  Service     │  │              │  │                │   │
│  └─────────────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘   │
│                          │                 │                   │            │
│                          ▼                 ▼                   ▼            │
│                   ┌────────────┐    ┌────────────┐     ┌─────────────┐      │
│                   │  Data      │    │  Output    │     │  Audit      │      │
│                   │  Store     │    │  Validator │     │  Store      │      │
│                   │ (Synthetic)│    │  & Guards  │     │ (Append-only)│      │
│                   └────────────┘    └──────┬─────┘     └─────────────┘      │
│                                            │                                │
│                                            ▼                                │
│                                    ┌──────────────┐                         │
│                                    │  LLM API     │                         │
│                                    │  (Gemini /   │                         │
│                                    │   OpenAI)    │                         │
│                                    └──────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Request Flow (Single Alert Analysis)

```
sequenceDiagram
    Analyst->>Frontend: Selects alert from queue
    Frontend->>API Gateway: GET /alerts/{id}/analyse
    API Gateway->>Context Assembly: Gather all context for alert
    Context Assembly->>Data Store: Fetch KYC profile
    Context Assembly->>Data Store: Fetch transaction ledger
    Context Assembly->>Data Store: Fetch rule metadata
    Context Assembly->>Data Store: Fetch prior alert history
    Context Assembly->>Data Store: Fetch counterparty/watchlist data
    Context Assembly-->>Copilot Engine: Structured context payload
    Copilot Engine->>Copilot Engine: Input completeness check
    alt Missing critical data
        Copilot Engine-->>Frontend: "Insufficient evidence" response
    else Data complete
        Copilot Engine->>LLM API: System prompt + context + user prompt
        LLM API-->>Copilot Engine: Structured JSON response
        Copilot Engine->>Output Validator: Validate citations, schema, hallucinations
        alt Validation passes
            Output Validator-->>Frontend: Validated analysis response
        else Validation fails
            Output Validator-->>Frontend: Degraded response with warning
        end
    end
    Analyst->>Frontend: Reviews, decides, submits
    Frontend->>Audit Logger: Log AI analysis + analyst decision
    Audit Logger->>Audit Store: Append immutable entry
```

---

## 2. Data Pipeline & Context Assembly

### 2.1 Context Assembly Service

The Context Assembly Service is responsible for gathering all relevant data for a given alert and packaging it into a structured payload for the LLM. In the prototype, this reads from local JSON files. In production, it would query KYC systems, core banking, watchlist databases, and case management systems.

### 2.2 Context Payload Schema

```json
{
  "alert": {
    "alert_id": "ALT-2026-001042",
    "rule_id": "STRUCT-001",
    "rule_name": "Potential Structuring — Multiple Sub-Threshold Cash Deposits",
    "rule_description": "Flags when 3+ cash deposits each below $10,000 occur within a 10-day window and total exceeds $20,000.",
    "trigger_date": "2026-11-09",
    "trigger_summary": "12 cash deposits totalling $94,800 over 9 days, each between $7,200 and $9,800."
  },
  "customer": {
    "customer_id": "CUST-88401",
    "name": "James Whitfield",
    "account_type": "Personal Checking",
    "occupation": "Retail Store Clerk",
    "declared_annual_income": 50400,
    "declared_monthly_income": 4200,
    "account_open_date": "2023-03-15",
    "risk_rating": "Medium",
    "nationality": "US",
    "pep_status": false,
    "expected_monthly_volume": {
      "deposits": 5000,
      "withdrawals": 4500
    }
  },
  "transactions": [
    {
      "txn_id": "TXN-990101",
      "date": "2026-11-01",
      "amount": 9800.00,
      "type": "Cash Deposit",
      "direction": "Credit",
      "counterparty": null,
      "channel": "Branch",
      "memo": "",
      "flagged": true
    }
  ],
  "prior_alerts": [
    {
      "alert_id": "ALT-2026-000819",
      "date": "2026-08-14",
      "rule": "Large Cash Deposit",
      "disposition": "Closed — False Positive",
      "analyst_notes": "One-time car sale, documentation provided."
    }
  ],
  "counterparties": [],
  "watchlist_hits": []
}
```

### 2.3 Input Completeness Check

Before sending context to the LLM, the system performs a completeness check:

| Field | Required? | If Missing |
|---|---|---|
| `alert.rule_name`, `alert.trigger_summary` | Yes | Block analysis — cannot proceed without knowing what fired |
| `customer.name`, `customer.occupation`, `customer.declared_annual_income` | Yes | Trigger "Insufficient Evidence — KYC profile incomplete" |
| `customer.expected_monthly_volume` | Yes | Trigger "Insufficient Evidence — no baseline for comparison" |
| `transactions` (≥1 flagged) | Yes | Block analysis — no transactions to analyse |
| `prior_alerts` | No | Proceed; note "No prior alert history on file" |
| `counterparties` | No | Proceed; note "Counterparty details not available" |
| `watchlist_hits` | No | Proceed; note "No watchlist data available" |

**Decision rule:** If any "Required = Yes" field is missing, the system returns an "Insufficient Evidence" response with the specific missing fields enumerated. The LLM is not called.

---

## 3. Prompt Engineering Architecture

### 3.1 Three-Layer Prompt Structure

The prompt sent to the LLM is composed of three layers, each with a distinct purpose:

#### Layer 1: System Prompt (Static — changes only with version updates)

```
You are an AML Alert Triage Copilot assisting a human analyst. Your role is to
PREPARE context and RECOMMEND a disposition. You do NOT make final decisions.

BEHAVIOURAL RULES (you must follow these without exception):
1. NEVER state that an activity "is" money laundering or "is" a crime.
   Instead, describe the patterns and how they deviate from expected behaviour.
2. EVERY factual claim must include an inline citation in brackets referencing
   the specific data source. Valid citation formats:
   - [KYC Profile] — for customer identity, income, occupation data
   - [Txn: TXN-XXXXXX] — for specific transaction references
   - [Rule: RULE-ID] — for monitoring rule details
   - [Prior Alert: ALT-XXXX] — for prior alert history
   - [Counterparty: NAME] — for counterparty information
   - [Watchlist] — for watchlist match information
3. If you do not have sufficient data to support a claim, do NOT fabricate it.
   Instead, state what data is missing and how it limits your analysis.
4. NEVER invent transactions, amounts, dates, counterparties, or any other
   data not present in the context provided.
5. Your recommendation must be exactly one of: "Close", "Investigate", or
   "Escalate".
6. If the evidence is genuinely ambiguous or critical data is missing, your
   recommendation must be "Investigate" and your confidence must be "Low",
   with a clear statement of what additional information would resolve
   the ambiguity.
7. When recommending "Escalate", generate an STR narrative draft following
   the 5W1H structure. Mark it clearly as "[DRAFT — REQUIRES ANALYST REVIEW]".
8. Do NOT make recommendations based on customer demographics (nationality,
   ethnicity, gender, age). Base all analysis on behavioural patterns, 
   transactional data, and KYC deviations.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object matching the schema provided.
Do NOT include any text outside the JSON object.
```

#### Layer 2: Context Injection (Dynamic — assembled per alert)

```
ALERT CONTEXT:
The following is the complete data available for this alert. Base your analysis
ONLY on this data. Do not assume or infer data not provided.

<alert_data>
{serialised context payload from Section 2.2}
</alert_data>
```

#### Layer 3: User Prompt + Output Schema (Static template)

```
Analyse the alert above. Provide:
1. A plain-language summary of why this alert fired and what is unusual
   compared to the customer's profile.
2. Your recommended disposition with cited reasoning.
3. If recommending "Escalate", a draft STR narrative.

Respond with a JSON object matching this schema:
{
  "summary": "string — plain-language summary with inline [citations]",
  "recommendation": "Close | Investigate | Escalate",
  "confidence": "High | Medium | Low",
  "rationale": [
    {
      "reason": "string — one specific reason supporting the recommendation",
      "source_citations": ["string — citation reference(s) for this reason"]
    }
  ],
  "risk_factors": [
    "string — each key risk factor identified, with citation"
  ],
  "mitigating_factors": [
    "string — each mitigating or explainable factor, with citation"
  ],
  "missing_data": ["string — data that would improve the analysis"] | null,
  "str_draft": "string — 5W1H narrative marked as DRAFT" | null
}
```

### 3.2 Prompt Versioning

Every prompt component is versioned:

| Component | Version ID Format | Example |
|---|---|---|
| System prompt | `SYS-v{major}.{minor}` | `SYS-v1.0` |
| Output schema | `SCHEMA-v{major}.{minor}` | `SCHEMA-v1.0` |
| User prompt template | `USR-v{major}.{minor}` | `USR-v1.0` |

The combination `SYS-v1.0 + SCHEMA-v1.0 + USR-v1.0` forms a **Prompt Bundle Version** (e.g., `PB-v1.0.0`) that is recorded in every audit log entry. Any change to any component creates a new bundle version and triggers the full evaluation suite before deployment.

### 3.3 Model Configuration

| Parameter | Prototype Setting | Rationale |
|---|---|---|
| **Model** | Gemini 2.5 Pro / GPT-4o / Claude Sonnet (evaluate all three) | Strong reasoning, instruction-following, structured output |
| **Temperature** | 0.1 | Prioritise determinism and consistency over creativity |
| **Max output tokens** | 4,096 | Sufficient for detailed analysis + STR draft |
| **Top-P** | 0.95 | Slight diversity allowed for natural language quality |
| **Response format** | JSON mode (where supported) | Enforce structured output |
| **Timeout** | 30 seconds | Hard cutoff; fallback to degraded response |

---

## 4. Citation Engine

### 4.1 Purpose

Citations serve three functions:
1. **Analyst trust:** The analyst can verify every claim against source data.
2. **Audit trail:** Regulators can trace AI reasoning to specific data points.
3. **Hallucination detection:** Claims that cannot be mapped to source data are flagged.

### 4.2 Citation Taxonomy

| Citation Type | Format | Maps To |
|---|---|---|
| KYC Profile | `[KYC Profile]` or `[KYC: {specific field}]` | `context.customer.*` |
| Transaction | `[Txn: TXN-XXXXXX]` | `context.transactions[].txn_id` |
| Monitoring Rule | `[Rule: RULE-ID]` | `context.alert.rule_id` |
| Prior Alert | `[Prior Alert: ALT-XXXX]` | `context.prior_alerts[].alert_id` |
| Counterparty | `[Counterparty: NAME]` | `context.counterparties[].name` |
| Watchlist | `[Watchlist]` or `[Watchlist: ENTITY]` | `context.watchlist_hits[]` |

### 4.3 Citation Validation (Post-Processing)

After receiving the LLM response, the Output Validator performs citation validation:

```
For each citation in the AI output:
  1. Extract the citation reference (e.g., "TXN-990101")
  2. Look up the reference in the input context payload
  3. If FOUND:
       → Mark citation as VALID
       → Verify the claim associated with the citation is consistent
         with the source data (e.g., amount matches)
  4. If NOT FOUND:
       → Mark citation as INVALID
       → Flag the associated claim as UNVERIFIED
       → If >20% of citations are invalid → trigger hallucination warning
  5. Count uncited factual claims (amounts, dates, names without citations)
       → If uncited claims exist → append warning to output
```

### 4.4 Frontend Citation Rendering

Citations in the UI are rendered as interactive elements:

- **Clickable:** Clicking `[Txn: TXN-990101]` scrolls the transaction ledger to highlight that transaction.
- **Hover preview:** Hovering over `[KYC Profile]` shows a tooltip with the relevant KYC field value.
- **Colour coding:** Valid citations render in blue; unverified citations render in amber with a warning icon.

---

## 5. Recommendation Logic & Confidence Scoring

### 5.1 Disposition Framework

The LLM is guided to reason about disposition using this framework (embedded in the system prompt reasoning examples):

```
┌──────────────────────────────────────────────────────────────────────┐
│                     DISPOSITION DECISION TREE                        │
│                                                                      │
│  Is the activity consistent with KYC profile and expected behaviour? │
│  ├── YES, fully explainable                                          │
│  │   └── Recommend: CLOSE                                            │
│  │       Confidence: High (if clear), Medium (if minor ambiguity)    │
│  │                                                                   │
│  ├── PARTIALLY — some deviation but potentially explainable          │
│  │   └── Recommend: INVESTIGATE                                      │
│  │       Confidence: Medium                                          │
│  │       Note: Specify what additional info would clarify             │
│  │                                                                   │
│  ├── NO — significant unexplained deviation / known red flags        │
│  │   └── Recommend: ESCALATE                                         │
│  │       Confidence: High (if pattern is clear), Medium (if complex) │
│  │       Action: Generate STR draft                                  │
│  │                                                                   │
│  └── CANNOT DETERMINE — critical data missing                        │
│      └── Recommend: INVESTIGATE                                      │
│          Confidence: Low                                              │
│          Note: "Insufficient evidence" — list missing data            │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Confidence Scoring Rubric

| Confidence Level | Criteria |
|---|---|
| **High** | All critical data present; pattern is clear and well-established (either clearly benign or clearly suspicious); no contradictory signals |
| **Medium** | Most data present; pattern suggests a disposition but some ambiguity remains; minor contradictory signals exist |
| **Low** | Critical data missing; contradictory signals; pattern does not clearly indicate any single disposition; "Insufficient evidence" scenarios |

### 5.3 Conservative Bias Design

The system is deliberately calibrated with a **conservative bias** — when uncertain, it leans toward recommending further investigation rather than closure:

| Ambiguity Level | Disposition Lean | Rationale |
|---|---|---|
| Clearly benign | Close (High confidence) | Analyst time is saved |
| Mostly benign with minor anomalies | Investigate (Medium confidence) | Err on the side of caution |
| Mixed signals | Investigate (Low-Medium confidence) | Do not risk a missed escalation |
| Clearly suspicious | Escalate (High confidence) | Strong pattern match to known typologies |
| Insufficient data | Investigate (Low confidence) | Never close what you cannot fully evaluate |

**Asymmetric error tolerance:** A false "Investigate" recommendation wastes some analyst time. A false "Close" recommendation on a genuinely suspicious alert is a regulatory and ethical failure. The system is calibrated to minimise the latter absolutely, even at the cost of more "Investigate" recommendations.

---

## 6. STR Narrative Generation

### 6.1 5W1H Narrative Structure

When the recommendation is "Escalate", the copilot generates a draft STR narrative following the standard 5W1H framework used by financial intelligence units:

```
[DRAFT — REQUIRES ANALYST REVIEW BEFORE SUBMISSION]

WHO:    Subject identification — name, account details, customer profile summary
WHAT:   Description of the suspicious activity — specific transactions, patterns,
        and total amounts involved
WHEN:   Timeframe of the activity — start date, end date, frequency
WHERE:  Accounts, branches, channels, and jurisdictions involved
WHY:    Basis for suspicion — how the activity deviates from expected behaviour,
        which red flags or typologies are present
HOW:    Method or mechanism — the pattern or technique observed
        (e.g., structuring, layering, rapid movement)

SUPPORTING DATA:
- Key transactions cited by ID
- KYC baseline comparison
- Prior alert history (if relevant)
```

### 6.2 Narrative Quality Rules

| Rule | Description |
|---|---|
| **Factual, not conclusory** | "12 cash deposits each below the $10,000 reporting threshold" — not "the subject laundered money" |
| **Quantified** | Include specific amounts, counts, dates, and timeframes |
| **Cited** | Every factual claim references source data |
| **Structured** | Follow 5W1H sections in order |
| **Marked as draft** | Header and footer both state `[DRAFT — REQUIRES ANALYST REVIEW]` |
| **No legal conclusions** | Describe patterns and deviations; do not state criminal intent |

### 6.3 Analyst Edit Tracking

When an analyst edits the AI-drafted narrative:
- The system stores both the **original AI draft** and the **analyst-edited version**.
- A **diff view** is available in the audit log showing what the analyst changed.
- This data serves two purposes:
  1. **Audit:** Regulators can see what was AI-generated vs. human-authored.
  2. **Improvement signal:** Systematic analyst edits indicate areas where the prompt or model should be refined.

---

## 7. Guardrail System

### 7.1 Guardrail Architecture (Defence in Depth)

```
┌────────────────────────────────────────────────────────────┐
│                   GUARDRAIL LAYERS                          │
│                                                            │
│  Layer 1: INPUT GUARDRAILS                                 │
│  ├── Input completeness check (missing KYC → block)        │
│  ├── Input sanitisation (strip injection attempts from      │
│  │   free-text fields like transaction memos)               │
│  └── Data freshness check (flag if KYC > 12 months old)    │
│                                                            │
│  Layer 2: PROMPT GUARDRAILS                                │
│  ├── Behavioural rules in system prompt                    │
│  ├── Citation requirements in system prompt                │
│  ├── Prohibited outputs list (no legal conclusions,        │
│  │   no demographic-based reasoning)                       │
│  └── Conservative bias instructions                        │
│                                                            │
│  Layer 3: OUTPUT GUARDRAILS                                │
│  ├── Schema validation (JSON structure matches spec)       │
│  ├── Citation validation (all citations map to source)     │
│  ├── Hallucination detection (amounts/dates in output      │
│  │   match input data)                                     │
│  ├── Prohibited content scan (legal conclusions, slurs,    │
│  │   demographic references in rationale)                  │
│  └── Confidence-disposition consistency check              │
│                                                            │
│  Layer 4: WORKFLOW GUARDRAILS                              │
│  ├── No auto-submission (analyst must click Submit)        │
│  ├── Rationale required (cannot submit without text)       │
│  ├── Override logging (divergence from AI → prompt note)   │
│  └── Audit completeness enforcement                        │
│                                                            │
│  Layer 5: EVALUATION GUARDRAILS                            │
│  ├── Missed escalation rate = 0% (hard gate)               │
│  ├── Hallucination rate < 2% (deployment blocker)          │
│  └── Regression testing on every prompt/model change       │
└────────────────────────────────────────────────────────────┘
```

### 7.2 Prompt Injection Defence

Transaction memo fields and other free-text customer data could contain adversarial strings designed to manipulate the LLM:

| Defence | Implementation |
|---|---|
| **Input sanitisation** | Strip or escape characters like `\n`, `---`, XML/HTML tags, and known injection patterns from free-text fields before inserting into prompt |
| **Data delimitation** | Wrap all injected data in clearly delimited XML-style tags (`<alert_data>...</alert_data>`) to separate data from instructions |
| **Output schema enforcement** | Use JSON mode; reject outputs that don't match the expected schema |
| **Anomaly detection** | Flag outputs where the recommendation text contains instructions, apologies, role-play language, or meta-references to the prompt |

### 7.3 Anti-Hallucination Validation

```python
# Pseudocode: Post-processing hallucination check
def validate_output(ai_output, input_context):
    issues = []
    
    # 1. Validate all cited transaction IDs exist in input
    for citation in extract_citations(ai_output, type="transaction"):
        if citation.txn_id not in input_context.transaction_ids:
            issues.append(f"HALLUCINATION: Transaction {citation.txn_id} not in input data")
    
    # 2. Validate amounts mentioned match source data
    for amount_claim in extract_amounts(ai_output):
        if not verify_amount_in_context(amount_claim, input_context):
            issues.append(f"HALLUCINATION: Amount ${amount_claim} not verifiable in input data")
    
    # 3. Validate dates mentioned are within input data range
    for date_claim in extract_dates(ai_output):
        if not verify_date_in_context(date_claim, input_context):
            issues.append(f"HALLUCINATION: Date {date_claim} not verifiable in input data")
    
    # 4. Validate customer details match
    for name_claim in extract_names(ai_output):
        if name_claim not in input_context.all_names:
            issues.append(f"HALLUCINATION: Name '{name_claim}' not in input data")
    
    # 5. Check for uncited factual claims
    uncited = count_uncited_factual_claims(ai_output)
    if uncited > 0:
        issues.append(f"WARNING: {uncited} factual claim(s) without citations")
    
    if len([i for i in issues if "HALLUCINATION" in i]) > 0:
        return ValidationResult(
            status="FAILED",
            issues=issues,
            action="SUPPRESS_RECOMMENDATION"  # Show degraded output
        )
    elif len(issues) > 0:
        return ValidationResult(
            status="WARNING", 
            issues=issues,
            action="SHOW_WITH_WARNINGS"
        )
    else:
        return ValidationResult(status="PASSED", issues=[], action="SHOW")
```

---

## 8. Output Validation & Post-Processing

### 8.1 Validation Pipeline

Every LLM response passes through the following validation pipeline before reaching the analyst:

```
LLM Raw Response
      │
      ▼
┌─────────────────┐    FAIL     ┌──────────────────────────┐
│  JSON Schema    │────────────▶│  Return error: "Copilot  │
│  Validation     │             │  could not generate a    │
│                 │             │  structured response."    │
└────────┬────────┘             └──────────────────────────┘
         │ PASS
         ▼
┌─────────────────┐    FAIL     ┌──────────────────────────┐
│  Recommendation │────────────▶│  Replace with:           │
│  Value Check    │             │  recommendation =        │
│  (Close/Inv/Esc)│             │  "Investigate",          │
│                 │             │  confidence = "Low"      │
└────────┬────────┘             └──────────────────────────┘
         │ PASS
         ▼
┌─────────────────┐  HALLUCINATION  ┌──────────────────────┐
│  Citation &     │────────────────▶│  Suppress specific    │
│  Hallucination  │                 │  claims; add warning  │
│  Validation     │                 │  banner to output     │
└────────┬────────┘                 └──────────────────────┘
         │ PASS / WARNING
         ▼
┌─────────────────┐    FAIL     ┌──────────────────────────┐
│  Prohibited     │────────────▶│  Redact prohibited       │
│  Content Scan   │             │  content; flag for review │
│                 │             │                           │
└────────┬────────┘             └──────────────────────────┘
         │ PASS
         ▼
┌─────────────────┐
│  Confidence-    │  Mismatch: adjust confidence or add
│  Disposition    │  warning (e.g., "Close" + "Low" is unusual)
│  Consistency    │
└────────┬────────┘
         │
         ▼
   Validated Output → Frontend
```

### 8.2 Degraded Response Format

When validation fails but partial output is usable:

```json
{
  "status": "DEGRADED",
  "warning": "The copilot's analysis could not be fully validated. Some claims may not be verifiable against source data. Please review all information independently.",
  "summary": "... (partial, with warnings inline) ...",
  "recommendation": null,
  "confidence": null,
  "rationale": [],
  "validation_issues": [
    "2 transaction citations could not be verified",
    "1 amount claim does not match source data"
  ]
}
```

---

## 9. Audit Logging Architecture

### 9.1 Audit Entry Schema

```json
{
  "entry_id": "AUD-2026-00001",
  "timestamp": "2026-11-09T14:32:18Z",
  "alert_id": "ALT-2026-001042",
  "customer_id": "CUST-88401",
  
  "ai_analysis": {
    "prompt_bundle_version": "PB-v1.0.0",
    "model_id": "gemini-2.5-pro",
    "model_version": "2026-10-01",
    "summary": "...",
    "recommendation": "Escalate",
    "confidence": "High",
    "rationale": [...],
    "risk_factors": [...],
    "mitigating_factors": [...],
    "missing_data": null,
    "str_draft": "...",
    "validation_result": "PASSED",
    "validation_issues": [],
    "response_time_ms": 4200
  },
  
  "analyst_decision": {
    "analyst_id": "ANALYST-042",
    "disposition": "Escalate",
    "rationale": "Agreed with AI assessment. Classic structuring pattern with no plausible explanation given customer profile.",
    "override": false,
    "override_reason": null,
    "str_final": "...(analyst-edited version)...",
    "str_edit_distance": 0.12,
    "decision_time_seconds": 185
  },
  
  "metadata": {
    "session_id": "SESS-20261109-042",
    "input_data_snapshot_hash": "sha256:a1b2c3d4...",
    "audit_entry_hash": "sha256:e5f6g7h8...",
    "previous_entry_hash": "sha256:i9j0k1l2..."
  }
}
```

### 9.2 Immutability & Integrity

| Property | Prototype Implementation | Production Implementation |
|---|---|---|
| **Append-only** | Audit entries written to append-only JSON file; no update/delete API | Write-once database table with no UPDATE/DELETE permissions |
| **Tamper evidence** | SHA-256 hash of each entry stored; each entry references previous hash (chain) | Cryptographic hash chain or integration with tamper-evident ledger |
| **Data snapshot** | Hash of the input context payload stored in audit entry | Full input snapshot archived alongside audit entry |
| **Version tracking** | Prompt bundle version + model version recorded | Same, plus infrastructure version |

### 9.3 Audit Query Capabilities

| Query | Purpose |
|---|---|
| "Show all decisions for customer X" | Examiner wants to see full history |
| "Show all overrides in the past 30 days" | Compliance manager monitors analyst-AI disagreement |
| "Show all 'Escalate' recommendations where analyst chose 'Close'" | Highest-risk overrides for quality review |
| "Show all alerts analysed with prompt bundle PB-v1.0.0" | Impact analysis before/after prompt changes |
| "Show all entries with validation warnings" | Quality monitoring of AI output |
| "Export audit log for date range as CSV" | Regulatory examination preparation |

---

## 10. Evaluation & Testing Harness

### 10.1 Evaluation Set Design

A curated **golden dataset** of 50+ alert scenarios with expert-labelled ground truth:

| Dimension | Coverage |
|---|---|
| **Alert archetypes** | All 12 from PRD Section 8.2 (structuring, layering, income inconsistency, dormant spike, round-trip, legitimate spike, salary pattern, explained large txn, missing KYC, mixed signals, PEP, watchlist hit) |
| **Expected dispositions** | Close (~40%), Investigate (~30%), Escalate (~25%), Insufficient Evidence (~5%) |
| **Edge cases** | Borderline amounts, partial structuring, single vs. multiple red flags |
| **Demographic diversity** | Varied names, nationalities, occupations — to test for bias |
| **Adversarial cases** | Transaction memos with injection-like strings |

### 10.2 Automated Evaluation Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│  Golden      │────▶│  Run each    │────▶│  Compare AI  │────▶│  Generate│
│  Dataset     │     │  alert thru  │     │  output vs.  │     │  Eval    │
│  (50+ cases) │     │  Copilot     │     │  expert      │     │  Report  │
│              │     │  Engine      │     │  labels      │     │          │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────┘

Eval Report contains:
├── Confusion matrix (Close / Investigate / Escalate / Insufficient)
├── Missed escalation rate (MUST = 0%)
├── False positive screening precision
├── Overall agreement rate
├── Citation accuracy rate
├── Hallucination count
├── Average response time
├── Per-archetype breakdown
└── Bias analysis (disposition distribution by customer demographics)
```

### 10.3 Evaluation Metrics & Thresholds

| Metric | Formula | Threshold | Action if Breached |
|---|---|---|---|
| **Missed escalation rate** | Expert="Escalate" & AI="Close" / Total expert "Escalate" | **0%** | BLOCK deployment; suspend "Close" suggestions |
| **FP screening precision** | AI "Close" matches expert "Close" / Total AI "Close" | ≥ 90% | Review prompt; consider raising "Investigate" threshold |
| **Overall agreement** | AI matches expert / Total | ≥ 85% | Review mismatched cases; refine prompt |
| **Citation accuracy** | Valid citations / Total citations | ≥ 95% | Strengthen citation instructions in prompt |
| **Hallucination rate** | Outputs with fabricated data / Total outputs | 0% target, < 2% hard limit | BLOCK deployment; strengthen output validation |
| **"Insufficient evidence" precision** | Correct "insufficient" / Total "insufficient" | ≥ 90% | Review input completeness thresholds |
| **Response time (p95)** | 95th percentile response time | < 10 seconds | Optimise prompt length or model selection |

### 10.4 Bias Evaluation

For every evaluation run, the system computes disposition distribution segmented by:
- Customer nationality
- Customer name (as a proxy for perceived ethnicity)
- Customer gender
- Customer occupation

**Alert:** If the disposition for any demographic segment deviates by >10 percentage points from the overall distribution without a corresponding difference in underlying alert patterns, a bias warning is triggered.

### 10.5 Regression Testing Protocol

| Trigger | Action |
|---|---|
| Any change to system prompt | Full evaluation suite run |
| Any change to output schema | Full evaluation suite run |
| Model version change | Full evaluation suite run |
| New alert archetype added to golden set | Full evaluation suite run |
| Weekly (regardless of changes) | Full evaluation suite run |

---

## 11. Failure Modes & Resilience

### 11.1 Failure Mode Analysis

| Failure | Impact | Detection | Response |
|---|---|---|---|
| **LLM API timeout** | No copilot analysis available | API response timeout (>30s) | Show alert data without copilot; analyst proceeds manually |
| **LLM API rate limit** | Delayed copilot analysis | HTTP 429 response | Queue request; show "Analysis in progress..."; retry with exponential backoff |
| **LLM returns malformed JSON** | Cannot parse recommendation | JSON parse error | Retry once; if still fails, show degraded response |
| **LLM hallucinates data** | False information shown to analyst | Output validation catches mismatch | Suppress recommendation; show warning banner |
| **Input data service unavailable** | Cannot assemble context | Data service timeout/error | Show partial context (what's available); copilot flags missing data |
| **Audit log write failure** | Decision not recorded | Write acknowledgement missing | Block submission; show error; retry; require manual fallback logging |

### 11.2 Graceful Degradation Hierarchy

```
Level 0: FULL SERVICE
  All systems operational — full copilot analysis with recommendation

Level 1: DEGRADED ANALYSIS  
  LLM available but output has validation warnings — show analysis with 
  warning banners; analyst proceeds with extra caution

Level 2: CONTEXT ONLY
  LLM unavailable — show assembled context data (KYC, transactions, rule 
  details) without AI analysis; analyst reviews manually

Level 3: ALERT ONLY
  Data services partially unavailable — show alert metadata only; analyst 
  must gather context from source systems manually

Level 4: SYSTEM UNAVAILABLE
  Core application down — analyst falls back to existing manual workflow
```

---

## 12. Security & Privacy Considerations

### 12.1 Prototype Scope

Since the prototype uses **synthetic data only**, production-grade security controls are not implemented but are documented here for the production roadmap:

| Concern | Prototype | Production |
|---|---|---|
| **Data classification** | Fictional data — no PII | All data classified as Confidential / Restricted |
| **LLM API** | External cloud API (acceptable for synthetic data) | On-premise or private cloud inference; no customer data leaves bank network |
| **Authentication** | None (single-user prototype) | SSO/SAML integration with bank's IAM |
| **Authorisation** | None | Role-based access: Analyst (triage), Manager (review + config), Auditor (read-only audit) |
| **Encryption** | HTTPS for API calls | TLS 1.3 in transit; AES-256 at rest; HSM for audit log signing keys |
| **Data retention** | In-memory / local file | Defined by bank's data retention policy and regulatory requirements |
| **Audit log access** | Open (prototype) | Restricted to Compliance and Audit roles; access itself is logged |

### 12.2 LLM-Specific Security Concerns

| Concern | Mitigation |
|---|---|
| **Prompt injection** | Input sanitisation + data delimitation + output validation (see Section 7.2) |
| **Data leakage to LLM provider** | Prototype: synthetic data only. Production: private deployment, no data sent to external APIs |
| **Model memorisation** | Do not fine-tune on real customer data without privacy review |
| **Output consistency** | Low temperature (0.1); pinned model version; evaluation regression testing |

---

## 13. Technology Stack (Prototype)

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Streamlit (Python) or React + Tailwind CSS | Streamlit for rapid prototyping; React for richer interactions |
| **Backend API** | FastAPI (Python) | Lightweight, async, good typing support, fast development |
| **LLM Integration** | LangChain or direct API calls (Gemini / OpenAI SDK) | Abstraction layer for multi-model evaluation |
| **Data Store** | JSON files (synthetic data) | No database setup needed for prototype |
| **Audit Store** | Append-only JSON file with hash chain | Simple, inspectable, sufficient for prototype |
| **Evaluation** | Python scripts + Pandas + pytest | Automated eval pipeline with assertion-based testing |
| **Hosting** | Local development / Streamlit Cloud | Easy to demo and share |

### 13.1 Prototype Directory Structure

```
AML-Alert-Triage-Copilot/
├── app/
│   ├── main.py                  # Streamlit app entry point
│   ├── pages/
│   │   ├── dashboard.py         # Alert queue dashboard
│   │   ├── triage.py            # Triage workspace (alert + copilot)
│   │   ├── audit.py             # Audit log viewer
│   │   └── evaluation.py        # Evaluation metrics dashboard
│   ├── copilot/
│   │   ├── engine.py            # Core copilot logic (context → LLM → validation)
│   │   ├── prompts.py           # Prompt templates (versioned)
│   │   ├── citations.py         # Citation extraction & validation
│   │   ├── validator.py         # Output validation pipeline
│   │   └── str_generator.py     # STR narrative generation
│   ├── data/
│   │   ├── context_assembler.py # Assembles context from data files
│   │   └── audit_logger.py      # Append-only audit log writer
│   └── utils/
│       ├── config.py            # Configuration and environment
│       └── sanitiser.py         # Input sanitisation for prompt injection
├── data/
│   ├── alerts.json              # Synthetic alert scenarios
│   ├── customers.json           # Synthetic KYC profiles
│   ├── transactions.json        # Synthetic transaction ledgers
│   └── watchlists.json          # Synthetic watchlist data
├── evaluation/
│   ├── golden_dataset.json      # Expert-labelled evaluation set
│   ├── run_evaluation.py        # Automated evaluation script
│   ├── metrics.py               # Metric computation functions
│   └── reports/                 # Generated evaluation reports
├── audit_log/
│   └── audit_log.jsonl          # Append-only audit log (JSONL format)
├── docs/
│   ├── PRD_AML_Copilot.md
│   ├── AI_SYSTEM_DESIGN.md
│   └── EVALUATION_FRAMEWORK.md
├── requirements.txt
└── README.md
```

---

## 14. Future Architecture (Production)

### 14.1 Production Architecture Vision

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BANK NETWORK BOUNDARY                        │
│                                                                     │
│  ┌────────────┐    ┌────────────┐    ┌──────────────────────────┐   │
│  │ Transaction│    │  KYC /     │    │  Case Management         │   │
│  │ Monitoring │───▶│  CDD       │    │  System                  │   │
│  │ System     │    │  System    │    │  (Actimize / in-house)   │   │
│  └─────┬──────┘    └─────┬──────┘    └────────────┬─────────────┘   │
│        │                 │                        │                 │
│        ▼                 ▼                        ▼                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                 INTEGRATION LAYER (APIs / ETL)                │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              AML COPILOT APPLICATION LAYER                    │   │
│  │  ┌──────────┐  ┌────────────┐  ┌───────────┐  ┌───────────┐ │   │
│  │  │ Context  │  │  Copilot   │  │  Output   │  │  Audit    │ │   │
│  │  │ Assembly │──│  Engine    │──│  Validator │──│  Logger   │ │   │
│  │  └──────────┘  └─────┬──────┘  └───────────┘  └───────────┘ │   │
│  └──────────────────────┼──────────────────────────────────────┘   │
│                         │                                           │
│                         ▼                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │          PRIVATE LLM INFERENCE (On-Premise / VPC)             │   │
│  │          No customer data leaves bank network                 │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.2 Production Enhancements

| Capability | Description |
|---|---|
| **RAG (Retrieval-Augmented Generation)** | Vector store of regulatory guidance, typology catalogues, and internal policy documents to enrich copilot reasoning |
| **Feedback loop** | Analyst corrections feed into prompt refinement and evaluation set expansion |
| **A/B testing** | Run multiple prompt versions side by side; measure analyst satisfaction and accuracy |
| **Model monitoring** | Track output distribution drift, latency degradation, and confidence calibration over time |
| **Multi-language support** | STR narrative generation in multiple languages for cross-border cases |
| **Alert prioritisation** | ML-based pre-scoring to rank alerts by likely severity before copilot analysis |

---

*End of AI System Design Document — Version 1.0*
