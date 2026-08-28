import sys
import os

PROJ_ROOT = r'c:\Users\vigne\Desktop\SIH2026\SIH_Proj\AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform Project'
if PROJ_ROOT not in sys.path:
    sys.path.insert(0, PROJ_ROOT)

from backend.app.core.database import SessionLocal, init_db
from backend.app.models.models import Submission, Case, CaseSubmission, Alert, Campaign, User
from backend.app.schemas.schemas import EmailSubmission, RawBody, SourceContext
from backend.analysis.parser.email_parser import email_parser
from backend.app.services.pipeline_orchestrator import pipeline_orchestrator

def seed():
    init_db()
    db = SessionLocal()
    try:
        sample_dir = os.path.join(PROJ_ROOT, 'datasets', 'sample_emails')
        files = ['phishing.eml', 'bec.eml', 'impersonation.eml', 'credential_phishing.eml', 'legitimate.eml']
        
        seeded_submission_ids = []

        for fname in files:
            fpath = os.path.join(sample_dir, fname)
            if not os.path.exists(fpath):
                continue
            with open(fpath, 'rb') as fp:
                file_bytes = fp.read()

            import uuid, hashlib
            from datetime import datetime, timezone
            sub_id = str(uuid.uuid4())
            sha = hashlib.sha256(file_bytes).hexdigest()
            parsed = email_parser.parse_raw_eml(file_bytes, sub_id, os.path.join(PROJ_ROOT, 'data', 'storage'))

            sub = Submission(
                submission_id=sub_id,
                tenant_id='tenant-cyber-sec-01',
                file_name=fname,
                file_size=len(file_bytes),
                sha256_hash=sha,
                sender=parsed.get('sender'),
                recipient=parsed.get('recipient'),
                subject=parsed.get('subject'),
                source='upload',
                status='analyzing',
                received_at=datetime.now(timezone.utc),
                ingested_at=datetime.now(timezone.utc)
            )
            db.add(sub)
            db.commit()

            sub_obj = EmailSubmission(
                submission_id=sub_id,
                received_at=datetime.now(timezone.utc).isoformat(),
                raw_headers=parsed['raw_headers'],
                raw_body=RawBody(
                    text_plain=parsed.get('text_plain'),
                    text_html=parsed.get('text_html')
                ),
                attachments=parsed.get('attachments', []),
                source_context=SourceContext(
                    ingested_via='upload',
                    tenant_id='tenant-cyber-sec-01'
                )
            )

            # Analyze
            assessment = pipeline_orchestrator.analyze_submission(sub_obj, db=db, actor='seed_service')
            seeded_submission_ids.append(sub_id)
            print(f"Seeded & Analyzed {fname}: Risk={assessment.risk_level}, Score={assessment.fraud_score}, Class={assessment.classification}")

        # Create demo incident cases
        if seeded_submission_ids and not db.query(Case).first():
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

            for sid in seeded_submission_ids[:3]:
                db.add(CaseSubmission(case_id=c1.case_id, submission_id=sid))
            db.commit()
            print("Created initial incident Case:", c1.case_id)

    finally:
        db.close()

if __name__ == '__main__':
    seed()
