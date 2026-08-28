"""Gateway API — FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description=(
        "**Email Threat Detection Gateway API** — handles authentication, "
        "email ingestion, case management, dashboard analytics, geo heatmap, "
        "audit logging, watchlists, and proxies to the Forensics & ML services."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins during development — tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create all SQLite tables on first run."""
    init_db()


app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.version,
        "forensic_api": settings.forensic_api,
        "ml_api": settings.ml_api,
    }
