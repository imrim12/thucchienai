# Text-to-SQL API Service

A web service that converts natural language questions into SQL queries using Google Gemini AI, with intelligent caching to avoid regenerating similar queries.

## Features

- 🧠 **AI-Powered**: Uses Google Gemini LLM for natural language to SQL conversion
- 🚀 **Smart Caching**: PostgreSQL-based cache with vector similarity search
- 🔍 **Similarity Search**: Finds similar cached queries to avoid redundant processing
- 🔧 **RESTful API**: Clean Flask-based REST API
- 📊 **Query Execution**: Optional SQL execution against target databases
- 🏥 **Health Monitoring**: Built-in health checks and cache statistics

## API Endpoints

### POST /api/text-to-sql
Convert natural language to SQL query.

**Request:**
```json
{
  "question": "Show me all users who joined last month"
}
```

**Response:**
```json
{
  "sql_query": "SELECT * FROM users WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')",
  "from_cache": false,
  "similarity_score": null,
  "cache_stats": {"total_entries": 1}
}
```

### POST /api/execute-sql
Execute SQL query against target database.

### POST /api/text-to-sql-and-execute
Convert to SQL and execute in one step.

### GET /api/cache/stats
Get cache statistics.

### POST /api/cache/clear
Clear the cache.

### GET /health
Service health check.

## Configuration

Set the following environment variables in `.env`:

```env
# Required
GOOGLE_API_KEY=your_google_api_key_here
POSTGRES_URI=postgresql://username:password@localhost:5432/cache_db

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

- **src/api/**: Flask API endpoints and server configuration
- **src/core/**: Configuration management
- **src/llm/**: Google Gemini LLM provider
- **src/database/**: PostgreSQL cache management
- **src/services/**: Core business logic
- **src/utils/**: Vector utilities and helpers

## Technology Stack

- **Web Framework**: Flask
- **LLM**: Google Gemini (via LangChain)
- **Cache Database**: PostgreSQL
- **Vector Operations**: NumPy, FAISS
- **Configuration**: Pydantic Settings