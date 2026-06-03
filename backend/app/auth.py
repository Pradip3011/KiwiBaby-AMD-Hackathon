import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest
from app.core.jwt_handler import create_session

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def get_user(db: Session, email: str):
    """
    Helper function used by dependencies.py to verify active sessions
    and fetch the current user context from the database.
    """
    return db.query(User).filter(User.email == email.strip().lower()).first()


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        email = request.email.strip().lower()
        password = request.password

        # Debug logging
        logger.info(f"Login attempt: {email}")
        logger.info(f"Password length: {len(password)}")

        # bcrypt limitation
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password exceeds bcrypt maximum length."
            )

        # Find user using our exposed helper function
        user = get_user(db, email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Verify password
        try:
            password_valid = pwd_context.verify(
                password,
                user.hashed_password
            )
        except Exception as bcrypt_error:
            logger.exception(
                f"Bcrypt verification failed: {bcrypt_error}"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password verification error"
            )

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Create JWT - Fixed: Passed as a structured dictionary payload
        token = create_session({"sub": user.email})

        return {
            "success": True,
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": getattr(user, "name", "")
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"Unexpected login error: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )