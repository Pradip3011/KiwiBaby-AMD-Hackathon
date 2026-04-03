from ..llm_client import generate_structured_testcases


# -------------------------
# FALLBACK
# -------------------------
def fallback_testcases(requirement: str):
    return [
        {
            "id": "TC_001",
            "title": f"Basic test for: {requirement[:30]}",
            "steps": ["Execute the main flow"],
            "expected": "System behaves as expected"
        }
    ]


# -------------------------
# VALIDATION
# -------------------------
def validate_testcases(testcases):
    valid = []

    for tc in testcases:
        if (
            isinstance(tc, dict)
            and tc.get("title")
            and tc.get("steps")
            and tc.get("expected")
        ):
            valid.append(tc)

    return valid


# -------------------------
# ID ASSIGNMENT
# -------------------------
def add_ids(testcases):
    for i, tc in enumerate(testcases, start=1):
        tc["id"] = f"TC_{i:03}"
    return testcases


# -------------------------
# 🔥 NEW: REQUIREMENT INTELLIGENCE LAYER
# -------------------------
def enrich_requirement(requirement: str):
    """
    Adds structured QA thinking BEFORE LLM call.
    This improves both JSON and GHERKIN indirectly.
    """

    return f"""
Requirement:
{requirement}

QA Analysis Instructions:
- Identify core user actions
- Identify validation rules
- Identify failure scenarios
- Identify edge cases
- Identify system-level risks (session, concurrency, rate limiting)

Ensure:
- Coverage includes UI + API if applicable
- Include real-world failure conditions
- Avoid generic scenarios
"""


# -------------------------
# 🔥 MAIN GENERATOR (UPGRADED)
# -------------------------
def generate_testcases(requirement: str):
    try:
        # 🔥 NEW: enrich requirement BEFORE sending to LLM
        enriched_requirement = enrich_requirement(requirement)

        testcases = generate_structured_testcases(enriched_requirement)

        testcases = validate_testcases(testcases)
        testcases = add_ids(testcases)

        if not testcases:
            return fallback_testcases(requirement)

        return testcases

    except Exception as e:
        print(f"[GENERATOR ERROR] {e}")
        return fallback_testcases(requirement)
