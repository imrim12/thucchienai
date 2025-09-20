"""
User prompts for text-to-SQL conversion.
These are the templates for constructing user messages to the LLM.
"""

# Template for basic text-to-SQL conversion
BASIC_TEXT_TO_SQL_USER_PROMPT = """Convert the following natural language question to a SQL query:

Question: {question}

Generate a clean, well-formatted SQL query without any explanations.
Only return the SQL query."""

# Template for readonly text-to-SQL conversion
READONLY_TEXT_TO_SQL_USER_PROMPT = """Convert the following natural language question to a SELECT query:

Question: {question}

Generate a clean, well-formatted SELECT query without any explanations.
Only return the SQL query.
Important: Only use SELECT statements, no INSERT, UPDATE, DELETE, or DDL operations."""

# Template for database-aware text-to-SQL conversion
DATABASE_AWARE_TEXT_TO_SQL_USER_PROMPT = """Based on the database schema provided, convert the following natural language question to a SQL query:

Question: {question}

Database Schema Information:
{schema_info}

Generate a clean, well-formatted SQL query that works with the provided schema.
Only return the SQL query without explanations."""


def get_user_prompt(
    question: str, readonly: bool = False, schema_info: str = None
) -> str:
    """
    Generate user prompt for text-to-SQL conversion.

    Args:
        question: Natural language question
        readonly: If True, emphasizes SELECT-only restrictions
        schema_info: Optional database schema information

    Returns:
        Formatted user prompt string
    """
    if schema_info:
        return DATABASE_AWARE_TEXT_TO_SQL_USER_PROMPT.format(
            question=question, schema_info=schema_info
        )
    elif readonly:
        return READONLY_TEXT_TO_SQL_USER_PROMPT.format(question=question)
    else:
        return BASIC_TEXT_TO_SQL_USER_PROMPT.format(question=question)
