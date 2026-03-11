# backend/app/main.py
import asyncio
import logging
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .schemas import GenerateReq, BatchReq
from .llm_client import generate_from_requirement
from .utils import try_parse_json, auto_number_test_cases
from .config import settings

# -------- logging --------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai-testcase-agent")

# -------- app --------
app = FastAPI(title="AI TestCase Agent")

# -------- CORS (configurable) --------
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

# -------- helpers --------
async def _call_llm(requirement: str, output_format: str) -> dict:
    """
    Call the blocking generate_from_requirement in a thread
    so we don't block the FastAPI event loop.
    """
    try:
        result = await asyncio.to_thread(
            generate_from_requirement,
            requirement,
            output_format,
        )
        return result or {}
    except Exception as e:
        logger.error("LLM call failed: %s\n%s", e, traceback.format_exc())
        raise


def _extract_raw_text(raw_resp: dict) -> str:
    """
    Safely extract raw text from llm_client response.
    Supports:
    - {"output": {"raw": "..."}}
    - {"raw": "..."}
    - plain string
    """
    if raw_resp is None:
        return ""

    if isinstance(raw_resp, str):
        return raw_resp

    if isinstance(raw_resp, dict):
        out = raw_resp.get("output")
        if isinstance(out, dict) and "raw" in out:
            return out.get("raw") or ""
        return raw_resp.get("raw") or ""

    return ""


# -------------------------
# ENDPOINT: Single requirement
# -------------------------
@app.post("/generate")
async def generate(req: GenerateReq):
    req_text = (req.requirement or "").strip()
    if not req_text:
        raise HTTPException(status_code=400, detail="Requirement empty")

    try:
        raw_resp = await _call_llm(req_text, req.output_format)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="LLM provider error, see server logs for details",
        )

    raw_text = _extract_raw_text(raw_resp)

    if req.output_format == "json":
        parsed = None

        try:
            parsed = try_parse_json(raw_text)
        except Exception as e:
            logger.warning("try_parse_json raised: %s", e)

        try:
            parsed = auto_number_test_cases(parsed) if parsed else None
        except Exception as e:
            logger.warning("auto_number_test_cases failed: %s", e)

        return {
            "format": req.output_format,
            "output": parsed if parsed else {"raw": raw_text},
        }

    return {
        "format": req.output_format,
        "output": {"raw": raw_text},
    }


# -------------------------
# ENDPOINT: Batch generation
# -------------------------
@app.post("/generate/batch")
async def generate_batch(req: BatchReq):
    if not req.requirements or len(req.requirements) == 0:
        raise HTTPException(status_code=400, detail="No requirements provided")

    async def _process_single(requirement: str) -> dict:
        req_text = (requirement or "").strip()

        if not req_text:
            return {
                "requirement": requirement,
                "error": "empty requirement",
                "output": None,
            }

        try:
            raw_resp = await _call_llm(req_text, req.output_format)
        except Exception:
            logger.exception("LLM error for requirement: %s", req_text)
            return {
                "requirement": requirement,
                "error": "llm_error",
                "output": None,
            }

        raw_text = _extract_raw_text(raw_resp)

        if req.output_format == "json":
            parsed = None

            try:
                parsed = try_parse_json(raw_text)
            except Exception:
                logger.warning("parse error for requirement: %s", requirement)

            try:
                parsed = auto_number_test_cases(parsed) if parsed else None
            except Exception:
                logger.warning("auto number failed for requirement: %s", requirement)

            return {
                "requirement": requirement,
                "format": req.output_format,
                "output": parsed if parsed else {"raw": raw_text},
            }

        return {
            "requirement": requirement,
            "format": req.output_format,
            "output": {"raw": raw_text},
        }

    coros = [_process_single(r) for r in req.requirements]
    results = await asyncio.gather(*coros, return_exceptions=False)

    valid_results = [r for r in results if r is not None]
    if not valid_results:
        raise HTTPException(status_code=400, detail="No valid requirements processed")

    return {"batch_results": valid_results}


# -------------------------
# RUN LOCAL DEV SERVER
# -------------------------
if __name__ == "__main__":
    host = getattr(settings, "HOST", "127.0.0.1")
    port = int(getattr(settings, "PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
