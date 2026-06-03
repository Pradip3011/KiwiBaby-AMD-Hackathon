import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt

# Core JWT Configuration
# In production, ensure JWT_SECRET_KEY is defined in your .env file
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-super-secret-key-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # default token lifespan: 24 hours

def create_session(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a secure JSON Web Token (JWT) representing an active user session.
    
    Args:
        data (dict): The payload dictionary containing user identities (e.g., {"sub": user_email})
        expires_delta (timedelta, optional): Custom expiration window override.
        
    Returns:
        str: Encoded JWT string token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    # Update payload with the standard JWT registered claim names
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_session(token: str) -> Optional[dict]:
    """
    Decodes and validates an incoming JWT session token.
    
    Args:
        token (str): The raw token string from the authorization headers.
        
    Returns:
        dict: The verified token payload data if valid, or None if expired/corrupted.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token timestamp has passed valid threshold
        return None
    except jwt.PyJWTError:
        # Signature verification failed or payload structurally modified
        return None