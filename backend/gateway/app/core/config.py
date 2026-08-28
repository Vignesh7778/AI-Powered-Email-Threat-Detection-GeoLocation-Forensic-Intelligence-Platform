import os
from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_file():
    possible_path = Path(__file__).resolve().parents[4] / "md" / ".env"
    return possible_path if possible_path.exists() else None


def _resolve_storage_dir():
    # If running in Vercel serverless environment or read-only filesystem
    if os.environ.get("VERCEL"):
        return "/tmp/storage"
    return str(Path(__file__).resolve().parents[3] / "storage")


def _resolve_db_url():
    # If running in Vercel serverless environment
    if os.environ.get("VERCEL"):
        return "sqlite:////tmp/gateway.db"
    return "sqlite:///" + str(Path(__file__).resolve().parents[3] / "gateway.db")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "Email Threat Gateway API"
    version: str = "1.0.0"

    # External service URLs from md/.env or Vercel Environment Variables
    forensic_api: str = Field(
        default="https://sih-nine-flax.vercel.app",
        validation_alias=AliasChoices("FORENSIC_API", "PIPELINE_FORENSIC_API"),
    )
    ml_api: str = Field(
        default="https://email-validation-micro-service.vercel.app",
        validation_alias=AliasChoices("ML_API", "PIPELINE_ML_API"),
    )

    # JWT config
    secret_key: str = "super-secret-change-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Pipeline webhook shared secret
    pipeline_signature: str = "pipeline-shared-secret"

    # SQLite DB path
    db_url: str = Field(default_factory=_resolve_db_url)

    # Local storage for raw .eml files
    storage_dir: str = Field(default_factory=_resolve_storage_dir)


settings = Settings()
