from pydantic import BaseModel, Field
from typing import List

class LinkScore(BaseModel):
    displayed_text: str
    actual_url: str
    obfuscated: bool
    risk_score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str]

class LinkExtractRequest(BaseModel):
    body_html: str = Field(..., description="HTML content of email body")

class LinkExtractResponse(BaseModel):
    links: List[LinkScore]

