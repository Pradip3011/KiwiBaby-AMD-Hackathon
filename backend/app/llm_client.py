import google.generativeai as genai
from .config import settings

# Configure Gemini globally
genai.configure(api_key=settings.LLM_API_KEY)

SYSTEM_PROMPT = """
You are an expert QA engineer with 10+ years of experience.

Your task is to generate test cases and summaries based on feature requirements.

Always begin with a brief Test Summary (2–4 sentences) describing the feature and testing scope.

Respond in the specified output format: JSON, Gherkin, Excel, or plain text.

Avoid unsafe, ambiguous, or imperative phrasing. Keep steps clear, logical, and test-ready.
"""

def generate_from_requirement(requirement: str, format: str = "text", model_name: str = None, temperature: float = 0.2):

    # IMPORTANT: create a fresh model per request (fixes empty-output bug)
    model = genai.GenerativeModel(model_name=settings.LLM_MODEL)

    fmt = format.lower()

    # ------------------------------
    # FORMAT-SPECIFIC PROMPTS
    # ------------------------------
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
        temperature = 0.20

    elif fmt == "gherkin":
        format_prompt = """
Generate a Test Summary followed by BDD-style test cases in Gherkin format.

Each scenario MUST follow:
Feature: <short name>
Scenario: <title>
Given <context>
When <action>
Then <outcome>

Include positive, negative, edge, and validation cases.
"""
        temperature = 0.4

    elif fmt == "excel":
        format_prompt = """
Generate a Test Summary and a table suitable for Excel:

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

    # ------------------------------
    # FINAL PROMPT
    # ------------------------------
    prompt = f"{SYSTEM_PROMPT}\n{format_prompt}\nRequirement:\n{requirement}"

    # ------------------------------
    # MODEL CALL FUNCTION
    # ------------------------------
    def call_model(temp: float):
        return model.generate_content(
            contents=[
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            generation_config={
                "temperature": temp,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 4096,   # 🔥 Prevent truncation
            }
        )

    # ------------------------------
    # FIRST ATTEMPT
    # ------------------------------
    response = call_model(temperature)

    # Retry if empty
    if not response.candidates or not response.candidates[0].content.parts:
        print("⚠️ Empty Gemini response. Retrying...")
        response = call_model(0.6)

    # If still no output → return failure
    if not response.candidates or not response.candidates[0].content.parts:
        return {
            "format": format,
            "output": {
                "raw": "⚠️ Model returned no output. Try expanding the requirement or switching format."
            }
        }

    # ------------------------------
    # MAIN TEXT OUTPUT
    # ------------------------------
    output_text = response.candidates[0].content.parts[0].text

    # ------------------------------
    # TRUNCATION DETECTION (JSON ONLY)
    # ------------------------------
    if fmt == "json":
        trimmed = output_text.strip()

        # If JSON does NOT end with '}'
        if not trimmed.endswith("}"):
            print("⚠️ JSON appears truncated. Requesting continuation...")

            continuation_prompt = f"""
The JSON below was cut off before completion.
Continue EXACTLY where it stopped and return ONLY the missing JSON text.
Do NOT repeat any existing content.

Existing JSON:
{output_text}

Continue from the next character:
"""

            continuation = model.generate_content(
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": continuation_prompt}]
                    }
                ],
                generation_config={
                    "temperature": 0.35,
                    "top_p": 1,
                    "top_k": 1,
                    "max_output_tokens": 4096
                }
            )

            if continuation.candidates and continuation.candidates[0].content.parts:
                more = continuation.candidates[0].content.parts[0].text
                output_text += more

    # ------------------------------
    # RETURN CLEAN RESPONSE
    # ------------------------------
    return {
        "format": format,
        "output": {
            "raw": output_text
        }
    }
