#!/bin/bash
# Setup script for e-invoice scaffold development environment

set -e

echo "Setting up e-invoice development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration, especially ENCRYPTION_KEY"
fi

# Start PostgreSQL with docker-compose
echo "Starting PostgreSQL with docker-compose..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Run database migrations (if database is accessible)
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Run: alembic upgrade head (to create database schema)"
echo "3. Run: uvicorn interface.api.main:app --reload (to start API)"
echo "4. Run: streamlit run interface/dashboard/app.py (to start dashboard)"

