import re
from sentence_transformers import SentenceTransformer, util

from ..llm_client import _safe_generate  # reuse your LLM safely

model = SentenceTransformer('all-MiniLM-L6-v2')


# -------------------------
# Clean requirement
# -------------------------
def clean_requirement(text: str) -> str:
    t = text.lower()

    t = re.sub(r"\b(as_a:|i_want:|so_that:)\b", " ", t)
    t = re.sub(r"\b[a-z]*\d[\w\.-]*\b", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    return t


# -------------------------
# 🔥 DYNAMIC SCENARIO EXTRACTION (LLM)
# -------------------------
def extract_dynamic_scenarios(requirement: str):
    prompt = f"""
You are a senior QA engineer.

Extract testing scenarios from the requirement.

Requirement:
{requirement}

Return ONLY a simple list:
- short phrases
- no explanation
- include:
  - positive scenarios
  - negative scenarios
  - edge cases
  - system scenarios
"""

    response = _safe_generate(prompt)

    if not response:
        return []

    lines = [l.strip("- ").strip() for l in response.split("\n") if l.strip()]
    return list(set(lines))


# -------------------------
# 🔥 QA ENFORCEMENT LAYER
# -------------------------
def enforce_qa_scenarios(scenarios):
    required = [
        "positive scenario",
        "negative scenario",
        "edge case",
        "validation scenario"
    ]

    return list(set(scenarios + required))


# -------------------------
# Convert testcase → text
# -------------------------
def testcase_to_text(tc):
    return " ".join([
        tc.get("title", ""),
        " ".join(tc.get("steps", [])),
        tc.get("expected", ""),
        tc.get("type", "")
    ]).lower()


# -------------------------
# Semantic coverage
# -------------------------
def is_semantically_covered(scenario, testcases, threshold=0.4):
    scenario_emb = model.encode(scenario, convert_to_tensor=True)

    tc_texts = [testcase_to_text(tc) for tc in testcases]
    tc_embs = model.encode(tc_texts, convert_to_tensor=True)

    scores = util.cos_sim(scenario_emb, tc_embs)
    max_score = scores.max().item()

    print(f"[COVERAGE DEBUG] Scenario: {scenario} | Score: {max_score:.3f}")

    return max_score >= threshold


# -------------------------
# 🔥 QA CATEGORY DETECTION
# -------------------------
def detect_qa_categories(testcases):
    text = " ".join([
        testcase_to_text(tc)
        for tc in testcases
    ])

    return {
        "positive": any(k in text for k in ["success", "valid"]),
        "negative": any(k in text for k in ["invalid", "error", "fail"]),
        "edge": any(k in text for k in ["empty", "boundary", "limit"]),
        "system": any(k in text for k in ["timeout", "concurrent", "rate", "session"])
    }


# -------------------------
# 🔥 FINAL COVERAGE ENGINE
# -------------------------
def simple_coverage(testcases, requirement):

    # 🔥 STEP 1: dynamic extraction
    scenarios = extract_dynamic_scenarios(requirement)

    # fallback safety
    if not scenarios:
        scenarios = [clean_requirement(requirement)]

    # 🔥 STEP 2: enforce QA basics
    scenarios = enforce_qa_scenarios(scenarios)

    if not testcases:
        return {
            "coverage_percent": 0,
            "covered_scenarios": [],
            "missing_scenarios": scenarios,
            "total_scenarios": len(scenarios),
            "qa_gaps": ["No testcases generated"],
            "qa_score": 0
        }

    # 🔥 STEP 3: semantic matching
    covered = []
    for sc in scenarios:
        if is_semantically_covered(sc, testcases):
            covered.append(sc)

    missing = list(set(scenarios) - set(covered))
    total = len(scenarios) if scenarios else 1

    # 🔥 STEP 4: QA gap detection
    qa_flags = detect_qa_categories(testcases)

    qa_gaps = []
    if not qa_flags["positive"]:
        qa_gaps.append("Missing positive scenarios")
    if not qa_flags["negative"]:
        qa_gaps.append("Missing negative scenarios")
    if not qa_flags["edge"]:
        qa_gaps.append("Missing edge cases")
    if not qa_flags["system"]:
        qa_gaps.append("Missing system scenarios")

    # 🔥 STEP 5: scoring
    qa_score = max(0, 100 - (len(qa_gaps) * 20))

    return {
        "coverage_percent": round((len(covered) / total) * 100, 2),
        "covered_scenarios": covered,
        "missing_scenarios": missing,
        "total_scenarios": total,
        "qa_gaps": qa_gaps,
        "qa_score": qa_score
    }
