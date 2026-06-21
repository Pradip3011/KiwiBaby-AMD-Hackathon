import re
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer, util

# 🔥 ROOT FIX: Import the integrated layout architecture to eliminate the circular dependency loop
from ..llm_client import generate_formatted_output

# Pre-load embedding model globally for fast memory access
model = SentenceTransformer('all-MiniLM-L6-v2')


# -------------------------
# Defensive Input Guard
# -------------------------
def normalize_testcases(testcases: Any) -> List[Dict[str, Any]]:
    """
    Guarantees that testcases are returned as a flat list of dictionaries,
    preventing runtime attribute errors if upstream types mutate.
    """
    if isinstance(testcases, dict):
        # Look for typical nested list keys from smart LLM schemas
        for key in ["test_cases", "testcases", "cases", "data"]:
            if isinstance(testcases.get(key), list):
                return testcases[key]
        return [testcases]
    
    if isinstance(testcases, list):
        return [tc for tc in testcases if isinstance(tc, dict)]
        
    return []


# -------------------------
# Clean requirement
# -------------------------
def clean_requirement(text: str) -> str:
    if not text:
        return ""
    t = text.lower()
    t = re.sub(r"\b(as_a:|i_want:|so_that:)\b", " ", t)
    t = re.sub(r"\b[a-z]*\d[\w\.-]*\b", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


# -------------------------
# Clean scenarios
# -------------------------
def clean_scenarios(scenarios: List[str]) -> List[str]:
    if not scenarios:
        return []
    cleaned = []
    for sc in scenarios:
        if not sc or not isinstance(sc, str):
            continue
        sc = sc.strip()
        # Strip trailing/leading markdown bullet artifacts
        sc = re.sub(r"^([\s\-\*\•]|\d+\.)+", "", sc).strip()
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
def filter_missing_scenarios(missing: List[str]) -> List[str]:
    filtered = []
    for sc in missing:
        if len(sc) < 10:
            continue
        if "scenario" in sc.lower() and len(sc.split()) < 3:
            continue
        filtered.append(sc)
    return filtered


# -------------------------
# Dynamic scenario extraction (HARDENED AGAINST CONVERSATIONAL FLUFF)
# -------------------------
def extract_dynamic_scenarios(requirement: str) -> List[str]:
    prompt = f"""
You are a QA engineer.

Extract ONLY realistic test scenarios.

Requirement:
{requirement}

Return:
- short phrases
- practical QA scenarios only
"""
    response = generate_formatted_output(prompt, output_format="text")
    if not response:
        return []
        
    lines = [l.strip() for l in response.split("\n") if l.strip()]
    cleaned = []
    
    for l in lines:
        l = re.sub(r"^([\s\-\*\•]|\d+\.)+", "", l).strip()
        if len(l.split()) < 3:
            continue
            
        if any(filler in l.lower() for filler in [
            "here are", "practical qa", "test scenarios", 
            "based on the", "the following", "sure, here", 
            "realistic test", "scenario analysis"
        ]):
            continue
            
        cleaned.append(l)
        
    return list(set(cleaned))


# -------------------------
# FIXED RULE EXTRACTION (QUALITY IMPROVED)
# -------------------------
def extract_dynamic_rules(requirement: str) -> List[str]:
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
    response = generate_formatted_output(prompt, output_format="text")
    if not response:
        return []

    rules = [r.strip("- ").strip() for r in response.split("\n") if r.strip()]
    cleaned = []
    
    for r in rules:
        r = re.sub(r"^([\s\-\*\•]|\d+\.)+", "", r).strip()
        if len(r.split()) < 4:
            continue
        if any(bad in r.lower() for bad in ["ensure", "should work", "properly"]):
            continue
        if any(filler in r.lower() for filler in [
            "here are", "specific, testable", "validation rules", 
            "based on the", "the following are"
        ]):
            continue
            
        cleaned.append(r)

    return list(set(cleaned))


# -------------------------
# Convert testcase → text
# -------------------------
def testcase_to_text(tc: Dict[str, Any]) -> str:
    if not isinstance(tc, dict):
        return ""
    steps = tc.get("steps", [])
    steps_str = " ".join(steps) if isinstance(steps, list) else str(steps)
    return " ".join([
        str(tc.get("title", "")),
        steps_str,
        str(tc.get("expected", "")),
        str(tc.get("type", ""))
    ]).lower()


# -------------------------
# Semantic coverage
# -------------------------
def is_semantically_covered(scenario: str, tc_texts: List[str], tc_embs, threshold=0.4) -> bool:
    if not tc_texts or tc_embs is None or len(tc_embs) == 0:
        return False
    scenario_emb = model.encode(scenario, convert_to_tensor=True, show_progress_bar=False)
    scores = util.cos_sim(scenario_emb, tc_embs)
    return scores.max().item() >= threshold


# -------------------------
# QA scoring
# -------------------------
def calculate_qa_score(testcases: List[Dict[str, Any]]) -> Tuple[int, Dict[str, bool]]:
    if not testcases:
        return 0, {"structure": False}
        
    text = " ".join([testcase_to_text(tc) for tc in testcases])
    score = 0
    details = {}

    checks = {
        "positive": ["success", "valid", "positive", "happy path"],
        "negative": ["invalid", "error", "fail", "negative"],
        "edge": ["empty", "limit", "boundary", "edge", "edgecase"],
        "validation": ["required", "format", "validation", "businesslogic"],
        "system": ["timeout", "concurrent", "rate", "session", "system"],
        "api": ["api", "status code", "endpoint"]
    }

    weights = {
        "positive": 20, "negative": 20, "edge": 15, 
        "validation": 15, "system": 10, "api": 10
    }

    for key, keywords in checks.items():
        present = any(k in text for k in keywords)
        details[key] = present
        if present:
            score += weights[key]

    structure = all(
        isinstance(tc, dict) and tc.get("title") and tc.get("steps") and tc.get("expected") 
        for tc in testcases
    )
    details["structure"] = structure
    if structure:
        score += 10

    return score, details


# -------------------------
# SEMANTIC RULE VALIDATION
# -------------------------
def dynamic_rule_validation(testcases: List[Dict[str, Any]], requirement: str, tc_texts: List[str], tc_embs) -> Tuple[float, Dict[str, bool]]:
    rules = extract_dynamic_rules(requirement)
    if not rules or not testcases or tc_embs is None or len(tc_embs) == 0:
        return 0.0, {}

    passed = 0
    results = {}

    # Batch encode all extracted rules simultaneously for high execution velocity
    rule_embs = model.encode(rules, convert_to_tensor=True, show_progress_bar=False)
    similarity_matrix = util.cos_sim(rule_embs, tc_embs)

    for idx, rule in enumerate(rules):
        max_score = similarity_matrix[idx].max().item()
        match = max_score >= 0.4
        results[rule] = match
        if match:
            passed += 1

    score = round((passed / len(rules)) * 100, 2) if rules else 0.0
    return score, results


# -------------------------
# Final score calculation
# -------------------------
def calculate_final_score(coverage_percent: float, qa_score: int, rule_score: float) -> Tuple[float, str]:
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
def make_decision(final_score: float, confidence: str) -> str:
    if confidence == "HIGH" and final_score >= 90:
        return "AUTO_APPROVED"
    elif confidence == "MEDIUM":
        return "NEEDS_REVIEW"
    else:
        return "REGENERATE"


# -------------------------
# FINAL ENGINE (BULLETPROOF WRAPPER)
# -------------------------
def simple_coverage(testcases: Any, requirement: str) -> Dict[str, Any]:
    # 🛡️ Step 1: Force type safety at the gateway boundary
    safe_testcases = normalize_testcases(testcases)
    
    # Pre-calculate testcase text mapping and embeddings once to optimize loops
    tc_texts = [testcase_to_text(tc) for tc in safe_testcases]
    if tc_texts:
        tc_embs = model.encode(tc_texts, convert_to_tensor=True, show_progress_bar=False)
    else:
        tc_embs = None

    # Step 2: Extract baseline evaluation matrix
    scenarios = clean_scenarios(extract_dynamic_scenarios(requirement))
    if not scenarios:
        scenarios = [clean_requirement(requirement)]

    # Step 3: Compute Semantic Matching Matrices
    covered = [sc for sc in scenarios if is_semantically_covered(sc, tc_texts, tc_embs)]
    covered = clean_scenarios(covered)

    missing = filter_missing_scenarios(list(set(scenarios) - set(covered)))

    total = len(scenarios)
    covered_count = len(covered)
    missing_count = len(missing)

    coverage_percent = round((covered_count / total) * 100, 2) if total > 0 else 0.0

    # Step 4: Run scoring components using optimized pre-computed states
    qa_score, qa_details = calculate_qa_score(safe_testcases)
    rule_score, rule_details = dynamic_rule_validation(safe_testcases, requirement, tc_texts, tc_embs)

    final_score, confidence = calculate_final_score(
        coverage_percent,
        qa_score,
        rule_score
    )

    decision = make_decision(final_score, confidence)

    # Telemetry logging console block
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