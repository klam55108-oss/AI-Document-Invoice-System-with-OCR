# Quickstart Guide

**Created**: 2024-12-19  
**Purpose**: Step-by-step setup instructions for the e-invoice scaffold

## Prerequisites

- **Python**: 3.12.2 (via miniconda3 at `/Users/william.jiang/miniconda3/bin/python`)
- **Docker & Docker Compose**: For PostgreSQL with extensions
- **Git**: For cloning repository (if applicable)
- **macOS**: MacBook Pro (as specified)

## Step 1: Clone and Navigate to Project

```bash
cd /Users/william.jiang/my-apps/ai-einvoicing
```

## Step 2: Create Virtual Environment

```bash
# Using the specified Python interpreter
/Users/william.jiang/miniconda3/bin/python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify Python version
python --version  # Should show 3.12.2
```

## Step 3: Install Dependencies

```bash
# Install project dependencies
pip install -e .

# Or if using pyproject.toml directly:
pip install -r requirements.txt  # (if generated from pyproject.toml)
```

**Expected packages installed:**
- FastAPI, uvicorn
- SQLAlchemy, asyncpg
- Pydantic v2
- LlamaIndex (minimal)
- Docling, pandas
- Streamlit
- cryptography
- structlog
- pytest, ruff, mypy

## Step 4: Set Up PostgreSQL with Docker Compose

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: ai-einvoicing-db
    environment:
      POSTGRES_USER: einvoice
      POSTGRES_PASSWORD: einvoice_dev
      POSTGRES_DB: einvoicing
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U einvoice"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

Start PostgreSQL:

```bash
docker-compose up -d

# Verify it's running
docker-compose ps
```

**Note**: The `pgvector/pgvector:pg16` image includes both `pgvector` and `pgqueuer` extensions.

## Step 5: Configure Environment Variables

Create `.env` file in project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://einvoice:einvoice_dev@localhost:5432/einvoicing
DATABASE_SYNC_URL=postgresql://einvoice:einvoice_dev@localhost:5432/einvoicing

# Encryption (generate a key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-generated-encryption-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Application
API_HOST=0.0.0.0
API_PORT=8000
STREAMLIT_PORT=8501
```

**Security Note**: Never commit `.env` to version control. Use `.env.example` as template.

## Step 6: Initialize Database

```bash
# Run database migrations (Alembic)
alembic upgrade head

# Or manually create extensions and tables:
# python -m core.database init
```

**Manual Setup** (if Alembic not configured yet):

```bash
# Connect to PostgreSQL
docker exec -it ai-einvoicing-db psql -U einvoice -d einvoicing

# In psql, run:
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgqueuer;
```

Then create tables using SQLAlchemy models (see `core/models.py`).

## Step 7: Create Data Directory

```bash
mkdir -p data
# Add sample invoice files here (PDF, Excel, Images)
```

## Step 8: Verify Installation

```bash
# Run health check
python -m interface.api.main --check

# Or start API server
uvicorn interface.api.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test health endpoint:
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T10:30:00Z",
  "version": "1.0.0"
}
```

## Step 9: Process Your First Invoice

### Option A: Via API

```bash
# Place a sample invoice in data/ directory
cp /path/to/sample_invoice.pdf data/

# Trigger processing via API
curl -X POST http://localhost:8000/api/v1/invoices/process \
  -H "Content-Type: application/json" \
  -d '{"file_path": "sample_invoice.pdf"}'
```

### Option B: Via Python Script

```bash
python -m ingestion.orchestrator process data/sample_invoice.pdf
```

## Step 10: View Results

### Option A: Via API

```bash
# List all invoices
curl http://localhost:8000/api/v1/invoices

# Get specific invoice details
curl http://localhost:8000/api/v1/invoices/{invoice_id}
```

### Option B: Via Streamlit Dashboard

```bash
# Start Streamlit dashboard
streamlit run interface/dashboard/app.py --server.port 8501

# Open browser to http://localhost:8501
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart if needed
docker-compose restart postgres
```

### Python Import Errors

```bash
# Verify virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install --upgrade -e .
```

### Port Already in Use

```bash
# Change ports in .env file or docker-compose.yml
# Or kill existing process:
lsof -ti:8000 | xargs kill  # For API
lsof -ti:8501 | xargs kill  # For Streamlit
```

### Missing Extensions

```bash
# Connect to database and verify extensions
docker exec -it ai-einvoicing-db psql -U einvoice -d einvoicing -c "\dx"

# Should show: pgvector, pgqueuer
```

## Next Steps

1. **Add Sample Data**: Place invoice files (PDF, Excel, Images) in `data/` directory
2. **Process Invoices**: Use API or Python scripts to process files
3. **Review Results**: Check dashboard or API responses for extracted data
4. **Explore Code**: Review `core/`, `ingestion/`, `brain/`, `interface/` modules
5. **Run Tests**: `pytest tests/` (when test suite is implemented)

## Development Workflow

1. **Make Changes**: Edit code in respective modules
2. **Run Linter**: `ruff check .`
3. **Type Check**: `mypy .`
4. **Run Tests**: `pytest`
5. **Start Services**: `docker-compose up -d` (database) + `uvicorn interface.api.main:app --reload`

## Project Structure Reference

```
ai-einvoicing/
├── core/              # Database, encryption, logging
├── ingestion/        # File processing (PDF, Excel, Images)
├── brain/            # Data extraction, validation
├── interface/        # FastAPI + Streamlit
│   ├── api/          # REST API
│   └── dashboard/    # Streamlit UI
├── data/             # Sample invoice files
├── tests/            # Test suite
├── docker-compose.yml
├── pyproject.toml
└── .env              # Environment variables (not in git)
```

## Support

- **Documentation**: See `README.md` and `docs/` directory
- **API Docs**: http://localhost:8000/docs (FastAPI auto-generated)
- **Specification**: `specs/1-e-invoice-scaffold/spec.md`
- **Implementation Plan**: `specs/1-e-invoice-scaffold/plan.md`

## Expected Setup Time

Following this guide, a new developer should be able to:
- Set up environment: **5-10 minutes**
- Start services: **2-3 minutes**
- Process first invoice: **2-5 minutes**

**Total: ~15-20 minutes** (within the 30-minute target from spec)

