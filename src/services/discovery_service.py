"""
Database discovery service for automatically detecting tables and columns.

This service connects to external databases and discovers their schema,
helping users configure which tables and columns to vectorize.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from src.database.database import get_db_session_context
from src.database.models import ColumnConfig, DatabaseConnection, TableConfig

logger = logging.getLogger(__name__)


class DatabaseDiscoveryService:
    """
    Service for discovering database schemas and suggesting vectorization configurations.
    """

    def __init__(self):
        self.supported_text_types = {
            "varchar",
            "char",
            "text",
            "nvarchar",
            "nchar",
            "ntext",
            "longtext",
            "mediumtext",
            "tinytext",
            "string",
            "json",
            "jsonb",
            "xml",
            "clob",
            "blob",
        }

        self.supported_numeric_types = {
            "int",
            "integer",
            "bigint",
            "smallint",
            "tinyint",
            "decimal",
            "numeric",
            "float",
            "double",
            "real",
            "money",
            "smallmoney",
        }

    def discover_database_schema(
        self, connection_string: str, database_type: str
    ) -> Dict[str, Any]:
        """
        Discover the complete schema of a database.

        Args:
            connection_string: Database connection string
            database_type: Type of database (postgresql, mysql, etc.)

        Returns:
            Dictionary containing schema information
        """
        try:
            # Create temporary engine for discovery
            engine = create_engine(connection_string)
            inspector = inspect(engine)

            schema_info = {
                "database_type": database_type,
                "tables": [],
                "total_tables": 0,
                "discoverable_tables": 0,
                "recommended_tables": [],
            }

            # Get all table names
            table_names = inspector.get_table_names()
            schema_info["total_tables"] = len(table_names)

            for table_name in table_names:
                table_info = self._analyze_table(inspector, table_name, engine)
                if table_info:
                    schema_info["tables"].append(table_info)
                    schema_info["discoverable_tables"] += 1

                    # Recommend tables with good vectorization potential
                    if table_info["vectorization_potential"] > 0.5:
                        schema_info["recommended_tables"].append(table_name)

            engine.dispose()
            return schema_info

        except Exception as e:
            logger.error(f"Error discovering database schema: {e}")
            raise

    def _analyze_table(
        self, inspector, table_name: str, engine: Engine
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a single table for vectorization potential.

        Args:
            inspector: SQLAlchemy inspector
            table_name: Name of the table
            engine: Database engine

        Returns:
            Dictionary with table analysis results
        """
        try:
            columns = inspector.get_columns(table_name)
            primary_keys = inspector.get_pk_constraint(table_name)

            table_info = {
                "name": table_name,
                "columns": [],
                "primary_key_columns": primary_keys.get("constrained_columns", []),
                "total_columns": len(columns),
                "text_columns": 0,
                "numeric_columns": 0,
                "vectorizable_columns": 0,
                "estimated_rows": 0,
                "vectorization_potential": 0.0,
                "recommended_strategy": "single_column",
                "recommended_columns": [],
            }

            # Analyze each column
            for column in columns:
                column_info = self._analyze_column(column)
                table_info["columns"].append(column_info)

                if column_info["is_text"]:
                    table_info["text_columns"] += 1
                if column_info["is_numeric"]:
                    table_info["numeric_columns"] += 1
                if column_info["vectorizable"]:
                    table_info["vectorizable_columns"] += 1
                    table_info["recommended_columns"].append(column["name"])

            # Estimate table size
            table_info["estimated_rows"] = self._estimate_table_size(engine, table_name)

            # Calculate vectorization potential
            table_info["vectorization_potential"] = (
                self._calculate_vectorization_potential(table_info)
            )

            # Recommend strategy
            table_info["recommended_strategy"] = self._recommend_strategy(table_info)

            return table_info

        except Exception as e:
            logger.warning(f"Error analyzing table {table_name}: {e}")
            return None

    def _analyze_column(self, column: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single column for vectorization potential.

        Args:
            column: Column information from SQLAlchemy inspector

        Returns:
            Dictionary with column analysis
        """
        column_type = str(column["type"]).lower()

        # Determine if column is suitable for vectorization
        is_text = any(
            text_type in column_type for text_type in self.supported_text_types
        )
        is_numeric = any(
            num_type in column_type for num_type in self.supported_numeric_types
        )

        # Text columns are generally good for vectorization
        # Large text fields are especially valuable
        vectorizable = is_text and ("text" in column_type or "varchar" in column_type)

        # Calculate potential score
        potential_score = 0.0
        if "text" in column_type or "longtext" in column_type:
            potential_score = 0.9
        elif "varchar" in column_type and (
            "description" in column["name"].lower()
            or "comment" in column["name"].lower()
            or "content" in column["name"].lower()
        ):
            potential_score = 0.8
        elif "varchar" in column_type:
            potential_score = 0.5
        elif "json" in column_type:
            potential_score = 0.7

        return {
            "name": column["name"],
            "type": column_type,
            "is_text": is_text,
            "is_numeric": is_numeric,
            "nullable": column.get("nullable", True),
            "vectorizable": vectorizable,
            "potential_score": potential_score,
            "recommended_for_embedding": potential_score > 0.6,
        }

    def _estimate_table_size(self, engine: Engine, table_name: str) -> int:
        """
        Estimate the number of rows in a table.

        Args:
            engine: Database engine
            table_name: Name of the table

        Returns:
            Estimated number of rows
        """
        try:
            with engine.connect() as conn:
                # Try fast count estimation first
                if "postgresql" in str(engine.url):
                    result = conn.execute(
                        text(f"""
                        SELECT reltuples::BIGINT AS estimate
                        FROM pg_class 
                        WHERE relname = '{table_name}'
                    """)
                    )
                    estimate = result.fetchone()
                    if estimate and estimate[0] > 0:
                        return int(estimate[0])

                # Fallback to actual count (limited for performance)
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name} LIMIT 100000")
                )
                count_result = result.fetchone()
                return count_result[0] if count_result else 0
        except Exception:
            # If count fails, return unknown
            return -1

    def _calculate_vectorization_potential(self, table_info: Dict[str, Any]) -> float:
        """
        Calculate how suitable a table is for vectorization.

        Args:
            table_info: Table analysis information

        Returns:
            Potential score between 0.0 and 1.0
        """
        if table_info["total_columns"] == 0:
            return 0.0

        # Base score from column analysis
        text_ratio = table_info["text_columns"] / table_info["total_columns"]
        vectorizable_ratio = (
            table_info["vectorizable_columns"] / table_info["total_columns"]
        )

        # Bonus for having good text content
        content_bonus = 0.0
        for column in table_info["columns"]:
            if column["potential_score"] > 0.7:
                content_bonus += 0.2

        # Penalty for very small tables
        size_factor = 1.0
        if 0 < table_info["estimated_rows"] < 100:
            size_factor = 0.5

        potential = (
            text_ratio * 0.4 + vectorizable_ratio * 0.6 + content_bonus
        ) * size_factor
        return min(1.0, potential)

    def _recommend_strategy(self, table_info: Dict[str, Any]) -> str:
        """
        Recommend the best vectorization strategy for a table.

        Args:
            table_info: Table analysis information

        Returns:
            Recommended strategy name
        """
        vectorizable_count = table_info["vectorizable_columns"]

        if vectorizable_count == 0:
            return "none"
        elif vectorizable_count == 1:
            return "single_column"
        elif vectorizable_count <= 3:
            return "concatenated"
        else:
            return "weighted_combination"

    def create_database_connection(
        self,
        name: str,
        connection_string: str,
        db_type: str,
        description: Optional[str] = None,
    ) -> DatabaseConnection:
        """
        Create a new database connection configuration.

        Args:
            name: Friendly name for the connection
            connection_string: Database connection string
            db_type: Type of database
            description: Optional description

        Returns:
            Created DatabaseConnection instance
        """
        # Validate connection first
        try:
            temp_engine = create_engine(connection_string)
            with temp_engine.connect():
                pass
            temp_engine.dispose()
        except Exception as e:
            raise ValueError(f"Invalid connection string: {e}")

        with get_db_session_context() as session:
            db_conn = DatabaseConnection(
                name=name,
                description=description,
                db_type=db_type,
                connection_string=connection_string,
                is_active=True,
            )
            session.add(db_conn)
            session.flush()
            return db_conn

    def auto_configure_table(
        self, database_connection_id: int, table_name: str, connection_string: str
    ) -> TableConfig:
        """
        Automatically configure a table for vectorization based on discovery.

        Args:
            database_connection_id: ID of the database connection
            table_name: Name of the table to configure
            connection_string: Connection string for discovery

        Returns:
            Created TableConfig instance
        """
        # Discover table schema
        engine = create_engine(connection_string)
        inspector = inspect(engine)
        table_info = self._analyze_table(inspector, table_name, engine)
        engine.dispose()

        if not table_info:
            raise ValueError(f"Could not analyze table {table_name}")

        with get_db_session_context() as session:
            # Create table config
            table_config = TableConfig(
                database_connection_id=database_connection_id,
                table_name=table_name,
                description=f"Auto-configured table with {table_info['vectorizable_columns']} vectorizable columns",
                is_enabled=table_info["vectorization_potential"] > 0.3,
                vectorization_strategy=table_info["recommended_strategy"],
                content_columns=table_info["recommended_columns"],
                metadata_columns=table_info["primary_key_columns"],
                primary_key_column=table_info["primary_key_columns"][0]
                if table_info["primary_key_columns"]
                else None,
                total_records=table_info["estimated_rows"]
                if table_info["estimated_rows"] > 0
                else 0,
            )
            session.add(table_config)
            session.flush()

            # Create column configs
            for column_info in table_info["columns"]:
                if column_info["vectorizable"]:
                    column_config = ColumnConfig(
                        table_config_id=table_config.id,
                        column_name=column_info["name"],
                        column_type=column_info["type"],
                        should_vectorize=column_info["recommended_for_embedding"],
                        embedding_weight=column_info["potential_score"],
                    )
                    session.add(column_config)

            session.flush()
            return table_config

    def get_discovery_summary(self, database_connection_id: int) -> Dict[str, Any]:
        """
        Get a summary of discovery results for a database connection.

        Args:
            database_connection_id: ID of the database connection

        Returns:
            Discovery summary
        """
        with get_db_session_context() as session:
            db_conn = session.query(DatabaseConnection).get(database_connection_id)
            if not db_conn:
                raise ValueError("Database connection not found")

            # Perform discovery
            schema_info = self.discover_database_schema(
                db_conn.connection_string, db_conn.db_type
            )

            return {
                "database_name": db_conn.name,
                "database_type": db_conn.db_type,
                "total_tables": schema_info["total_tables"],
                "recommended_tables": len(schema_info["recommended_tables"]),
                "vectorizable_tables": [
                    {
                        "name": table["name"],
                        "potential": table["vectorization_potential"],
                        "strategy": table["recommended_strategy"],
                        "columns": len(table["recommended_columns"]),
                    }
                    for table in schema_info["tables"]
                    if table["vectorization_potential"] > 0.3
                ],
            }
