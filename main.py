"""
Main entry point for the Text-to-SQL API service.
"""

from src.api.server import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)