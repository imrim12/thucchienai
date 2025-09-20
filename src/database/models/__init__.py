"""
Database models for the vectorization system.

This package contains all SQLAlchemy models for managing database vectorization:
- DatabaseConnection: Store external database connections
- TableConfig: Configure table vectorization settings
- ColumnConfig: Detailed column configurations
- VectorizationJob: Track processing jobs and status
"""

# Import the base
from .base import Base

# Import enums
from .enums import DatabaseType, VectorizationStrategy, VectorizationStatus

# Import all models
from .database_connection import DatabaseConnection
from .table_config import TableConfig
from .column_config import ColumnConfig
from .vectorization_job import VectorizationJob

# Utility functions
from typing import List, Optional
from sqlalchemy.orm import Session


def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def get_active_database_connections(session: Session) -> List[DatabaseConnection]:
    """Get all active database connections."""
    return session.query(DatabaseConnection).filter(DatabaseConnection.is_active == True).all()


def get_enabled_table_configs(session: Session, database_connection_id: Optional[int] = None) -> List[TableConfig]:
    """Get all enabled table configurations."""
    query = session.query(TableConfig).filter(TableConfig.is_enabled == True)
    if database_connection_id:
        query = query.filter(TableConfig.database_connection_id == database_connection_id)
    return query.all()


def get_vectorizable_columns(session: Session, table_config_id: int) -> List[ColumnConfig]:
    """Get all columns marked for vectorization in a table."""
    return (session.query(ColumnConfig)
            .filter(ColumnConfig.table_config_id == table_config_id)
            .filter(ColumnConfig.should_vectorize == True)
            .all())


def get_pending_jobs(session: Session) -> List[VectorizationJob]:
    """Get all pending vectorization jobs."""
    return (session.query(VectorizationJob)
            .filter(VectorizationJob.status == VectorizationStatus.PENDING)
            .all())


__all__ = [
    'Base',
    'DatabaseType',
    'VectorizationStrategy', 
    'VectorizationStatus',
    'DatabaseConnection',
    'TableConfig',
    'ColumnConfig',
    'VectorizationJob',
    'create_tables',
    'get_active_database_connections',
    'get_enabled_table_configs',
    'get_vectorizable_columns',
    'get_pending_jobs'
]