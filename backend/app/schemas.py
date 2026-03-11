# backend/app/schemas.py

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


# -------------------------
# Allowed output formats
# -------------------------
OutputFormat = Literal["json", "gherkin", "excel", "text"]


# -------------------------
# Single requirement input
# -------------------------
class GenerateReq(BaseModel):
    requirement: str = Field(..., min_length=1)
    output_format: OutputFormat = "json"


# -------------------------
# Batch requirements input
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
    type: Optional[str] = "Positive"  # Positive | Negative | Edge | Validation
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
# Single requirement response
# -------------------------
class GenerateResponse(BaseModel):
    format: OutputFormat
    output: Union[Dict[str, Any], List[Any], str]


# -------------------------
# Batch test case output
# -------------------------
class RequirementOutput(BaseModel):
    requirement: str
    format: OutputFormat
    output: Union[Dict[str, Any], List[Any], str]


class BatchOutput(BaseModel):
    batch_results: List[RequirementOutput] = Field(default_factory=list)
