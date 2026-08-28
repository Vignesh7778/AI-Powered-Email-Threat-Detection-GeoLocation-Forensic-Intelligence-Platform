"""Append-only audit logger for gateway-side actions (view, export, acknowledge, etc.)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import AuditLog


def log_action(
    db: Session,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    submission_id: Optional[str] = None,
    case_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Insert an immutable audit log entry and commit."""
    entry = AuditLog(
        log_id=str(uuid.uuid4()),
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        submission_id=submission_id,
        case_id=case_id,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    return entry
