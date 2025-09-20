"""
Database initialization and session management for SQLAlchemy.

This module handles the SQLAlchemy engine, session factory, and
database connection management for the vectorization metadata system.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings
from src.database.models import Base


class DatabaseManager:
    """
    Manages SQLAlchemy database connections and sessions.
    """

    def __init__(self):
        self.settings = get_settings()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database engine and session factory."""
        # Create engine with appropriate settings
        engine_kwargs: Dict[str, Any] = {
            "echo": self.settings.SQLALCHEMY_ECHO,
            "pool_pre_ping": True,  # Verify connections before use
        }

        # Special handling for SQLite
        if self.settings.METADATA_DATABASE_URL.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "poolclass": StaticPool,
                    "connect_args": {"check_same_thread": False, "timeout": 20},
                }
            )
        else:
            # For PostgreSQL, MySQL, etc.
            engine_kwargs.update(
                {
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_timeout": 30,
                    "pool_recycle": 3600,  # Recycle connections every hour
                }
            )

        self.engine = create_engine(
            self.settings.METADATA_DATABASE_URL, **engine_kwargs
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def create_tables(self):
        """Create all tables defined in models."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db_manager.session_scope() as session:
                # Your database operations here
                pass
        """
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            if self.engine is None:
                return False
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

    def close(self):
        """Close the database engine."""
        if self.engine:
            self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def get_db_session() -> Session:
    """Get a new database session (remember to close it!)."""
    return db_manager.get_session()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.

    Usage:
        with get_db_session_context() as session:
            # Your database operations here
            pass
    """
    with db_manager.session_scope() as session:
        yield session


def init_database():
    """Initialize the database by creating all tables."""
    try:
        print("Creating database tables...")
        db_manager.create_tables()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False


def test_database_connection() -> bool:
    """Test the database connection."""
    return db_manager.test_connection()


# Database utilities for common operations


def get_or_create(session: Session, model, **kwargs):
    """
    Get an existing instance or create a new one.

    Args:
        session: Database session
        model: SQLAlchemy model class
        **kwargs: Fields to match/create with

    Returns:
        tuple: (instance, created_bool)
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()  # Get the ID without committing
        return instance, True


def safe_delete(session: Session, instance):
    """
    Safely delete an instance with error handling.

    Args:
        session: Database session
        instance: SQLAlchemy model instance to delete

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        session.delete(instance)
        session.flush()
        return True
    except Exception as e:
        print(f"Error deleting instance: {e}")
        session.rollback()
        return False


def bulk_insert(session: Session, model, data_list: list):
    """
    Efficiently insert multiple records.

    Args:
        session: Database session
        model: SQLAlchemy model class
        data_list: List of dictionaries with model data

    Returns:
        int: Number of records inserted
    """
    try:
        session.bulk_insert_mappings(model, data_list)
        session.flush()
        return len(data_list)
    except Exception as e:
        print(f"Error in bulk insert: {e}")
        session.rollback()
        return 0
