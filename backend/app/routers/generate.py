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
from ..router import evaluate_requirement_complexity  # 🔥 TRACK 1 ROUTER IMPORT
from ..llm_client import dispatch_hybrid_generation   # 🔥 TRACK 1 INFRA DISPATCHER

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
    x_forwarded = request.headers.get("x-forwarded-for")
    ip = x_forwarded.split(",")[0] if x_forwarded else request.client.host
    
    try:
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

# ---------------------------------------------------------
# 🔥 AMENDED HYBRID AGENT PIPELINE FOR TRACK 1
# ---------------------------------------------------------
def run_generation_pipeline(requirement: str, output_format: str):
    """
    Executes the generation pipeline enhanced with dynamic routing intelligence.
    Preserves historical agent logic while shifting model execution to the hybrid chassis.
    """
    if output_format == "gherkin":
        enriched_requirement = enrich_requirement_for_gherkin(requirement)
    else:
        enriched_requirement = requirement

    # 🧠 Pass payload to the sub-2ms complexity matrix evaluation brain
    routing_meta = evaluate_requirement_complexity(enriched_requirement)

    # 🏎️ Dispatch to optimal infrastructure (Local v/s Remote AMD)
    execution_result = dispatch_hybrid_generation(enriched_requirement, output_format, routing_meta)

    # Run downstream semantic evaluation using the output data stream content
    from ..utils import try_parse_json
    parsed_json = try_parse_json(execution_result["output_text"]) if output_format == "json" else []
    coverage = simple_coverage(parsed_json if parsed_json else [], requirement)

    return {
        "type": "json" if output_format == "json" else "formatted",
        "data": parsed_json if output_format == "json" else execution_result["output_text"],
        "coverage": coverage,
        "metrics": execution_result  # Track 1 performance metadata payload
    }

# -------------------------
# 🔥 ROUTE (SECURED + TRACK 1 METRICS TELEMETRY)
# -------------------------
@router.post("/generate")
def generate(
    req: GenerateRequest,
    request: Request,
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

        # Execute integrated engine stack pipeline
        result = run_generation_pipeline(requirement, req.output_format)
        coverage = result.get("coverage", {})
        metrics = result["metrics"]

        # Format mappings for database serialization step
        test_output = json.dumps(result["data"]) if result["type"] == "json" else result["data"]
        format_type = "json" if result["type"] == "json" else req.output_format

        # Instantiate full database record reflecting all leaderboard tracking fields
        run = TestRun(
            user_id=user_id,
            requirement=requirement,
            output=test_output,
            format=format_type,
            coverage_percent=coverage.get("coverage_percent", 0.0),
            trigger_ip=geo["ip"],
            trigger_city=geo["city"],
            trigger_country=geo["country"],
            
            # 🏎️ Track 1 Telemetry Data Integration Map
            routing_destination=metrics["routing_destination"],
            input_tokens=metrics["input_tokens"],
            output_tokens=metrics["output_tokens"],
            total_tokens=metrics["total_tokens"],
            execution_latency_ms=metrics["execution_latency_ms"],
            estimated_cost_saved=metrics["estimated_cost_saved"],
            compression_ratio=metrics["compression_ratio"]
        )

        db.add(run)
        db.commit()

        # Assemble comprehensive response schema payload for the frontend UI dashboard
        response_data = {
            "coverage_percent": coverage.get("coverage_percent"),
            "qa_score": coverage.get("qa_score"),
            "rule_score": coverage.get("rule_score"),
            "missing_scenarios": coverage.get("missing_scenarios"),
            
            # Real-time infrastructure telemetry metrics block for frontend dashboard UI
            "telemetry": {
                "routing_destination": metrics["routing_destination"],
                "total_tokens": metrics["total_tokens"],
                "execution_latency_ms": metrics["execution_latency_ms"],
                "estimated_cost_saved": metrics["estimated_cost_saved"],
                "compression_ratio": metrics["compression_ratio"]
            }
        }
        
        if result["type"] == "json":
            response_data["testcases"] = result["data"]
        else:
            response_data["formatted_output"] = result["data"]

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))