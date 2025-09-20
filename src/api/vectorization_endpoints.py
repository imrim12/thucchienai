"""
API endpoints for database vectorization management.

This module provides REST endpoints for:
- Discovering database schemas
- Configuring vectorization settings
- Managing vectorization jobs
- Searching vectorized content
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import logging

from src.services.discovery_service import DatabaseDiscoveryService
from src.services.vectorization_service import VectorizationService
from src.database.database import get_db_session_context, init_database
from src.database.models import DatabaseConnection, TableConfig, VectorizationJob

logger = logging.getLogger(__name__)

# Create blueprint for vectorization endpoints
vectorization_bp = Blueprint('vectorization', __name__, url_prefix='/api/vectorization')

# Initialize services
discovery_service = DatabaseDiscoveryService()
vectorization_service = VectorizationService()


@vectorization_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for vectorization services."""
    try:
        # Test database connection
        from src.database.database import test_database_connection
        db_healthy = test_database_connection()
        
        return jsonify({
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "services": {
                "discovery": "available",
                "vectorization": "available",
                "chromadb": "available"
            }
        }), 200 if db_healthy else 503
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@vectorization_bp.route('/databases', methods=['POST'])
def add_database_connection():
    """Add a new database connection for vectorization."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'connection_string', 'db_type']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create database connection
        db_conn = discovery_service.create_database_connection(
            name=data['name'],
            connection_string=data['connection_string'],
            db_type=data['db_type'],
            description=data.get('description')
        )
        
        return jsonify({
            "message": "Database connection created successfully",
            "database_id": db_conn.id,
            "name": db_conn.name
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding database connection: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/databases/<int:db_id>/discover', methods=['POST'])
def discover_database_schema(db_id: int):
    """Discover the schema of a database connection."""
    try:
        summary = discovery_service.get_discovery_summary(db_id)
        return jsonify({
            "message": "Database discovery completed",
            "summary": summary
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error discovering database schema: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/databases/<int:db_id>/tables/<table_name>/configure', methods=['POST'])
def auto_configure_table(db_id: int, table_name: str):
    """Automatically configure a table for vectorization."""
    try:
        with get_db_session_context() as session:
            db_conn = session.query(DatabaseConnection).get(db_id)
            if not db_conn:
                return jsonify({"error": "Database connection not found"}), 404
            
            table_config = discovery_service.auto_configure_table(
                database_connection_id=db_id,
                table_name=table_name,
                connection_string=db_conn.connection_string
            )
            
            return jsonify({
                "message": "Table configured successfully",
                "table_config_id": table_config.id,
                "strategy": table_config.vectorization_strategy,
                "enabled": table_config.is_enabled
            }), 201
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error configuring table: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/tables/<int:table_config_id>/vectorize', methods=['POST'])
def start_vectorization(table_config_id: int):
    """Start vectorization for a configured table."""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        
        job = vectorization_service.start_vectorization_job(
            table_config_id=table_config_id,
            user_id=user_id
        )
        
        # Start processing in background (in a real app, use Celery or similar)
        # For now, we'll just return the job ID
        return jsonify({
            "message": "Vectorization job started",
            "job_id": job.id,
            "status": job.status,
            "collection_name": job.chromadb_collection_name
        }), 202
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error starting vectorization: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/jobs/<int:job_id>/process', methods=['POST'])
def process_vectorization_job(job_id: int):
    """Process a vectorization job (usually called by background worker)."""
    try:
        success = vectorization_service.process_vectorization_job(job_id)
        
        if success:
            return jsonify({
                "message": "Vectorization job completed successfully",
                "job_id": job_id
            }), 200
        else:
            return jsonify({
                "message": "Vectorization job failed",
                "job_id": job_id
            }), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error processing vectorization job: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/jobs/<int:job_id>/status', methods=['GET'])
def get_job_status(job_id: int):
    """Get the status of a vectorization job."""
    try:
        status = vectorization_service.get_job_status(job_id)
        
        if status:
            return jsonify({
                "job": status
            }), 200
        else:
            return jsonify({"error": "Job not found"}), 404
            
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/search', methods=['POST'])
def search_vectorized_content():
    """Search across vectorized content."""
    try:
        data = request.get_json()
        
        if 'query' not in data:
            return jsonify({"error": "Missing required field: query"}), 400
        
        results = vectorization_service.search_vectorized_content(
            query=data['query'],
            collection_name=data.get('collection_name'),
            top_k=data.get('top_k', 5),
            SIMILARITY_THRESHOLD=data.get('SIMILARITY_THRESHOLD', 0.7)
        )
        
        return jsonify({
            "query": data['query'],
            "results": results,
            "total_results": len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching vectorized content: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/databases', methods=['GET'])
def list_database_connections():
    """List all database connections."""
    try:
        with get_db_session_context() as session:
            connections = session.query(DatabaseConnection).filter(
                DatabaseConnection.is_active == True
            ).all()
            
            result = []
            for conn in connections:
                result.append({
                    "id": conn.id,
                    "name": conn.name,
                    "description": conn.description,
                    "db_type": conn.db_type,
                    "created_at": conn.created_at.isoformat(),
                    "table_count": len(conn.table_configs)
                })
            
            return jsonify({
                "databases": result,
                "total": len(result)
            }), 200
            
    except Exception as e:
        logger.error(f"Error listing database connections: {e}")
        return jsonify({"error": "Internal server error"}), 500


@vectorization_bp.route('/tables', methods=['GET'])
def list_table_configurations():
    """List all table configurations."""
    try:
        with get_db_session_context() as session:
            tables = session.query(TableConfig).filter(
                TableConfig.is_enabled == True
            ).all()
            
            result = []
            for table in tables:
                result.append({
                    "id": table.id,
                    "table_name": table.table_name,
                    "database_name": table.database_connection.name,
                    "strategy": table.vectorization_strategy,
                    "total_records": table.total_records,
                    "vectorized_records": table.vectorized_records,
                    "last_vectorized": table.last_vectorized.isoformat() if table.last_vectorized else None
                })
            
            return jsonify({
                "tables": result,
                "total": len(result)
            }), 200
            
    except Exception as e:
        logger.error(f"Error listing table configurations: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Initialize database tables on first import
try:
    init_database()
except Exception as e:
    logger.warning(f"Database initialization failed: {e}")


def register_vectorization_blueprint(app):
    """Register the vectorization blueprint with the Flask app."""
    app.register_blueprint(vectorization_bp)