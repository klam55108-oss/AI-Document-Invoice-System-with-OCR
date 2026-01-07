#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Strip +asyncpg if present for compatibility with standard DSN tools
# pgqueuer CLI uses PGDSN or --pg-dsn
DSN=$(echo $DATABASE_URL | sed 's/+asyncpg//')
export PGDSN=$DSN

echo "Installing pgqueuer schema..."
# Assuming pgqueuer is installed in the current environment
# We use python -m pgqueuer for reliability
# If it's already installed, 'install' will fail, so we ignore DuplicateObjectError or use verify
python -m pgqueuer install --durability balanced 2>/dev/null || echo "pgqueuer might already be installed, verifying..."

echo "Verifying pgqueuer installation..."
python -m pgqueuer verify --expect present

echo "pgqueuer schema is healthy and installed successfully."
