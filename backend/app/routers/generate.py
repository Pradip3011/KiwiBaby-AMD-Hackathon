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

        # ---------------- JSON FLOW ----------------
        if req.output_format == "json":
            testcases = generate_testcases(requirement)
            coverage = simple_coverage(testcases, requirement)

            # 🔥 DEBUG: Coverage visibility
            print("\n===== COVERAGE DEBUG =====")
            print("Coverage:", coverage)
            print("==========================\n")

            # 🔥 STORE MEMORY (store structured output)
            store_memory(requirement, json.dumps(testcases))

            # 🔥 STORE IN DB
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
            formatted_output = generate_formatted_output(
                requirement,
                req.output_format
            )

            # 🔥 STORE MEMORY (store formatted output also)
            store_memory(requirement, formatted_output)

            # 🔥 STORE IN DB
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
