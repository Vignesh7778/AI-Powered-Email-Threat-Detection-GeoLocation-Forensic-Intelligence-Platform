from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="""
# AI/ML Microservice Backend
AI/ML Detection & Fraud Classification Service.
Includes:
- **NLP Analysis**: Urgency cues, impersonation detection, pattern extraction with character spans.
- **Link Risk Scorer**: Obfuscation detection, IP literal host checking, shorteners, mismatch flags.
- **Core Classifier**: Machine learning fraud classification model with feature importance.
- **Attachment Scanner**: Malware heuristics and payload scoring.
- **Score Aggregator**: Unified multi-signal aggregation into final `FraudAssessment`.
- **Model Ops**: Health monitoring and analyst feedback loop.
    """
)

# Set up CORS middleware
if settings.ALLOWED_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

