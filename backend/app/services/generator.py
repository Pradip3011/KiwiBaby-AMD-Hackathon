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
            "expected": "System behaves as expected",
            "type": "Positive" # <--- Add this
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
            # Ensure the type field exists for the evaluator
            if "type" not in tc:
                tc["type"] = "General"
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
# 🔥 CLEAN + MERGE SCENARIOS (CRITICAL FIX)
# -------------------------
def prepare_missing_scenarios(missing_scenarios):
    """
    Cleans + deduplicates missing scenarios before injecting into LLM.
    Prevents noisy prompts and repeated ideas.
    """

    if not missing_scenarios:
        return []

    cleaned = []

    for sc in missing_scenarios:
        sc = sc.strip()

        if not sc:
            continue

        # remove noise
        if "here are" in sc.lower():
            continue
        if sc.startswith("**"):
            continue
        if len(sc) < 10:
            continue

        cleaned.append(sc)

    # remove duplicates + limit size
    return list(set(cleaned))[:5]


# -------------------------
# 🔥 REQUIREMENT INTELLIGENCE LAYER
# -------------------------
def enrich_requirement(requirement: str, missing_scenarios=None):
    """
    Adds structured QA thinking BEFORE LLM call.
    Injects CLEANED missing scenarios for controlled self-improvement.
    """

    missing_block = ""

    cleaned_missing = prepare_missing_scenarios(missing_scenarios)

    if cleaned_missing:
        missing_block = "\nMissing Scenarios to Improve Coverage:\n"
        for m in cleaned_missing:
            missing_block += f"- {m}\n"

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
- Avoid generic or duplicate scenarios

{missing_block}
"""


# -------------------------
# 🔥 MAIN GENERATOR (STABLE + SELF-IMPROVING)
# -------------------------
def generate_testcases(requirement: str, missing_scenarios=None):
    try:
        # 🔥 Controlled enrichment (no noise injection)
        enriched_requirement = enrich_requirement(requirement, missing_scenarios)

        testcases = generate_structured_testcases(enriched_requirement)

        testcases = validate_testcases(testcases)
        testcases = add_ids(testcases)

        if not testcases:
            return fallback_testcases(requirement)

        return testcases

    except Exception as e:
        print(f"[GENERATOR ERROR] {e}")
        return fallback_testcases(requirement)
