from pydantic import BaseModel
from typing import Optional, List, Dict

# -------------------------
# Single requirement input
# -------------------------
class GenerateReq(BaseModel):
    requirement: str
    output_format: Optional[str] = "json"  # json | gherkin | csv | xlsx | text

# -------------------------
# Batch requirements input
# -------------------------
class BatchReq(BaseModel):
    requirements: List[str]
    output_format: Optional[str] = "json"

# -------------------------
# Test case structure
# -------------------------
class TestCase(BaseModel):
    id: str                       # TC-001, TC-002, etc.
    description: str               # Short test title
    preconditions: Optional[str]  # Optional preconditions
    steps: List[str]               # Step-by-step instructions
    expected: str                  # Expected result
    type: Optional[str] = "Positive"  # Positive | Negative | Edge | Validation
    priority: Optional[str] = None
    severity: Optional[str] = None
    tags: Optional[List[str]] = []

# -------------------------
# Batch test case output structure (optional)
# -------------------------
class RequirementOutput(BaseModel):
    requirement: str
    format: str
    output: Dict  # Can be raw JSON or structured dict with test_cases

class BatchOutput(BaseModel):
    batch_results: List[RequirementOutput]
