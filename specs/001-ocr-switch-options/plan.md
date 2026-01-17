# Implementation Plan: Switchable OCR Providers

**Branch**: `001-ocr-switch-options` | **Date**: Jan 15, 2026 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ocr-switch-options/spec.md`

## Summary

Deliver configurable OCR provider selection between PaddleOCR and DeepSeek OCR, including a side-by-side comparison workflow, admin-only provider configuration, default provider behavior, and resilient handling when one provider fails. The plan explicitly supports CPU-only DeepSeek OCR on macOS (Apple M3 Pro) with no CUDA/GPU.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), asyncpg, paddleocr, deepseek  
**Storage**: PostgreSQL  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: macOS (dev on Apple M3 Pro, CPU-only), Linux server (deployment)  
**Project Type**: Single Python service with API + dashboard  
**Performance Goals**: p95 < 500ms sync endpoints, < 2s async initiation; 95% single-invoice OCR within 30s  
**Constraints**: CPU-only DeepSeek OCR (no CUDA/GPU), < 512MB per request, comparison limited to single invoice  
**Scale/Scope**: Single-invoice comparisons, tens of concurrent OCR jobs

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
- [x] UI consistency patterns identified (if applicable)
- [x] Loading states and progress indicators planned

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation)
- [x] Database query optimization strategy identified
- [x] Memory usage bounds defined (< 512MB per request)
- [x] Caching strategy planned
- [x] Async I/O patterns confirmed
- [x] Performance regression testing planned

## Project Structure

### Documentation (this feature)

```text
specs/001-ocr-switch-options/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
alembic/
brain/
core/
ingestion/
interface/
tests/
scripts/
docs/
```

**Structure Decision**: Single Python repository with FastAPI API (`interface/api`) and Streamlit dashboard (`interface/dashboard`), shared core and ingestion modules.

## Complexity Tracking

No constitution violations identified.
