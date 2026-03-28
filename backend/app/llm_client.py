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
# PROMPT BUILDER
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
{{user_input}}

MANDATORY OUTPUT STRUCTURE:

1. Test Summary

2. Feature: <Feature Name>

3. BDD Scenarios in strict numbered Gherkin format

4. Supporting sections after scenarios:
   - Simplified Requirement Traceability Matrix
   - Optimized Gherkin Design
   - Risk-Based Testing View
   - Test Data Strategy
   - Exit Criteria

STRICT GHERKIN RULES:

Use only the following scenario formats.

STANDARD SCENARIO FORMAT:

@<tag1> @<tag2> @<tag3>
Scenario_01: <Scenario Title>
Given <initial context>


When <first user action>
And <additional user action if needed>

Then <expected result>
Then <additional expected result if needed>

SCENARIO OUTLINE FORMAT:

@<tag1> @<tag2> @<tag3>
Scenario_Outline_01: <Scenario Title>
Given <initial context>
And <additional precondition if needed>

When <first user action using "<placeholder>">
And <additional user action if needed>

Then <expected result>
Then <additional expected result if needed>

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
10. Use Then for every expected result.
11. Never use And after Then.
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
Then I should see a welcome message

@P0 @Regression
Scenario_Outline_01: Login attempt with invalid credentials
Given I am on the login page
When I enter "<email>"
And I enter "<password>"
And I click the Login button
Then I should see an error message "<error_message>"
Then I should remain on the login page

Examples:
| email                | password       | error_message                    |
| wrong@example.com    | ValidPass123!  | Invalid email or password.       |
| valid@example.com    | WrongPass123!  | Invalid email or password.       |
|                     | ValidPass123!  | Email cannot be empty.           |
| valid@example.com    |               | Password cannot be empty.        |


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

    client = OpenAI(api_key=settings.LLM_API_KEY)

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

    genai.configure(api_key=settings.LLM_API_KEY)

    model = genai.GenerativeModel(DEFAULT_GEMINI_MODEL)

    resp = model.generate_content(prompt)

    return getattr(resp, "text", str(resp))


def _generate(requirement: str, fmt: str):
    prompt = _format_prompt_for(fmt, requirement)

    provider = (settings.LLM_PROVIDER or "openai").lower()

    try:
        if provider == "gemini":
            return _gen_gemini(prompt)

        return _gen_openai(prompt)

    except Exception:
        logger.exception("LLM generation failed")
        return ""


# -------------------------
# STRUCTURED OUTPUT (WITH MEMORY)
# -------------------------
def generate_structured_testcases(requirement: str):

    # 🔥 MEMORY RETRIEVAL
    past = retrieve_similar(requirement)

    context = ""
    if past:
        print("🔥 MEMORY USED:", past)  # demo proof
        context = "\n\nSimilar past requirements:\n" + "\n".join(past)

    enhanced_requirement = requirement + context

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
# FORMATTED OUTPUT
# -------------------------
def generate_formatted_output(requirement: str, fmt: str):
    raw = _generate(requirement, fmt)
    return raw if raw else "No output generated"


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
