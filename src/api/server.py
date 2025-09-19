"""
Flask API server for the Text-to-SQL service.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import Dict, Any
import traceback

from src.services.text_to_sql_service import TextToSQLService
from src.core.config import get_settings


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize the Text-to-SQL service
    try:
        text_to_sql_service = TextToSQLService()
        print("Text-to-SQL service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Text-to-SQL service: {e}")
        text_to_sql_service = None
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        if text_to_sql_service is None:
            return jsonify({
                "status": "error",
                "message": "Service not initialized"
            }), 503
        
        try:
            health_status = text_to_sql_service.health_check()
            return jsonify({
                "status": "healthy",
                "components": health_status
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @app.route('/api/text-to-sql', methods=['POST'])
    def text_to_sql():
        """
        Convert natural language question to SQL query.
        
        Expected JSON payload:
        {
            "question": "your natural language question here"
        }
        
        Returns:
        {
            "sql_query": "generated SQL query",
            "from_cache": boolean,
            "similarity_score": number (if from cache),
            "cached_question": string (if from cache),
            "cache_stats": object
        }
        """
        if text_to_sql_service is None:
            return jsonify({
                "error": "Service not initialized"
            }), 503
        
        try:
            # Validate request
            if not request.is_json:
                return jsonify({
                    "error": "Request must be JSON"
                }), 400
            
            data = request.get_json()
            
            if not data or 'question' not in data:
                return jsonify({
                    "error": "Missing 'question' field in request"
                }), 400
            
            question = data['question']
            
            if not question or not question.strip():
                return jsonify({
                    "error": "Question cannot be empty"
                }), 400
            
            # Process the question
            result = text_to_sql_service.process_question(question.strip())
            
            return jsonify(result), 200
            
        except Exception as e:
            print(f"Error in text-to-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    
    @app.route('/api/execute-sql', methods=['POST'])
    def execute_sql():
        """
        Execute SQL query against the target database.
        
        Expected JSON payload:
        {
            "sql_query": "SELECT * FROM table_name"
        }
        
        Returns:
        {
            "success": boolean,
            "result": query results (if successful),
            "error": error message (if failed),
            "query": the executed query
        }
        """
        if text_to_sql_service is None:
            return jsonify({
                "error": "Service not initialized"
            }), 503
        
        try:
            # Validate request
            if not request.is_json:
                return jsonify({
                    "error": "Request must be JSON"
                }), 400
            
            data = request.get_json()
            
            if not data or 'sql_query' not in data:
                return jsonify({
                    "error": "Missing 'sql_query' field in request"
                }), 400
            
            sql_query = data['sql_query']
            
            if not sql_query or not sql_query.strip():
                return jsonify({
                    "error": "SQL query cannot be empty"
                }), 400
            
            # Execute the SQL query
            result = text_to_sql_service.execute_sql(sql_query.strip())
            
            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400
            
        except Exception as e:
            print(f"Error in execute-sql endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    
    @app.route('/api/text-to-sql-and-execute', methods=['POST'])
    def text_to_sql_and_execute():
        """
        Convert natural language to SQL and execute it in one step.
        
        Expected JSON payload:
        {
            "question": "your natural language question here"
        }
        
        Returns:
        {
            "sql_query": "generated SQL query",
            "from_cache": boolean,
            "similarity_score": number (if from cache),
            "execution_result": execution results,
            "success": boolean
        }
        """
        if text_to_sql_service is None:
            return jsonify({
                "error": "Service not initialized"
            }), 503
        
        try:
            # Validate request
            if not request.is_json:
                return jsonify({
                    "error": "Request must be JSON"
                }), 400
            
            data = request.get_json()
            
            if not data or 'question' not in data:
                return jsonify({
                    "error": "Missing 'question' field in request"
                }), 400
            
            question = data['question']
            
            if not question or not question.strip():
                return jsonify({
                    "error": "Question cannot be empty"
                }), 400
            
            # Convert to SQL
            sql_result = text_to_sql_service.process_question(question.strip())
            sql_query = sql_result['sql_query']
            
            # Execute SQL
            execution_result = text_to_sql_service.execute_sql(sql_query)
            
            # Combine results
            response = {
                "sql_query": sql_query,
                "from_cache": sql_result['from_cache'],
                "similarity_score": sql_result.get('similarity_score'),
                "cached_question": sql_result.get('cached_question'),
                "execution_result": execution_result,
                "success": execution_result['success']
            }
            
            status_code = 200 if execution_result['success'] else 400
            return jsonify(response), status_code
            
        except Exception as e:
            print(f"Error in text-to-sql-and-execute endpoint: {e}")
            print(traceback.format_exc())
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    
    @app.route('/api/cache/stats', methods=['GET'])
    def cache_stats():
        """Get cache statistics."""
        if text_to_sql_service is None:
            return jsonify({
                "error": "Service not initialized"
            }), 503
        
        try:
            stats = text_to_sql_service.get_cache_statistics()
            return jsonify(stats), 200
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear the cache."""
        if text_to_sql_service is None:
            return jsonify({
                "error": "Service not initialized"
            }), 503
        
        try:
            success = text_to_sql_service.clear_cache()
            if success:
                return jsonify({"message": "Cache cleared successfully"}), 200
            else:
                return jsonify({"error": "Failed to clear cache"}), 500
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return jsonify({
                "error": "Internal server error",
                "message": str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            "error": "Endpoint not found"
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 errors."""
        return jsonify({
            "error": "Method not allowed"
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            "error": "Internal server error"
        }), 500
    
    return app


if __name__ == "__main__":
    # For development purposes only
    app = create_app()
    settings = get_settings()
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug
    )