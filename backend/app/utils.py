# backend/app/utils.py
import json
import re
from typing import Any


def try_parse_json(text: str) -> Any | None:
    """
    Safely parse JSON from LLM output.

    Handles:
    - markdown code fences
    - extra commentary
    - truncated JSON
    - JSON objects or arrays

    Returns parsed JSON or None.
    """
    if not text or not isinstance(text, str):
        return None

    cleaned = text.strip()

    # Remove markdown code fences like ```json ... ```
    cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = cleaned.strip()

    # Try parsing directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract first JSON object or array from surrounding text
    try:
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if match:
            candidate = match.group(0).strip()
            return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Attempt simple repair for truncated JSON
    try:
        if cleaned.startswith("{") and not cleaned.endswith("}"):
            return json.loads(cleaned + "}")

        if cleaned.startswith("[") and not cleaned.endswith("]"):
            return json.loads(cleaned + "]")
    except json.JSONDecodeError:
        pass

    return None


def auto_number_test_cases(json_data: Any) -> Any:
    """
    Assign sequential IDs to test cases: TC-001, TC-002, etc.

    Supports:
    - {"test_cases": [...]}
    - direct list [...]

    Does not overwrite an existing non-empty id.
    """
    if not json_data:
        return json_data

    # Case 1: dict with test_cases
    if isinstance(json_data, dict) and isinstance(json_data.get("test_cases"), list):
        for i, tc in enumerate(json_data["test_cases"], start=1):
            if isinstance(tc, dict) and not tc.get("id"):
                tc["id"] = f"TC-{i:03}"
        return json_data

    # Case 2: direct list of test case dicts
    if isinstance(json_data, list):
        for i, tc in enumerate(json_data, start=1):
            if isinstance(tc, dict) and not tc.get("id"):
                tc["id"] = f"TC-{i:03}"
        return json_data

    return json_data
