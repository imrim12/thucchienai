"""
Configuration management for the Text-to-SQL service.
Handles environment variables and application settings.
"""

import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Load environment variables from .env file if it exists
        if os.path.exists(".env"):
            from dotenv import load_dotenv
            load_dotenv()
        
        # Google AI API Configuration - support both old and new names
        self.google_api_key = (
            os.getenv("GOOGLE_API_KEY") or 
            os.getenv("GEMINI_API_KEY") or
            ""
        )
        
        # ChromaDB Configuration
        self.chroma_collection_name = os.getenv("CHROMA_COLLECTION_NAME", "sql_queries")
        
        # Target Database Configuration (for SQL execution)
        self.target_db_uri = os.getenv("TARGET_DB_URI")
        
        # Vector similarity threshold for cache lookup
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
        
        # Database schema
        self.db_schema = os.getenv("DB_SCHEMA", "public")
        
        # Flask configuration
        self.flask_debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
        self.flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
        self.flask_port = int(os.getenv("FLASK_PORT", "5000"))


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings instance."""
    return settings