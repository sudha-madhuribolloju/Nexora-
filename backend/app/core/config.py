import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Nexora AI Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS Configuration
    # Store as a comma-separated string to avoid Pydantic Settings JSON parsing errors
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """
        Helper property to parse the comma-separated CORS origins into a list of strings.
        """
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    # Security Configuration
    JWT_SECRET: str = "default_secret_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFICATION_REQUIRED: bool = False


   

    # PostgreSQL Direct Link
    DATABASE_URL: str

    # Future Ready Integrations
    REDIS_URL: str = "redis://localhost:6379/0"
    GOOGLE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Load configuration from .env file
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
