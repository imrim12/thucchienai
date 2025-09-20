#!/bin/bash
set -e

echo "Post-startup database restoration script..."

# Set PostgreSQL password for non-interactive connections
export PGPASSWORD=postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U postgres; do
  echo "PostgreSQL is not ready yet... waiting"
  sleep 2
done
echo "PostgreSQL is ready!"

# Check if data already exists in the main database
TABLES_COUNT=$(psql -h postgres -U postgres -d applydb -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

if [ "$TABLES_COUNT" -gt 0 ]; then
    echo "Database already contains $TABLES_COUNT tables. Skipping restoration."
    exit 0
fi

echo "Database is empty. Starting restoration..."

# Extract database name from METADATA_DATABASE_URL if available
if [ -n "$METADATA_DATABASE_URL" ]; then
    METADATA_DB_NAME=$(echo "$METADATA_DATABASE_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
    echo "Creating metadata database: $METADATA_DB_NAME"
    
    # Create the metadata database if it doesn't exist
    psql -h postgres -U postgres -d postgres << EOF
SELECT 'CREATE DATABASE $METADATA_DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$METADATA_DB_NAME')
\gexec
EOF
fi

# Check if backup file exists
if [ -f "/app/docker/init-db/dump.bak" ]; then
    echo "Found backup file, restoring to applydb..."
    
    # Restore the backup using pg_restore for custom format (-Fc) dumps
    pg_restore -v \
        --host=postgres \
        --username=postgres \
        --dbname=applydb \
        --no-owner \
        --no-privileges \
        --clean \
        --if-exists \
        --format=custom \
        /app/docker/init-db/dump.bak
    
    echo "Database restored from backup successfully!"
else
    echo "ERROR: No backup file found at /app/docker/init-db/dump.bak"
    exit 1
fi

echo "Database restoration completed!"