from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from backend.app.core.database import get_db
from backend.app.models.models import ChainOfCustody
from backend.app.schemas.schemas import (
    HeaderParseRequest, HeaderParseResponse,
    AuthValidateRequest, AuthValidateResponse,
    OriginTraceRequest, OriginTraceResponse,
    GeoLookupRequest, GeoLocation,
    InfraFlagsRequest, InfraFlagsResponse,
    DomainIntelRequest, DomainIntel,
    LookalikeCheckRequest, LookalikeCheckResponse,
    EvidenceLogRequest, EvidenceLogResponse,
    ChainOfCustodyResponse, ChainEntry
)
from backend.analysis.headers.header_analyzer import header_analyzer
from backend.analysis.authentication.auth_validator import auth_validator
from backend.analysis.origin.origin_tracer import origin_tracer
from backend.analysis.geolocation.geo_service import geo_service
from backend.analysis.threat_intel.infra_flags import threat_intel
from backend.analysis.domain.domain_intel import domain_intel_provider
from backend.analysis.domain.lookalike import lookalike_detector
from backend.analysis.evidence.evidence_logger import evidence_logger

router = APIRouter()

@router.post("/headers/parse", response_model=HeaderParseResponse, tags=["Forensics"])
def parse_headers_endpoint(req: HeaderParseRequest):
    return header_analyzer.parse_headers(req.raw_headers)

@router.post("/auth/validate", response_model=AuthValidateResponse, tags=["Forensics"])
def validate_auth_endpoint(req: AuthValidateRequest):
    return auth_validator.validate(req.raw_headers, req.sender_domain)

@router.post("/origin/trace", response_model=OriginTraceResponse, tags=["Forensics"])
def trace_origin_endpoint(req: OriginTraceRequest):
    return origin_tracer.trace_origin(req.received_chain, req.trusted_relay_ranges)

@router.post("/geo/lookup", response_model=GeoLocation, tags=["Forensics"])
def geo_lookup_endpoint(req: GeoLookupRequest):
    return geo_service.lookup(req.ip)

@router.post("/infra/flags", response_model=InfraFlagsResponse, tags=["Forensics"])
def infra_flags_endpoint(req: InfraFlagsRequest):
    return threat_intel.get_flags(req.ip)

@router.post("/domain/intel", tags=["Forensics"])
def domain_intel_endpoint(req: DomainIntelRequest):
    return domain_intel_provider.analyze(req.domain)

@router.post("/domain/lookalike-check", response_model=LookalikeCheckResponse, tags=["Forensics"])
def lookalike_check_endpoint(req: LookalikeCheckRequest):
    return lookalike_detector.check(req.domain, req.compare_against)

@router.post("/evidence/log", response_model=EvidenceLogResponse, status_code=status.HTTP_201_CREATED, tags=["Forensics"])
def log_evidence_endpoint(req: EvidenceLogRequest, db: Session = Depends(get_db)):
    entry = evidence_logger.log_event(
        db=db,
        submission_id=req.submission_id,
        actor=req.actor,
        action=req.action,
        details=req.details
    )
    return EvidenceLogResponse(log_id=entry.log_id)

@router.get("/evidence/{submission_id}/chain", response_model=ChainOfCustodyResponse, tags=["Forensics"])
def get_chain_endpoint(submission_id: str, db: Session = Depends(get_db)):
    entries = db.query(ChainOfCustody).filter(ChainOfCustody.submission_id == submission_id).order_by(ChainOfCustody.timestamp.asc()).all()
    results = [
        ChainEntry(
            log_id=e.log_id,
            actor=e.actor,
            action=e.action,
            timestamp=e.timestamp.isoformat() if e.timestamp else "",
            integrity_hash=e.integrity_hash,
            details=e.details
        ) for e in entries
    ]
    return ChainOfCustodyResponse(submission_id=submission_id, entries=results)
