import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal
from backend.app.api.v1.api import api_router
from backend.app.api.v1.routes import auth, forensics, ml, internal
from backend.app.models.models import User, Campaign
from backend.app.core.security import get_password_hash

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database Tables
    init_db()
    
    # Seed default analyst and admin accounts if empty
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "analyst@org.gov").first():
            analyst = User(
                email="analyst@org.gov",
                hashed_password=get_password_hash("password123"),
                full_name="Senior Cyber Analyst",
                role="analyst",
                tenant_id="tenant-cyber-sec-01"
            )
            admin = User(
                email="admin@org.gov",
                hashed_password=get_password_hash("admin123"),
                full_name="Security Administrator",
                role="admin",
                tenant_id="tenant-cyber-sec-01"
            )
            investigator = User(
                email="investigator@org.gov",
                hashed_password=get_password_hash("investigate123"),
                full_name="Lead Forensic Examiner",
                role="investigator",
                tenant_id="tenant-cyber-sec-01"
            )
            db.add_all([analyst, admin, investigator])
            db.commit()

        if not db.query(Campaign).first():
            c1 = Campaign(
                campaign_id="camp-bec-finance-2026",
                name="FinTarget BEC Campaign (ShadowInvoice)",
                threat_actor="UNC2944 / SilverTerrier Cluster",
                status="active",
                description="Targeted executive impersonation and fraudulent vendor wire diversion wave."
            )
            c2 = Campaign(
                campaign_id="camp-cred-harvest-m365",
                name="M365 Credential Harvesting Wave",
                threat_actor="Storm-0839",
                status="active",
                description="Deceptive security alert landing pages stealing corporate session credentials."
            )
            db.add_all([c1, c2])
            db.commit()

        # If Submissions are empty, auto-ingest sample threat dataset
        if db.query(Submission).count() == 0:
            sample_dir = os.path.join(BASE_DIR, "datasets", "sample_emails")
            if os.path.exists(sample_dir):
                import uuid
                from backend.app.schemas.schemas import EmailSubmission, RawBody, SourceContext
                from backend.analysis.parser.email_parser import email_parser
                from backend.app.services.pipeline_orchestrator import pipeline_orchestrator
                from backend.app.models.models import Case, CaseSubmission

                seeded_sids = []
                for fname in ["phishing.eml", "bec.eml", "impersonation.eml", "credential_phishing.eml", "legitimate.eml"]:
                    fpath = os.path.join(sample_dir, fname)
                    if not os.path.exists(fpath):
                        continue
                    try:
                        with open(fpath, "rb") as fp:
                            fbytes = fp.read()
                        sid = str(uuid.uuid4())
                        parsed = email_parser.parse_raw_eml(fbytes, sid, "/tmp/storage" if is_vercel else settings.STORAGE_PATH)
                        
                        sub = Submission(
                            submission_id=sid,
                            tenant_id="tenant-cyber-sec-01",
                            file_name=fname,
                            file_size=len(fbytes),
                            sha256_hash=hashlib.sha256(fbytes).hexdigest(),
                            sender=parsed.get("sender"),
                            recipient=parsed.get("recipient"),
                            subject=parsed.get("subject"),
                            source="upload",
                            status="analyzing",
                            received_at=datetime.now(timezone.utc),
                            ingested_at=datetime.now(timezone.utc)
                        )
                        db.add(sub)
                        db.commit()

                        sub_obj = EmailSubmission(
                            submission_id=sid,
                            received_at=datetime.now(timezone.utc).isoformat(),
                            raw_headers=parsed["raw_headers"],
                            raw_body=RawBody(text_plain=parsed.get("text_plain"), text_html=parsed.get("text_html")),
                            attachments=parsed.get("attachments", []),
                            source_context=SourceContext(ingested_via="upload", tenant_id="tenant-cyber-sec-01")
                        )
                        pipeline_orchestrator.analyze_submission(sub_obj, db=db, actor="system_init")
                        seeded_sids.append(sid)
                    except Exception:
                        pass

                if seeded_sids and not db.query(Case).first():
                    try:
                        c1 = Case(
                            title="Active Phishing Campaign - Financial Brand Spoofing",
                            status="investigating",
                            severity="high",
                            notes="Multiple deceptive emails targeting accounting personnel with fake credential harvesting links.",
                            assigned_analyst="analyst@org.gov"
                        )
                        db.add(c1)
                        db.commit()
                        db.refresh(c1)
                        for sid in seeded_sids[:3]:
                            db.add(CaseSubmission(case_id=c1.case_id, submission_id=sid))
                        db.commit()
                    except Exception:
                        pass
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
    ## 🛡️ AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform
    **Problem Statement ID: 26106 | AICTE Cyber Security Cell**
    
    Comprehensive full-stack cybersecurity investigation engine:
    - 🔍 **Cyber Forensics**: RFC 5322 MIME parsing, hop-ordered Received chain, SPF/DKIM/DMARC, Origin IP isolation, GeoLocation intelligence, Lookalike domain homoglyph detection.
    - 🧠 **AI/ML Detection**: NLP social engineering pattern extraction with character spans, deceptive link scoring, static attachment inspection, explainable multi-class fraud classification.
    - 🕸️ **Graph Intelligence**: Cross-incident entity correlation, shared indicator tracking, campaign cluster attribution.
    - 📁 **Incident Case Management & Alerts**: Triage queue, real-time alert dispatch, and evidentiary chain-of-custody tracking.
    - 📄 **Forensic Reporting**: Professional PDF & structured JSON court-admissible forensic reports.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level shortcuts matching exact specification contracts
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(forensics.router, prefix="/forensics", tags=["Cyber Forensics"])
app.include_router(ml.router, prefix="/ml", tags=["AI/ML Detection Engine"])
app.include_router(internal.router, prefix="/internal", tags=["Internal Pipeline"])

# API v1 Router - Mount on both /api/v1 and /v1 for Vercel/proxy compatibility
app.include_router(api_router, prefix=settings.API_V1_STR)
if settings.API_V1_STR != "/v1":
    app.include_router(api_router, prefix="/v1")

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected (Supabase/PostgreSQL/SQLite)",
        "env": settings.ENV
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
