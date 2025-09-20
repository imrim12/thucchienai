"""
Gemini LLM and Embedding provider using LangChain.
"""

from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.core.config import get_settings


def get_gemini_llm(
    model_name: str = "gemini-pro",
    temperature: float = 0.0,
    max_output_tokens: Optional[int] = None,
) -> ChatGoogleGenerativeAI:
    """
    Initialize and return a Gemini LLM instance.

    Args:
        model_name: The Gemini model to use (default: "gemini-pro")
        temperature: Controls randomness in output (default: 0.0 for deterministic)
        max_output_tokens: Maximum number of tokens in output

    Returns:
        ChatGoogleGenerativeAI: Initialized Gemini LLM instance
    """
    settings = get_settings()

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )


def get_gemini_embeddings(
    model_name: str = "models/embedding-001",
) -> GoogleGenerativeAIEmbeddings:
    """
    Initialize and return a Gemini embeddings model instance.

    Args:
        model_name: The Gemini embeddings model to use

    Returns:
        GoogleGenerativeAIEmbeddings: Initialized Gemini embeddings instance
    """
    settings = get_settings()

    return GoogleGenerativeAIEmbeddings(
        model=model_name, google_api_key=settings.GOOGLE_API_KEY
    )
