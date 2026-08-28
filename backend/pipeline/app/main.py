from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.services.orchestrator import orchestrator

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Phase Two orchestration service for email forensics and fraud assessment.",
)
app.include_router(router)
app.state.orchestrator = orchestrator


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy", "service": settings.project_name, "version": settings.version, "modules": ["forensics", "ml", "aggregation", "evidence"]}
