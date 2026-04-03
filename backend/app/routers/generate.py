from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from ..database import get_db
from ..services.generator import generate_testcases
from ..services.coverage import simple_coverage
from ..models import TestRun
from ..dependencies import get_current_user
from ..schemas import GenerateRequest
from ..llm_client import generate_formatted_output
from ..memory import store_memory

router = APIRouter()


# -------------------------
# 🔥 GHERKIN INTELLIGENCE LAYER (SAFE)
# -------------------------
def enrich_requirement_for_gherkin(requirement: str):
    """
    Adds lightweight intelligence BEFORE your GHERKIN prompt.
    DOES NOT modify your prompt.
    ONLY improves input quality.
    """

    return f"""
Requirement:
{requirement}

QA Intelligence Instructions:
- Ensure coverage includes:
  • Positive scenarios
  • Negative scenarios
  • Edge cases
  • Validation scenarios

- Ensure system-level scenarios where applicable:
  • Session timeout
  • Concurrent access
  • Rate limiting

- Ensure business logic validation:
  • Authentication rules
  • Failure handling
  • Input validation

- Include API + UI validation if relevant

- Avoid missing critical real-world scenarios
"""


# -------------------------
# 🔥 AGENT PIPELINE (NEW)
# -------------------------
def run_generation_pipeline(requirement: str, output_format: str):
    """
    Central orchestration layer.
    Enables future multi-step agent upgrades.
    """

    # 🔥 Inject intelligence ONLY for GHERKIN
    if output_format == "gherkin":
        enriched_requirement = enrich_requirement_for_gherkin(requirement)
    else:
        enriched_requirement = requirement

    # ---------------- JSON FLOW ----------------
    if output_format == "json":
        testcases = generate_testcases(enriched_requirement)
        coverage = simple_coverage(testcases, requirement)

        return {
            "type": "json",
            "data": testcases,
            "coverage": coverage
        }

    # ---------------- NON-JSON (GHERKIN / EXCEL / TEXT) ----------------
    else:
        formatted_output = generate_formatted_output(
            enriched_requirement,
            output_format
        )

        return {
            "type": "formatted",
            "data": formatted_output
        }


# -------------------------
# ROUTE
# -------------------------
@router.post("/generate")
def generate(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        requirement = req.requirement.strip()

        if not requirement:
            raise HTTPException(status_code=400, detail="Requirement cannot be empty")

        user_id = hash(user) % 10000

        # 🔥 NEW: Use pipeline
        result = run_generation_pipeline(
            requirement,
            req.output_format
        )

        # ---------------- JSON FLOW ----------------
        if result["type"] == "json":
            testcases = result["data"]
            coverage = result["coverage"]

            print("\n===== COVERAGE DEBUG =====")
            print("Coverage:", coverage)
            print("==========================\n")

            # MEMORY
            store_memory(requirement, json.dumps(testcases))

            # DB STORE
            run = TestRun(
                user_id=user_id,
                requirement=requirement,
                output=json.dumps(testcases),
                format="json",
                coverage_percent=coverage.get("coverage_percent")
            )

            db.add(run)
            db.commit()

            return {
                "testcases": testcases,
                "coverage": coverage
            }

        # ---------------- NON-JSON FLOW ----------------
        else:
            formatted_output = result["data"]

            # MEMORY
            store_memory(requirement, formatted_output)

            # DB STORE
            run = TestRun(
                user_id=user_id,
                requirement=requirement,
                output=formatted_output,
                format=req.output_format,
                coverage_percent=None
            )

            db.add(run)
            db.commit()

            return formatted_output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
