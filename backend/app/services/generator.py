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
            "type": "Positive"
        }
    ]


# -------------------------
# VALIDATION
# -------------------------
def validate_testcases(testcases):
    valid = []
    if not testcases:
        return valid

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
# 🔥 CLEAN + MERGE SCENARIOS (BUSTER FIX FOR PARSER DUMPS)
# -------------------------
def prepare_missing_scenarios(missing_scenarios):
    """
    Cleans + deduplicates missing scenarios before injecting into LLM.
    Explicitly filters out corrupted parser dumps from failing evaluation cycles.
    """
    if not missing_scenarios:
        return []

    cleaned = []

    for sc in missing_scenarios:
        if not isinstance(sc, str):
            continue
            
        sc = sc.strip()

        if not sc:
            continue

        # 🛑 FILTER: Catch raw conversational phrases
        if any(phrase in sc.lower() for phrase in ["here are", "let's give them", "good luck configuring"]):
            continue
            
        # 🛑 FILTER: Catch corrupted parser dumps containing raw schema artifacts
        if any(artifact in sc.lower() for artifact in ["json id tc_", "expected the system successfully", "bypasses speed of light"]):
            continue
            
        # 🛑 FILTER: Catch generic formatting indicators
        if sc.startswith("**") or len(sc) < 10:
            continue

        cleaned.append(sc)

    # Remove duplicates + limit size to avoid prompt bloat
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
        missing_block = "\nMissing Scenarios to Improve Coverage (Address these specifically):\n"
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
        # Controlled enrichment (no noise injection)
        enriched_requirement = enrich_requirement(requirement, missing_scenarios)

        # Call underlying client
        testcases = generate_structured_testcases(enriched_requirement)

        # Post-processing pipeline
        testcases = validate_testcases(testcases)
        testcases = add_ids(testcases)

        if not testcases:
            return fallback_testcases(requirement)

        return testcases

    except Exception as e:
        print(f"[GENERATOR ERROR] {e}")
        return fallback_testcases(requirement)