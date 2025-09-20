# Text-to-SQL API Service

A web service that converts natural language questions into SQL queries using Google Gemini AI, with intelligent caching and SQL validation.

## Features

- 🧠 **AI-Powered**: Uses Google Gemini LLM for natural language to SQL conversion
- 🚀 **Smart Caching**: PostgreSQL-based cache with vector similarity search
- 🔍 **Similarity Search**: Finds similar cached queries to avoid redundant processing
- 🔧 **RESTful API**: Clean Flask-based REST API
- 📊 **Query Execution**: Optional SQL execution against target databases
- 🛡️ **SQL Validation**: Built-in SQL syntax validation and security checks
- 🔒 **Readonly Mode**: Restricts output to SELECT-only queries for security
- 🛡️ **CSRF Protection**: Cross-Site Request Forgery protection for all POST endpoints
- 🌐 **CORS Security**: Configurable CORS with restricted origins and headers
- 🏥 **Health Monitoring**: Built-in health checks and cache statistics

## API Endpoints

### POST /api/text-to-sql
Convert natural language to SQL query with validation.

**Request:**
```json
{
  "question": "Show me all users who joined last month",
  "readonly": true  // optional, restricts to SELECT queries only
}
```

**Response:**
```json
{
  "sql_query": "SELECT * FROM users WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
  "from_cache": false,
  "similarity_score": null,
  "cache_stats": {"total_entries": 1},
  "is_valid": true
}
```

### POST /api/explain-sql
Generate natural language explanation of SQL queries.

**Request:**
```json
{
  "sql_query": "SELECT COUNT(*) FROM users WHERE status = 'active'"
}
```

**Response:**
```json
{
  "explanation": "This query counts the number of users in the users table who have an active status."
}
```

### POST /api/validate-sql
Basic SQL syntax validation (local parsing).

**Request:**
```json
{
  "sql_query": "SELECT * FROM users; DROP TABLE users;",
  "readonly": true
}
```

**Response:**
```json
{
  "is_valid": false,
  "cleaned_sql": "",
  "is_select_only": false,
  "passed_readonly_check": false
}
```

### POST /api/validate-sql-with-llm
Advanced SQL validation and correction using LLM.

**Request:**
```json
{
  "sql_query": "SELCT * FROM users WERE age > 25",  // typos
  "readonly": false
}
```

**Response:**
```json
{
  "is_valid": true,
  "corrected_sql": "SELECT * FROM users WHERE age > 25",
  "explanation": "SQL corrected by LLM."
}
```

### POST /api/execute-sql
Execute SQL query against target database.

### POST /api/text-to-sql-and-execute
Convert to SQL and execute in one step (supports readonly parameter).

### GET /api/cache/stats
Get cache statistics.

### POST /api/cache/clear
Clear the cache.

### GET /health
Service health check.

## 🔐 Authentication & Security

### CSRF Protection
All POST endpoints require CSRF token validation when enabled. To use protected endpoints:

1. **Get CSRF Token:**
```bash
curl -X GET http://localhost:5000/api/csrf-token
```

Response:
```json
{
  "csrf_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

2. **Include Token in POST Requests:**
```bash
curl -X POST http://localhost:5000/api/text-to-sql \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN_HERE" \
  -d '{"question": "Show me all users"}'
```

### CORS Configuration
CORS is configured with restricted origins and headers for security:
- **Allowed Origins**: Configurable via `CORS_ORIGINS` environment variable
- **Allowed Headers**: `Content-Type`, `X-CSRFToken`
- **Credentials**: Supported for cookie-based authentication

## SQL Validation Features

### 🛡️ **Security Features**
- **Syntax Validation**: Ensures SQL is syntactically correct
- **Readonly Mode**: When `readonly=true`, only SELECT statements are allowed
- **Query Cleaning**: Removes markdown, comments, and explanatory text
- **Empty String on Invalid**: Returns empty string instead of potentially dangerous SQL

### 🔍 **Supported Validations**
- SQL syntax parsing using `sqlparse`
- Detection of DML operations (INSERT, UPDATE, DELETE)
- Detection of DDL operations (CREATE, DROP, ALTER)
- Cleaning of LLM response artifacts (markdown code blocks, explanations)

## Configuration

Set the following environment variables in `.env`:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here
CACHE_DB_URI=postgresql://username:password@localhost:5432/cache_db

# Security (Required for production)
CSRF_SECRET=your_csrf_secret_key_here
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional
TARGET_DB_URI=postgresql://username:password@localhost:5432/target_db
SIMILARITY_THRESHOLD=0.8
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database for caching

3. Configure environment variables in `.env`

4. Run the service:
```bash
python main.py
```

## Architecture

- **src/agents/**: Text-to-SQL agent with validation logic
- **src/api/**: Flask API endpoints and server configuration
- **src/core/**: Configuration management
- **src/llm/**: Google Gemini LLM provider (renamed from gemini_provider.py)
- **src/database/**: PostgreSQL cache management
- **src/prompts/**: Centralized prompt management system
  - `system.py`: System prompts for different modes
  - `user.py`: User message templates
  - `validation.py`: SQL validation prompts
  - `helpers.py`: Utility prompts for explanations
- **src/utils/**: Vector utilities and helpers (renamed from vector_utils.py)

## Prompt Management System

The service now uses a centralized prompt management system with the following benefits:

### 🎯 **Organized Prompts**
- **System Prompts**: Define AI behavior and constraints
- **User Prompts**: Template user messages with dynamic content
- **Validation Prompts**: Specialized prompts for SQL correction
- **Helper Prompts**: Utility prompts for explanations and analysis

### 🔄 **Easy Maintenance**
- All prompts are externalized from code
- Version control for prompt changes
- Easy A/B testing of different prompt variations
- Centralized prompt optimization

### 📝 **Available Prompt Types**
```python
# System prompts
get_text_to_sql_prompt(readonly=False)

# User prompts
get_user_prompt(question, readonly=False, schema_info=None)

# Validation prompts
get_validation_prompt(sql_query, readonly=False)

# Helper prompts
get_explanation_prompt(sql_query)
```

## Technology Stack

- **Web Framework**: Flask
- **LLM**: Google Gemini (via LangChain)
- **Cache Database**: PostgreSQL
- **SQL Validation**: sqlparse
- **Vector Operations**: NumPy, FAISS
- **Configuration**: Pydantic Settings