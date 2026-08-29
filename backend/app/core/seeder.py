import os
import sys
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn.error")

_SEEDED_ONCE = False

def seed_database_if_empty(db: Session, force: bool = False):
    global _SEEDED_ONCE
    if _SEEDED_ONCE and not force:
        return

    try:
        from backend.app.models.models import User, Campaign, Submission, Case, CaseSubmission
        from backend.app.core.security import get_password_hash
        from backend.app.schemas.schemas import EmailSubmission, RawBody, SourceContext
        from backend.analysis.parser.email_parser import email_parser
        from backend.app.services.pipeline_orchestrator import pipeline_orchestrator
        from backend.app.core.config import settings

        # 1. Seed Default Users
        seed_users = [
            ("analyst@org.gov", "password123", "Senior Cyber Analyst", "analyst"),
            ("analyst@org.gov", "Analyst@2026!", "Senior Cyber Analyst", "analyst"),
            ("admin@org.gov", "admin123", "Security Administrator", "admin"),
            ("investigator@org.gov", "investigate123", "Lead Forensic Examiner", "investigator")
        ]
        for email, pwd, name, role in seed_users:
            try:
                if not db.query(User).filter(User.email == email).first():
                    u = User(
                        email=email,
                        hashed_password=get_password_hash(pwd),
                        full_name=name,
                        role=role,
                        tenant_id="tenant-cyber-sec-01"
                    )
                    db.add(u)
                    db.commit()
            except Exception:
                db.rollback()

        # 2. Seed Campaigns
        try:
            if db.query(Campaign).count() == 0:
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
        except Exception:
            db.rollback()

        # 3. Seed Submissions & Forensic Pipeline
        if db.query(Submission).count() == 0 or force:
            logger.info("Initializing self-healing forensic sample dataset...")
            seeded_sids = []
            target_storage = "/tmp/storage" if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) else settings.STORAGE_PATH
            try:
                os.makedirs(target_storage, exist_ok=True)
            except Exception:
                pass

            # Search in several possible sample directory locations
            possible_dirs = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "datasets", "sample_emails"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "datasets", "sample_emails"),
                "./datasets/sample_emails",
                "./backend/datasets/sample_emails"
            ]
            sample_dir = None
            for p in possible_dirs:
                if os.path.exists(p) and os.listdir(p):
                    sample_dir = p
                    break

            if sample_dir:
                for fname in sorted(os.listdir(sample_dir)):
                    if not fname.endswith(".eml"):
                        continue
                    fpath = os.path.join(sample_dir, fname)
                    try:
                        with open(fpath, "rb") as fp:
                            fbytes = fp.read()
                        sid = str(uuid.uuid4())
                        parsed = email_parser.parse_raw_eml(fbytes, sid, target_storage)
                        sha256_hash = hashlib.sha256(fbytes).hexdigest()

                        sub = Submission(
                            submission_id=sid,
                            tenant_id="tenant-cyber-sec-01",
                            file_name=fname,
                            file_size=len(fbytes),
                            sha256_hash=sha256_hash,
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
                            raw_headers=parsed.get("raw_headers", {}),
                            raw_body=RawBody(text_plain=parsed.get("text_plain"), text_html=parsed.get("text_html")),
                            attachments=parsed.get("attachments", []),
                            source_context=SourceContext(ingested_via="upload", tenant_id="tenant-cyber-sec-01")
                        )
                        pipeline_orchestrator.analyze_submission(sub_obj, db=db, actor="system_seeder")
                        seeded_sids.append(sid)
                    except Exception as e:
                        logger.warning(f"Error seeding sample {fname}: {e}")
                        db.rollback()

            # 4. Seed Incident Cases
            if seeded_sids and db.query(Case).count() == 0:
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
                    db.rollback()

        _SEEDED_ONCE = True
    except Exception as e:
        logger.warning(f"Seeder execution warning: {e}")
