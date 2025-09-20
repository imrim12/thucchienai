Act as an expert Python developer specializing in building LLM-powered applications.

I want you to bootstrap a Text-to-SQL API service. Please generate the complete project structure and boilerplate code based on the following detailed requirements.

Project Overview
The goal is to create a web service that accepts a natural language question, converts it into a SQL query, executes it against a database, and returns the result. The service must include a caching mechanism to avoid re-generating SQL for similar questions.

Core Technology Stack
Web Framework: Flask

LLM Framework: LangChain

LLM & Embedding Model: Google Gemini (please use the langchain-google-genai library).

Database for Caching: PostgreSQL

Vector Store for Similarity Search: Use a simple in-memory store like FAISS or a file-based one for the initial setup, as we will query the cache first.

Project Structure
Please adhere strictly to this directory structure. It is designed for clarity, scalability, and maintainability.

/text-to-sql-service
|
├── .env
├── .gitignore
├── main.py
├── requirements.txt
├── README.md
|
└── src/
    |
    ├── __init__.py
    |
    ├── api/
    |   ├── __init__.py
    |   └── server.py         # Flask app definition, routes, and API endpoints.
    |
    ├── core/
    |   ├── __init__.py
    |   └── config.py         # Manages environment variables (API keys, DB URIs).
    |
    ├── llm/
    |   ├── __init__.py
    |   └── gemini_provider.py  # Initializes Gemini LLM and Embedding models.
    |
    ├── database/
    |   ├── __init__.py
    |   ├── chroma_db.py        # Manages ChromaDB for vector similarity caching
    |   ├── database.py         # SQLAlchemy session management
    |   └── models/             # Database models for vectorization system
    |       ├── __init__.py
    |       ├── base.py
    |       ├── enums.py
    |       ├── database_connection.py
    |       ├── table_config.py
    |       ├── column_config.py
    |       └── vectorization_job.py
    |
    ├── services/
    |   ├── __init__.py
    |   └── text_to_sql_service.py # Core business logic for the Text-to-SQL conversion.
    |
    └── utils/
        ├── __init__.py
        └── vector_utils.py     # Helper functions for vector operations.

Key Implementation Details
src/core/config.py:

Create a Settings class using Pydantic or a simple class to load GOOGLE_API_KEY and database connection settings from the .env file.

src/database/chroma_db.py:

Define a class ChromaCache.

Implement a method connect() to establish the ChromaDB connection.

Implement methods like add_to_cache(question, sql, vector) and find_similar_question(vector, threshold).

src/database/models/:

SQLAlchemy models for managing database vectorization configurations:
- DatabaseConnection: Store external database connections
- TableConfig: Configure table vectorization settings  
- ColumnConfig: Detailed column configurations
- VectorizationJob: Track processing jobs and status

src/llm/gemini_provider.py:

Create functions get_gemini_llm() and get_gemini_embeddings() that initialize and return instances of the respective models using the API key from the config.

src/services/text_to_sql_service.py:

This is the main logic hub. Create a TextToSQLService class.

In its __init__, it should initialize the LLM, embedding model, and the ChromaCache.

Implement the primary method: def process_question(natural_question: str).

The logic for process_question must be:
a.  Generate an embedding for the natural_question.
b.  Query the ChromaCache to find if a similar question vector exists above a certain similarity threshold.
c.  If a similar question is found in the cache: Return the cached SQL query.
d.  If not found:
i.  Use LangChain's SQL Chain (create_sql_query_chain) with the Gemini LLM to generate the SQL query from the natural_question.
ii. Store the new natural_question, the generated sql_query, and its question_vector into the ChromaDB cache.
iii. Return the newly generated SQL query.

src/api/server.py:

Create a simple Flask application.

Define a POST endpoint, e.g., /api/text-to-sql.

This endpoint should receive a JSON payload like {"question": "your question here"}.

It will call the process_question method from the TextToSQLService and return the resulting SQL query in a JSON response.

main.py:

The entry point of the application. It should import the Flask app instance from src/api/server.py and run it.

requirements.txt:

Please include all necessary libraries: flask, langchain, langchain-google-genai, psycopg2-binary, numpy, faiss-cpu, and any others required.

Please generate the code with clear comments, type hints, and follow snake_case for files and functions and PascalCase for classes. Thank you!