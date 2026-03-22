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

Generate a Test Summary followed by BDD-style test cases in Gherkin format.

STRICT GHERKIN RULES:

Each scenario MUST follow this structure:

Feature: <Feature Name>

Scenario_01: <Scenario Title>
Given <initial context>

When <first user action>
And <additional user actions if needed>

Then <expected result>
Then <additional expected results if needed>

IMPORTANT RULES:

1. Each scenario must be numbered sequentially.
2. Use Scenario_01, Scenario_02, Scenario_03 ... etc.
3. Do NOT use plain "Scenario:" without numbering.
4. Use **When** for the first action.
5. Use **And** only for additional actions after When.
6. Use **Then** for every expected result.
7. NEVER use **And** after Then.
8. Do NOT use numbered steps inside scenarios.
9. Ensure coverage includes positive, negative, and edge scenarios.

Example:

Feature: User Login

Scenario_01: Successful login with valid credentials
Given I am on the login page
When I enter a valid email address
And I enter a valid password
And I click the Login button
Then I should be redirected to the dashboard
Then I should see a welcome message

Scenario_02: Login attempt with incorrect password
Given I am on the login page
When I enter a valid email address
And I enter an incorrect password
And I click the Login button
Then I should see an error message
Then I should remain on the login page


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
