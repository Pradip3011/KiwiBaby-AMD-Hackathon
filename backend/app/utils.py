import json
import re
import logging
from typing import Any

logger = logging.getLogger("kiwibaby.utils")


# -------------------------
# JSON PARSER
# -------------------------
def try_parse_json(text: str) -> Any | None:
    """
    Robust JSON parser for LLM output.
    """
    if not text or not isinstance(text, str):
        logger.warning("Invalid input to try_parse_json")
        return None

    cleaned = text.strip()

    # Remove markdown fences
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # Attempt direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract JSON block
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
    if match:
        candidate = match.group(0).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = candidate  # fallback to repair

    # Repair truncated JSON (simple heuristics)
    try:
        open_braces = cleaned.count("{")
        close_braces = cleaned.count("}")
        if open_braces > close_braces:
            cleaned += "}" * (open_braces - close_braces)

        open_brackets = cleaned.count("[")
        close_brackets = cleaned.count("]")
        if open_brackets > close_brackets:
            cleaned += "]" * (open_brackets - close_brackets)

        return json.loads(cleaned)
    except Exception:
        logger.warning("JSON parsing failed after repair attempt")
        return None


# -------------------------
# AUTO NUMBERING
# -------------------------
def auto_number_test_cases(json_data: Any) -> Any:
    """
    Assign sequential IDs: TC_001, TC_002
    """
    if not json_data:
        return json_data

    # Case 1: dict with test_cases
    if isinstance(json_data, dict) and isinstance(json_data.get("test_cases"), list):
        for i, tc in enumerate(json_data["test_cases"], start=1):
            if isinstance(tc, dict) and not tc.get("id"):
                tc["id"] = f"TC_{i:03}"
        return json_data

    # Case 2: direct list
    if isinstance(json_data, list):
        for i, tc in enumerate(json_data, start=1):
            if isinstance(tc, dict) and not tc.get("id"):
                tc["id"] = f"TC_{i:03}"
        return json_data

    return json_data


# ---------------------------------------------------------
# 🏎️ TRACK 1 PROMPT COMPRESSION ENGINE
# ---------------------------------------------------------
def compress_prompt_payload(prompt: str) -> tuple[str, float]:
    """
    Slices non-essential conversational words and redundant fluff.
    Targets a 20-35% token reduction for Tier 2 remote optimizations
    while explicitly guarding core operational logic predicates.
    """
    if not prompt or not prompt.strip():
        return prompt, 1.0

    original_words = prompt.split()
    original_count = len(original_words)

    # Fluff arrays to scrub for token optimization
    conversational_noise = [
        r"\bplease\b", r"\bcould you\b", r"\bkindly\b", r"\bwrite a test case for\b",
        r"\bgenerate test cases for\b", r"\bi want to\b", r"\bcan you help me\b",
        r"\bmake sure to\b", r"\bas an agent\b", r"\bfor the purpose of\b"
    ]

    compressed_text = prompt
    for pattern in conversational_noise:
        compressed_text = re.sub(pattern, "", compressed_text, flags=re.IGNORECASE)

    # Collapse extra spacing artifacts left from stripping
    compressed_text = re.sub(r"\s+", " ", compressed_text).strip()
    
    compressed_words = compressed_text.split()
    compressed_count = len(compressed_words)

    # Protect meaning: If compression accidentally clears out too much, fall back to original
    if compressed_count < 5 and original_count > 10:
        logger.warning("Compression degraded payload context integrity. Falling back to original.")
        return prompt, 1.0

    compression_ratio = round(compressed_count / original_count, 4) if original_count > 0 else 1.0
    reduction = 1.0 - compression_ratio

    if reduction < 0.20 and original_count > 40:
        logger.info(f"Compression yield minimal: {reduction * 100:.1f}% reduction recorded.")

    return compressed_text, compression_ratio