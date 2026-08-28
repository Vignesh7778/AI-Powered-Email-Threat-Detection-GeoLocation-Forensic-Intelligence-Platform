from pathlib import Path
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / "md" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    project_name: str = "Email Threat Analysis Pipeline"
    version: str = "0.1.0"
    forensic_api: str = Field(validation_alias=AliasChoices("FORENSIC_API", "PIPELINE_FORENSIC_API"))
    ml_api: str = Field(validation_alias=AliasChoices("ML_API", "PIPELINE_ML_API"))
    protected_domains: list[str] = Field(
        default_factory=lambda: ["aicte.org", "microsoft.com", "paypal.com", "google.com"]
    )
    trusted_relay_ranges: list[str] = Field(default_factory=lambda: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"])

settings = Settings()
