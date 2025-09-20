"""
Validation prompts for SQL query verification and correction.
"""

# Prompt for SQL validation and correction
SQL_VALIDATION_PROMPT = """You are a SQL validator and corrector. Your task is to analyze the given SQL query and either validate it or provide corrections.

SQL Query to validate:
{sql_query}

Instructions:
1. Check for syntax errors
2. Verify the query follows SQL standards
3. If there are errors, provide a corrected version
4. If the query is valid, return it as-is
5. Return ONLY the SQL query without explanations

If the query cannot be corrected or is fundamentally flawed, return an empty response."""

# Prompt for readonly validation
READONLY_SQL_VALIDATION_PROMPT = """You are a SQL validator specialized in read-only operations. Your task is to validate that the SQL query contains ONLY SELECT statements.

SQL Query to validate:
{sql_query}

CRITICAL REQUIREMENTS:
- Query must contain ONLY SELECT statements
- NO INSERT, UPDATE, DELETE operations allowed
- NO DDL operations (CREATE, DROP, ALTER, etc.) allowed
- NO data modification of any kind allowed

Instructions:
1. Check if the query contains only SELECT statements
2. If it contains any non-SELECT operations, return an empty response
3. If it's a valid SELECT-only query, return it cleaned up
4. Return ONLY the SQL query without explanations

If the query violates readonly restrictions, return an empty response."""

def get_validation_prompt(sql_query: str, readonly: bool = False) -> str:
    """
    Generate validation prompt for SQL query verification.
    
    Args:
        sql_query: SQL query to validate
        readonly: If True, applies readonly restrictions
        
    Returns:
        Formatted validation prompt string
    """
    if readonly:
        return READONLY_SQL_VALIDATION_PROMPT.format(sql_query=sql_query)
    else:
        return SQL_VALIDATION_PROMPT.format(sql_query=sql_query)