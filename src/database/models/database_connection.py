"""
Database connection model for managing external database connections.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    pass


class DatabaseConnection(Base):
    """
    Stores connection information for source databases.
    """

    __tablename__ = "database_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Connection details
    db_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # DatabaseType enum
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Should be encrypted

    # Additional connection parameters (JSON)
    connection_params: Mapped[Optional[dict]] = mapped_column(
        JSON
    )  # SSL, timeout, etc.

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_tested: Mapped[Optional[datetime]] = mapped_column(DateTime)
    test_status: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # ConnectionStatus enum

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    table_configs = relationship(
        "TableConfig",
        back_populates="database_connection",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DatabaseConnection(name='{self.name}', type='{self.db_type}')>"

    @property
    def connection_string(self) -> str:
        """Generate connection string for the database."""
        return f"{self.db_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
