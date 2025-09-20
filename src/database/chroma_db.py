"""
ChromaDB implementation for caching text-to-SQL queries with vector similarity search.
"""

import os
import uuid
import logging
import numpy as np
from typing import Optional, List, Tuple, Dict, Any, cast
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection
from chromadb.api import ClientAPI

logger = logging.getLogger(__name__)


class ChromaCache:
    """ChromaDB-based cache for storing and retrieving text-to-SQL queries with vector similarity."""
    
    def __init__(self, host: str = "localhost", port: int = 8000, persist_directory: str = "./chroma_data", collection_name: str = "sql_queries"):
        """
        Initialize ChromaDB cache.
        
        Args:
            host: ChromaDB server host (for HTTP client)
            port: ChromaDB server port (for HTTP client)
            persist_directory: Directory to persist ChromaDB data (for local client)
            collection_name: Name of the collection to store queries
        """
        self.collection_name = collection_name
        
        # Try to connect to ChromaDB server first, fallback to local persistent client
        try:
            # Try HTTP client first (for Docker/server deployment)
            self.client: Optional[ClientAPI] = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # Test connection
            self.client.heartbeat()
            print(f"Connected to ChromaDB server at {host}:{port}")
        except Exception as e:
            print(f"Failed to connect to ChromaDB server at {host}:{port}: {e}")
            print("Falling back to local persistent client...")
            
            # Fallback to persistent client (for local development)
            self.persist_directory = persist_directory
            os.makedirs(persist_directory, exist_ok=True)
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            print(f"Using local ChromaDB at {persist_directory}")
        
        # Get or create collection
        try:
            self.collection: Optional[Collection] = self.client.get_collection(name=collection_name)
            print(f"Loaded existing ChromaDB collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Text-to-SQL query cache with vector similarity search"}
            )
            print(f"Created new ChromaDB collection: {collection_name}")
        
        print(f"ChromaDB cache initialized with {self.get_cache_size()} cached queries")
    
    def add_to_cache(self, natural_question: str, sql_query: str, question_vector: np.ndarray) -> Optional[str]:
        """
        Add a new question-SQL pair to the cache.
        
        Args:
            natural_question: Natural language question
            sql_query: Corresponding SQL query
            question_vector: Embedding vector for the question
            
        Returns:
            Document ID of the added cache entry
        """
        try:
            # Generate unique ID for this cache entry
            doc_id = str(uuid.uuid4())
            
            # Convert numpy array to list for ChromaDB
            embedding = question_vector.tolist() if isinstance(question_vector, np.ndarray) else question_vector
            
            # Check if collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return None
            
            # Add to collection
            self.collection.add(
                embeddings=[embedding],
                documents=[natural_question],
                metadatas=[{
                    "sql_query": sql_query,
                    "timestamp": str(np.datetime64('now'))
                }],
                ids=[doc_id]
            )
            
            print(f"Added new query to cache with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"Error adding to cache: {e}")
            raise
    
    def find_similar_question(self, question_vector: np.ndarray, threshold: float = 0.8) -> Optional[Tuple[str, str, float]]:
        """
        Find the most similar cached question based on vector similarity.
        
        Args:
            question_vector: Embedding vector of the query question
            threshold: Minimum similarity threshold (0-1, where 1 is identical)
            
        Returns:
            Tuple of (original_question, sql_query, similarity_score) if found, None otherwise
        """
        try:
            # Convert numpy array to list for ChromaDB
            embedding = question_vector.tolist() if isinstance(question_vector, np.ndarray) else question_vector
            
            # Query for the most similar document
            if not self.collection:
                return None
                
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=1,
                include=["documents", "metadatas", "distances"]
            )
            
            # Check if we have results and if similarity meets threshold
            if (results and results.get("documents") and results.get("distances") and 
                cast(Any, results["documents"]) and cast(Any, results["distances"]) and
                len(cast(Any, results["documents"])[0]) > 0):
                # ChromaDB returns distances (lower is more similar)
                # Convert distance to similarity score (1 - normalized_distance)
                distance = cast(Any, results["distances"])[0][0]
                
                # Normalize distance to similarity score (this is an approximation)
                # For cosine distance, similarity = 1 - distance
                similarity_score = 1 - distance
                
                if similarity_score >= threshold:
                    original_question = str(cast(Any, results["documents"])[0][0])
                    sql_query = str(cast(Any, results["metadatas"])[0][0]["sql_query"])
                    
                    print(f"Found similar question with similarity: {similarity_score:.3f}")
                    return original_question, sql_query, float(similarity_score)
                else:
                    print(f"Best match similarity {similarity_score:.3f} below threshold {threshold}")
                    
            return None
            
        except Exception as e:
            print(f"Error finding similar question: {e}")
            return None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            if not self.collection:
                return {}
            cache_size = self.collection.count()
            
            return {
                "total_entries": cache_size,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {
                "total_entries": 0,
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory,
                "error": str(e)
            }
    
    def get_cache_size(self) -> int:
        """
        Get the number of entries in the cache.
        
        Returns:
            Number of cached queries
        """
        try:
            if not self.collection:
                return 0
            return self.collection.count()
        except Exception as e:
            print(f"Error getting cache size: {e}")
            return 0
    
    def clear_cache(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the collection and recreate it
            if self.client:
                self.client.delete_collection(name=self.collection_name)
            
            # Recreate the collection
            if self.client:
                self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Text-to-SQL query cache with vector similarity search"}
            )
            
            print("Cache cleared successfully")
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def get_all_queries(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all cached queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of dictionaries containing question, sql_query, and metadata
        """
        try:
            # Get all documents from the collection
            if not self.collection:
                return []
            results = self.collection.get(
                include=["documents", "metadatas"],
                limit=limit
            )
            
            queries = []
            if (results and results.get("documents") and results.get("metadatas") and 
                results["documents"] and results["metadatas"]):
                for i, doc in enumerate(results["documents"]):
                    queries.append({
                        "question": doc,
                        "sql_query": results["metadatas"][i]["sql_query"],
                        "timestamp": results["metadatas"][i].get("timestamp", "unknown")
                    })
            
            return queries
            
        except Exception as e:
            print(f"Error getting all queries: {e}")
            return []
    
    def remove_query(self, query_id: str) -> bool:
        """
        Remove a specific query from the cache by ID.
        
        Args:
            query_id: ID of the query to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.collection:
                self.collection.delete(ids=[query_id])
            print(f"Removed query with ID: {query_id}")
            return True
            
        except Exception as e:
            print(f"Error removing query: {e}")
            return False
    
    def close(self):
        """
        Close the ChromaDB connection and clean up resources.
        """
        try:
            # ChromaDB client doesn't need explicit closing, but we can set references to None
            self.collection: Optional[Collection] = None
            self.client: Optional[ClientAPI] = None
            print("ChromaDB cache connection closed")
            
        except Exception as e:
            print(f"Error closing ChromaDB cache: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'client') and self.client is not None:
            self.close()
