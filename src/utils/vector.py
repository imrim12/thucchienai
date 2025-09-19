"""
Utility functions for vector operations.
"""

import numpy as np
from typing import List


def cosine_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vector1: First vector
        vector2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    # Ensure vectors are numpy arrays
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    # Calculate dot product
    dot_product = np.dot(v1, v2)
    
    # Calculate magnitudes
    magnitude1 = np.linalg.norm(v1)
    magnitude2 = np.linalg.norm(v2)
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # Calculate cosine similarity
    similarity = dot_product / (magnitude1 * magnitude2)
    
    return float(similarity)


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Normalize a vector to unit length.
    
    Args:
        vector: Input vector
        
    Returns:
        Normalized vector
    """
    vector = np.array(vector)
    magnitude = np.linalg.norm(vector)
    
    if magnitude == 0:
        return vector
    
    return vector / magnitude


def euclidean_distance(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """
    Calculate Euclidean distance between two vectors.
    
    Args:
        vector1: First vector
        vector2: Second vector
        
    Returns:
        Euclidean distance
    """
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    return float(np.linalg.norm(v1 - v2))


def batch_cosine_similarity(
    query_vector: np.ndarray, 
    vectors: List[np.ndarray]
) -> List[float]:
    """
    Calculate cosine similarity between a query vector and a batch of vectors.
    
    Args:
        query_vector: The query vector
        vectors: List of vectors to compare against
        
    Returns:
        List of similarity scores
    """
    similarities = []
    query_vector = np.array(query_vector)
    
    for vector in vectors:
        similarity = cosine_similarity(query_vector, vector)
        similarities.append(similarity)
    
    return similarities


def find_most_similar_vector(
    query_vector: np.ndarray, 
    vectors: List[np.ndarray],
    threshold: float = 0.0
) -> tuple[int, float]:
    """
    Find the index and similarity score of the most similar vector.
    
    Args:
        query_vector: The query vector
        vectors: List of vectors to search through
        threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (index, similarity_score) or (-1, 0.0) if none found
    """
    if not vectors:
        return -1, 0.0
    
    similarities = batch_cosine_similarity(query_vector, vectors)
    
    max_similarity = max(similarities)
    if max_similarity >= threshold:
        max_index = similarities.index(max_similarity)
        return max_index, max_similarity
    
    return -1, 0.0