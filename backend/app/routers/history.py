# backend/app/routers/history.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import logging

from ..models import TestRun, User
from ..database import get_db
from ..dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger("ai-testcase-agent")

@router.get("/history")
def history(
    db: Session = Depends(get_db),
    user=Depends(get_current_user) # 🔐 'user' here is the email from JWT sub
):
    try:
        # 🔐 Step 1: Securely fetch the user record from your Neon DB
        db_user = db.query(User).filter(User.email == user).first()

        if not db_user:
            logger.error(f"History access attempt with non-existent user: {user}")
            raise HTTPException(status_code=401, detail="User not found")

        # 🔐 Step 2: Query only this user's runs from the Singapore Cloud DB
        runs = (
            db.query(TestRun)
            .filter(TestRun.user_id == db_user.id)
            .order_by(TestRun.created_at.desc())
            .all()
        )

        response = []

        for r in runs:
            # Safely handle JSON strings stored in the database
            try:
                if r.format == "json" and isinstance(r.output, str):
                    output = json.loads(r.output)
                else:
                    output = r.output
            except Exception as e:
                logger.warning(f"JSON Parse failed for run {r.id}: {str(e)}")
                output = r.output

            response.append({
                "id": r.id,
                "requirement": r.requirement,
                "output": output,
                "format": r.format,
                "coverage": r.coverage_percent,
                "created_at": r.created_at
            })

        return response

    except Exception as e:
        logger.error(f"History Fetch Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")