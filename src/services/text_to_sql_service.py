"""
Core Text-to-SQL service with caching and similarity search.
"""

import numpy as np
from typing import Optional, Dict, Any
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase

from src.llm.google import get_gemini_llm, get_gemini_embeddings
from src.database.postgres_cache import PostgresCache
from src.core.config import get_settings


class TextToSQLService:
    """Main service for converting natural language to SQL with caching."""
    
    def __init__(self):
        """Initialize the Text-to-SQL service."""
        self.settings = get_settings()
        
        # Initialize LLM and embeddings
        self.llm = get_gemini_llm()
        self.embeddings = get_gemini_embeddings()
        
        # Initialize cache
        self.cache = PostgresCache()
        
        # Initialize target database connection (if provided)
        self.target_db = None
        if self.settings.target_db_uri:
            try:
                self.target_db = SQLDatabase.from_uri(self.settings.target_db_uri)
                print("Connected to target database for SQL execution")
            except Exception as e:
                print(f"Warning: Could not connect to target database: {e}")
        
        print("TextToSQLService initialized successfully")
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for the given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            embedding = self.embeddings.embed_query(text)
            return np.array(embedding)
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def _generate_sql_query(self, natural_question: str) -> str:
        """
        Generate SQL query from natural language using LangChain.
        
        Args:
            natural_question: Natural language question
            
        Returns:
            Generated SQL query
        """
        try:
            if self.target_db is None:
                # If no target database is available, use a generic approach
                # This is a fallback for demonstration purposes
                prompt = f"""
                Convert the following natural language question to a SQL query:
                
                Question: {natural_question}
                
                Generate a clean, well-formatted SQL query without any explanations.
                Only return the SQL query.
                """
                
                response = self.llm.invoke(prompt)
                sql_query = response.content.strip()
                
                # Clean up the response to extract just the SQL
                if sql_query.startswith("```sql"):
                    sql_query = sql_query[6:]
                if sql_query.endswith("```"):
                    sql_query = sql_query[:-3]
                
                return sql_query.strip()
            else:
                # Use LangChain's SQL chain with the target database
                chain = create_sql_query_chain(self.llm, self.target_db)
                sql_query = chain.invoke({"question": natural_question})
                return sql_query
                
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            raise
    
    def process_question(self, natural_question: str) -> Dict[str, Any]:
        """
        Process a natural language question and return SQL query.
        
        This method implements the core logic:
        1. Generate embedding for the question
        2. Check cache for similar questions
        3. If found, return cached SQL
        4. If not found, generate new SQL and cache it
        
        Args:
            natural_question: Natural language question
            
        Returns:
            Dictionary containing:
            - sql_query: The generated or cached SQL query
            - from_cache: Boolean indicating if result came from cache
            - similarity_score: Similarity score if from cache
            - cache_stats: Current cache statistics
        """
        try:
            print(f"Processing question: {natural_question}")
            
            # Step 1: Generate embedding for the question
            question_vector = self._generate_embedding(natural_question)
            
            # Step 2: Check cache for similar questions
            similar_result = self.cache.find_similar_question(
                question_vector, 
                self.settings.similarity_threshold
            )
            
            # Step 3: Return cached result if found
            if similar_result:
                cached_question, cached_sql, similarity_score = similar_result
                print(f"Returning cached SQL for similar question: {cached_question[:50]}...")
                
                return {
                    "sql_query": cached_sql,
                    "from_cache": True,
                    "similarity_score": similarity_score,
                    "cached_question": cached_question,
                    "cache_stats": self.cache.get_cache_stats()
                }
            
            # Step 4: Generate new SQL query
            print("No similar question found in cache. Generating new SQL...")
            sql_query = self._generate_sql_query(natural_question)
            
            # Step 5: Store in cache
            self.cache.add_to_cache(natural_question, sql_query, question_vector)
            
            return {
                "sql_query": sql_query,
                "from_cache": False,
                "similarity_score": None,
                "cached_question": None,
                "cache_stats": self.cache.get_cache_stats()
            }
            
        except Exception as e:
            print(f"Error processing question: {e}")
            raise
    
    def execute_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute SQL query against the target database.
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            Dictionary containing execution results or error information
        """
        if self.target_db is None:
            return {
                "success": False,
                "error": "No target database configured"
            }
        
        try:
            result = self.target_db.run(sql_query)
            return {
                "success": True,
                "result": result,
                "query": sql_query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": sql_query
            }
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_cache_stats()
    
    def clear_cache(self) -> bool:
        """Clear the cache."""
        try:
            self.cache.clear_cache()
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the service components."""
        health_status = {
            "llm_available": False,
            "embeddings_available": False,
            "cache_available": False,
            "target_db_available": False
        }
        
        # Check LLM
        try:
            response = self.llm.invoke("Test")
            health_status["llm_available"] = True
        except Exception as e:
            print(f"LLM health check failed: {e}")
        
        # Check embeddings
        try:
            self.embeddings.embed_query("test")
            health_status["embeddings_available"] = True
        except Exception as e:
            print(f"Embeddings health check failed: {e}")
        
        # Check cache
        try:
            self.cache.get_cache_stats()
            health_status["cache_available"] = True
        except Exception as e:
            print(f"Cache health check failed: {e}")
        
        # Check target database
        if self.target_db:
            try:
                self.target_db.run("SELECT 1")
                health_status["target_db_available"] = True
            except Exception as e:
                print(f"Target DB health check failed: {e}")
        
        return health_status
    
    def __del__(self):
        """Cleanup resources when service is destroyed."""
        if hasattr(self, 'cache'):
            self.cache.close()