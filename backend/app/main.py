import datetime
import logging
import time
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

# 🎯 CRITICAL VERCEL FIX: Transitioned from relative to absolute package imports
from app import models
from app.database import Base, engine
from app.config import settings
from app.routers import auth, generate, history

# -------- logging (Architectural Telemetry) --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-testcase-agent")

# -------- app initialization (SINGLE INSTANCE) --------
app = FastAPI(title="AI TestCase Agent")

# -------- CORS Middleware (Cross-Origin Resource Sharing) --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- DB init (Persistence Layer) --------
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database Schema verified/created successfully.")
except Exception as e:
    logger.exception("Database initialization failed")


# -------- SYSTEM UTILITIES --------

@app.get("/")
async def root():
    """Returns health status instantly on root URL hit."""
    return {
        "status": "online",
        "message": "KiwiBaby AI Testing Agent Backend is Live!",
        "node": "Auckland Bridge Node",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Silences browser favicon noise."""
    return Response(status_code=204)


@app.get("/health")
def health_check():
    """The Auckland Bridge Heartbeat."""
    return {"status": "Auckland Bridge is Active", "timestamp": time.time()}


# -------- MOBILE COMMAND CENTER (Your Clarity Page) --------

@app.get("/telemetry", response_class=HTMLResponse)
async def live_telemetry():
    """Architect's Real-Time Log View: Dynamic Global Tracking."""
    now = datetime.datetime.now().strftime("%H:%M:%S")

    # 🌍 FETCH LATEST GLOBAL TELEMETRY FROM DB
    db = Session(bind=engine)
    try:
        last_run = (
            db.query(models.TestRun)
            .order_by(desc(models.TestRun.created_at))
            .first()
        )

        # Default values if no runs exist
        location = "No active tasks"
        origin_ip = "N/A"
        task_title = "Standby"

        if last_run:
            city = last_run.trigger_city or "Unknown"
            country = last_run.trigger_country or "Unknown"
            location = f"{city}, {country}"
            origin_ip = last_run.trigger_ip or "Local"
            # Extracting a snippet of the requirement as the title
            task_title = (
                (last_run.requirement[:35] + "...")
                if len(last_run.requirement) > 35
                else last_run.requirement
            )

    except Exception as e:
        logger.error(f"Telemetry DB pull failed: {e}")
        location, origin_ip, task_title = "Telemetry Error", "N/A", "Offline"
    finally:
        db.close()

    # Standard multiline string prevents Tailwind brackets from breaking Python string parsing
    html_template = """
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.tailwindcss.com"></script>
            <title>Agent Telemetry</title>
        </head>
        <body class="bg-black text-emerald-400 font-mono p-4 text-[11px]">
            <div class="fixed top-0 left-0 w-full bg-slate-900 p-4 border-b border-emerald-900 flex justify-between items-center z-50 shadow-lg">
                <span class="font-bold tracking-tighter text-sm italic">🛰️ AGENT COMMAND</span>
                <span class="animate-pulse text-emerald-500 font-bold text-[9px]">● LIVE</span>
            </div>
            
            <div class="mt-20 space-y-4">
                <div class="bg-slate-950 p-4 rounded-lg border border-slate-800 shadow-xl shadow-emerald-500/5">
                    <p class="text-slate-500 mb-2 border-b border-slate-800 pb-1 uppercase text-[9px]">Core Node: Auckland</p>
                    <div class="flex justify-between py-1"><span>Status:</span><span class="text-white font-bold">ACTIVE</span></div>
                    <div class="flex justify-between py-1"><span>Latest Task:</span><span class="text-blue-400 text-right">{task_title}</span></div>
                </div>

                <div class="bg-slate-950 p-4 rounded-lg border border-emerald-900/40 shadow-xl shadow-emerald-500/10">
                    <p class="text-emerald-600 mb-2 border-b border-emerald-900/30 pb-1 uppercase text-[9px] font-bold">🌍 Global Telemetry</p>
                    <div class="flex justify-between py-1"><span>Trigger Location:</span><span class="text-white">{location}</span></div>
                    <div class="flex justify-between py-1"><span>Origin IP:</span><span class="text-slate-400">{origin_ip}</span></div>
                    <div class="flex justify-between py-1"><span>System Clock:</span><span class="text-emerald-500">{system_clock}</span></div>
                </div>
            </div>
        </body>
    </html>
    """
    
    return html_template.format(
        task_title=task_title,
        location=location,
        origin_ip=origin_ip,
        system_clock=now
    )


# -------- ROUTER INCLUSIONS --------
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(generate.router, prefix="", tags=["Generation"])
app.include_router(history.router, prefix="/history", tags=["History"])