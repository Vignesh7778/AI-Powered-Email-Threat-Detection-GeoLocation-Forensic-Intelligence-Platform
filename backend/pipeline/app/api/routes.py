from typing import Union
from fastapi import APIRouter, HTTPException, Request, Response, status

from app.schemas import AnalysisRecord, AnalyzeAccepted, EmailSubmission, EvidenceEntry, FraudAssessment
from app.services.evidence import evidence_ledger

router = APIRouter(tags=["Pipeline"])


@router.post("/internal/analyze", response_model=Union[FraudAssessment, AnalyzeAccepted])
def analyze(submission: EmailSubmission, response: Response, request: Request):
    result = request.app.state.orchestrator.analyze(submission)
    if isinstance(result, AnalyzeAccepted):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.get("/internal/analysis/{submission_id}", response_model=AnalysisRecord)
def analysis_status(submission_id: str, request: Request):
    record = request.app.state.orchestrator.repository.get(submission_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown submission_id")
    return record


@router.get("/internal/evidence/{submission_id}", response_model=list[EvidenceEntry])
def evidence_chain(submission_id: str):
    entries = evidence_ledger.chain(submission_id)
    if not entries:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No evidence events found")
    return entries
