#!/bin/bash

source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start Database
docker-compose up -d

# Run Migrations
alembic upgrade head


