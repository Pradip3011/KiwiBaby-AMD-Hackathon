import re
from sentence_transformers import SentenceTransformer, util

from ..llm_client import _safe_generate

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
# 🔥 DYNAMIC SCENARIO EXTRACTION (LLM) — LIGHTWEIGHT
# -------------------------
def extract_dynamic_scenarios(requirement: str):
    prompt = f"""
You are a QA engineer.

Extract ONLY realistic test scenarios.

Requirement:
{requirement}

Return:
- short phrases
- practical QA scenarios only
- exclude performance, logging, internal system details
"""

    response = _safe_generate(prompt)

    if not response:
        return []

    lines = [l.strip("- ").strip() for l in response.split("\n") if l.strip()]
    return list(set(lines))


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
# Semantic coverage (clean)
# -------------------------
def is_semantically_covered(scenario, testcases, threshold=0.4):
    scenario_emb = model.encode(scenario, convert_to_tensor=True, show_progress_bar=False)

    tc_texts = [testcase_to_text(tc) for tc in testcases]
    tc_embs = model.encode(tc_texts, convert_to_tensor=True, show_progress_bar=False)

    scores = util.cos_sim(scenario_emb, tc_embs)
    max_score = scores.max().item()

    return max_score >= threshold


# -------------------------
# 🔥 REAL QA SCORING ENGINE
# -------------------------
def calculate_qa_score(testcases):
    text = " ".join([
        testcase_to_text(tc)
        for tc in testcases
    ])

    score = 0
    details = {}

    # Positive
    has_positive = any(k in text for k in ["success", "valid"])
    score += 20 if has_positive else 0
    details["positive"] = has_positive

    # Negative
    has_negative = any(k in text for k in ["invalid", "error", "fail"])
    score += 20 if has_negative else 0
    details["negative"] = has_negative

    # Edge
    has_edge = any(k in text for k in ["empty", "limit", "boundary"])
    score += 15 if has_edge else 0
    details["edge"] = has_edge

    # Validation
    has_validation = any(k in text for k in ["required", "format", "validation"])
    score += 15 if has_validation else 0
    details["validation"] = has_validation

    # System
    has_system = any(k in text for k in ["timeout", "concurrent", "rate", "session"])
    score += 10 if has_system else 0
    details["system"] = has_system

    # API
    has_api = any(k in text for k in ["api", "status code"])
    score += 10 if has_api else 0
    details["api"] = has_api

    # Structure
    has_structure = all([
        tc.get("title"),
        tc.get("steps"),
        tc.get("expected")
    ] for tc in testcases)

    score += 10 if has_structure else 0
    details["structure"] = has_structure

    return score, details


# -------------------------
# 🔥 FINAL COVERAGE ENGINE
# -------------------------
def simple_coverage(testcases, requirement):

    # 🔥 Step 1: lightweight scenario extraction
    scenarios = extract_dynamic_scenarios(requirement)

    if not scenarios:
        scenarios = [clean_requirement(requirement)]

    # 🔥 Step 2: semantic coverage
    covered = []
    for sc in scenarios:
        if is_semantically_covered(sc, testcases):
            covered.append(sc)

    total = len(scenarios) if scenarios else 1
    coverage_percent = round((len(covered) / total) * 100, 2)

    # 🔥 Step 3: QA scoring (REAL metric)
    qa_score, qa_details = calculate_qa_score(testcases)

    # 🔥 Final prints (clean)
    print(f"[COVERAGE] {coverage_percent}%")
    print(f"[QA SCORE] {qa_score}/100")

    return {
        "coverage_percent": coverage_percent,
        "total_scenarios": total,
        "covered_scenarios": covered,
        "qa_score": qa_score,
        "qa_details": qa_details
    }
