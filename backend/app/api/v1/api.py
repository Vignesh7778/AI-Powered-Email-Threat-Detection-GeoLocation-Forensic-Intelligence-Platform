from fastapi import APIRouter
from backend.app.api.v1.routes import (
    auth, emails, cases, alerts, dashboard,
    forensics, ml, privacy, internal, campaigns
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(emails.router, prefix="/emails", tags=["Email Ingestion & Triage"])
api_router.include_router(cases.router, prefix="/cases", tags=["Case Management"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Threat Alerting"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Security Dashboard"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Threat Campaigns"])
api_router.include_router(privacy.router, tags=["Tenant Privacy & Governance"])
api_router.include_router(forensics.router, prefix="/forensics", tags=["Cyber Forensics"])
api_router.include_router(ml.router, prefix="/ml", tags=["AI/ML Detection Engine"])
api_router.include_router(internal.router, prefix="/internal", tags=["Internal Pipeline"])

