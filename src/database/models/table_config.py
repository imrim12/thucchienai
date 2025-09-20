"""
Table configuration model for vectorization settings.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .database_connection import DatabaseConnection
    from .column_config import ColumnConfig
    from .vectorization_job import VectorizationJob


class TableConfig(Base):
    """
    Configuration for which tables to vectorize and how.
    """
    __tablename__ = "table_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    database_connection_id: Mapped[int] = mapped_column(Integer, ForeignKey("database_connections.id"), nullable=False)
    
    # Table identification
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    schema_name: Mapped[Optional[str]] = mapped_column(String(100))  # For databases that support schemas
    
    # Vectorization settings
    vectorization_strategy: Mapped[str] = mapped_column(String(50), default="full_table", nullable=False)  # VectorizationStrategy enum
    batch_size: Mapped[int] = mapped_column(Integer, default=1000)
    chunk_size: Mapped[Optional[int]] = mapped_column(Integer)  # For text chunking
    
    # ChromaDB settings
    chromadb_collection_name: Mapped[Optional[str]] = mapped_column(String(100))
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-ada-002", nullable=False)
    
    # Processing options
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_update: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Auto-reprocess on data changes
    update_frequency: Mapped[Optional[str]] = mapped_column(String(20))  # daily, weekly, monthly
    
    # Custom processing settings (JSON)
    processing_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Custom options, filters, etc.
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    database_connection = relationship("DatabaseConnection", back_populates="table_configs")
    column_configs = relationship("ColumnConfig", back_populates="table_config", cascade="all, delete-orphan")
    vectorization_jobs = relationship("VectorizationJob", back_populates="table_config", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TableConfig(table='{self.table_name}', strategy='{self.vectorization_strategy}')>"