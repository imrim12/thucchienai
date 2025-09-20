# Text-to-SQL Development Helper Scripts for Windows
# PowerShell version

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Service = ""
)

# Colors for output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if .env file exists and is configured
function Test-Environment {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found"
        Write-Status "Copying .env.example to .env"
        Copy-Item ".env.example" ".env"
        Write-Warning "Please edit .env and add your GOOGLE_API_KEY"
        return $false
    }
    
    $envContent = Get-Content ".env" -Raw
    if ($envContent -notmatch "GOOGLE_API_KEY=.+" -or $envContent -match 'GOOGLE_API_KEY=""') {
        Write-Warning "GOOGLE_API_KEY not set in .env file"
        Write-Warning "Please edit .env and add your Google API key"
        return $false
    }
    
    return $true
}

# Start all services
function Start-Services {
    Write-Status "Starting Text-to-SQL development environment..."
    
    if (-not (Test-Environment)) {
        Write-Error "Environment setup required. Please configure .env file first."
        exit 1
    }
    
    # Create data directories if they don't exist
    New-Item -ItemType Directory -Force -Path "docker\chroma_data" | Out-Null
    New-Item -ItemType Directory -Force -Path "data\postgres_data" | Out-Null
    
    docker-compose -f docker-compose.dev.yml up -d
    
    Write-Status "Waiting for services to be ready..."
    Start-Sleep -Seconds 10
    
    # Check health
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5
        Write-Status "✅ Text-to-SQL API is ready at http://localhost:5000"
    }
    catch {
        Write-Warning "⚠️  Text-to-SQL API health check failed"
    }
    
    Write-Status "🐘 PostgreSQL is available at localhost:5432"
    Write-Status "📊 pgAdmin is available at http://localhost:8080 (with --profile pgadmin)"
}

# Start with pgAdmin
function Start-WithPgAdmin {
    Write-Status "Starting Text-to-SQL development environment with pgAdmin..."
    
    if (-not (Test-Environment)) {
        Write-Error "Environment setup required. Please configure .env file first."
        exit 1
    }
    
    New-Item -ItemType Directory -Force -Path "docker\chroma_data" | Out-Null
    New-Item -ItemType Directory -Force -Path "data\postgres_data" | Out-Null
    
    docker-compose -f docker-compose.dev.yml --profile pgadmin up -d
    
    Write-Status "Waiting for services to be ready..."
    Start-Sleep -Seconds 15
    
    Write-Status "✅ Text-to-SQL API is ready at http://localhost:5000"
    Write-Status "🐘 PostgreSQL is available at localhost:5432"
    Write-Status "📊 pgAdmin is available at http://localhost:8080"
    Write-Status "   - Email: admin@example.com"
    Write-Status "   - Password: admin"
}

# Stop all services
function Stop-Services {
    Write-Status "Stopping Text-to-SQL development environment..."
    docker-compose -f docker-compose.dev.yml down
    Write-Status "✅ All services stopped"
}

# Clean restart
function Start-Clean {
    Write-Status "Cleaning up and restarting..."
    docker-compose -f docker-compose.dev.yml down -v
    Write-Status "Removed all volumes"
    
    # Clean up data directories
    if (Test-Path "docker\chroma_data") {
        Remove-Item -Path "docker\chroma_data\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path "data\postgres_data") {
        Remove-Item -Path "data\postgres_data\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Status "Cleaned data directories"
    
    Start-Services
}

# Show logs
function Show-Logs {
    param([string]$ServiceName = "")
    
    if ($ServiceName -eq "") {
        docker-compose -f docker-compose.dev.yml logs -f
    }
    else {
        docker-compose -f docker-compose.dev.yml logs -f $ServiceName
    }
}

# Show status
function Show-Status {
    Write-Status "Service Status:"
    docker-compose -f docker-compose.dev.yml ps
    
    Write-Host
    Write-Status "Health Checks:"
    
    # API Health
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET -TimeoutSec 5
        Write-Status "✅ API: Healthy"
    }
    catch {
        Write-Error "❌ API: Unhealthy"
    }
    
    # PostgreSQL Health
    try {
        $null = docker exec text-to-sql-postgres pg_isready -U postgres 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "✅ PostgreSQL: Ready"
        }
        else {
            Write-Error "❌ PostgreSQL: Not ready"
        }
    }
    catch {
        Write-Error "❌ PostgreSQL: Not ready"
    }
}

# Test API
function Test-API {
    Write-Status "Testing Text-to-SQL API..."
    
    Write-Host
    Write-Status "Health Check:"
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET
        $healthResponse | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Error "Health check failed: $_"
    }
    
    Write-Host
    Write-Status "Sample Text-to-SQL Query:"
    try {
        $body = @{
            question = "Show me all customers from New York"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:5000/api/text-to-sql" -Method POST -Body $body -ContentType "application/json"
        $response | ConvertTo-Json -Depth 10
    }
    catch {
        Write-Error "API test failed: $_"
    }
}

# Show help
function Show-Help {
    Write-Host "Text-to-SQL Development Helper for Windows"
    Write-Host
    Write-Host "Usage: .\dev.ps1 [command] [service]"
    Write-Host
    Write-Host "Commands:"
    Write-Host "  start              Start all services"
    Write-Host "  start-pgadmin      Start all services including pgAdmin"
    Write-Host "  stop               Stop all services"
    Write-Host "  clean              Clean restart (removes all data)"
    Write-Host "  logs [service]     Show logs (optional: specify service)"
    Write-Host "  status             Show service status and health"
    Write-Host "  test               Test the API endpoints"
    Write-Host "  help               Show this help message"
    Write-Host
    Write-Host "Examples:"
    Write-Host "  .\dev.ps1 start           # Start development environment"
    Write-Host "  .\dev.ps1 logs text-to-sql-api  # Show API logs"
    Write-Host "  .\dev.ps1 test            # Test the API"
}

# Main script logic
switch ($Command.ToLower()) {
    "start" {
        Start-Services
    }
    "start-pgadmin" {
        Start-WithPgAdmin
    }
    "stop" {
        Stop-Services
    }
    "clean" {
        Start-Clean
    }
    "logs" {
        Show-Logs -ServiceName $Service
    }
    "status" {
        Show-Status
    }
    "test" {
        Test-API
    }
    "help" {
        Show-Help
    }
    default {
        Write-Error "Unknown command: $Command"
        Show-Help
        exit 1
    }
}