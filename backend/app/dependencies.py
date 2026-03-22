from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from .auth import get_user

# This creates proper Swagger auth support
api_key_header = APIKeyHeader(name="Authorization")


def get_current_user(token: str = Security(api_key_header)):
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Handle optional Bearer prefix
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    user = get_user(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user
