from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from ..models import TestRun, User
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter()


@router.get("/history")
def history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        # 🔐 FIX: get real user_id from DB (stable & secure)
        db_user = db.query(User).filter(User.email == user).first()

        if not db_user:
            raise HTTPException(status_code=401, detail="User not found")

        user_id = db_user.id

        runs = (
            db.query(TestRun)
            .filter(TestRun.user_id == user_id)
            .order_by(TestRun.created_at.desc())
            .all()
        )

        response = []

        for r in runs:
            # Handle JSON safely
            if r.format == "json":
                try:
                    output = json.loads(r.output)
                except Exception:
                    output = r.output
            else:
                output = r.output

            response.append({
                "requirement": r.requirement,
                "output": output,
                "format": r.format,
                "coverage": r.coverage_percent,
                "created_at": r.created_at
            })

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
