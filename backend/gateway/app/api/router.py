"""Main API router — collects all sub-routers."""
from fastapi import APIRouter

from app.api.routers import (
    alerts,
    audit,
    auth,
    cases,
    dashboard,
    emails,
    geo,
    reports,
    rules,
    settings,
    users,
    webhooks,
)

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Auth"])
api_router.include_router(emails.router, tags=["Emails"])
api_router.include_router(cases.router, tags=["Cases"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(geo.router, tags=["Geo"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(rules.router, tags=["Rules & Watchlists"])
api_router.include_router(users.router, tags=["Users"])
api_router.include_router(audit.router, tags=["Audit"])
api_router.include_router(settings.router, tags=["Settings"])
api_router.include_router(webhooks.router, tags=["Webhooks"])
