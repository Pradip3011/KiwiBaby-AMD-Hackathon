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
from . import models 
Base.metadata.create_all(bind=engine)

# -------- CORS (Production Ready) --------
# We explicitly list all possible origins to prevent "Failed to Fetch" 
# on mobile and remote devices.
origins = [
    "http://localhost:5173",                            # Local React Dev
    "https://kia-ora-pradip-agent.vercel.app",          # Your Permanent POC Link
    "https://playtime-facebook-discard.ngrok-free.dev"  # Your Ngrok Bridge
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Allows Authorization and Content-Type headers
)

# -------- routers --------
app.include_router(auth.router, prefix="/auth")
app.include_router(generate.router)
app.include_router(history.router)

@app.get("/")
async def root():
    return {"message": "Auckland Bridge is Active", "status": "online"}