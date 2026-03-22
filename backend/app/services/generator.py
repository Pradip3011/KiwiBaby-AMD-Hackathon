from ..llm_client import generate_structured_testcases


def fallback_testcases(requirement: str):
    return [
        {
            "id": "TC_001",
            "title": f"Basic test for: {requirement[:30]}",
            "steps": ["Execute the main flow"],
            "expected": "System behaves as expected"
        }
    ]


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


def add_ids(testcases):
    for i, tc in enumerate(testcases, start=1):
        tc["id"] = f"TC_{i:03}"
    return testcases


def generate_testcases(requirement: str):
    try:
        testcases = generate_structured_testcases(requirement)

        testcases = validate_testcases(testcases)
        testcases = add_ids(testcases)

        if not testcases:
            return fallback_testcases(requirement)

        return testcases

    except Exception as e:
        print(f"[GENERATOR ERROR] {e}")
        return fallback_testcases(requirement)
