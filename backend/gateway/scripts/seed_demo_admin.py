"""Create the local demo administrator used by the AI EMIL frontend.

This script is intentionally explicit: demo credentials are never created as
part of normal application startup or production deployments.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.models import User  # noqa: E402
from app.services.auth import get_password_hash  # noqa: E402


DEMO_EMAIL = "admin@aiemil.demo"
DEMO_PASSWORD = "AIEMIL-Demo-2026!"
DEMO_TENANT = "demo-tenant"


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                hashed_password=get_password_hash(DEMO_PASSWORD),
                role="admin",
                department="Security Operations",
                tenant_id=DEMO_TENANT,
                mfa_enabled=False,
                mfa_enforced=False,
                is_active=True,
            )
            db.add(user)
            db.commit()
            print(f"Created demo admin: {DEMO_EMAIL}")
        else:
            print(f"Demo admin already exists: {DEMO_EMAIL}")
        print(f"Tenant: {DEMO_TENANT}")
        print(f"Password: {DEMO_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
