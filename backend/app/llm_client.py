from typing import Optional
import logging
import time

from .config import settings
from .utils import try_parse_json
from .memory import retrieve_similar  # 🔥 MEMORY IMPORT

# Third-party stability libraries
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception,
)

logger = logging.getLogger("ai-testcase-agent.llm")

# -------------------------
# COMPATIBLE PROVIDER IMPORTS & INITIALIZATION
# -------------------------
try:
    from google import genai  # Modern unified Google GenAI SDK framework
    from google.genai.errors import ServerError, ClientError  
except Exception:
    genai = None
    ServerError = Exception
    ClientError = Exception

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

DEFAULT_GEMINI_MODEL = settings.LLM_MODEL or "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = settings.LLM_MODEL or "gpt-4o-mini"

# Initialize global client singletons safely to reuse connection pools
openai_client = None
gemini_client = None

if OpenAI and getattr(settings, "OPENAI_API_KEY", None):
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

if genai and getattr(settings, "GEMINI_API_KEY", None):
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)


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
      "title": "Short title",  # 🔥 FIXED: Changed from "description" to "title" to align with validator
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
# RESILIENT ENGINE PROVIDERS
# -------------------------
def _gen_openai(prompt: str) -> str:
    if openai_client is None:
        raise RuntimeError("OpenAI SDK or API Key not initialized properly")

    resp = openai_client.chat.completions.create(
        model=DEFAULT_OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1500,
    )
    return resp.choices[0].message.content or ""


def _is_retryable_gemini_exception(exception: Exception) -> bool:
    """Predicate function filtering for structural ServerErrors (503) and Client Rate-Limits (429)."""
    exc_str = str(exception)
    if ServerError and isinstance(exception, ServerError):
        return True
    if ClientError and isinstance(exception, ClientError):
        status_code = getattr(exception, "status_code", None)
        if status_code == 429 or "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
            return True
    if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "503" in exc_str:
        return True
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=15, max=60),
    retry=retry_if_exception(_is_retryable_gemini_exception),
    before_sleep=lambda retry_state: logger.warning(
        f"Gemini retry attempt {retry_state.attempt_number}"
    ),
)
def _gen_gemini(prompt: str) -> str:
    if gemini_client is None:
        raise RuntimeError("Gemini SDK or API Key not initialized properly")

    response = gemini_client.models.generate_content(
        model=DEFAULT_GEMINI_MODEL,
        contents=prompt,
    )
    return response.text or ""


# -------------------------
# SAFE GENERATION WRAPPER
# -------------------------
def _safe_generate(prompt: str) -> str:
    """Executes the request via Gemini with automatic, clean failover to OpenAI if configured."""
    try:
        if gemini_client:
            try:
                return _gen_gemini(prompt)
            except Exception as gemini_err:
                logger.warning(f"Gemini primary route failed. Error: {gemini_err}")
                if openai_client:
                    logger.info("Switching to OpenAI backup route...")
                    return _gen_openai(prompt)
                raise gemini_err

        if openai_client:
            return _gen_openai(prompt)

        raise RuntimeError(
            "No LLM provider configured. Configure GEMINI_API_KEY or OPENAI_API_KEY."
        )

    except Exception as e:
        logger.exception(f"Generation failed on both channels: {e}")
        return ""


# -------------------------
# STRUCTURED TESTCASE GENERATION
# -------------------------
def generate_structured_testcases(
    requirement: str,
    output_format: str = "json"
):
    prompt = _format_prompt_for(output_format, requirement)
    response = _safe_generate(prompt)

    if not response:
        return []

    # If the model returns JSON text
    parsed = try_parse_json(response)

    if isinstance(parsed, dict):
        return parsed.get("test_cases", [])

    if isinstance(parsed, list):
        return parsed

    return []


# -------------------------
# GENERIC FORMATTER
# -------------------------
def generate_formatted_output(
    requirement: str,
    output_format: str = "gherkin"
):
    prompt = _format_prompt_for(output_format, requirement)
    response = _safe_generate(prompt)

    if not response:
        return f"Failed to generate {output_format} output."

    return response