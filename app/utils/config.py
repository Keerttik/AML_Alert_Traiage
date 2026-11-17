import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIT_LOG_DIR = BASE_DIR / "audit_log"
EVALUATION_DIR = BASE_DIR / "evaluation"

# Ensure directories exist
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_LOG_FILE = AUDIT_LOG_DIR / "audit_log.jsonl"

# Prompt & Model Versioning
PROMPT_BUNDLE_VERSION = "PB-v1.0.0"
SYSTEM_PROMPT_VERSION = "SYS-v1.0"
OUTPUT_SCHEMA_VERSION = "SCHEMA-v1.0"
DEFAULT_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "deterministic-aml-rule-engine-v1"

# API Keys (from environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
