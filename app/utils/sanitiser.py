import re
from typing import Any

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?prior\s+instructions",
    r"(?i)system\s*:\s*",
    r"(?i)disregard\s+(the\s+)?above",
    r"(?i)you\s+are\s+now\s+a",
    r"(?i)output\s+only\s+JSON\s+that\s+says",
    r"(?i)<script[\s\S]*?>[\s\S]*?</script>",
    r"(?i)drop\s+table",
]

def sanitise_string(text: Any) -> str:
    """Sanitises input strings by escaping XML/HTML delimiters,

    stripping control characters, and neutralising potential prompt injection strings.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Remove null bytes and non-printable control chars
    clean_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Escape HTML/XML tags
    clean_text = clean_text.replace("<", "&lt;").replace(">", "&gt;")

    # Redact injection attempts
    for pattern in INJECTION_PATTERNS:
        clean_text = re.sub(pattern, "[REDACTED_PROMPT_INJECTION_PATTERN]", clean_text)

    return clean_text.strip()

def sanitise_payload(data: Any) -> Any:
    """Recursively traverses dictionary/list structures and sanitises all string values."""
    if isinstance(data, dict):
        return {k: sanitise_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitise_payload(item) for item in data]
    elif isinstance(data, str):
        return sanitise_string(data)
    return data
