"""
Configuration management for the Text-to-SQL service.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google AI API Configuration
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    
    # PostgreSQL Cache Database Configuration
    postgres_uri: str = Field(..., env="POSTGRES_URI")
    
    # Target Database Configuration (for SQL execution)
    target_db_uri: Optional[str] = Field(None, env="TARGET_DB_URI")
    
    # Vector similarity threshold for cache lookup
    similarity_threshold: float = Field(0.8, env="SIMILARITY_THRESHOLD")
    
    # Database schema
    db_schema: str = Field("public", env="DB_SCHEMA")
    
    # Flask configuration
    flask_debug: bool = Field(False, env="FLASK_DEBUG")
    flask_host: str = Field("0.0.0.0", env="FLASK_HOST")
    flask_port: int = Field(5000, env="FLASK_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings instance."""
    return settings