"""Settings routes: mailbox integrations and privacy/retention config."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.models import MailboxIntegration, PrivacyConfig
from app.schemas.schemas import (
    MailboxCreate,
    MailboxRead,
    PrivacyConfigRead,
    PrivacyConfigUpdate,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Mailbox integrations
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/tenants/{tenant_id}/integrations/mailboxes",
    response_model=list[MailboxRead],
)
def list_mailboxes(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return (
        db.query(MailboxIntegration)
        .filter(MailboxIntegration.tenant_id == tenant_id)
        .all()
    )


@router.post(
    "/api/v1/tenants/{tenant_id}/integrations/mailboxes",
    response_model=MailboxRead,
    status_code=status.HTTP_201_CREATED,
)
def add_mailbox(
    tenant_id: str,
    body: MailboxCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    integration = MailboxIntegration(
        integration_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        mailbox_address=body.mailbox_address,
        domain=body.domain,
    )
    db.add(integration)
    db.commit()
    return integration


# ---------------------------------------------------------------------------
# Privacy / Retention config
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/tenants/{tenant_id}/privacy-config",
    response_model=PrivacyConfigRead,
)
def get_privacy_config(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.query(PrivacyConfig).filter(PrivacyConfig.tenant_id == tenant_id).first()
    if not row:
        return PrivacyConfigRead(
            retention_days=180,
            mask_pii_in_dashboard=True,
            auto_purge_low_risk=False,
            updated_at=datetime.now(timezone.utc),
        )
    return row


@router.put(
    "/api/v1/tenants/{tenant_id}/privacy-config",
    response_model=PrivacyConfigRead,
)
def update_privacy_config(
    tenant_id: str,
    body: PrivacyConfigUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    row = db.query(PrivacyConfig).filter(PrivacyConfig.tenant_id == tenant_id).first()
    if not row:
        row = PrivacyConfig(tenant_id=tenant_id)
        db.add(row)

    if body.retention_days is not None:
        row.retention_days = body.retention_days
    if body.mask_pii_in_dashboard is not None:
        row.mask_pii_in_dashboard = body.mask_pii_in_dashboard
    if body.auto_purge_low_risk is not None:
        row.auto_purge_low_risk = body.auto_purge_low_risk
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return row
