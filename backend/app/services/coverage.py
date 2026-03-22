import re
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

# -------------------------
# Clean requirement
# -------------------------
def clean_requirement(text: str) -> str:
    t = text.lower()

    # remove common story prefixes
    t = re.sub(r"\b(as_a:|i_want:|so_that:)\b", " ", t)

    # remove IDs / codes / special tokens
    t = re.sub(r"\b[a-z]*\d[\w\.-]*\b", " ", t)  # e.g., br8.6-12-b, tc_01...
    t = re.sub(r"[^\w\s]", " ", t)               # punctuation
    t = re.sub(r"\s+", " ", t).strip()

    return t


# -------------------------
# Extract meaningful scenarios (phrases)
# -------------------------
def extract_scenarios(requirement: str):
    t = clean_requirement(requirement)

    # domain seed concepts (helps a lot)
    base = [
        "login", "account", "user", "contact", "contacts",
        "update", "view", "create", "delete",
        "validation", "error", "invalid input", "valid input", "empty input"
    ]

    # extract 1–2 word phrases (not just single noisy tokens)
    words = [w for w in t.split() if len(w) > 3]
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]

    # keep only useful tokens (filter common stop/noise words)
    stop = {"that", "this", "with", "from", "into", "through", "their", "within", "without"}
    filtered = [w for w in words if w not in stop]

    scenarios = set(base + filtered + bigrams)

    return list(scenarios)


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
def is_semantically_covered(scenario, testcases, threshold=0.3):
    scenario_emb = model.encode(scenario, convert_to_tensor=True)

    tc_texts = [testcase_to_text(tc) for tc in testcases]
    tc_embs = model.encode(tc_texts, convert_to_tensor=True)

    scores = util.cos_sim(scenario_emb, tc_embs)
    max_score = scores.max().item()

    # debug
    print(f"[COVERAGE DEBUG] Scenario: {scenario} | Score: {max_score:.3f}")

    return max_score >= threshold


# -------------------------
# Coverage calculation
# -------------------------
def simple_coverage(testcases, requirement):
    scenarios = extract_scenarios(requirement)

    if not testcases:
        return {
            "coverage_percent": 0,
            "covered_scenarios": [],
            "missing_scenarios": scenarios,
            "total_scenarios": len(scenarios)
        }

    covered = []
    for sc in scenarios:
        if is_semantically_covered(sc, testcases):
            covered.append(sc)

    missing = list(set(scenarios) - set(covered))
    total = len(scenarios) if scenarios else 1

    return {
        "coverage_percent": round((len(covered) / total) * 100, 2),
        "covered_scenarios": covered,
        "missing_scenarios": missing,
        "total_scenarios": total
    }
