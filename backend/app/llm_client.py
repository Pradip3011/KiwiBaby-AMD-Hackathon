# backend/app/llm_client.py
"""
Multi-provider LLM client.

Exports:
    generate_from_requirement(requirement: str, format: str = "text", model_name: str | None = None, temperature: float = 0.2) -> dict

Behavior:
- Routes to OpenAI if settings.LLM_PROVIDER == "openai"
- Routes to Gemini if settings.LLM_PROVIDER == "gemini"
- Keeps retry / continuation logic for truncated JSON
- Returns consistent shape:
    {
        "format": "...",
        "output": {"raw": "..."},
        "meta": {...}
    }
"""
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger("ai-testcase-agent.llm")

# Optional provider imports
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

DEFAULT_GEMINI_MODEL = settings.LLM_MODEL or "gemini-1.5-flash"
DEFAULT_OPENAI_MODEL = settings.LLM_MODEL or "gpt-4o-mini"


SYSTEM_PROMPT = """
You are an expert QA engineer with 10+ years of experience.

Your task is to generate test cases and summaries based on feature requirements.

Always begin with a brief Test Summary (2–4 sentences) describing the feature and testing scope.

Respond in the specified output format: JSON, Gherkin, Excel, or plain text.

Avoid unsafe, ambiguous, or imperative phrasing. Keep steps clear, logical, and test-ready.
"""


def _format_prompt_for(fmt: str, requirement: str) -> str:
    fmt = fmt.lower()

    if fmt == "json":
        format_prompt = """
Return ONLY valid JSON. No markdown, no backticks, no commentary.

STRICT FORMAT:
{
  "summary": "<2–4 sentence summary>",
  "test_cases": [
    {
      "id": "TC-001",
      "description": "Short test title",
      "preconditions": "Preconditions or null",
      "steps": ["Step 1", "Step 2"],
      "expected": "Expected result",
      "type": "Positive | Negative | Edge | Validation"
    }
  ]
}

RULES:
- Output JSON ONLY.
- NEVER stop mid-sentence.
- NEVER stop until JSON is fully closed with the final '}'.
- If unsure, KEEP GENERATING until JSON is complete.
- Ensure fully valid JSON.
"""
    elif fmt == "gherkin":
        format_prompt = """
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
"""
    elif fmt == "excel":
        format_prompt = """
Generate a Test Summary and a table suitable for Excel.

Columns:
Test Case ID | Title | Precondition | Steps | Expected Result | Type
"""
    else:
        format_prompt = """
Generate a Test Summary and detailed test cases:
- Positive
- Negative
- Edge
- Validation
"""
        if len(requirement.split()) < 8:
            requirement += " The system should validate inputs and return appropriate success or error messages."

    return f"{SYSTEM_PROMPT}\n{format_prompt}\nRequirement:\n{requirement}"


def _extract_gemini_text(resp) -> str:
    try:
        if hasattr(resp, "candidates") and resp.candidates:
            cand = resp.candidates[0]
            if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                parts = cand.content.parts
                if parts and hasattr(parts[0], "text"):
                    return parts[0].text
        if getattr(resp, "text", None):
            return resp.text
        return str(resp)
    except Exception:
        logger.exception("Error extracting text from Gemini response")
        return ""


def _extract_openai_text(resp) -> str:
    try:
        if resp is None:
            return ""

        choices = getattr(resp, "choices", None)
        if not choices:
            return getattr(resp, "text", "") or str(resp)

        first = choices[0]

        if hasattr(first, "message") and getattr(first.message, "content", None):
            content = first.message.content

            # Usually content is a string
            if isinstance(content, str):
                return content

            # Handle list-based content parts if returned
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    elif hasattr(item, "text"):
                        parts.append(getattr(item, "text", ""))
                return "".join(parts)

        if getattr(first, "text", None):
            return first.text

        return str(first)
    except Exception:
        logger.exception("Error extracting text from OpenAI response")
        return ""


def _gen_gemini(
    requirement: str,
    format: str = "text",
    model_name: Optional[str] = None,
    temperature: float = 0.2,
) -> dict:
    if genai is None:
        raise RuntimeError(
            "google.generativeai not installed. Install google-generativeai or switch provider to openai."
        )

    api_key = settings.LLM_API_KEY
    if not api_key:
        raise RuntimeError(
            "Gemini API key not set. Set GEMINI_API_KEY or LLM_API_KEY in your environment."
        )

    genai.configure(api_key=api_key)

    model_name = model_name or settings.LLM_MODEL or DEFAULT_GEMINI_MODEL
    fmt = format.lower()
    prompt = _format_prompt_for(fmt, requirement)

    try:
        model = genai.GenerativeModel(model_name=model_name)
    except Exception:
        model = None

    def call_model(temp: float):
        if model is not None:
            return model.generate_content(
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                generation_config={
                    "temperature": temp,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": int(settings.MAX_TOKENS or 4096),
                },
            )

        return genai.text.generate(
            model=model_name,
            prompt=prompt,
            max_output_tokens=int(settings.MAX_TOKENS or 4096),
            temperature=temp,
        )

    response = call_model(temperature)
    output_text = _extract_gemini_text(response)

    if not output_text:
        logger.warning("Empty Gemini response. Retrying...")
        response = call_model(0.6)
        output_text = _extract_gemini_text(response)

    if not output_text:
        return {
            "format": format,
            "output": {
                "raw": "Model returned no output. Try expanding the requirement or switching format."
            },
            "meta": {"provider": "gemini", "model": model_name},
        }

    if fmt == "json":
        trimmed = output_text.strip()
        if not trimmed.endswith("}"):
            logger.warning("Gemini JSON appears truncated. Requesting continuation...")
            continuation_prompt = f"""
The JSON below was cut off before completion.
Continue EXACTLY where it stopped and return ONLY the missing JSON text.
Do NOT repeat any existing content.

Existing JSON:
{output_text}

Continue from the next character:
"""
            try:
                if model is not None:
                    continuation = model.generate_content(
                        contents=[{"role": "user", "parts": [{"text": continuation_prompt}]}],
                        generation_config={
                            "temperature": 0.35,
                            "top_p": 1,
                            "top_k": 1,
                            "max_output_tokens": int(settings.MAX_TOKENS or 4096),
                        },
                    )
                else:
                    continuation = genai.text.generate(
                        model=model_name,
                        prompt=continuation_prompt,
                        max_output_tokens=int(settings.MAX_TOKENS or 4096),
                        temperature=0.35,
                    )

                more = _extract_gemini_text(continuation)
                if more:
                    output_text += more
            except Exception:
                logger.exception("Gemini continuation generation failed")

    return {
        "format": format,
        "output": {"raw": output_text},
        "meta": {"provider": "gemini", "model": model_name},
    }


def _gen_openai(
    requirement: str,
    format: str = "text",
    model_name: Optional[str] = None,
    temperature: float = 0.2,
) -> dict:
    if OpenAI is None:
        raise RuntimeError(
            "OpenAI SDK not installed. Install openai package or switch provider to gemini."
        )

    api_key = settings.LLM_API_KEY
    if not api_key:
        raise RuntimeError(
            "OpenAI API key not set. Set OPENAI_API_KEY or LLM_API_KEY in your environment."
        )

    model_name = model_name or settings.LLM_MODEL or DEFAULT_OPENAI_MODEL
    client = OpenAI(api_key=api_key)

    fmt = format.lower()
    prompt = _format_prompt_for(fmt, requirement)

    def call_openai(temp: float):
        return client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful QA test case generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=temp,
            max_tokens=min(int(settings.MAX_TOKENS or 1500), 1500),
        )

    try:
        resp = call_openai(temperature)
    except Exception:
        logger.exception("OpenAI generate failed on first attempt; retrying...")
        try:
            resp = call_openai(min(0.6, max(temperature, 0.6)))
        except Exception:
            logger.exception("OpenAI retry failed")
            return {
                "format": format,
                "output": {"raw": "OpenAI provider call failed. See server logs."},
                "meta": {"provider": "openai", "model": model_name},
            }

    output_text = _extract_openai_text(resp)

    if not output_text:
        logger.warning("OpenAI returned empty content")
        return {
            "format": format,
            "output": {
                "raw": "OpenAI returned no output. Try expanding the requirement or switching format."
            },
            "meta": {"provider": "openai", "model": model_name},
        }

    if fmt == "json":
        trimmed = output_text.strip()
        if not trimmed.endswith("}"):
            logger.warning("OpenAI JSON appears truncated. Requesting continuation...")
            continuation_prompt = f"""
The JSON below was cut off before completion.
Continue EXACTLY where it stopped and return ONLY the missing JSON text.
Do NOT repeat any existing content.

Existing JSON:
{output_text}

Continue from the next character:
"""
            try:
                cont_resp = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful QA test case generator."},
                        {"role": "user", "content": continuation_prompt},
                    ],
                    temperature=0.35,
                    max_tokens=min(int(settings.MAX_TOKENS or 1500), 1500),
                )
                more = _extract_openai_text(cont_resp)
                if more:
                    output_text += more
            except Exception:
                logger.exception("OpenAI continuation attempt failed")

    return {
        "format": format,
        "output": {"raw": output_text},
        "meta": {"provider": "openai", "model": model_name},
    }


def generate_from_requirement(
    requirement: str,
    format: str = "text",
    model_name: Optional[str] = None,
    temperature: float = 0.2,
) -> dict:
    """
    Public entrypoint.
    Keep this synchronous so existing FastAPI code can call it via asyncio.to_thread().
    """
    provider = (settings.LLM_PROVIDER or "openai").strip().lower()

    try:
        if provider == "openai":
            return _gen_openai(
                requirement,
                format=format,
                model_name=model_name,
                temperature=temperature,
            )

        if provider == "gemini":
            return _gen_gemini(
                requirement,
                format=format,
                model_name=model_name,
                temperature=temperature,
            )

        raise ValueError(f"Unsupported LLM provider: {provider}")

    except Exception as e:
        logger.exception("generate_from_requirement failed: %s", e)
        return {
            "format": format,
            "output": {"raw": f"LLM generation failed: {str(e)}. See server logs."},
            "meta": {"provider": provider, "error": str(e)},
        }
