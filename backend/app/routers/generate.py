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
from ..memory import store_memory, retrieve_learning  # 🔥 NEW

router = APIRouter()


# -------------------------
# 🔥 GHERKIN INTELLIGENCE LAYER (SAFE)
# -------------------------
def enrich_requirement_for_gherkin(requirement: str):
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
# 🔥 AGENT PIPELINE (SELF-IMPROVING + LEARNING)
# -------------------------
def run_generation_pipeline(requirement: str, output_format: str):

    if output_format == "gherkin":
        enriched_requirement = enrich_requirement_for_gherkin(requirement)
    else:
        enriched_requirement = requirement

    # -------------------------
    # 🔥 PASS 0: LEARN FROM PAST RUNS
    # -------------------------
    learned_gaps = retrieve_learning(requirement)

    if learned_gaps:
        print("\n🧠 Applying learned gaps from memory...\n")

    # -------------------------
    # PASS 1: INITIAL GENERATION
    # -------------------------
    structured_testcases = generate_testcases(
        enriched_requirement,
        missing_scenarios=learned_gaps
    )

    coverage = simple_coverage(structured_testcases, requirement)
    missing = coverage.get("missing_scenarios", [])

    # -------------------------
    # PASS 2: SELF-IMPROVEMENT (CURRENT RUN)
    # -------------------------
    if missing and len(missing) > 0:
        print("\n🔁 Improving testcases using current missing scenarios...\n")

        improved_testcases = generate_testcases(
            enriched_requirement,
            missing_scenarios=missing
        )

        improved_coverage = simple_coverage(improved_testcases, requirement)

        if improved_coverage.get("coverage_percent", 0) > coverage.get("coverage_percent", 0):
            structured_testcases = improved_testcases
            coverage = improved_coverage

    # -------------------------
    # OUTPUT HANDLING
    # -------------------------
    if output_format == "json":
        return {
            "type": "json",
            "data": structured_testcases,
            "coverage": coverage
        }

    else:
        formatted_output = generate_formatted_output(
            enriched_requirement,
            output_format
        )

        return {
            "type": "formatted",
            "data": formatted_output,
            "coverage": coverage
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

        result = run_generation_pipeline(
            requirement,
            req.output_format
        )

        coverage = result.get("coverage")

        # 🔥 CLEAN METRICS PRINT
        if coverage:
            print("\n===== QA METRICS =====")
            print(f"COVERAGE: {coverage.get('coverage_percent')}%")
            print(f"QA SCORE: {coverage.get('qa_score')}/100")
            print(f"RULE SCORE: {coverage.get('rule_score')}/100")
            print("======================\n")

        # ---------------- JSON FLOW ----------------
        if result["type"] == "json":
            testcases = result["data"]

            # 🔥 STORE WITH LEARNING
            store_memory(
                requirement,
                json.dumps(testcases),
                missing_scenarios=coverage.get("missing_scenarios")
            )

            run = TestRun(
                user_id=user_id,
                requirement=requirement,
                output=json.dumps(testcases),
                format="json",
                coverage_percent=coverage.get("coverage_percent") if coverage else None
            )

            db.add(run)
            db.commit()

            return {
                "testcases": testcases,
                "coverage_percent": coverage.get("coverage_percent"),
                "qa_score": coverage.get("qa_score"),
                "rule_score": coverage.get("rule_score"),
                "qa_details": coverage.get("qa_details"),
                "rule_details": coverage.get("rule_details"),
                "missing_scenarios": coverage.get("missing_scenarios")
            }

        # ---------------- NON-JSON FLOW ----------------
        else:
            formatted_output = result["data"]

            # 🔥 STORE WITH LEARNING
            store_memory(
                requirement,
                formatted_output,
                missing_scenarios=coverage.get("missing_scenarios")
            )

            run = TestRun(
                user_id=user_id,
                requirement=requirement,
                output=formatted_output,
                format=req.output_format,
                coverage_percent=coverage.get("coverage_percent") if coverage else None
            )

            db.add(run)
            db.commit()

            return formatted_output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
