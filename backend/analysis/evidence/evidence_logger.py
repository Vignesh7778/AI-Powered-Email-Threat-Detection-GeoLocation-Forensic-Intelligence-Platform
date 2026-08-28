import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import ChainOfCustody
from backend.app.schemas.schemas import EvidenceLogRequest, EvidenceLogResponse

class EvidenceLogger:
    """
    Forensic Chain of Custody & Evidence Logger.
    Maintains an auditable, tamper-evident log for every access or modification of raw evidence.
    """

    @staticmethod
    def log_event(
        db: Session,
        submission_id: str,
        actor: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        raw_bytes: Optional[bytes] = None
    ) -> ChainOfCustody:
        integrity_hash = None
        if raw_bytes:
            integrity_hash = hashlib.sha256(raw_bytes).hexdigest()

        entry = ChainOfCustody(
            submission_id=submission_id,
            actor=actor,
            action=action,
            integrity_hash=integrity_hash,
            details=details or {},
            timestamp=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

evidence_logger = EvidenceLogger()
