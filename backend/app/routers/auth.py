from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from ..database import get_db
from ..models import User
from ..schemas import LoginRequest

router = APIRouter()

# 🔐 Load environment variables
load_dotenv()

# 🔐 Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 JWT CONFIG (FROM ENV)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 🔐 ADMIN SECRET (FROM ENV)
ADMIN_SECRET = os.getenv("ADMIN_SECRET")

# -------------------------
# 🔥 RATE LIMIT CONFIG
# -------------------------
RATE_LIMIT_WINDOW = timedelta(minutes=1)
MAX_ATTEMPTS = 5

login_attempts = {}


def register_failed_attempt(ip: str):
    now = datetime.utcnow()
    attempts = login_attempts.get(ip, [])

    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]

    attempts.append(now)
    login_attempts[ip] = attempts


def check_rate_limit(ip: str):
    now = datetime.utcnow()
    attempts = login_attempts.get(ip, [])

    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW]

    if len(attempts) >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Please try again later."
        )

    login_attempts[ip] = attempts


def reset_attempts(ip: str):
    if ip in login_attempts:
        del login_attempts[ip]


# -------------------------
# CREATE JWT TOKEN
# -------------------------
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# 🔐 PASSWORD VALIDATION (🔥 NEW)
# -------------------------
def validate_password(password: str):
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 bytes allowed)"
        )


# -------------------------
# LOGIN (SMART RATE LIMITED)
# -------------------------
@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host

    check_rate_limit(client_ip)

    email = data.email.strip()
    password = data.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # 🔐 enforce password constraint
    validate_password(password)

    user = db.query(User).filter(User.email == email).first()

    if not user or not pwd_context.verify(password, user.hashed_password):
        register_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    reset_attempts(client_ip)

    token = create_access_token({"sub": email})

    return {
        "token": token,
        "user": email
    }


# -------------------------
# CREATE USER (🔒 ADMIN ONLY)
# -------------------------
@router.post("/create-user")
def create_user(
    data: LoginRequest,
    db: Session = Depends(get_db),
    x_admin_key: str = Header(default=None)
):
    if not ADMIN_SECRET:
        raise HTTPException(status_code=500, detail="Admin secret not configured")

    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized access")

    email = data.email.strip()
    password = data.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # 🔐 enforce password constraint
    validate_password(password)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(password)

    new_user = User(
        email=email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "email": email
    }
