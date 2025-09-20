"""
Helper prompts for various utility functions in the Text-to-SQL service.
"""

# Prompt for explaining SQL queries in natural language
SQL_EXPLANATION_PROMPT = """You are a SQL expert. Explain the following SQL query in clear, simple language.

SQL Query:
{sql_query}

Provide a brief, clear explanation of what this query does without using technical jargon.
Focus on what data it retrieves and any conditions or operations it performs."""

# Prompt for suggesting similar questions based on SQL
SIMILAR_QUESTIONS_PROMPT = """Based on the following SQL query, suggest 3-5 similar natural language questions that would generate similar queries.

SQL Query:
{sql_query}

Generate questions that would result in similar database operations.
Focus on variations in wording while maintaining the same intent."""

# Prompt for generating test data
TEST_DATA_PROMPT = """Generate sample data that would work with the following SQL query for testing purposes.

SQL Query:
{sql_query}

Provide:
1. Table structure (CREATE TABLE statements)
2. Sample INSERT statements with realistic test data
3. Expected result of running the query

Format as clean SQL statements."""

def get_explanation_prompt(sql_query: str) -> str:
    """Generate prompt for explaining SQL queries."""
    return SQL_EXPLANATION_PROMPT.format(sql_query=sql_query)

def get_similar_questions_prompt(sql_query: str) -> str:
    """Generate prompt for suggesting similar questions."""
    return SIMILAR_QUESTIONS_PROMPT.format(sql_query=sql_query)

def get_test_data_prompt(sql_query: str) -> str:
    """Generate prompt for creating test data."""
    return TEST_DATA_PROMPT.format(sql_query=sql_query)