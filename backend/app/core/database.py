import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("uvicorn.error")

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

fallback_sqlite = "sqlite:///./data/email_threat_intel.db"

def build_engine(url: str):
    c_args = {}
    if url.startswith("sqlite"):
        c_args = {"check_same_thread": False}
        os.makedirs("./data", exist_ok=True)
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    return create_engine(url, connect_args=c_args, echo=False)

# Try Supabase PostgreSQL connection; fallback if password placeholder or connection issue
engine = None
if "[YOUR-PASSWORD]" in db_url or "YOUR_ACTUAL_PASSWORD_HERE" in db_url:
    logger.info("Supabase placeholder detected in DATABASE_URL. Using SQLite database until Supabase password is provided.")
    engine = build_engine(fallback_sqlite)
else:
    try:
        test_engine = build_engine(db_url)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        logger.info("Successfully connected to Supabase PostgreSQL database!")
    except Exception as e:
        logger.warning(f"Could not connect to Supabase PostgreSQL ({e}). Falling back to SQLite.")
        engine = build_engine(fallback_sqlite)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        from backend.app.models import models
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error initializing DB tables: {e}")

# Auto-initialize tables
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
