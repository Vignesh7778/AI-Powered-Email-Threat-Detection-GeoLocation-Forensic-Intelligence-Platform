from pydantic import BaseModel, Field
from typing import List, Tuple, Literal

PatternType = Literal[
    "payment_diversion",
    "fake_invoice",
    "credential_harvesting",
    "executive_impersonation",
    "urgency_cue"
]

class DetectedPattern(BaseModel):
    type: PatternType
    excerpt_span: Tuple[int, int] = Field(
        ...,
        description="Character offset [start, end] into original body text"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)

class NLPAnalyzeRequest(BaseModel):
    subject: str = Field(..., description="Email subject line")
    body_text: str = Field(..., description="Plain text email body")

class NLPAnalyzeResponse(BaseModel):
    urgency_score: float = Field(..., ge=0.0, le=1.0)
    impersonation_language_score: float = Field(..., ge=0.0, le=1.0)
    detected_patterns: List[DetectedPattern]
    language_model_version: str = "v2.3.1"

