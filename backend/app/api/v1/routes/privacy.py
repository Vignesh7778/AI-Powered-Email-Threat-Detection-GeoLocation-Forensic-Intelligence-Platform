from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import PrivacyConfig
from backend.app.schemas.schemas import PrivacyConfigSchema

router = APIRouter()

@router.get("/tenants/{tenant_id}/privacy-config", response_model=PrivacyConfigSchema)
def get_privacy_config(tenant_id: str, db: Session = Depends(get_db)):
    cfg = db.query(PrivacyConfig).filter(PrivacyConfig.tenant_id == tenant_id).first()
    if not cfg:
        cfg = PrivacyConfig(tenant_id=tenant_id, retention_days=180, mask_pii_in_dashboard=True, auto_purge_low_risk=False)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return PrivacyConfigSchema(
        retention_days=cfg.retention_days,
        mask_pii_in_dashboard=cfg.mask_pii_in_dashboard,
        auto_purge_low_risk=cfg.auto_purge_low_risk
    )

@router.put("/tenants/{tenant_id}/privacy-config", response_model=PrivacyConfigSchema)
def update_privacy_config(tenant_id: str, req: PrivacyConfigSchema, db: Session = Depends(get_db)):
    cfg = db.query(PrivacyConfig).filter(PrivacyConfig.tenant_id == tenant_id).first()
    if not cfg:
        cfg = PrivacyConfig(tenant_id=tenant_id)
        db.add(cfg)
    
    cfg.retention_days = req.retention_days
    cfg.mask_pii_in_dashboard = req.mask_pii_in_dashboard
    cfg.auto_purge_low_risk = req.auto_purge_low_risk
    db.commit()
    db.refresh(cfg)

    return PrivacyConfigSchema(
        retention_days=cfg.retention_days,
        mask_pii_in_dashboard=cfg.mask_pii_in_dashboard,
        auto_purge_low_risk=cfg.auto_purge_low_risk
    )
