# backend/app/schemas.py

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


# -------------------------
# Allowed output formats
# -------------------------
OutputFormat = Literal["json", "gherkin", "excel", "text"]


# -------------------------
# AUTH (🔥 UPDATED)
# -------------------------
class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


# -------------------------
# Generate
# -------------------------
class GenerateRequest(BaseModel):
    requirement: str = Field(..., min_length=1)
    output_format: OutputFormat = "json"


# -------------------------
# Batch (optional)
# -------------------------
class BatchReq(BaseModel):
    requirements: List[str] = Field(..., min_items=1)
    output_format: OutputFormat = "json"


# -------------------------
# Test case structure
# -------------------------
class TestCase(BaseModel):
    id: Optional[str] = None
    description: str
    preconditions: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    expected: str
    type: Optional[str] = "Positive"
    priority: Optional[str] = None
    severity: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# -------------------------
# Structured JSON output
# -------------------------
class TestCaseOutput(BaseModel):
    summary: Optional[str] = None
    test_cases: List[TestCase] = Field(default_factory=list)


# -------------------------
# Coverage response
# -------------------------
class CoverageResponse(BaseModel):
    coverage_percent: float
    covered_keywords: List[str] = []
    missing_keywords: List[str] = []
    total_keywords: int


# -------------------------
# Final API response
# -------------------------
class GenerateResponse(BaseModel):
    testcases: List[Dict[str, Any]]
    coverage: CoverageResponse


# -------------------------
# History response
# -------------------------
class HistoryItem(BaseModel):
    requirement: str
    output: List[Dict[str, Any]]
    created_at: Any


# -------------------------
# Batch output
# -------------------------
class RequirementOutput(BaseModel):
    requirement: str
    format: OutputFormat
    output: Union[Dict[str, Any], List[Any], str]


class BatchOutput(BaseModel):
    batch_results: List[RequirementOutput] = Field(default_factory=list)
