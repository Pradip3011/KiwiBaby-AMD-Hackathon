from fastapi import APIRouter, HTTPException
from ..auth import create_session
from ..schemas import LoginRequest

router = APIRouter()


@router.post("/login")
def login(data: LoginRequest):
    username = data.username.strip()

    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    token = create_session(username)

    return {
        "token": token,
        "user": username
    }
