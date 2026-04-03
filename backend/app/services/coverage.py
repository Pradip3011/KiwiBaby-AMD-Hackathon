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
# Clean scenarios
# -------------------------
def clean_scenarios(scenarios):
    cleaned = []
    for sc in scenarios:
        sc = sc.strip()
        if not sc:
            continue
        if "here are" in sc.lower():
            continue
        if sc.startswith("**"):
            continue
        if len(sc) < 10:
            continue
        cleaned.append(sc)
    return list(set(cleaned))


# -------------------------
# Filter missing scenarios
# -------------------------
def filter_missing_scenarios(missing):
    filtered = []
    for sc in missing:
        if len(sc) < 10:
            continue
        if "scenario" in sc.lower() and len(sc.split()) < 3:
            continue
        filtered.append(sc)
    return filtered


# -------------------------
# Dynamic scenario extraction
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
"""
    response = _safe_generate(prompt)
    if not response:
        return []
    lines = [l.strip("- ").strip() for l in response.split("\n") if l.strip()]
    return list(set(lines))


# -------------------------
# 🔥 FIXED RULE EXTRACTION (QUALITY IMPROVED)
# -------------------------
def extract_dynamic_rules(requirement: str):
    prompt = f"""
You are a senior QA architect.

Extract SPECIFIC, TESTABLE validation rules.

Requirement:
{requirement}

STRICT:
- Must be concrete and testable
- Avoid generic statements
- Focus on:
  - input validation
  - business rules
  - system behavior
  - failure conditions

Return:
- short, precise rules
- max 6
"""
    response = _safe_generate(prompt)

    if not response:
        return []

    rules = [r.strip("- ").strip() for r in response.split("\n") if r.strip()]

    # Remove weak/generic rules
    cleaned = []
    for r in rules:
        if len(r.split()) < 4:
            continue
        if any(bad in r.lower() for bad in ["ensure", "should work", "properly"]):
            continue
        cleaned.append(r)

    return list(set(cleaned))


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
    scenario_emb = model.encode(scenario, convert_to_tensor=True, show_progress_bar=False)
    tc_texts = [testcase_to_text(tc) for tc in testcases]
    tc_embs = model.encode(tc_texts, convert_to_tensor=True, show_progress_bar=False)
    scores = util.cos_sim(scenario_emb, tc_embs)
    return scores.max().item() >= threshold


# -------------------------
# QA scoring
# -------------------------
def calculate_qa_score(testcases):
    text = " ".join([testcase_to_text(tc) for tc in testcases])

    score = 0
    details = {}

    checks = {
        "positive": ["success", "valid"],
        "negative": ["invalid", "error", "fail"],
        "edge": ["empty", "limit", "boundary"],
        "validation": ["required", "format", "validation"],
        "system": ["timeout", "concurrent", "rate", "session"],
        "api": ["api", "status code"]
    }

    weights = {
        "positive": 20,
        "negative": 20,
        "edge": 15,
        "validation": 15,
        "system": 10,
        "api": 10
    }

    for key, keywords in checks.items():
        present = any(k in text for k in keywords)
        details[key] = present
        if present:
            score += weights[key]

    structure = all(tc.get("title") and tc.get("steps") and tc.get("expected") for tc in testcases)
    details["structure"] = structure
    if structure:
        score += 10

    return score, details


# -------------------------
# 🔥 SEMANTIC RULE VALIDATION (ROOT FIX)
# -------------------------
def dynamic_rule_validation(testcases, requirement):
    rules = extract_dynamic_rules(requirement)

    if not rules:
        return 0, {}

    tc_texts = [testcase_to_text(tc) for tc in testcases]
    tc_embs = model.encode(tc_texts, convert_to_tensor=True, show_progress_bar=False)

    passed = 0
    results = {}

    for rule in rules:
        rule_emb = model.encode(rule, convert_to_tensor=True, show_progress_bar=False)
        scores = util.cos_sim(rule_emb, tc_embs)
        max_score = scores.max().item()

        match = max_score >= 0.4
        results[rule] = match

        if match:
            passed += 1

    score = round((passed / len(rules)) * 100, 2)
    return score, results


# -------------------------
# Final score
# -------------------------
def calculate_final_score(coverage_percent, qa_score, rule_score):
    final_score = round(
        (qa_score * 0.5) +
        (rule_score * 0.3) +
        (coverage_percent * 0.2),
        2
    )

    if final_score >= 90:
        confidence = "HIGH"
    elif final_score >= 70:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return final_score, confidence


# -------------------------
# Decision engine
# -------------------------
def make_decision(final_score, confidence):
    if confidence == "HIGH" and final_score >= 90:
        return "AUTO_APPROVED"
    elif confidence == "MEDIUM":
        return "NEEDS_REVIEW"
    else:
        return "REGENERATE"


# -------------------------
# FINAL ENGINE
# -------------------------
def simple_coverage(testcases, requirement):

    scenarios = clean_scenarios(extract_dynamic_scenarios(requirement))
    if not scenarios:
        scenarios = [clean_requirement(requirement)]

    covered = [sc for sc in scenarios if is_semantically_covered(sc, testcases)]
    covered = clean_scenarios(covered)

    missing = filter_missing_scenarios(list(set(scenarios) - set(covered)))

    total = len(scenarios)
    covered_count = len(covered)
    missing_count = len(missing)

    coverage_percent = round((covered_count / total) * 100, 2)

    qa_score, qa_details = calculate_qa_score(testcases)
    rule_score, rule_details = dynamic_rule_validation(testcases, requirement)

    final_score, confidence = calculate_final_score(
        coverage_percent,
        qa_score,
        rule_score
    )

    decision = make_decision(final_score, confidence)

    print("\n===== FINAL QA ANALYSIS =====")
    print(f"Extracted: {total} | Covered: {covered_count} | Missing: {missing_count}")
    print(f"Coverage: {coverage_percent}% | QA: {qa_score} | Rule: {rule_score}")
    print(f"Final: {final_score} | Confidence: {confidence} | Decision: {decision}")

    if missing:
        print("\nMissing:")
        for m in missing[:5]:
            print(f"- {m}")

    print("============================\n")

    return {
        "coverage_percent": coverage_percent,
        "total_scenarios": total,
        "covered_count": covered_count,
        "missing_count": missing_count,
        "covered_scenarios": covered,
        "missing_scenarios": missing,
        "qa_score": qa_score,
        "qa_details": qa_details,
        "rule_score": rule_score,
        "rule_details": rule_details,
        "final_score": final_score,
        "confidence": confidence,
        "decision": decision
    }
