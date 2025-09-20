"""
Configuration management for the Text-to-SQL service.
Handles environment variables and application settings.

Database Architecture:
- METADATA_DATABASE_URL: Stores application metadata (vectorization jobs, table configs, etc.)
- TARGET_DB_URI: The database we generate SQL queries against
- ChromaDB: Vector storage for query caching and similarity search
"""

import os

from pydantic import SecretStr


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Load environment variables from .env file if it exists
        if os.path.exists(".env"):
            from dotenv import load_dotenv

            load_dotenv()

        # Google AI API Configuration - support both old and new names
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        self.GOOGLE_API_KEY = SecretStr(api_key)

        # ChromaDB Configuration
        self.CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
        self.CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
        self.CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "sql_queries")
        self.CHROMA_PERSIST_DIRECTORY = os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./chroma_data"
        )

        # Metadata Database Configuration (for storing vectorization jobs, table configs, etc.)
        self.METADATA_DATABASE_URL = os.getenv(
            "METADATA_DATABASE_URL",
            "postgresql://user:password@localhost:5432/text_to_sql_metadata",
        )
        self.SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

        # Target Database Configuration (the database we generate SQL queries against)
        self.TARGET_DB_URI = os.getenv("TARGET_DB_URI")

        # Vector similarity threshold for cache lookup
        self.SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))

        # Database schema
        self.DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

        # Flask configuration
        self.FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
        self.FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
        self.FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

        # CSRF Protection
        self.CSRF_SECRET = os.getenv("CSRF_SECRET", "")
        if not self.CSRF_SECRET:
            print("WARNING: CSRF_SECRET not set. CSRF protection will be disabled.")

        # CORS Configuration
        self.CORS_ORIGINS = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
            ).split(",")
            if origin.strip()
        ]
        self.CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.CORS_HEADERS = ["Content-Type", "Authorization", "X-CSRFToken"]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings instance."""
    return settings
