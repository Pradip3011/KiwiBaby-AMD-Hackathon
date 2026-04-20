from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
import json
import os
import requests

from jose import JWTError, jwt
from dotenv import load_dotenv

from ..database import get_db
from ..services.generator import generate_testcases
from ..services.coverage import simple_coverage
from ..models import TestRun
from ..schemas import GenerateRequest
from ..llm_client import generate_formatted_output
from ..memory import store_memory, retrieve_learning

router = APIRouter()

# 🔐 LOAD ENV
load_dotenv()

# 🔐 JWT CONFIG
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# -------------------------
# 🌍 GEO-TELEMETRY HELPER
# -------------------------
def get_geo_location(request: Request):
    """Architect's Helper: Intercepts Ngrok IP and resolves City/Country."""
    # Ngrok forwards real IP in this header
    x_forwarded = request.headers.get("x-forwarded-for")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.client.host
    
    try:
        # Fast, no-auth API for real-time tracking
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2).json()
        return {
            "ip": ip,
            "city": response.get("city", "Unknown"),
            "country": response.get("country", "Unknown")
        }
    except:
        return {"ip": ip, "city": "Unknown", "country": "Unknown"}

# -------------------------
# 🔐 AUTH VALIDATION (NO-TOUCH)
# -------------------------
def get_current_user(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# -------------------------
# 🔥 GHERKIN INTELLIGENCE LAYER (NO-TOUCH)
# -------------------------
def enrich_requirement_for_gherkin(requirement: str):
    return f"""
Requirement:
{requirement}

QA Intelligence Instructions:
- Ensure coverage includes: Positive, Negative, Edge, and Validation scenarios.
- Include system-level checks: Session timeout, Concurrent access, Rate limiting.
"""

# -------------------------
# 🔥 AGENT PIPELINE (NO-TOUCH)
# -------------------------
def run_generation_pipeline(requirement: str, output_format: str):
    # Core reasoning logic preserved exactly as established
    if output_format == "gherkin":
        enriched_requirement = enrich_requirement_for_gherkin(requirement)
    else:
        enriched_requirement = requirement
    learned_gaps = retrieve_learning(requirement)
    structured_testcases = generate_testcases(enriched_requirement, missing_scenarios=learned_gaps)
    coverage = simple_coverage(structured_testcases, requirement)
    missing = coverage.get("missing_scenarios", [])

    if missing:
        improved_testcases = generate_testcases(enriched_requirement, missing_scenarios=missing)
        improved_coverage = simple_coverage(improved_testcases, requirement)
        if improved_coverage.get("coverage_percent", 0) > coverage.get("coverage_percent", 0):
            structured_testcases = improved_testcases
            coverage = improved_coverage

    if output_format == "json":
        return {"type": "json", "data": structured_testcases, "coverage": coverage}
    else:
        strict_context_prompt = f"{enriched_requirement}\n\nPRE-APPROVED SCENARIOS:\n{json.dumps(structured_testcases)}"
        formatted_output = generate_formatted_output(strict_context_prompt, output_format)
        return {"type": "formatted", "data": formatted_output, "coverage": coverage}

# -------------------------
# 🔥 ROUTE (SECURED + GEO-TRACING)
# -------------------------
@router.post("/generate")
def generate(
    req: GenerateRequest,
    request: Request, # Added for IP Interception
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        requirement = req.requirement.strip()
        if not requirement:
            raise HTTPException(status_code=400, detail="Requirement cannot be empty")

        user_id = hash(user) % 10000
        
        # 🌍 Capture Global Telemetry
        geo = get_geo_location(request)

        result = run_generation_pipeline(requirement, req.output_format)
        coverage = result.get("coverage", {})

        # PERSISTENCE WITH GEO-DATA
        test_output = json.dumps(result["data"]) if result["type"] == "json" else result["data"]
        format_type = "json" if result["type"] == "json" else req.output_format

        run = TestRun(
            user_id=user_id,
            requirement=requirement,
            output=test_output,
            format=format_type,
            coverage_percent=coverage.get("coverage_percent"),
            trigger_ip=geo["ip"],      # Captured Geo Data
            trigger_city=geo["city"],  # Captured Geo Data
            trigger_country=geo["country"] # Captured Geo Data
        )

        db.add(run)
        db.commit()

        # Return response (Metrics + Data)
        response_data = {
            "coverage_percent": coverage.get("coverage_percent"),
            "qa_score": coverage.get("qa_score"),
            "rule_score": coverage.get("rule_score"),
            "missing_scenarios": coverage.get("missing_scenarios")
        }
        
        if result["type"] == "json":
            response_data["testcases"] = result["data"]
        else:
            response_data["formatted_output"] = result["data"]

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))