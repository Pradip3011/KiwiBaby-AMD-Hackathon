from typing import Optional
import logging

from .config import settings
from .utils import try_parse_json
from .memory import retrieve_similar  # 🔥 MEMORY IMPORT

logger = logging.getLogger("ai-testcase-agent.llm")

# Optional provider imports
try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

DEFAULT_GEMINI_MODEL = settings.LLM_MODEL or "gemini-1.5-flash"
DEFAULT_OPENAI_MODEL = settings.LLM_MODEL or "gpt-4o-mini"


# -------------------------
# SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = """
You are an expert QA engineer with 10+ years of experience.

MANDATORY COVERAGE:
- Positive scenarios
- Negative scenarios
- Edge cases
- Validation scenarios

Ensure:
- No duplicate test cases
- Each test covers a unique condition
- Full requirement coverage

Always begin with a short Test Summary (2–4 sentences).
"""


# -------------------------
# PROMPT BUILDER (UNCHANGED)
# -------------------------
def _format_prompt_for(fmt: str, requirement: str) -> str:
    fmt = fmt.lower()

    if fmt == "json":
        return f"""{SYSTEM_PROMPT}

Return ONLY valid JSON. No markdown, no backticks.

STRICT FORMAT:
{{
  "summary": "<summary>",
  "test_cases": [
    {{
      "id": "TC-001",
      "description": "Short title",
      "preconditions": "Preconditions or null",
      "steps": ["Step 1", "Step 2"],
      "expected": "Expected result",
      "type": "Positive | Negative | Edge | Validation"
    }}
  ]
}}

RULES:
- NEVER truncate JSON
- Ensure valid closing braces
- Include all scenario types

Requirement:
{requirement}
"""

    elif fmt == "gherkin":
        return f"""{SYSTEM_PROMPT}

Generate a COMPLETE QA deliverable in Gherkin format for the following requirement.

Requirement:
{requirement}

STRICT GHERKIN RULES:

Use only the following scenario formats.

STANDARD SCENARIO FORMAT:

@<tag1> @<tag2> @<tag3>
Scenario_01: <Scenario Title>
Given <initial context>
And <additional precondition if needed>
When <first user action>
And <additional user action if needed>
Then <expected result>
And <additional expected result if needed>

SCENARIO OUTLINE FORMAT:

@<tag1> @<tag2> @<tag3>
Scenario_Outline_01: <Scenario Title>
Given <initial context>
And <additional precondition if needed>
When <first user action using "<placeholder>">
And <additional user action if needed>
Then <expected result>
And <additional expected result if needed>

Examples:
| column_1 | column_2 | column_3 |

IMPORTANT RULES:

1. Each scenario must be numbered sequentially.
2. Use Scenario_01, Scenario_02, Scenario_03 for normal scenarios.
3. Use Scenario_Outline_01, Scenario_Outline_02 for scenario outlines.
4. Never use plain "Scenario:" without numbering.
5. Tags must appear immediately above the scenario title.
6. Use Given for the initial context.
7. Use And after Given only for additional preconditions.
8. Use When for the first action.
9. Use And after When only for additional actions.
10. Use Then for the first expected result.
11. Use And after Then for any additional expected results (never stack multiple Then keywords sequentially).
12. Do not use numbered steps inside scenarios.
13. Keep steps atomic, clear, and execution-ready.
14. Ensure coverage includes positive, negative, and edge scenarios.
15. If Scenario Outline is used, remove duplicate or redundant example rows.
16. Do not generate excessive scenarios. Keep the output concise and maintainable.
17. Maximum 10 scenarios total.
18. Maximum 2 scenario outlines total.

MANDATORY QA ENHANCEMENTS:

Enhance the QA deliverable with the following:

1. Simplified Requirement Traceability Matrix
   - Provide concise mapping: Requirement -> Scenario IDs

2. Optimize Gherkin Design
   - Use Scenario Outline where applicable
   - Reduce redundancy
   - Improve maintainability

3. Risk-Based Testing View
   - Clearly identify P0 scenarios
   - Highlight critical flows if testing time is limited

4. Test Data Strategy
   - Define data creation
   - Define data management
   - Define cleanup approach
   - Include environment considerations

5. Exit Criteria
   - Define clear pass/fail conditions for release readiness

ADVANCED QA REQUIREMENTS:

1. Add scenario tags directly in Gherkin:
   - @P0 or @P1
   - @Smoke or @Regression
   - Optional domain tags such as @API, @Validation, @BusinessLogic, @EdgeCase, @System

2. Ensure minimal but essential business logic coverage where relevant:
   - account lock
   - session handling
   - authentication validation

3. Add lightweight API validation scenarios where relevant:
   - one success scenario
   - one failure scenario

4. Add at least one system-level edge case where relevant:
   - rate limiting
   - concurrent login
   - session timeout

IMPORTANT CONSTRAINTS:

- Keep output concise, practical, and maintainable.
- Do not over-engineer.
- Do not regenerate an unnecessarily large test suite.
- Focus on execution-ready QA design.
- Balance coverage with simplicity.
- Use consistent error messages and scenario naming.
- Do not include commentary inside scenario steps.
- For API steps, avoid long inline JSON payloads unless necessary for clarity.

REFERENCE EXAMPLE:

Test Summary:
This test suite validates the login feature across positive, negative, and edge scenarios.

Feature: User Login

@P0 @Smoke @Regression
Scenario_01: Successful login with valid credentials
Given I am on the login page
When I enter a valid email address
And I enter a valid password
And I click the Login button
Then I should be redirected to the dashboard
And I should see a welcome message

@P0 @Regression
Scenario_Outline_01: Login attempt with invalid credentials
Given I am on the login page
When I enter "<email>"
And I enter "<password>"
And I click the Login button
Then I should see an error message "<error_message>"
And I should remain on the login page

Examples:
| email                | password       | error_message                    |
| wrong@example.com    | ValidPass123!  | Invalid email or password.       |
| valid@example.com    | WrongPass123!  | Invalid email or password.       |
|                      | ValidPass123!  | Email cannot be empty.           |
| valid@example.com    |                | Password cannot be empty.        |

Requirement:
{requirement}
"""

    elif fmt == "excel":
        return f"""{SYSTEM_PROMPT}

Generate test cases in table format:

Columns:
Test Case ID | Title | Preconditions | Steps | Expected Result | Type

Requirement:
{requirement}
"""

    else:
        return f"""{SYSTEM_PROMPT}

Generate detailed test cases.

Requirement:
{requirement}
"""


# -------------------------
# PROVIDERS
# -------------------------
def _gen_openai(prompt: str):
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK not installed")

    client = OpenAI(api_key=settings.GEMINI_API_KEY)

    resp = client.chat.completions.create(
        model=DEFAULT_OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )

    return resp.choices[0].message.content


def _gen_gemini(prompt: str):
    if genai is None:
        raise RuntimeError("Gemini SDK not installed")

    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)

    # Explicitly set a longer timeout (120 seconds) for complex generations
    resp = model.generate_content(
        prompt,
        request_options={"timeout": 600.0}
    )

    return getattr(resp, "text", str(resp))


# -------------------------
# SAFE GENERATION (NEW)
# -------------------------
def _safe_generate(prompt: str, retries: int = 2):
    for attempt in range(retries):
        try:
            provider = (settings.LLM_PROVIDER or "openai").lower()

            if provider == "gemini":
                return _gen_gemini(prompt)

            return _gen_openai(prompt)

        except Exception:
            logger.exception(f"LLM attempt {attempt+1} failed")

    return ""


# -------------------------
# CORE GENERATION
# -------------------------
def _generate(requirement: str, fmt: str):
    prompt = _format_prompt_for(fmt, requirement)
    return _safe_generate(prompt)


# -------------------------
# CONTROL LAYER (FINAL)
# -------------------------
def _control_gherkin_output(output: str) -> str:
    lines = output.split("\n")

    controlled = []
    scenario_count = 0
    outline_count = 0
    example_rows = 0
    in_examples = False

    for line in lines:

        # Limit normal scenarios
        if line.strip().startswith("Scenario_") and not line.strip().startswith("Scenario_Outline_"):
            if scenario_count >= 10:
                continue
            scenario_count += 1

        # Limit outlines
        if "Scenario_Outline_" in line:
            if outline_count >= 2:
                continue
            outline_count += 1

        # Handle Examples
        if line.strip().startswith("Examples"):
            in_examples = True
            example_rows = 0
            controlled.append(line)
            continue

        # ❌ Remove meta-commentary
        if any(bad in line.lower() for bad in [
            "proposed improvement",
            "revised",
            "here are",
            "suggestion",
            "review",
            "improvement",
            "###"
        ]):
            continue

        if in_examples:
            if "|" in line:
                if example_rows >= 8:
                    continue
                example_rows += 1
            else:
                in_examples = False

        # Remove broken huge lines
        if len(line) > 300:
            continue

        controlled.append(line)

    return "\n".join(controlled)

# -------------------------
# STRUCTURE VALIDATION (NEW)
# -------------------------
def _validate_gherkin_structure(output: str) -> str:
    lines = output.split("\n")

    fixed = []
    scenario_counter = 1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Detect missing scenario BEFORE Given
        if stripped.startswith("Given"):
            prev_line = fixed[-1].strip() if fixed else ""

            if not prev_line.startswith("Scenario_") and not prev_line.startswith("Scenario_Outline_"):
                # Only add if next few lines look like real scenario
                fixed.append(f"Scenario_{scenario_counter:02d}: Inferred scenario")
                scenario_counter += 1

        # Normalize numbering
        if stripped.startswith("Scenario_"):
            parts = stripped.split(":")[0].split("_")
            if len(parts) > 1:
                fixed.append(f"Scenario_{scenario_counter:02d}: {line.split(':',1)[1].strip()}")
                scenario_counter += 1
                continue

        # Remove "Generated scenario" junk
        if "generated scenario" in stripped.lower():
            continue

        # Remove duplicate separators
        if stripped == "---":
            if fixed and fixed[-1].strip() == "---":
                continue

        fixed.append(line)

    return "\n".join(fixed)


# -------------------------
# REVIEW LAYER (FINAL FIXED)
# -------------------------
def _review_output(requirement: str, output: str, fmt: str):
    review_prompt = f"""
You are a senior QA reviewer.

Requirement:
{requirement}

Generated Output:
{output}

Your task:
- Improve ONLY if critical issues exist
- Fix missing edge cases, duplicates, and clarity issues
- COMPLETE any empty sections
- FIX structure to match expected format

EXPECTED OUTPUT STRUCTURE (MANDATORY):
1. Test Summary (2–4 sentences)
2. Feature
3. Scenarios
4. Supporting Sections (STRICT):
   ### 1. Simplified Requirement Traceability Matrix (with table)
   ### 2. Optimized Gherkin Design
   ### 3. Risk-Based Testing View
   ### 4. Test Data Strategy
   ### 5. Exit Criteria

SECTION ENFORCEMENT (STRICT):
- Supporting Sections MUST be present and MUST include ALL of the following EXACT headers:

- DO NOT skip any section
- DO NOT output section content without its header
- DO NOT merge sections
- If any section is missing → you MUST generate it
- Keep output concise, BUT completeness is mandatory over brevity

VALIDATION RULES:
- If "Examples:" appears, the scenario name MUST be "Scenario_Outline_XX" (no exceptions)
- Scenario Outline MUST include a valid Examples table
- Ensure all Scenario IDs referenced exist and match exactly
- Ensure numbering is sequential with no gaps
- Ensure section numbering starts from 1 and is complete
- Ensure consistent error message wording across scenarios
- NEVER use placeholder names like "Generated scenario" or "Inferred scenario"
- If scenario is missing title → fix title based on content
- Scenario titles must always describe the scenario clearly; no generic names allowed
- MANDATORY GHERKIN SYNTAX: Never stack multiple 'Then' keywords sequentially. Use 'And' for subsequent expected results. # <--- ADD THIS LINE

SEMANTIC CONSISTENCY (MANDATORY):
- Ensure Scenario priorities follow QA standards:
    - P0 = core business flow only
    - P1 = validation, edge, system scenarios
- Ensure all Scenario IDs referenced in:
    - Traceability Matrix
    - Risk-Based Testing
    - match actual scenarios exactly
- Ensure Scenario numbering reflects actual order and meaning
- Ensure Scenario Outline naming is consistent wherever Examples are used
- Avoid over-promoting scenarios to P0 unless they are core functionality

SCENARIO ID & NAMING CONSISTENCY (STRICT):
- If a scenario contains "Examples", it MUST be named "Scenario_Outline_XX"
- Scenario Outline numbering must be consistent across:
    - Scenario definition
    - Traceability Matrix
    - Risk-Based Testing section
- All Scenario IDs referenced must exist and match exactly
- Do NOT reference non-existent scenarios
- Do NOT reuse incorrect numbering

- Traceability Matrix must cover ALL major scenario categories:
  Positive, Negative, Validation, API, System

FORMAT RULES:
- DO NOT use markdown code blocks
- DO NOT add explanations or commentary
- DO NOT rewrite everything unnecessarily
- Keep output concise and maintainable

SCENARIO TITLE ENFORCEMENT (MANDATORY):

- Each scenario must appear exactly once with one valid scenario title
- Do NOT duplicate scenario titles
- Do NOT generate placeholder titles such as "Inferred scenario" or "Generated scenario"
- If a scenario title is missing, infer a meaningful title from the scenario content
- Bold markdown formatting must not be used for scenario titles
- Scenario references in supporting sections must match the actual scenario titles exactly

SECTION HEADER ENFORCEMENT (MANDATORY):

- Under "## Supporting Sections", include these exact headers:
    ### 1. Simplified Requirement Traceability Matrix
    ### 2. Optimized Gherkin Design
    ### 3. Risk-Based Testing View
    ### 4. Test Data Strategy
    ### 5. Exit Criteria
- Do NOT output section content without its required header

SECTION ENFORCEMENT (MANDATORY):
- Output MUST include:
    ## Supporting Sections

- Supporting Sections MUST contain EXACTLY:
    ### 1. Simplified Requirement Traceability Matrix (with table)
    ### 2. Optimized Gherkin Design
    ### 3. Risk-Based Testing View
    ### 4. Test Data Strategy
    ### 5. Exit Criteria

- Do NOT skip any section
- Do NOT merge sections
- Do NOT output section content without headers

Return ONLY the final structured output.

If output is already correct:
→ return it as is
"""

    reviewed = _safe_generate(review_prompt)

    # fallback safety
    final_output = reviewed if reviewed and len(reviewed.strip()) > 50 else output

    # 🔥 Apply control ONLY for GHERKIN
    if fmt == "gherkin":
        final_output = _control_gherkin_output(final_output)
        final_output = _validate_gherkin_structure(final_output)

    return final_output
# -------------------------
# STRUCTURED OUTPUT (WITH MEMORY IMPROVED)
# -------------------------
def generate_structured_testcases(requirement: str):

    past = retrieve_similar(requirement)

    context = ""
    if past:
        context = "\n".join(past)

    enhanced_requirement = f"""
Current Requirement:
{requirement}

Reference Past Cases:
{context}

Instructions:
- Use past cases to improve edge coverage
- Do not copy blindly
"""

    raw = _generate(enhanced_requirement, "json")

    if not raw:
        return fallback_testcases(requirement)

    try:
        parsed = try_parse_json(raw)
        testcases = parsed.get("test_cases", [])

        if not isinstance(testcases, list) or not testcases:
            return fallback_testcases(requirement)

        normalized = []
        for i, tc in enumerate(testcases, start=1):
            normalized.append({
                "id": f"TC_{i:03}",
                "title": tc.get("description", "No title"),
                "steps": tc.get("steps", []),
                "expected": tc.get("expected", ""),
                "type": tc.get("type", "General"),
            })

        return normalized

    except Exception:
        logger.warning("JSON parsing failed")
        return fallback_testcases(requirement)


# -------------------------
# FORMATTED OUTPUT (UPGRADED)
# -------------------------
def generate_formatted_output(requirement: str, fmt: str):
    raw = _generate(requirement, fmt)

    if not raw:
        return "No output generated"

    improved = _review_output(requirement, raw, fmt)

    return improved or raw


# -------------------------
# FALLBACK
# -------------------------
def fallback_testcases(requirement: str):
    return [
        {
            "id": "TC_001",
            "title": f"Basic test for: {requirement[:30]}",
            "steps": ["Execute main flow"],
            "expected": "System behaves correctly",
            "type": "Positive",
        }
    ]
