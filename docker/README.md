# Docker Development Setup

This directory contains Docker configuration for the Text-to-SQL service development environment.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```

2. **Start all services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Check service health:**
   ```bash
   curl http://localhost:5000/health
   ```

4. **Test the API:**
   ```bash
   curl -X POST http://localhost:5000/api/text-to-sql \
     -H "Content-Type: application/json" \
     -d '{"question": "Show me all customers from New York"}'
   ```

## Services

### text-to-sql-api
- **Port:** 5000
- **Description:** Main Flask application with Text-to-SQL functionality
- **Health Check:** `http://localhost:5000/health`
- **API Endpoint:** `http://localhost:5000/api/text-to-sql`

### postgres
- **Port:** 5432
- **Description:** PostgreSQL database with sample data for testing SQL queries
- **Database:** testdb
- **Username:** postgres
- **Password:** postgres

### pgadmin (Optional)
- **Port:** 8080
- **Description:** Web-based PostgreSQL administration tool
- **Username:** admin@example.com
- **Password:** admin
- **Profile:** pgadmin (use `--profile pgadmin` to include)

## Commands

### Start all services:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Start with pgAdmin:
```bash
docker-compose -f docker-compose.dev.yml --profile pgadmin up -d
```

### View logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f text-to-sql-api
```

### Stop all services:
```bash
docker-compose -f docker-compose.dev.yml down
```

### Clean up volumes and start fresh:
```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

### Rebuild and start:
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

## Development

The application code is mounted as a volume for hot reloading during development. Any changes to the source code will be reflected immediately without rebuilding the container.

### Accessing the Database

**Via psql:**
```bash
docker exec -it text-to-sql-postgres psql -U postgres -d testdb
```

**Via pgAdmin:**
1. Start with pgAdmin profile: `docker-compose -f docker-compose.dev.yml --profile pgadmin up -d`
2. Open http://localhost:8080
3. Login with admin@example.com / admin
4. Add server with host: postgres, port: 5432, database: testdb, username: postgres, password: postgres

## Sample Data

The PostgreSQL database is initialized with sample tables:
- `customers` - Customer information
- `orders` - Order records
- `products` - Product catalog
- `order_items` - Order line items

## Troubleshooting

### Health Check Failing
```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# Check application logs
docker-compose -f docker-compose.dev.yml logs text-to-sql-api

# Check if all dependencies are running
docker-compose -f docker-compose.dev.yml logs postgres
```

### ChromaDB Data Persistence
ChromaDB data is persisted in `./data/chroma_data`. If you need to reset the cache:
```bash
rm -rf ./data/chroma_data/*
docker-compose -f docker-compose.dev.yml restart text-to-sql-api
```

### PostgreSQL Data Reset
To reset the PostgreSQL data:
```bash
docker-compose -f docker-compose.dev.yml down -v
rm -rf ./data/postgres_data/*
docker-compose -f docker-compose.dev.yml up -d
```