import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    PROJECT_NAME: str = "TraceX — AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform"
    PROJECT_SLUG: str = "tracex"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENV: str = "development"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Security & Auth
    JWT_SECRET: str = "super-secret-key-change-in-production-26106-sih"
    JWT_REFRESH_SECRET: str = "super-refresh-key-change-in-production-26106-sih"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database Configuration (Supabase PostgreSQL / SQLite fallback)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_HOST: Optional[str] = None
    SUPABASE_PORT: Optional[int] = 5432
    SUPABASE_DB: Optional[str] = "postgres"
    SUPABASE_USER: Optional[str] = "postgres"
    SUPABASE_PASSWORD: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None
    DATABASE_URL: str = "sqlite:///./data/email_threat_intel.db"

    # Storage
    STORAGE_PATH: str = "/tmp/storage" if (os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")) else "./data/storage"
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Groq AI Intelligence & Reasoning
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Real-Time External Services & Timeouts
    MOCK_EXTERNAL_SERVICES: bool = False  # STRICT ZERO-HALLUCINATION / REAL DATA
    GEOIP_TIMEOUT: float = 3.0
    DNS_TIMEOUT: float = 2.5
    THREAT_INTEL_PROVIDER: str = "dnsbl_live"

    # Webhooks & Pipeline
    PIPELINE_BASE_URL: str = "http://127.0.0.1:8000"
    PIPELINE_SHARED_SECRET: str = "sih2026-pipeline-hmac-secret"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]

settings = Settings()
