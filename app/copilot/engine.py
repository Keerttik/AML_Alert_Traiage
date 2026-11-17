import time
from typing import Dict, Any, Optional
from app.data.context_assembler import ContextAssembler
from app.copilot.llm_client import LLMClient
from app.copilot.validator import OutputValidator
from app.utils.config import PROMPT_BUNDLE_VERSION

class CopilotEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.context_assembler = ContextAssembler()
        self.llm_client = LLMClient(api_key=api_key)
        self.validator = OutputValidator()

    def set_api_key(self, api_key: str):
        self.llm_client.api_key = api_key

    def triage_alert(self, alert_id: str) -> Dict[str, Any]:
        """Executes the full copilot pipeline for an alert:

        Context Assembly -> LLM Generation / Reasoning -> Output Validation -> Citation Check
        """
        start_time = time.time()

        # 1. Assemble context
        context = self.context_assembler.assemble_context(alert_id)

        # 2. Generate analysis
        raw_analysis = self.llm_client.generate_analysis(context)

        # 3. Output validation & citation checks
        validation_res = self.validator.validate(raw_analysis, context)

        elapsed_ms = int((time.time() - start_time) * 1000)

        model_used = raw_analysis.get("_model_used", "unknown")
        # Clean internal keys
        analysis_cleaned = {k: v for k, v in raw_analysis.items() if not k.startswith("_")}

        return {
            "alert_id": alert_id,
            "context": context,
            "analysis": analysis_cleaned,
            "validation": {
                "status": validation_res["status"],
                "issues": validation_res["issues"],
                "citation_stats": validation_res.get("citation_stats", {}),
                "hallucinations_detected": validation_res["hallucinations_detected"]
            },
            "metadata": {
                "prompt_bundle_version": PROMPT_BUNDLE_VERSION,
                "model_id": model_used,
                "response_time_ms": elapsed_ms
            }
        }
