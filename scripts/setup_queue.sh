#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is not set."
    exit 1
fi

# Extract connection details from DATABASE_URL
# postgresql+asyncpg://user:password@host:port/dbname
# We need to convert it to standard format for pgq CLI or psql if needed
# pgq CLI actually might take the URL or environment variables

echo "Installing pgqueuer schema..."
# Assuming pgqueuer is installed in the current environment
# We use python -m pgqueuer for reliability
python -m pgqueuer install --durability balanced

echo "pgqueuer schema installed successfully."
