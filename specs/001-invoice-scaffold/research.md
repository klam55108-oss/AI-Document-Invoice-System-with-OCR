# Technology Research & Decisions

**Created**: 2024-12-19  
**Purpose**: Document technology choices, rationale, and alternatives considered for the e-invoice scaffold

## Core Framework Decisions

### FastAPI 0.115+

**Decision**: Use FastAPI 0.115+ as the async web framework

**Rationale**:
- Native async/await support aligns with I/O-bound operations (database, file I/O)
- Automatic OpenAPI documentation generation
- Pydantic v2 integration for request/response validation
- High performance (comparable to Node.js and Go)
- Excellent type hint support for Python 3.12

**Alternatives Considered**:
- **Flask**: Synchronous by default, requires additional libraries for async
- **Django**: Over-engineered for API-only use case, heavier footprint
- **Starlette**: Lower-level, FastAPI built on top provides better DX

**Implementation Notes**:
- Use `uvicorn` as ASGI server with standard workers
- Leverage FastAPI dependency injection for database sessions
- Use Pydantic models for all request/response schemas

### SQLAlchemy 2.0 Async

**Decision**: Use SQLAlchemy 2.0 with async engine via `asyncpg`

**Rationale**:
- Native async support in SQLAlchemy 2.0
- Type-safe ORM with excellent Python 3.12 typing support
- `asyncpg` is fastest async PostgreSQL driver
- Alembic integration for migrations
- Supports both ORM and core SQL approaches

**Alternatives Considered**:
- **Tortoise ORM**: Async-first but less mature ecosystem
- **Databases**: Lower-level, requires more boilerplate
- **Raw asyncpg**: Too low-level, loses ORM benefits

**Implementation Notes**:
- Use async session factory pattern
- Connection pooling via SQLAlchemy engine
- Separate sync engine for Alembic migrations (if needed)

### Pydantic v2

**Decision**: Use Pydantic v2 for all data validation and schemas

**Rationale**:
- Fast validation (Rust-based core in v2)
- Excellent type inference and validation
- Native FastAPI integration
- Supports both validation and serialization
- Field-level validation for business rules

**Implementation Notes**:
- Define schemas in `brain/schemas.py` for domain models
- Define API schemas in `interface/api/schemas.py` for request/response
- Use Pydantic Settings for configuration management

## Database & Extensions

### PostgreSQL with pgvector

**Decision**: Use PostgreSQL with `pgvector` extension for vector storage

**Rationale**:
- "Complexity Collapse" strategy: single database for relational data and vectors
- Eliminates need for separate vector database (Pinecone, Weaviate)
- Cost-effective for MVP
- `pgvector` is mature and well-maintained
- Supports similarity search for future RAG features

**Alternatives Considered**:
- **Pinecone**: Managed service, adds cost and external dependency
- **Weaviate**: Separate service, increases infrastructure complexity
- **Chroma**: Embedded option but less mature than pgvector

**Implementation Notes**:
- Install `pgvector` extension in PostgreSQL via docker-compose
- Use `pgvector` Python client for vector operations (future)
- Store embeddings as `vector` type in PostgreSQL

### pgqueuer (PostgreSQL-based Queue)

**Decision**: Use PostgreSQL-based queue via `pgqueuer` extension

**Rationale**:
- Continues "Complexity Collapse" strategy
- No separate Redis/Celery infrastructure needed
- ACID guarantees for job processing
- Simple setup for MVP

**Alternatives Considered**:
- **Celery + Redis**: More features but adds infrastructure complexity
- **RQ (Redis Queue)**: Requires separate Redis instance
- **In-memory queue**: Not persistent, loses jobs on restart

**Implementation Notes**:
- Install `pgqueuer` extension in PostgreSQL
- Use async job enqueueing/dequeueing
- Process jobs in separate worker processes (CPU-intensive tasks)

## Document Processing

### Docling for PDF Processing

**Decision**: Use Docling as primary PDF/document parser

**Rationale**:
- Modern, AI-powered document parsing
- Structured output (JSON) suitable for extraction
- Handles complex layouts better than traditional OCR
- Cost-effective (open-source alternative to cloud APIs)

**Alternatives Considered**:
- **DeepSeek-OCR**: Mentioned in docs, but Docling more mature
- **PaddleOCR**: Good for images, less structured output
- **Tesseract**: Traditional OCR, lower accuracy
- **Cloud APIs (AWS Textract, Google Vision)**: Expensive per-page pricing

**Implementation Notes**:
- Use Docling for PDF parsing
- Fallback to `pypdf` for simple text extraction if needed
- Store raw extracted text for future RAG indexing

### Pandas for Excel/CSV

**Decision**: Use Pandas for Excel and CSV file processing

**Rationale**:
- Industry standard for tabular data
- Excellent Excel support via `openpyxl`
- Handles various Excel formats and edge cases
- Easy data transformation and validation

**Implementation Notes**:
- Use `pandas.read_excel()` for Excel files
- Use `pandas.read_csv()` for CSV files
- Extract structured data into Pydantic models

## AI/ML Framework

### LlamaIndex (Minimal Setup)

**Decision**: Include LlamaIndex in scaffold with minimal setup

**Rationale**:
- Leading framework for RAG applications
- Good PostgreSQL/pgvector integration
- Agentic workflow support (future)
- Active development and community

**Alternatives Considered**:
- **LangChain**: More complex, larger dependency footprint
- **Haystack**: Good but less focused on RAG
- **Custom RAG**: Too much implementation overhead

**Implementation Notes**:
- Minimal setup in scaffold (connection to PostgreSQL)
- Full RAG implementation deferred to later phase
- Prepare data structures for future vector embeddings

## Concurrency Model

### Hybrid Async/Process Model

**Decision**: Use async/await for I/O, separate processes for CPU-intensive tasks

**Rationale**:
- Python GIL limits true parallelism in threads
- Async I/O maximizes throughput for database/file operations
- Separate processes bypass GIL for CPU-bound work (OCR, AI)
- Aligns with user's explicit requirement

**Implementation Pattern**:
```python
# I/O operations: async/await
async def read_file(path: str) -> bytes:
    async with aiofiles.open(path, 'rb') as f:
        return await f.read()

# CPU-intensive: separate process
from multiprocessing import Process

def process_ocr(file_data: bytes) -> dict:
    # CPU-intensive OCR work
    return ocr_result
```

**Alternatives Considered**:
- **Pure async**: Would block on CPU tasks, poor performance
- **Pure threading**: GIL limits effectiveness
- **Pure multiprocessing**: Overhead for I/O operations

## Security & Encryption

### File-Level Encryption (cryptography library)

**Decision**: Use `cryptography` library for file encryption at rest

**Rationale**:
- Industry-standard library (used by many security tools)
- Supports symmetric encryption (AES) for file storage
- Key management via environment variables
- Meets spec requirement for "basic file-level encryption"

**Implementation Notes**:
- Use Fernet (symmetric encryption) for simplicity
- Store encryption key in environment variable
- Encrypt files before writing to disk
- Decrypt when reading for processing

**Alternatives Considered**:
- **No encryption**: Doesn't meet spec requirement
- **Full disk encryption**: OS-level, not application-controlled
- **Database encryption**: Doesn't protect files on disk

## Logging & Observability

### Structured Logging (structlog)

**Decision**: Use `structlog` for structured, JSON-formatted logs

**Rationale**:
- Structured logs easier to parse and search
- JSON format supports log aggregation tools
- Context propagation for request tracing
- Sensitive data filtering capabilities

**Implementation Notes**:
- Configure JSON output for production
- Filter sensitive fields (invoice numbers, amounts)
- Include request IDs for tracing

**Alternatives Considered**:
- **Standard logging**: Less structured, harder to parse
- **Loguru**: Good but structlog more standard

## Development Tools

### Ruff for Linting/Formatting

**Decision**: Use `ruff` for linting and code formatting

**Rationale**:
- Fast (Rust-based, replaces multiple tools)
- Replaces `black`, `isort`, `flake8`, `pylint`
- Good Python 3.12 support
- Minimal configuration needed

### mypy for Type Checking

**Decision**: Use `mypy` for static type checking

**Rationale**:
- Industry standard for Python type checking
- Good FastAPI/Pydantic integration
- Catches type errors before runtime
- Supports Python 3.12 typing features

## Summary

All technology decisions align with:
1. **Complexity Collapse Strategy**: Minimize infrastructure (PostgreSQL for everything)
2. **Local-First MVP**: All components run locally without cloud dependencies
3. **Python 3.12 Compatibility**: Latest language features and type system
4. **Async-First**: Maximize I/O throughput with async/await
5. **Type Safety**: Full type hints for maintainability and correctness

No critical unknowns remain. All decisions are based on mature, well-documented technologies with active maintenance.

