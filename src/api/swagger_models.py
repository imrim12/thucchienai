"""
Swagger/OpenAPI documentation models and configuration for the Text-to-SQL API.
"""

from flask_restx import Api, fields

# Create the API documentation instance
api = Api(
    title="Text-to-SQL API",
    version="1.0.0",
    description="""
    A powerful Text-to-SQL service that converts natural language questions into SQL queries,
    executes them against your database, and provides intelligent caching with vector similarity search.

    ## Features
    - **Natural Language to SQL**: Convert questions to executable SQL queries
    - **Query Execution**: Execute generated SQL against your database
    - **Smart Caching**: Vector-based similarity search for query caching
    - **Database Discovery**: Automatically discover and configure database schemas
    - **SQL Validation**: Validate SQL syntax and semantics
    - **Query Explanation**: Get human-readable explanations of SQL queries

    ## Security
    - CSRF protection for state-changing operations
    - CORS configuration for cross-origin requests
    - Input validation and sanitization
    """,
    doc="/docs/",  # Swagger UI endpoint
    authorizations={
        "csrf": {
            "type": "apiKey",
            "in": "header",
            "name": "X-CSRFToken",
            "description": "CSRF token for protection against cross-site request forgery",
        }
    },
    security="csrf",
)

# Request/Response Models

# Text-to-SQL Models
text_to_sql_request = api.model(
    "TextToSQLRequest",
    {
        "question": fields.String(
            required=True,
            description="Natural language question to convert to SQL",
            example="How many customers are there in New York?",
        ),
        "include_metadata": fields.Boolean(
            default=False,
            description="Include query metadata and caching information in response",
        ),
    },
)

text_to_sql_response = api.model(
    "TextToSQLResponse",
    {
        "sql": fields.String(
            required=True,
            description="Generated SQL query",
            example="SELECT COUNT(*) FROM customers WHERE city = 'New York';",
        ),
        "question": fields.String(description="Original natural language question"),
        "cached": fields.Boolean(
            description="Whether the result was retrieved from cache"
        ),
        "similarity_score": fields.Float(
            description="Similarity score for cached results (0-1)"
        ),
        "metadata": fields.Raw(
            description="Additional metadata about the query generation process"
        ),
    },
)

# SQL Execution Models
execute_sql_request = api.model(
    "ExecuteSQLRequest",
    {
        "sql": fields.String(
            required=True,
            description="SQL query to execute",
            example="SELECT COUNT(*) FROM customers WHERE city = 'New York';",
        ),
        "limit": fields.Integer(
            default=100,
            description="Maximum number of rows to return",
            min=1,
            max=10000,
        ),
    },
)

execute_sql_response = api.model(
    "ExecuteSQLResponse",
    {
        "data": fields.List(
            fields.Raw(), description="Query results as array of objects"
        ),
        "columns": fields.List(
            fields.String(), description="Column names in the result set"
        ),
        "row_count": fields.Integer(description="Number of rows returned"),
        "execution_time": fields.Float(description="Query execution time in seconds"),
        "sql": fields.String(description="Executed SQL query"),
    },
)

# Combined Text-to-SQL and Execute Models
text_to_sql_execute_request = api.model(
    "TextToSQLExecuteRequest",
    {
        "question": fields.String(
            required=True,
            description="Natural language question to convert to SQL and execute",
            example="Show me the top 5 customers by total orders",
        ),
        "limit": fields.Integer(
            default=100,
            description="Maximum number of rows to return",
            min=1,
            max=10000,
        ),
        "include_metadata": fields.Boolean(
            default=False,
            description="Include query metadata and caching information in response",
        ),
    },
)

text_to_sql_execute_response = api.model(
    "TextToSQLExecuteResponse",
    {
        "sql": fields.String(required=True, description="Generated SQL query"),
        "data": fields.List(
            fields.Raw(), description="Query results as array of objects"
        ),
        "columns": fields.List(
            fields.String(), description="Column names in the result set"
        ),
        "row_count": fields.Integer(description="Number of rows returned"),
        "execution_time": fields.Float(description="Query execution time in seconds"),
        "question": fields.String(description="Original natural language question"),
        "cached": fields.Boolean(
            description="Whether the SQL was retrieved from cache"
        ),
        "similarity_score": fields.Float(
            description="Similarity score for cached results (0-1)"
        ),
        "metadata": fields.Raw(
            description="Additional metadata about the query generation process"
        ),
    },
)

# SQL Explanation Models
explain_sql_request = api.model(
    "ExplainSQLRequest",
    {
        "sql": fields.String(
            required=True,
            description="SQL query to explain",
            example="SELECT c.name, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY order_count DESC LIMIT 5;",
        )
    },
)

explain_sql_response = api.model(
    "ExplainSQLResponse",
    {
        "explanation": fields.String(
            required=True, description="Human-readable explanation of the SQL query"
        ),
        "sql": fields.String(description="Original SQL query"),
        "complexity": fields.String(
            description="Query complexity assessment (simple, medium, complex)",
            enum=["simple", "medium", "complex"],
        ),
    },
)

# SQL Validation Models
validate_sql_request = api.model(
    "ValidateSQLRequest",
    {
        "sql": fields.String(
            required=True,
            description="SQL query to validate",
            example="SELECT * FROM customers WHERE id = 1;",
        )
    },
)

validate_sql_response = api.model(
    "ValidateSQLResponse",
    {
        "valid": fields.Boolean(
            required=True, description="Whether the SQL is syntactically valid"
        ),
        "sql": fields.String(description="Original SQL query"),
        "errors": fields.List(
            fields.String(), description="List of validation errors if any"
        ),
        "warnings": fields.List(
            fields.String(), description="List of validation warnings if any"
        ),
    },
)

# LLM SQL Validation Models
validate_sql_llm_request = api.model(
    "ValidateSQLLLMRequest",
    {
        "sql": fields.String(
            required=True,
            description="SQL query to validate using LLM",
            example="SELECT * FROM customers WHERE id = 1;",
        ),
        "context": fields.String(
            description="Additional context for validation (optional)",
            example="This query should return customer details for a specific customer ID",
        ),
    },
)

validate_sql_llm_response = api.model(
    "ValidateSQLLLMResponse",
    {
        "valid": fields.Boolean(
            required=True,
            description="Whether the SQL is semantically valid according to LLM",
        ),
        "sql": fields.String(description="Original SQL query"),
        "feedback": fields.String(description="LLM feedback about the query"),
        "suggestions": fields.List(
            fields.String(), description="Suggested improvements if any"
        ),
        "confidence_score": fields.Float(
            description="LLM confidence in the validation (0-1)"
        ),
    },
)

# Health Check Models
health_response = api.model(
    "HealthResponse",
    {
        "status": fields.String(
            required=True,
            description="Service health status",
            enum=["healthy", "degraded", "unhealthy"],
        ),
        "timestamp": fields.String(description="Health check timestamp"),
        "version": fields.String(description="API version"),
        "database": fields.String(description="Database connection status"),
        "llm": fields.String(description="LLM service status"),
        "vectorstore": fields.String(description="Vector store (ChromaDB) status"),
    },
)

# CSRF Token Models
csrf_token_response = api.model(
    "CSRFTokenResponse",
    {
        "csrf_token": fields.String(
            required=True, description="CSRF token for subsequent requests"
        ),
        "expires_in": fields.Integer(description="Token expiration time in seconds"),
    },
)

# Error Models
error_response = api.model(
    "ErrorResponse",
    {
        "error": fields.String(required=True, description="Error message"),
        "code": fields.String(description="Error code"),
        "details": fields.Raw(description="Additional error details"),
    },
)

# Vectorization Models (for the vectorization endpoints)
database_connection_model = api.model(
    "DatabaseConnection",
    {
        "id": fields.Integer(description="Database connection ID"),
        "name": fields.String(required=True, description="Connection name"),
        "connection_string": fields.String(
            required=True, description="Database connection string"
        ),
        "database_type": fields.String(required=True, description="Type of database"),
        "is_active": fields.Boolean(description="Whether the connection is active"),
    },
)

table_config_model = api.model(
    "TableConfig",
    {
        "id": fields.Integer(description="Table configuration ID"),
        "connection_id": fields.Integer(
            required=True, description="Database connection ID"
        ),
        "table_name": fields.String(required=True, description="Name of the table"),
        "vectorization_enabled": fields.Boolean(
            description="Whether vectorization is enabled"
        ),
        "description": fields.String(description="Table description"),
    },
)
