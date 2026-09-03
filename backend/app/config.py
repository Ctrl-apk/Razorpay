from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database — defaults to SQLite for zero-config local dev
    database_url: str = "sqlite:///./incident_investigator.db"

    # Application
    debug: bool = False
    demo_mode: bool = True
    log_level: str = "INFO"
    secret_key: str = "change-this-in-production"

    # AI Provider
    ai_provider: str = "stub"  # openai, anthropic, stub
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # GitHub
    github_token: Optional[str] = None

    # Webhook secrets
    razorpay_webhook_secret: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
