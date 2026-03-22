# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routers import auth, generate, history
from .database import Base, engine
from .config import settings

# -------- logging --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-testcase-agent")

# -------- app --------
app = FastAPI(title="AI TestCase Agent")

# -------- DB init --------
Base.metadata.create_all(bind=engine)

# -------- CORS --------
_frontend_url = getattr(settings, "FRONTEND_URL", None)

if _frontend_url:
    origins = [o.strip() for o in _frontend_url.split(",") if o.strip()]
else:
    origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- routers --------
app.include_router(auth.router, prefix="/auth")
app.include_router(generate.router)
app.include_router(history.router)
