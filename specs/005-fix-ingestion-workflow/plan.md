# Implementation Plan: Fix Ingestion Workflow

**Branch**: `005-fix-ingestion-workflow` | **Date**: 2025-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-fix-ingestion-workflow/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Fix the ingestion workflow to ensure reliable file processing, accurate status tracking, and proper error handling. The primary issues are: (1) schema mismatches between database and code models, (2) insufficient error handling and logging, (3) dashboard query failures, and (4) file structure cleanup. The solution involves verifying database schema alignment, adding comprehensive error handling, improving dashboard error messages, and cleaning up temporary probe files.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, asyncpg, Streamlit  
**Storage**: PostgreSQL with pgvector extension  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux/macOS server (FastAPI backend), Web browser (Streamlit dashboard)  
**Project Type**: Web application (backend API + dashboard frontend)  
**Performance Goals**: API endpoints p95 < 500ms (sync), < 2s (async initiation), dashboard queries < 1s  
**Constraints**: < 512MB memory per request processing, async I/O for all database operations, graceful error handling without data loss  
**Scale/Scope**: Handle 10+ concurrent file processing tasks, support 1000+ invoices in database

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitution principles:

### I. Code Quality Standards
- [x] Type hints defined for all function signatures (existing codebase uses type hints)
- [x] Static analysis tools (ruff, mypy) configured and passing (project uses ruff)
- [x] Error handling strategy defined with structured logging (core.logging module exists)
- [x] Security practices identified (input validation via Pydantic, parameterized queries via SQLAlchemy)
- [x] Dependencies will be pinned with exact versions (pyproject.toml uses poetry)

### II. Testing Discipline
- [x] Test-driven development (TDD) approach confirmed (tests/ directory exists with unit/integration structure)
- [x] Test coverage targets defined (80% core, 60% overall - per constitution)
- [x] Test categories identified (unit, integration, contract - existing test structure)
- [x] Async test patterns defined (pytest-asyncio - used in existing tests)
- [x] CI/CD test automation planned (pytest.ini configured)

### III. User Experience Consistency
- [x] API response format standards defined (interface/api/schemas.py defines response models)
- [x] Error message format and user guidance strategy defined (HTTPException with detail messages)
- [x] UI consistency patterns identified (Streamlit dashboard uses consistent components)
- [x] Loading states and progress indicators planned (dashboard shows processing status)

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation - per constitution)
- [x] Database query optimization strategy identified (indexes on key columns, async queries)
- [x] Memory usage bounds defined (< 512MB per request - per constitution)
- [x] Caching strategy planned (not needed for this fix, but can be added later)
- [x] Async I/O patterns confirmed (all database operations use async/await)
- [x] Performance regression testing planned (can add benchmarks if needed)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
core/
├── config.py           # Configuration management
├── database.py         # Database connection and session management
├── encryption.py       # File encryption utilities
├── jobs.py             # Job queue management
├── logging.py          # Structured logging setup
└── models.py           # SQLAlchemy ORM models

ingestion/
├── excel_processor.py  # Excel/CSV file processing
├── file_discovery.py   # File discovery utilities
├── file_hasher.py      # File hash calculation
├── image_processor.py # Image OCR processing
├── orchestrator.py     # Main processing orchestration
└── pdf_processor.py    # PDF processing

interface/
├── api/
│   ├── main.py         # FastAPI application
│   ├── routes/
│   │   ├── invoices.py # Invoice API endpoints
│   │   └── uploads.py  # File upload endpoints
│   └── schemas.py      # Pydantic request/response models
└── dashboard/
    ├── app.py          # Streamlit dashboard application
    ├── components/    # Dashboard UI components
    ├── queries.py      # Database query utilities
    └── utils/          # Dashboard utility functions

scripts/
├── process_invoices.py # Batch processing script
└── [other utility scripts]

tests/
├── fixtures/           # Test fixtures
├── integration/       # Integration tests
└── unit/              # Unit tests

alembic/
├── versions/           # Database migration scripts
└── env.py             # Alembic environment configuration
```

**Structure Decision**: This is a web application with a three-layer architecture (Sensory/Ingestion, Brain/Processing, Interaction/Interface). The structure separates concerns: `core/` for shared infrastructure, `ingestion/` for file processing, `interface/` for API and dashboard, and `scripts/` for utility tools.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. All constitution principles are satisfied with existing codebase patterns and planned improvements.
