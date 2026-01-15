# Implementation Plan: E-Invoice Implementation Scaffold

**Status**: Draft  
**Created**: 2024-12-19  
**Last Updated**: 2024-12-19  
**Feature**: [spec.md](./spec.md)

## Technical Context

### Technology Stack

**Language & Runtime:**
- Python 3.12.2 (via miniconda3 at `/Users/william.jiang/miniconda3/bin/python`)
- Virtual environment: Single venv for MVP (as per spec assumptions)

**Database:**
- PostgreSQL (via docker-compose on MacBook Pro)
- Extensions: `pgvector` (vector storage), `pgqueuer` (job queue management)
- Connection: Async via `asyncpg` for I/O operations

**Core Frameworks:**
- FastAPI 0.115+ (async web framework for API endpoints)
- Pydantic v2 (data validation and schema definition)
- SQLAlchemy 2.0 (async ORM for database operations)
- LlamaIndex (RAG and agentic AI workflows)

**Ingestion Layer:**
- Docling (PDF/document parsing)
- Pandas (Excel/CSV parsing)
- DeepSeek-OCR (structured OCR output) - alternative option

**Interface Layer:**
- FastAPI (REST API with async endpoints)
- Streamlit (review dashboard UI)

**Infrastructure:**
- File encryption: `cryptography` library for file-level encryption at rest
- Logging: `structlog` or standard `logging` with JSON formatting
- Process management: `multiprocessing` for CPU-intensive tasks

### Architecture Decisions

1. **Concurrency Model**: Hybrid approach
   - Async/await coroutines for I/O (file reading, database operations, API calls)
   - Separate processes for CPU-intensive tasks (OCR, image processing, AI inference)
   - Rationale: Maximizes I/O throughput while preventing GIL blocking for CPU work

2. **File Identity**: SHA-256 hash-based
   - Each file gets content hash for duplicate detection
   - Version tracking allows reprocessing same file
   - Rationale: Enables version history and prevents true duplicates

3. **Error Handling**: Fail-fast with continuation
   - Failed jobs are logged and marked as failed
   - Processing continues with other files
   - Rationale: Prevents single failure from blocking entire batch

4. **Data Protection**: File-level encryption at rest
   - Sensitive invoice files encrypted before disk storage
   - No encryption in transit for local development
   - Rationale: Balances security with MVP simplicity

5. **API Response Format**: Structured JSON envelope
   - Consistent envelope with status, timestamps, pagination
   - Invoice data and validation results nested within
   - Rationale: Extensible format supporting future features

### Project Structure

```
ai-einvoicing/
├── core/              # Infrastructure: Postgres connection, pgvector, pgqueuer
│   ├── __init__.py
│   ├── database.py    # Async database connection and session management
│   ├── models.py      # SQLAlchemy models (Invoice, ProcessingJob, etc.)
│   ├── encryption.py  # File encryption utilities
│   └── logging.py     # Logging configuration
├── ingestion/         # Sensory Layer: OCR, Docling, Pandas parsing
│   ├── __init__.py
│   ├── file_discovery.py  # Discover files in data/ directory
│   ├── file_hasher.py     # SHA-256 hash calculation
│   ├── pdf_processor.py   # PDF processing via Docling
│   ├── excel_processor.py # Excel/CSV processing via Pandas
│   ├── image_processor.py # Image processing (future)
│   └── orchestrator.py    # Coordinate processing pipeline
├── brain/            # Brain Layer: LlamaIndex, Pydantic schemas, RAG logic
│   ├── __init__.py
│   ├── schemas.py     # Pydantic models for invoice data
│   ├── extractor.py   # Data extraction logic
│   ├── validator.py   # Validation rules (math checks, etc.)
│   └── rag.py         # RAG setup (future, out of scope for scaffold)
├── interface/        # Interaction Layer: FastAPI endpoints, Streamlit UI
│   ├── __init__.py
│   ├── api/          # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py    # FastAPI app entry point
│   │   ├── routes/    # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── invoices.py
│   │   │   └── health.py
│   │   └── schemas.py # API request/response models
│   └── dashboard/    # Streamlit dashboard
│       ├── __init__.py
│       └── app.py     # Streamlit app entry point
├── data/             # Local storage for sample invoices (PDF, CSV, XLSX)
│   └── .gitkeep
├── tests/            # Test suite (basic structure)
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker-compose.yml # PostgreSQL with pgvector
├── pyproject.toml     # Unified dependency management
├── .env.example       # Environment variable template
└── README.md          # Setup and usage instructions
```

### Dependencies (Latest Versions for Python 3.12)

**Core:**
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.0` - ASGI server
- `pydantic>=2.9.0` - Data validation
- `pydantic-settings>=2.6.0` - Settings management

**Database:**
- `asyncpg>=0.30.0` - Async PostgreSQL driver
- `sqlalchemy[asyncio]>=2.0.36` - Async ORM
- `alembic>=1.14.0` - Database migrations

**AI/ML:**
- `llama-index>=0.11.0` - RAG framework (scaffold phase: minimal setup)
- `pandas>=2.2.0` - Excel/CSV processing

**Document Processing:**
- `docling>=1.0.0` - PDF/document parsing
- `pypdf>=5.0.0` - PDF utilities (fallback)
- `openpyxl>=3.1.0` - Excel file support

**Utilities:**
- `python-multipart>=0.0.12` - File uploads
- `cryptography>=43.0.0` - File encryption
- `structlog>=24.4.0` - Structured logging
- `python-dotenv>=1.0.1` - Environment variables

**Development:**
- `pytest>=8.3.0` - Testing framework
- `pytest-asyncio>=0.24.0` - Async test support
- `httpx>=0.27.0` - HTTP client for testing
- `ruff>=0.6.0` - Linting and formatting
- `mypy>=1.11.0` - Type checking

**UI:**
- `streamlit>=1.39.0` - Dashboard interface

### Integration Points

1. **PostgreSQL Connection**: Async connection pool via `asyncpg`, managed through SQLAlchemy async engine
2. **File Storage**: Local filesystem with encryption wrapper
3. **Processing Queue**: PostgreSQL-based queue using `pgqueuer` extension
4. **Vector Storage**: PostgreSQL `pgvector` extension for future RAG embeddings

### Unknowns & Research Needed

See [research.md](./research.md) for detailed technology research and decisions.

## Constitution Check

### I. Code Quality Standards ✅

- **Type Safety**: All functions will use Python type hints (Python 3.12 supports latest typing features)
- **Self-Documenting**: Clear module structure, descriptive names, single responsibility per module
- **Error Handling**: Explicit exception handling with structured logging
- **Security**: Input validation via Pydantic, parameterized queries, file encryption
- **Dependencies**: Exact versions pinned in `pyproject.toml`
- **Code Reviews**: Will verify type coverage, documentation, security

**Compliance**: ✅ All requirements addressed in project structure and dependencies

### II. Testing Discipline ⚠️

- **Test-First**: Will be enforced during implementation phase
- **Coverage Targets**: 80% for core extraction/validation, 60% overall
- **Test Categories**: Unit, integration, contract tests planned
- **Automation**: Tests will run in CI/CD (setup deferred to later phase per spec)

**Compliance**: ⚠️ Testing structure defined, but test-first approach will be enforced during `/speckit.tasks` phase

### III. User Experience Consistency ✅

- **Dashboard UI**: Streamlit provides responsive components
- **Error Messages**: Structured error responses with actionable guidance
- **Progress Indicators**: Async processing with status updates
- **Accessibility**: Streamlit components meet basic accessibility (advanced features deferred)

**Compliance**: ✅ MVP requirements met, advanced features deferred per spec

### IV. Performance Requirements ⚠️

- **Extraction Latency**: Target p95 <3s (to be validated during implementation)
- **Database Performance**: Async queries with connection pooling
- **Concurrent Processing**: Hybrid async/process model supports concurrency
- **Memory Footprint**: Process isolation for CPU tasks limits memory per worker
- **Monitoring**: Basic logging in place, metrics deferred to later phase

**Compliance**: ⚠️ Architecture supports requirements, but performance validation deferred to implementation/testing phase

### Gate Evaluation

**Pre-Implementation Gates:**
1. ✅ Specification approved with clarifications
2. ✅ Constitution check completed (this document)
3. ⚠️ Test design deferred to `/speckit.tasks` phase
4. ✅ Dependency review completed (see research.md)

**Status**: ✅ Ready to proceed to Phase 1 (Design & Contracts)

## Phase 0: Research & Technology Decisions

See [research.md](./research.md) for complete research findings.

**Key Decisions:**
1. FastAPI 0.115+ for async API framework
2. SQLAlchemy 2.0 async for database operations
3. LlamaIndex for RAG foundation (minimal setup in scaffold)
4. Docling for PDF processing
5. Hybrid async/process concurrency model
6. File-level encryption using `cryptography` library

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete entity definitions, relationships, and validation rules.

**Core Entities:**
- `Invoice` - Processed invoice documents with versioning
- `ExtractedData` - Structured invoice information
- `ValidationResult` - Validation rule outcomes
- `ProcessingJob` - Job tracking and status

### API Contracts

See [contracts/](./contracts/) directory for OpenAPI specifications.

**Endpoints:**
- `GET /health` - Health check
- `GET /api/v1/invoices` - List processed invoices (paginated)
- `GET /api/v1/invoices/{invoice_id}` - Get invoice details
- `POST /api/v1/invoices/process` - Trigger invoice processing

### Quickstart Guide

See [quickstart.md](./quickstart.md) for setup and usage instructions.

## Phase 2: Implementation Planning

Implementation will be broken down into tasks via `/speckit.tasks` command.

**High-Level Phases:**
1. **Infrastructure Setup** (core/, docker-compose)
2. **File Ingestion** (ingestion/ layer)
3. **Data Extraction** (brain/ schemas and extractor)
4. **Validation Framework** (brain/ validator)
5. **API Layer** (interface/api/)
6. **Dashboard UI** (interface/dashboard/)
7. **Integration & Testing**

## Next Steps

1. Review and approve this implementation plan
2. Execute `/speckit.tasks` to break down into actionable tasks
3. Begin implementation with infrastructure setup

