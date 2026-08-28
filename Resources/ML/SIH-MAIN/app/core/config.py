from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI/ML Fraud Classification Engine"
    API_V1_STR: str = "/ml"
    VERSION: str = "4.1.0"
    NLP_MODEL_VERSION: str = "v2.3.1"
    CLASSIFIER_MODEL_VERSION: str = "v4.1.0"
    ATTACHMENT_SCANNER_VERSION: str = "v1.2.0"
    
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        case_sensitive = True

settings = Settings()

