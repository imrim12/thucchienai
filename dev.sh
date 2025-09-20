#!/bin/bash

# Text-to-SQL Development Helper Scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found"
        print_status "Copying .env.example to .env"
        cp .env.example .env
        print_warning "Please edit .env and add your GOOGLE_API_KEY"
        return 1
    fi
    
    if ! grep -q "GOOGLE_API_KEY=" .env || grep -q "GOOGLE_API_KEY=\"\"" .env; then
        print_warning "GOOGLE_API_KEY not set in .env file"
        print_warning "Please edit .env and add your Google API key"
        return 1
    fi
    
    return 0
}

# Start all services
start() {
    print_status "Starting Text-to-SQL development environment..."
    
    if ! check_env; then
        print_error "Environment setup required. Please configure .env file first."
        exit 1
    fi
    
    # Create data directories if they don't exist
    mkdir -p docker/chroma_data data/postgres_data
    
    docker-compose -f docker-compose.dev.yml up -d
    
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "✅ Text-to-SQL API is ready at http://localhost:5000"
    else
        print_warning "⚠️  Text-to-SQL API health check failed"
    fi
    
    print_status "🐘 PostgreSQL is available at localhost:5432"
    print_status "📊 pgAdmin is available at http://localhost:8080 (with --profile pgadmin)"
}

# Start with pgAdmin
start_with_pgadmin() {
    print_status "Starting Text-to-SQL development environment with pgAdmin..."
    
    if ! check_env; then
        print_error "Environment setup required. Please configure .env file first."
        exit 1
    fi
    
    mkdir -p docker/chroma_data data/postgres_data
    
    docker-compose -f docker-compose.dev.yml --profile pgadmin up -d
    
    print_status "Waiting for services to be ready..."
    sleep 15
    
    print_status "✅ Text-to-SQL API is ready at http://localhost:5000"
    print_status "🐘 PostgreSQL is available at localhost:5432"
    print_status "📊 pgAdmin is available at http://localhost:8080"
    print_status "   - Email: admin@example.com"
    print_status "   - Password: admin"
}

# Stop all services
stop() {
    print_status "Stopping Text-to-SQL development environment..."
    docker-compose -f docker-compose.dev.yml down
    print_status "✅ All services stopped"
}

# Clean restart
clean() {
    print_status "Cleaning up and restarting..."
    docker-compose -f docker-compose.dev.yml down -v
    print_status "Removed all volumes"
    
    # Clean up data directories
    rm -rf docker/chroma_data/* data/postgres_data/*
    print_status "Cleaned data directories"
    
    start
}

# Show logs
logs() {
    if [ -z "$1" ]; then
        docker-compose -f docker-compose.dev.yml logs -f
    else
        docker-compose -f docker-compose.dev.yml logs -f "$1"
    fi
}

# Show status
status() {
    print_status "Service Status:"
    docker-compose -f docker-compose.dev.yml ps
    
    echo
    print_status "Health Checks:"
    
    # API Health
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        print_status "✅ API: Healthy"
    else
        print_error "❌ API: Unhealthy"
    fi
    
    # PostgreSQL Health
    if docker exec text-to-sql-postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_status "✅ PostgreSQL: Ready"
    else
        print_error "❌ PostgreSQL: Not ready"
    fi
}

# Test API
test() {
    print_status "Testing Text-to-SQL API..."
    
    echo
    print_status "Health Check:"
    curl -s http://localhost:5000/health | jq '.' || print_error "Health check failed"
    
    echo
    print_status "Sample Text-to-SQL Query:"
    curl -s -X POST http://localhost:5000/api/text-to-sql \
        -H "Content-Type: application/json" \
        -d '{"question": "Show me all customers from New York"}' | jq '.' || print_error "API test failed"
}

# Show help
help() {
    echo "Text-to-SQL Development Helper"
    echo
    echo "Usage: $0 [command]"
    echo
    echo "Commands:"
    echo "  start              Start all services"
    echo "  start-pgadmin      Start all services including pgAdmin"
    echo "  stop               Stop all services"
    echo "  clean              Clean restart (removes all data)"
    echo "  logs [service]     Show logs (optional: specify service)"
    echo "  status             Show service status and health"
    echo "  test               Test the API endpoints"
    echo "  help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start           # Start development environment"
    echo "  $0 logs api        # Show API logs"
    echo "  $0 test            # Test the API"
}

# Main script logic
case "$1" in
    "start")
        start
        ;;
    "start-pgadmin")
        start_with_pgadmin
        ;;
    "stop")
        stop
        ;;
    "clean")
        clean
        ;;
    "logs")
        logs "$2"
        ;;
    "status")
        status
        ;;
    "test")
        test
        ;;
    "help"|"")
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac