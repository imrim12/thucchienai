"""
Flask API server for the Text-to-SQL service with CSRF protection and CORS security.
"""

import hashlib
import hmac
import secrets
import time
import traceback
from typing import Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

from src.agents.text_to_sql import TextToSQLService
from src.api.vectorization_endpoints import register_vectorization_blueprint
from src.core.config import get_settings


class CSRFValidator:
    """Custom CSRF token validator."""

    def __init__(self, secret_key: str):
        self.secret_key = (
            secret_key.encode() if isinstance(secret_key, str) else secret_key
        )

    def generate_token(self, session_id: Optional[str] = None) -> str:
        """Generate a CSRF token."""
        if not session_id:
            session_id = secrets.token_urlsafe(32)

        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key, message.encode(), hashlib.sha256
        ).hexdigest()

        return f"{session_id}:{timestamp}:{signature}"

    def validate_token(self, token: str, max_age: int = 3600) -> bool:
        """Validate a CSRF token."""
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False

            session_id, timestamp, signature = parts

            # Check timestamp
            token_time = int(timestamp)
            if time.time() - token_time > max_age:
                return False

            # Verify signature
            message = f"{session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key, message.encode(), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except (ValueError, TypeError):
            return False


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    settings = get_settings()

    # Configure Flask secret key for sessions
    app.secret_key = settings.CSRF_SECRET or secrets.token_urlsafe(32)

    # Configure CORS with restricted origins and headers
    CORS(
        app,
        origins=settings.CORS_ORIGINS,
        methods=settings.CORS_METHODS,
        allow_headers=settings.CORS_HEADERS,
        supports_credentials=True,
    )

    # Initialize CSRF protection if secret is provided
    csrf_validator = None
    if settings.CSRF_SECRET:
        csrf_validator = CSRFValidator(settings.CSRF_SECRET)
        print("CSRF protection enabled")
    else:
        print(
            "WARNING: CSRF protection disabled - set CSRF_SECRET environment variable"
        )

    def validate_csrf_token():
        """Validate CSRF token for POST requests."""
        if not csrf_validator:
            return True  # Skip validation if CSRF is not configured

        if request.method in ["POST", "PUT", "DELETE"]:
            csrf_token = request.headers.get("X-CSRFToken") or request.form.get(
                "csrf_token"
            )
            if not csrf_token:
                return False
            return csrf_validator.validate_token(csrf_token)
        return True

    # Register vectorization endpoints
    register_vectorization_blueprint(app)

    # Initialize the Text-to-SQL service
    try:
        text_to_sql_service = TextToSQLService()
        print("Text-to-SQL service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Text-to-SQL service: {e}")
        text_to_sql_service = None

    @app.route("/api/csrf-token", methods=["GET"])
    def get_csrf_token():
        """Get CSRF token for client-side requests."""
        if not csrf_validator:
            return jsonify({"error": "CSRF protection not configured"}), 503

        token = csrf_validator.generate_token()
        return jsonify({"csrf_token": token}), 200

    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        if text_to_sql_service is None:
            return jsonify(
                {"status": "error", "message": "Service not initialized"}
            ), 503

        try:
            health_status = text_to_sql_service.health_check()
            return jsonify(
                {
                    "status": "healthy",
                    "components": health_status,
                    "csrf_enabled": csrf_validator is not None,
                }
            ), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/text-to-sql", methods=["POST"])
    def text_to_sql():
        """
        Convert natural language question to SQL query.

        Expected JSON payload:
        {
            "question": "your natural language question here",
            "readonly": false  // optional, defaults to false
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "sql_query": "generated SQL query" or "",
            "from_cache": boolean,
            "similarity_score": number (if from cache),
            "cached_question": string (if from cache),
            "cache_stats": object,
            "is_valid": boolean
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "question" not in data:
                return jsonify({"error": "Missing 'question' field in request"}), 400

            question = data["question"]
            readonly = data.get("readonly", False)  # Default to False

            if not question or not question.strip():
                return jsonify({"error": "Question cannot be empty"}), 400

            # Validate readonly parameter
            if not isinstance(readonly, bool):
                return jsonify({"error": "'readonly' must be a boolean"}), 400

            # Process the question
            result = text_to_sql_service.process_question(question.strip(), readonly)

            return jsonify(result), 200

        except Exception as e:
            print(f"Error in text-to-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/execute-sql", methods=["POST"])
    def execute_sql():
        """
        Execute SQL query against the target database.

        Expected JSON payload:
        {
            "sql_query": "SELECT * FROM table_name"
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "success": boolean,
            "result": query results (if successful),
            "error": error message (if failed),
            "query": the executed query
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "sql_query" not in data:
                return jsonify({"error": "Missing 'sql_query' field in request"}), 400

            sql_query = data["sql_query"]

            if not sql_query or not sql_query.strip():
                return jsonify({"error": "SQL query cannot be empty"}), 400

            # Execute the SQL query
            result = text_to_sql_service.execute_sql(sql_query.strip())

            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify(result), 400

        except Exception as e:
            print(f"Error in execute-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/text-to-sql-and-execute", methods=["POST"])
    def text_to_sql_and_execute():
        """
        Convert natural language to SQL and execute it in one step.

        Expected JSON payload:
        {
            "question": "your natural language question here",
            "readonly": false  // optional, defaults to false
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "sql_query": "generated SQL query",
            "from_cache": boolean,
            "similarity_score": number (if from cache),
            "execution_result": execution results,
            "success": boolean,
            "is_valid": boolean
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "question" not in data:
                return jsonify({"error": "Missing 'question' field in request"}), 400

            question = data["question"]
            readonly = data.get("readonly", False)  # Default to False

            if not question or not question.strip():
                return jsonify({"error": "Question cannot be empty"}), 400

            # Validate readonly parameter
            if not isinstance(readonly, bool):
                return jsonify({"error": "'readonly' must be a boolean"}), 400

            # Convert to SQL
            sql_result = text_to_sql_service.process_question(
                question.strip(), readonly
            )
            sql_query = sql_result["sql_query"]

            # Check if SQL is valid before execution
            if not sql_result["is_valid"] or not sql_query:
                return jsonify(
                    {
                        "sql_query": sql_query,
                        "from_cache": sql_result["from_cache"],
                        "similarity_score": sql_result.get("similarity_score"),
                        "cached_question": sql_result.get("cached_question"),
                        "execution_result": {
                            "success": False,
                            "error": "Invalid SQL generated",
                        },
                        "success": False,
                        "is_valid": False,
                    }
                ), 400

            # Execute SQL
            execution_result = text_to_sql_service.execute_sql(sql_query)

            # Combine results
            response = {
                "sql_query": sql_query,
                "from_cache": sql_result["from_cache"],
                "similarity_score": sql_result.get("similarity_score"),
                "cached_question": sql_result.get("cached_question"),
                "execution_result": execution_result,
                "success": execution_result["success"],
                "is_valid": sql_result["is_valid"],
            }

            status_code = 200 if execution_result["success"] else 400
            return jsonify(response), status_code

        except Exception as e:
            print(f"Error in text-to-sql-and-execute endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/explain-sql", methods=["POST"])
    def explain_sql():
        """
        Generate natural language explanation of SQL query.

        Expected JSON payload:
        {
            "sql_query": "SELECT * FROM users WHERE age > 25"
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "explanation": "This query retrieves all columns from the users table..."
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "sql_query" not in data:
                return jsonify({"error": "Missing 'sql_query' field in request"}), 400

            sql_query = data["sql_query"]

            if not sql_query or not sql_query.strip():
                return jsonify({"error": "SQL query cannot be empty"}), 400

            # Generate explanation
            explanation = text_to_sql_service.explain_sql(sql_query.strip())

            return jsonify({"explanation": explanation}), 200

        except Exception as e:
            print(f"Error in explain-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/validate-sql-with-llm", methods=["POST"])
    def validate_sql_with_llm():
        """
        Validate and potentially correct SQL using LLM.

        Expected JSON payload:
        {
            "sql_query": "SELCT * FROM users",  // potentially incorrect SQL
            "readonly": true  // optional, defaults to false
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "is_valid": boolean,
            "corrected_sql": "corrected SQL or original if valid",
            "explanation": "explanation of validation result"
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "sql_query" not in data:
                return jsonify({"error": "Missing 'sql_query' field in request"}), 400

            sql_query = data["sql_query"]
            readonly = data.get("readonly", False)

            if not sql_query or not sql_query.strip():
                return jsonify({"error": "SQL query cannot be empty"}), 400

            # Validate readonly parameter
            if not isinstance(readonly, bool):
                return jsonify({"error": "'readonly' must be a boolean"}), 400

            # Perform LLM validation
            result = text_to_sql_service.validate_sql_with_llm(
                sql_query.strip(), readonly
            )

            return jsonify(result), 200

        except Exception as e:
            print(f"Error in validate-sql-with-llm endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/validate-sql", methods=["POST"])
    def validate_sql():
        """
        Validate SQL query syntax and readonly constraints.

        Expected JSON payload:
        {
            "sql_query": "SELECT * FROM users; DROP TABLE users;",
            "readonly": true
        }

        Headers:
        X-CSRFToken: <csrf_token>  // required if CSRF is enabled

        Returns:
        {
            "is_valid": boolean,
            "cleaned_sql": "cleaned SQL or empty string",
            "is_select_only": boolean,
            "passed_readonly_check": boolean
        }
        """
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            # Validate request
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400

            data = request.get_json()

            if not data or "sql_query" not in data:
                return jsonify({"error": "Missing 'sql_query' field in request"}), 400

            sql_query = data["sql_query"]
            readonly = data.get("readonly", False)

            if not sql_query or not sql_query.strip():
                return jsonify({"error": "SQL query cannot be empty"}), 400

            # Validate readonly parameter
            if not isinstance(readonly, bool):
                return jsonify({"error": "'readonly' must be a boolean"}), 400

            # Perform validation
            cleaned_sql = text_to_sql_service.validator.validate_and_clean_sql(
                sql_query, readonly
            )
            is_valid = bool(cleaned_sql)
            is_select_only = text_to_sql_service.validator.is_select_only(sql_query)
            passed_readonly_check = not readonly or is_select_only

            return jsonify(
                {
                    "is_valid": is_valid,
                    "cleaned_sql": cleaned_sql,
                    "is_select_only": is_select_only,
                    "passed_readonly_check": passed_readonly_check,
                }
            ), 200

        except Exception as e:
            print(f"Error in validate-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/cache/stats", methods=["GET"])
    def cache_stats():
        """Get cache statistics."""
        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            stats = text_to_sql_service.get_cache_statistics()
            return jsonify(stats), 200
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.route("/api/cache/clear", methods=["POST"])
    def clear_cache():
        """Clear the cache."""
        # Validate CSRF token
        if not validate_csrf_token():
            return jsonify({"error": "Invalid or missing CSRF token"}), 403

        if text_to_sql_service is None:
            return jsonify({"error": "Service not initialized"}), 503

        try:
            success = text_to_sql_service.clear_cache()
            if success:
                return jsonify({"message": "Cache cleared successfully"}), 200
            else:
                return jsonify({"error": "Failed to clear cache"}), 500
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return jsonify({"error": "Internal server error", "message": str(e)}), 500

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors."""
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500

    return app


# Create the app instance for imports
app = create_app()

if __name__ == "__main__":
    # For development purposes only
    settings = get_settings()
    app.run(
        host=settings.FLASK_HOST, port=settings.FLASK_PORT, debug=settings.FLASK_DEBUG
    )
