from pydantic import BaseModel, Field
from typing import Optional, Literal

AttachmentStatus = Literal["complete", "sandboxing"]

class AttachmentScanRequest(BaseModel):
    storage_ref: str = Field(..., description="Storage URI or reference identifier")
    sha256: str = Field(..., description="SHA-256 hash of attachment file")
    content_type: str = Field(..., description="MIME content type")

class AttachmentScanResponse(BaseModel):
    status: AttachmentStatus
    malware_score: float = Field(..., ge=0.0, le=1.0)
    detected_type: str = Field(..., description="E.g. macro_dropper, executable, suspicious_pdf, none")
    sandbox_report_ref: Optional[str] = None

