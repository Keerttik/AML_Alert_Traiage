import json
from typing import Dict, Any
from app.utils.config import (
    PROMPT_BUNDLE_VERSION,
    SYSTEM_PROMPT_VERSION,
    OUTPUT_SCHEMA_VERSION
)

SYSTEM_PROMPT = """You are an AML Alert Triage Copilot assisting a human compliance analyst.
Your role is to PREPARE context and RECOMMEND a disposition. You do NOT make final decisions.

BEHAVIOURAL RULES (you must strictly follow these without exception):
1. NEVER state that an activity "is" money laundering or "is" a crime. Instead, describe observed transactional patterns and how they deviate from expected customer behaviour.
2. EVERY factual claim must include an inline citation in brackets referencing the specific data source. Valid citation formats:
   - [KYC: FieldName] or [KYC Profile] — for customer identity, income, occupation, baseline
   - [Txn: TXN-XXXXXX] — for specific transaction references
   - [Rule: RULE-ID] — for monitoring rule details
   - [Prior Alert: ALT-XXXX] — for prior alert history
   - [Counterparty: NAME] — for counterparty information
   - [Watchlist: LIST_NAME] or [Watchlist] — for watchlist match information
3. If you do not have sufficient data to support a claim, do NOT fabricate it. Instead, state what data is missing and how it limits your analysis.
4. NEVER invent transactions, amounts, dates, counterparties, or any other data not present in the context provided.
5. Your recommendation must be exactly one of: "Close", "Investigate", or "Escalate".
6. If the evidence is genuinely ambiguous or critical data is missing, your recommendation must be "Investigate" and your confidence must be "Low", with a clear statement in "missing_data" of what additional information would resolve the ambiguity.
7. When recommending "Escalate", generate an STR narrative draft following the standard 5W1H structure. Mark it clearly as "[DRAFT — REQUIRES ANALYST REVIEW]".
8. Do NOT make recommendations based on customer demographics (nationality, ethnicity, gender, age). Base all analysis on behavioural patterns, transactional data, and KYC deviations.

OUTPUT FORMAT:
Respond ONLY with a valid JSON object matching the schema provided. Do NOT include any text, markdown backticks, or commentary outside the JSON object.
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Plain-language summary of why the alert fired and unusual deviations, with inline citations."
        },
        "recommendation": {
            "type": "string",
            "enum": ["Close", "Investigate", "Escalate"]
        },
        "confidence": {
            "type": "string",
            "enum": ["High", "Medium", "Low"]
        },
        "rationale": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "source_citations": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["reason", "source_citations"]
            }
        },
        "risk_factors": {
            "type": "array",
            "items": {"type": "string"}
        },
        "mitigating_factors": {
            "type": "array",
            "items": {"type": "string"}
        },
        "missing_data": {
            "type": ["array", "null"],
            "items": {"type": "string"}
        },
        "str_draft": {
            "type": ["string", "null"],
            "description": "5W1H narrative marked as [DRAFT - REQUIRES ANALYST REVIEW] if recommendation is Escalate, otherwise null."
        }
    },
    "required": ["summary", "recommendation", "confidence", "rationale", "risk_factors", "mitigating_factors"]
}

def build_prompt_payload(context_payload: Dict[str, Any]) -> Dict[str, str]:
    """Builds prompt parts for LLM submission."""
    user_instruction = (
        "Analyse the alert and customer context provided below. Provide:\n"
        "1. A plain-language summary of why this alert fired and what is unusual compared to the customer's profile.\n"
        "2. Your recommended disposition (Close, Investigate, or Escalate) with cited reasoning.\n"
        "3. Key risk factors and mitigating factors (each with source citations).\n"
        "4. If recommending 'Escalate', a draft 5W1H STR narrative.\n\n"
        f"ALERT CONTEXT:\n{json.dumps(context_payload, indent=2)}\n\n"
        "Remember: output strictly valid JSON conforming to the specified schema."
    )
    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": user_instruction,
        "prompt_bundle_version": PROMPT_BUNDLE_VERSION,
        "system_version": SYSTEM_PROMPT_VERSION,
        "schema_version": OUTPUT_SCHEMA_VERSION
    }
