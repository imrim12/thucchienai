"""
Column configuration model for detailed column settings.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .table_config import TableConfig


class ColumnConfig(Base):
    """
    Detailed configuration for individual columns.
    """
    __tablename__ = "column_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("table_configs.id"), nullable=False)
    column_name: Mapped[str] = mapped_column(String(100), nullable=False)
    column_type: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., 'varchar', 'text', 'int', etc.
    
    # Vectorization settings
    should_vectorize: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    embedding_weight: Mapped[float] = mapped_column(Float, default=1.0)  # Weight for this column in the final embedding
    
    # Processing options
    preprocessing_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)  # Cleaning, normalization, etc.
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    table_config = relationship("TableConfig", back_populates="column_configs")

    def __repr__(self) -> str:
        return f"<ColumnConfig(column='{self.column_name}', vectorize={self.should_vectorize})>"