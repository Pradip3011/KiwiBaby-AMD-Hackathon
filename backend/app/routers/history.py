from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from ..models import TestRun
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        user_id = hash(user) % 10000

        runs = (
            db.query(TestRun)
            .filter(TestRun.user_id == user_id)
            .order_by(TestRun.created_at.desc())
            .all()
        )

        response = []

        for r in runs:
            # 🔥 Handle JSON safely
            if r.format == "json":
                try:
                    output = json.loads(r.output)
                except Exception:
                    output = r.output
            else:
                output = r.output  # plain string (gherkin/text)

            response.append({
                "requirement": r.requirement,
                "output": output,
                "format": r.format,  # 🔥 NEW
                "coverage": r.coverage_percent,  # 🔥 NEW
                "created_at": r.created_at
            })

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
