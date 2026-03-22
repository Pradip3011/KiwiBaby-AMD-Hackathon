# backend/app/utils.py

import json
import re
import logging
from typing import Any

logger = logging.getLogger("ai-testcase-agent.utils")


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
