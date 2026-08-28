from pydantic import BaseModel, Field
from typing import List

class ModelHealthItem(BaseModel):
    name: str
    version: str
    last_trained: str
    status: str

class ModelHealthResponse(BaseModel):
    models: List[ModelHealthItem]

class FeedbackRequest(BaseModel):
    submission_id: str
    analyst_verdict: str = Field(..., description="legitimate|suspicious|impersonation|phishing|bec_fraud")
    analyst_id: str

class FeedbackResponse(BaseModel):
    status: str = "queued_for_retraining"

