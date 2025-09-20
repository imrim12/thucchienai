"""
Vectorization job model for tracking processing status.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    pass


class VectorizationJob(Base):
    """
    Tracks the status and progress of vectorization jobs.
    """

    __tablename__ = "vectorization_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("table_configs.id"), nullable=False
    )

    # Job status
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # VectorizationStatus enum
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    # Processing metrics
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    successful_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # Detailed error information

    # ChromaDB settings
    chromadb_collection_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # User who started the job

    # Relationships
    table_config = relationship("TableConfig", back_populates="vectorization_jobs")

    def __repr__(self) -> str:
        return f"<VectorizationJob(id={self.id}, status='{self.status}', progress={self.progress_percentage}%)>"
