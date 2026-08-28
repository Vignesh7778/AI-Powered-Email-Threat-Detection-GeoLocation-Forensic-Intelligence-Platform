from fastapi import APIRouter, status, Response
from app.schemas.attachment import AttachmentScanRequest, AttachmentScanResponse
from app.ml.attachment_engine import attachment_scanner

router = APIRouter()

@router.post(
    "/attachments/scan",
    response_model=AttachmentScanResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Scan complete"},
        202: {"description": "Scan accepted and sandboxing initiated"}
    }
)
async def scan_attachment(payload: AttachmentScanRequest, response: Response):
    """
    Attachment malware scanner evaluating file attributes, sha256, and content types.
    Returns malware_score, detected_type, status, and sandbox_report_ref.
    """
    result = attachment_scanner.scan(payload)
    if result.status == "sandboxing":
        response.status_code = status.HTTP_202_ACCEPTED
    return result

