"""
PostgreSQL cache for storing and retrieving cached Text-to-SQL results.
"""

import pickle
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Tuple, Any
import numpy as np
from src.core.config import get_settings
from src.utils.vector import cosine_similarity


class PostgresCache:
    """PostgreSQL cache for storing Text-to-SQL query results and embeddings."""
    
    def __init__(self):
        """Initialize the PostgreSQL cache."""
        self.settings = get_settings()
        self.connection = None
        self.connect()
        self.create_cache_table()
    
    def connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(self.settings.postgres_uri)
            self.connection.autocommit = True
            print("Successfully connected to PostgreSQL cache database")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise
    
    def create_cache_table(self) -> None:
        """Create the query_cache table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS query_cache (
            id SERIAL PRIMARY KEY,
            natural_question TEXT NOT NULL,
            sql_query TEXT NOT NULL,
            question_vector BYTEA NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_query_cache_question 
        ON query_cache USING GIN (to_tsvector('english', natural_question));
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_query)
            print("Cache table created successfully")
        except Exception as e:
            print(f"Error creating cache table: {e}")
            raise
    
    def _serialize_vector(self, vector: np.ndarray) -> bytes:
        """Serialize numpy array to bytes for storage."""
        return pickle.dumps(vector)
    
    def _deserialize_vector(self, vector_bytes: bytes) -> np.ndarray:
        """Deserialize bytes back to numpy array."""
        return pickle.loads(vector_bytes)
    
    def add_to_cache(
        self, 
        natural_question: str, 
        sql_query: str, 
        question_vector: np.ndarray
    ) -> None:
        """
        Add a new question-SQL pair to the cache.
        
        Args:
            natural_question: The original natural language question
            sql_query: The generated SQL query
            question_vector: The embedding vector for the question
        """
        insert_query = """
        INSERT INTO query_cache (natural_question, sql_query, question_vector)
        VALUES (%s, %s, %s)
        """
        
        try:
            serialized_vector = self._serialize_vector(question_vector)
            with self.connection.cursor() as cursor:
                cursor.execute(
                    insert_query, 
                    (natural_question, sql_query, serialized_vector)
                )
            print(f"Added new entry to cache for question: {natural_question[:50]}...")
        except Exception as e:
            print(f"Error adding to cache: {e}")
            raise
    
    def find_similar_question(
        self, 
        question_vector: np.ndarray, 
        threshold: Optional[float] = None
    ) -> Optional[Tuple[str, str, float]]:
        """
        Find the most similar cached question above the similarity threshold.
        
        Args:
            question_vector: The embedding vector of the query question
            threshold: Similarity threshold (uses config default if None)
            
        Returns:
            Tuple of (natural_question, sql_query, similarity_score) if found,
            None otherwise
        """
        if threshold is None:
            threshold = self.settings.similarity_threshold
        
        select_query = """
        SELECT natural_question, sql_query, question_vector 
        FROM query_cache
        """
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(select_query)
                results = cursor.fetchall()
            
            best_match = None
            best_similarity = -1.0
            
            for row in results:
                cached_vector = self._deserialize_vector(row['question_vector'])
                similarity = cosine_similarity(question_vector, cached_vector)
                
                if similarity > best_similarity and similarity >= threshold:
                    best_similarity = similarity
                    best_match = (
                        row['natural_question'], 
                        row['sql_query'], 
                        similarity
                    )
            
            if best_match:
                print(f"Found similar question with similarity {best_similarity:.3f}")
                return best_match
            else:
                print("No similar question found in cache")
                return None
                
        except Exception as e:
            print(f"Error searching cache: {e}")
            return None
    
    def get_cache_stats(self) -> dict:
        """Get statistics about the cache."""
        stats_query = "SELECT COUNT(*) as total_entries FROM query_cache"
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(stats_query)
                result = cursor.fetchone()
            return {"total_entries": result['total_entries']}
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"total_entries": 0}
    
    def clear_cache(self) -> None:
        """Clear all entries from the cache."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM query_cache")
            print("Cache cleared successfully")
        except Exception as e:
            print(f"Error clearing cache: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed")