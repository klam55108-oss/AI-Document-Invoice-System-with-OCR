# Implementation Plan: Dataset Upload UI

**Branch**: `003-dataset-upload-ui` | **Date**: 2026-01-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-dataset-upload-ui/spec.md`

## Summary

Add a file upload UI to the Streamlit dashboard that allows users to upload invoice files directly through the web interface as an alternative to manually placing files in the `data/` folder. The feature includes single and multiple file upload support, progress tracking, duplicate detection, error handling, and automatic processing integration with the existing pipeline. Additionally, extend the Invoice model with metadata fields (subfolder path, group/batch/category) for better organization and display in the detail view.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI 0.115.0+, Streamlit 1.39.0+, SQLAlchemy 2.0.36+, Pydantic 2.9.0+  
**Storage**: PostgreSQL (asyncpg), File system (data/ directory structure)  
**Testing**: pytest 8.3.0+, pytest-asyncio 0.24.0+  
**Target Platform**: Linux/macOS server (FastAPI), Web browser (Streamlit dashboard)  
**Project Type**: Web application (FastAPI backend + Streamlit frontend)  
**Performance Goals**: Upload initiation < 1s, progress updates every 2s, processing status updates within 5s, file uploads up to 50MB  
**Constraints**: p95 response time < 500ms (sync), < 2s (async initiation), memory < 512MB per request, file size limit 50MB per file  
**Scale/Scope**: Unlimited concurrent uploads, supports existing file types (PDF, Excel, CSV, images), integrates with existing processing pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitution principles:

### I. Code Quality Standards
- [x] Type hints defined for all function signatures
- [x] Static analysis tools (ruff, mypy) configured and passing
- [x] Error handling strategy defined with structured logging
- [x] Security practices identified (input validation, encryption, parameterized queries)
- [x] Dependencies will be pinned with exact versions

### II. Testing Discipline
- [x] Test-driven development (TDD) approach confirmed
- [x] Test coverage targets defined (80% core, 60% overall)
- [x] Test categories identified (unit, integration, contract)
- [x] Async test patterns defined (pytest-asyncio)
- [x] CI/CD test automation planned

### III. User Experience Consistency
- [x] API response format standards defined
- [x] Error message format and user guidance strategy defined
- [x] UI consistency patterns identified (Streamlit dashboard integration)
- [x] Loading states and progress indicators planned

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation)
- [x] Database query optimization strategy identified
- [x] Memory usage bounds defined (< 512MB per request)
- [x] Caching strategy planned (not required for upload feature)
- [x] Async I/O patterns confirmed
- [x] Performance regression testing planned

## Project Structure

### Documentation (this feature)

```text
specs/003-dataset-upload-ui/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
interface/
├── api/
│   ├── routes/
│   │   └── uploads.py          # New: File upload API endpoints
│   └── schemas.py              # Updated: Add upload request/response schemas
├── dashboard/
│   ├── components/
│   │   └── upload.py           # New: Upload UI component
│   └── app.py                  # Updated: Add upload tab
core/
├── models.py                   # Updated: Add metadata field to Invoice model
ingestion/
└── orchestrator.py             # Updated: Support metadata in processing
alembic/
└── versions/
    └── 003_add_upload_metadata.py  # New: Migration for metadata field
tests/
├── integration/
│   └── test_upload_api.py      # New: Upload API integration tests
└── unit/
    └── test_upload_component.py # New: Upload component unit tests
```

**Structure Decision**: Single project structure with FastAPI backend and Streamlit frontend. Upload functionality integrated into existing dashboard as new tab. New API route for file uploads. Database migration for metadata field.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
