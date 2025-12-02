# utils.py

import json
import re

def try_parse_json(text: str):
    """
    Attempts to safely parse JSON.
    Auto-fixes truncated or fenced JSON strings.
    Returns parsed JSON or None.
    """
    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown fences
    cleaned = re.sub(r"```[a-zA-Z]*", "", cleaned)
    cleaned = cleaned.replace("```", "").strip()

    # Attempt to parse directly
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to close unclosed JSON object
        if not cleaned.endswith("}"):
            cleaned += "}"
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: extract first JSON block using regex
            try:
                match = re.search(r"\{[\s\S]*\}", cleaned)
                if match:
                    return json.loads(match.group(0))
            except:
                return None
    return None

# ----------------------------------
# Add this function to utils.py
# ----------------------------------
def auto_number_test_cases(json_data: dict):
    """
    Assign sequential IDs to all test cases: TC-001, TC-002, etc.
    """
    if not json_data or "test_cases" not in json_data:
        return json_data

    for i, tc in enumerate(json_data["test_cases"], start=1):
        tc["id"] = f"TC-{i:03}"
    return json_data
