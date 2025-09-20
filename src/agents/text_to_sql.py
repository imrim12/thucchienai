"""
Core Text-to-SQL agent with caching, similarity search, and SQL validation.
"""

import numpy as np
import sqlparse
from typing import Optional, Dict, Any, List
from langchain.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase

from src.llm.google import get_gemini_llm, get_gemini_embeddings
from src.database.chroma_db import ChromaCache
from src.core.config import get_settings
from src.prompts import get_text_to_sql_prompt, get_user_prompt, get_explanation_prompt, get_validation_prompt


class SQLValidator:
    """SQL validator and parser for ensuring safe SQL output."""
    
    @staticmethod
    def clean_sql_response(response: str) -> str:
        """
        Clean and extract SQL from LLM response.
        
        Args:
            response: Raw LLM response that may contain markdown, explanations, etc.
            
        Returns:
            Clean SQL query string or empty string if invalid
        """
        if not response or not response.strip():
            return ""
        
        # Remove markdown code blocks
        cleaned = response.strip()
        if cleaned.startswith("```sql"):
            cleaned = cleaned[6:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "SQL:",
            "Query:",
            "Here is the SQL:",
            "The SQL query is:",
            "SQL query:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned.strip()
    
    @staticmethod
    def parse_sql_statements(sql: str) -> List[sqlparse.sql.Statement]:
        """
        Parse SQL string into statements.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of parsed SQL statements
        """
        try:
            return list(sqlparse.parse(sql))
        except Exception:
            return []
    
    @staticmethod
    def is_select_only(sql: str) -> bool:
        """
        Check if SQL contains only SELECT statements.
        
        Args:
            sql: SQL query string
            
        Returns:
            True if only SELECT statements, False otherwise
        """
        statements = SQLValidator.parse_sql_statements(sql)
        
        for statement in statements:
            if not statement.tokens:
                continue
                
            # Get the first meaningful token
            first_token = None
            for token in statement.tokens:
                if token.ttype is None and str(token).strip():
                    first_token = str(token).strip().upper()
                    break
                elif token.ttype in (sqlparse.tokens.Keyword, sqlparse.tokens.Keyword.DML):
                    first_token = str(token).strip().upper()
                    break
            
            if first_token and not first_token.startswith('SELECT'):
                return False
        
        return True
    
    @staticmethod
    def validate_sql_syntax(sql: str) -> bool:
        """
        Validate SQL syntax.
        
        Args:
            sql: SQL query string
            
        Returns:
            True if valid syntax, False otherwise
        """
        if not sql or not sql.strip():
            return False
        
        try:
            statements = SQLValidator.parse_sql_statements(sql)
            
            # Check if we got at least one valid statement
            if not statements:
                return False
            
            # Check for basic SQL structure
            for statement in statements:
                if not statement.tokens:
                    return False
                
                # Convert to string and check for basic patterns
                sql_str = str(statement).strip()
                if not sql_str:
                    return False
                
                # Very basic validation - ensure it's not just a comment or empty
                if sql_str.startswith('--') or sql_str.startswith('/*'):
                    continue
                
                # Should contain at least one SQL keyword
                sql_upper = sql_str.upper()
                sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
                if not any(keyword in sql_upper for keyword in sql_keywords):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def validate_and_clean_sql(sql: str, readonly: bool = False) -> str:
        """
        Validate and clean SQL query.
        
        Args:
            sql: Raw SQL string
            readonly: If True, only allow SELECT statements
            
        Returns:
            Clean SQL string or empty string if invalid
        """
        # Clean the SQL response
        cleaned_sql = SQLValidator.clean_sql_response(sql)
        
        if not cleaned_sql:
            return ""
        
        # Validate syntax
        if not SQLValidator.validate_sql_syntax(cleaned_sql):
            return ""
        
        # Check readonly constraint
        if readonly and not SQLValidator.is_select_only(cleaned_sql):
            return ""
        
        return cleaned_sql


class TextToSQLService:
    """Main agent for converting natural language to SQL with caching and validation."""
    
    def __init__(self):
        """Initialize the Text-to-SQL agent."""
        self.settings = get_settings()
        
        # Initialize LLM and embeddings
        self.llm = get_gemini_llm()
        self.embeddings = get_gemini_embeddings()
        
        # Initialize cache
        self.cache = ChromaCache(
            host=self.settings.CHROMA_HOST,
            port=self.settings.CHROMA_PORT,
            persist_directory=self.settings.CHROMA_PERSIST_DIRECTORY,
            collection_name=self.settings.CHROMA_COLLECTION_NAME
        )

        # Initialize SQL validator
        self.validator = SQLValidator()
        
        # Initialize target database connection (if provided)
        self.target_db = None
        if self.settings.TARGET_DB_URI:
            try:
                self.target_db = SQLDatabase.from_uri(self.settings.TARGET_DB_URI)
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
    
    def _generate_sql_query(self, natural_question: str, readonly: bool = False) -> str:
        """
        Generate SQL query from natural language using LangChain.
        
        Args:
            natural_question: Natural language question
            readonly: If True, only generate SELECT queries
            
        Returns:
            Generated and validated SQL query or empty string if invalid
        """
        try:
            raw_sql = ""
            
            if self.target_db is None:
                # If no target database is available, use a generic approach with prompts
                system_prompt = get_text_to_sql_prompt(readonly)
                user_prompt = get_user_prompt(natural_question, readonly)
                
                # Combine system and user prompts
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.llm.invoke(full_prompt)
                # Handle both string and list responses from LLM
                if isinstance(response.content, list):
                    raw_sql = str(response.content[0]).strip() if response.content else ""
                else:
                    raw_sql = str(response.content).strip()
                
            else:
                # Use LangChain's SQL chain with the target database
                chain = create_sql_query_chain(self.llm, self.target_db)
                raw_sql = chain.invoke({"question": natural_question})
            
            # Validate and clean the SQL
            validated_sql = self.validator.validate_and_clean_sql(raw_sql, readonly)
            
            if not validated_sql:
                print(f"Generated SQL failed validation: {raw_sql[:100]}...")
                return ""
            
            return validated_sql
                
        except Exception as e:
            print(f"Error generating SQL query: {e}")
            return ""
    
    def process_question(self, natural_question: str, readonly: bool = False) -> Dict[str, Any]:
        """
        Process a natural language question and return validated SQL query.
        
        This method implements the core logic:
        1. Generate embedding for the question
        2. Check cache for similar questions
        3. If found, return cached SQL (validate if readonly mode changed)
        4. If not found, generate new SQL and cache it
        
        Args:
            natural_question: Natural language question
            readonly: If True, only allow SELECT queries
            
        Returns:
            Dictionary containing:
            - sql_query: The generated or cached SQL query (empty if invalid)
            - from_cache: Boolean indicating if result came from cache
            - similarity_score: Similarity score if from cache
            - cache_stats: Current cache statistics
            - is_valid: Boolean indicating if SQL passed validation
        """
        try:
            print(f"Processing question: {natural_question} (readonly: {readonly})")
            
            # Step 1: Generate embedding for the question
            question_vector = self._generate_embedding(natural_question)
            
            # Step 2: Check cache for similar questions
            similar_result = self.cache.find_similar_question(
                question_vector, 
                self.settings.SIMILARITY_THRESHOLD
            )
            
            # Step 3: Return cached result if found (but validate for readonly mode)
            if similar_result:
                cached_question, cached_sql, similarity_score = similar_result
                print(f"Found cached SQL for similar question: {cached_question[:50]}...")
                
                # Validate cached SQL against readonly constraint
                validated_sql = self.validator.validate_and_clean_sql(cached_sql, readonly)
                
                if validated_sql:
                    print(f"Cached SQL passed validation")
                    return {
                        "sql_query": validated_sql,
                        "from_cache": True,
                        "similarity_score": similarity_score,
                        "cached_question": cached_question,
                        "cache_stats": self.cache.get_cache_stats(),
                        "is_valid": True
                    }
                else:
                    print(f"Cached SQL failed readonly validation, generating new query...")
            
            # Step 4: Generate new SQL query
            print("Generating new SQL query...")
            sql_query = self._generate_sql_query(natural_question, readonly)
            
            if not sql_query:
                # Failed validation
                return {
                    "sql_query": "",
                    "from_cache": False,
                    "similarity_score": None,
                    "cached_question": None,
                    "cache_stats": self.cache.get_cache_stats(),
                    "is_valid": False
                }
            
            # Step 5: Store in cache (only if valid)
            try:
                self.cache.add_to_cache(natural_question, sql_query, question_vector)
            except Exception as e:
                print(f"Warning: Failed to cache result: {e}")
            
            return {
                "sql_query": sql_query,
                "from_cache": False,
                "similarity_score": None,
                "cached_question": None,
                "cache_stats": self.cache.get_cache_stats(),
                "is_valid": True
            }
            
        except Exception as e:
            print(f"Error processing question: {e}")
            return {
                "sql_query": "",
                "from_cache": False,
                "similarity_score": None,
                "cached_question": None,
                "cache_stats": {"total_entries": 0},
                "is_valid": False
            }
    
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
    
    def explain_sql(self, sql_query: str) -> str:
        """
        Generate a natural language explanation of a SQL query.
        
        Args:
            sql_query: SQL query to explain
            
        Returns:
            Natural language explanation of the query
        """
        try:
            if not sql_query or not sql_query.strip():
                return "No SQL query provided."
            
            prompt = get_explanation_prompt(sql_query)
            response = self.llm.invoke(prompt)
            # Handle both string and list responses from LLM
            if isinstance(response.content, list):
                return str(response.content[0]).strip() if response.content else "No explanation available."
            else:
                return str(response.content).strip()
            
        except Exception as e:
            print(f"Error explaining SQL query: {e}")
            return "Error generating explanation."
    
    def validate_sql_with_llm(self, sql_query: str, readonly: bool = False) -> Dict[str, Any]:
        """
        Use LLM to validate and potentially correct SQL query.
        
        Args:
            sql_query: SQL query to validate
            readonly: If True, applies readonly restrictions
            
        Returns:
            Dictionary with validation results and corrected SQL if applicable
        """
        try:
            if not sql_query or not sql_query.strip():
                return {
                    "is_valid": False,
                    "corrected_sql": "",
                    "explanation": "Empty SQL query provided."
                }
            
            # First try local validation
            local_validation = self.validator.validate_and_clean_sql(sql_query, readonly)
            
            if local_validation:
                return {
                    "is_valid": True,
                    "corrected_sql": local_validation,
                    "explanation": "SQL query is valid."
                }
            
            # If local validation fails, try LLM validation
            prompt = get_validation_prompt(sql_query, readonly)
            response = self.llm.invoke(prompt)
            # Handle both string and list responses from LLM
            if isinstance(response.content, list):
                corrected_sql = str(response.content[0]).strip() if response.content else sql_query
            else:
                corrected_sql = str(response.content).strip()
            
            # Validate the LLM's correction
            final_validation = self.validator.validate_and_clean_sql(corrected_sql, readonly)
            
            return {
                "is_valid": bool(final_validation),
                "corrected_sql": final_validation,
                "explanation": "SQL corrected by LLM." if final_validation else "SQL could not be corrected."
            }
            
        except Exception as e:
            print(f"Error in LLM SQL validation: {e}")
            return {
                "is_valid": False,
                "corrected_sql": "",
                "explanation": f"Error during validation: {str(e)}"
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