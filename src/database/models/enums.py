"""
Enums used across database models.
"""

from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"


class VectorizationStrategy(str, Enum):
    """Strategies for vectorizing table data."""

    SINGLE_COLUMN = "single_column"  # Vectorize individual columns
    CONCATENATED = "concatenated"  # Combine multiple columns
    WEIGHTED_COMBINATION = "weighted"  # Weighted combination of columns
    SEMANTIC_CHUNKS = "semantic_chunks"  # Split large text into semantic chunks


class VectorizationStatus(str, Enum):
    """Status of vectorization jobs."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
