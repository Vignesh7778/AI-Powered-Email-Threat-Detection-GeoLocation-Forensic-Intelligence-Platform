import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

logger = logging.getLogger("uvicorn.error")

import urllib.parse

def sanitize_db_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.count("@") > 1:
        scheme, rest = url.split("://", 1)
        last_at = rest.rfind("@")
        userinfo = rest[:last_at]
        hostinfo = rest[last_at + 1:]
        if ":" in userinfo:
            user, pwd = userinfo.split(":", 1)
            encoded_pwd = urllib.parse.quote(pwd)
            return f"{scheme}://{user}:{encoded_pwd}@{hostinfo}"
    return url

# Select database URL: prioritize SUPABASE_DB_URL if configured
raw_db_url = settings.SUPABASE_DB_URL if (settings.SUPABASE_DB_URL and not settings.SUPABASE_DB_URL.startswith("sqlite") and "[YOUR-PASSWORD]" not in settings.SUPABASE_DB_URL and "[YOUR_PASSWORD]" not in settings.SUPABASE_DB_URL) else settings.DATABASE_URL
db_url = sanitize_db_url(raw_db_url)

is_vercel = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
fallback_sqlite = "sqlite:////tmp/email_threat_intel.db" if is_vercel else "sqlite:///./data/email_threat_intel.db"

# Force /tmp database on Vercel only if SQLite fallback is explicitly active
if is_vercel and db_url.startswith("sqlite"):
    db_url = fallback_sqlite

def build_engine(url: str):
    c_args = {}
    engine_kwargs = {"echo": False}
    if url.startswith("sqlite"):
        c_args = {"check_same_thread": False}
        db_path = url.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception:
                pass
        try:
            target_storage = "/tmp/storage" if is_vercel else settings.STORAGE_PATH
            os.makedirs(target_storage, exist_ok=True)
        except Exception:
            pass
    elif url.startswith("postgresql"):
        c_args = {"connect_timeout": 10}
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300
    return create_engine(url, connect_args=c_args, **engine_kwargs)

# Try Supabase PostgreSQL connection; fallback if password placeholder or connection issue
engine = None
if "[YOUR-PASSWORD]" in db_url or "YOUR_ACTUAL_PASSWORD_HERE" in db_url or "[YOUR_PASSWORD]" in db_url:
    logger.info("Supabase placeholder detected in DATABASE_URL. Using fallback SQLite database until Supabase credentials are configured.")
    engine = build_engine(fallback_sqlite)
else:
    try:
        test_engine = build_engine(db_url)
        with test_engine.connect() as conn:
            pass
        engine = test_engine
        if not db_url.startswith("sqlite"):
            logger.info("🛡️ Successfully connected to Supabase PostgreSQL database!")
    except Exception as e:
        logger.warning(f"Could not connect to database ({e}). Falling back to SQLite.")
        engine = build_engine(fallback_sqlite)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    try:
        from backend.app.models import models
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Error initializing DB tables: {e}")

# Auto-initialize tables on module load
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
