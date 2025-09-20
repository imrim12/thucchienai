"""
Main entry point for the Text-to-SQL API service.
"""

from src.api.server import app
from src.core.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    app.run(
        host=settings.FLASK_HOST, 
        port=settings.FLASK_PORT, 
        debug=settings.FLASK_DEBUG
    )