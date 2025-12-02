from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

from .schemas import GenerateReq
from .llm_client import generate_from_requirement
from .utils import try_parse_json, auto_number_test_cases
from .config import settings

# -------------------------
# APP SETUP
# -------------------------
app = FastAPI(title="AI TestCase Agent")

# -------------------------
# CORS (for frontend React app)
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# ENDPOINT: Single requirement
# -------------------------
@app.post("/generate")
async def generate(req: GenerateReq):
    req_text = req.requirement.strip()
    if not req_text:
        raise HTTPException(status_code=400, detail="Requirement empty")

    raw = generate_from_requirement(req_text, format=req.output_format)
    raw_text = raw["output"]["raw"]

    # Parse JSON safely
    parsed = try_parse_json(raw_text)

    # Auto-number test cases if JSON
    parsed = auto_number_test_cases(parsed) if parsed else None

    # Return response
    return {
        "format": req.output_format,
        "output": parsed if parsed else {"raw": raw_text}
    }

# -------------------------
# ENDPOINT: Batch generation
# -------------------------
class BatchReq(BaseModel):
    requirements: List[str]
    output_format: str = "json"

@app.post("/generate/batch")
async def generate_batch(req: BatchReq):
    if not req.requirements or len(req.requirements) == 0:
        raise HTTPException(status_code=400, detail="No requirements provided")

    results = []

    for requirement in req.requirements:
        if not requirement.strip():
            continue

        raw = generate_from_requirement(requirement, format=req.output_format)
        raw_text = raw["output"]["raw"]

        # Parse JSON safely
        parsed = try_parse_json(raw_text)
        parsed = auto_number_test_cases(parsed) if parsed else None

        results.append({
            "requirement": requirement,
            "format": req.output_format,
            "output": parsed if parsed else {"raw": raw_text}
        })

    if not results:
        raise HTTPException(status_code=400, detail="No valid requirements provided")

    return {"batch_results": results}

# -------------------------
# RUN LOCAL DEV SERVER
# -------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
