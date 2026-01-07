# Implementation Plan: UI and Multi-Format Data Extraction Quality Improvements

**Branch**: `001-ui-data-extract-quality` | **Date**: January 7, 2026 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-ui-data-extract-quality/spec.md`

## Summary

This feature enhances the e-invoicing dashboard with comprehensive data extraction quality visibility and format-specific processing optimizations. The implementation focuses on three core areas: (1) adding file preview capabilities (PDF, CSV, images) to the Invoice Detail tab, (2) improving extraction accuracy for PDF and Excel/CSV formats through format-specific strategies and enhanced prompts, and (3) implementing parallel processing for batch ingestion to improve throughput. The technical approach includes adding per-field confidence tracking in the data model, creating reusable file preview components in Streamlit, enhancing extraction prompts with format-specific guidance, and refactoring the orchestrator to support concurrent processing with async patterns.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI 0.115.x, Streamlit 1.40.x, SQLAlchemy 2.0.36, Pydantic 2.10.x, pandas 2.2.3, pypdf 5.1.x, PaddleOCR 2.9.x, OpenAI 1.58.x  
**Storage**: PostgreSQL 17 with pgvector extension  
**Testing**: pytest 8.3.x, pytest-asyncio 0.24.x, pytest-cov 6.0.x  
**Target Platform**: Linux/macOS server (Docker containerized)  
**Project Type**: Web application (FastAPI backend + Streamlit dashboard)  
**Performance Goals**: 
- File preview rendering < 2 seconds for files up to 10MB
- Extraction accuracy 85%+ for critical fields across all formats
- Parallel processing: 20 concurrent invoices without quality degradation
- Dashboard quality metrics page load < 3 seconds for 1000+ invoices  
**Constraints**: 
- Memory usage < 512MB per invoice processing request
- p95 API latency < 500ms for preview endpoints, < 2s for extraction initiation
- Extraction processing time < 15 seconds for 95% of files  
**Scale/Scope**: 
- Support 1000+ invoices in dashboard with sub-3-second load times
- Handle concurrent batch uploads of 50+ files
- Store and query per-field confidence metrics for all invoices

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitution principles:

### I. Code Quality Standards
- [x] Type hints defined for all function signatures
- [x] Static analysis tools (ruff, mypy) configured and passing
- [x] Error handling strategy defined with structured logging
- [x] Security practices identified (input validation, encryption, parameterized queries)
- [x] Dependencies will be pinned with exact versions

**Details**: All new modules will use strict type hints. File preview components will validate file paths to prevent directory traversal attacks. Pydantic models will validate all input data. Error handling will use structured logging with sensitive data filtering.

### II. Testing Discipline
- [x] Test-driven development (TDD) approach confirmed
- [x] Test coverage targets defined (80% core, 60% overall)
- [x] Test categories identified (unit, integration, contract)
- [x] Async test patterns defined (pytest-asyncio)
- [x] CI/CD test automation planned

**Details**: Tests will be written before implementation. Unit tests for extraction logic, integration tests for file preview rendering, contract tests for new API endpoints. Async tests for parallel processing with proper fixture isolation.

### III. User Experience Consistency
- [x] API response format standards defined
- [x] Error message format and user guidance strategy defined
- [x] UI consistency patterns identified (if applicable)
- [x] Loading states and progress indicators planned

**Details**: File previews will show loading spinners with progress indicators. Extraction confidence scores will use consistent color coding (red <50%, yellow 50-70%, green >70%). Error messages will be user-friendly with actionable guidance.

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation)
- [x] Database query optimization strategy identified
- [x] Memory usage bounds defined (< 512MB per request)
- [x] Caching strategy planned
- [x] Async I/O patterns confirmed
- [x] Performance regression testing planned

**Details**: File previews will use caching to avoid re-reading files. Database queries will use indexes on confidence scores and extraction status. Parallel processing will use asyncio.gather with semaphore to limit concurrency. Performance tests will monitor memory usage and latency under load.

## Project Structure

### Documentation (this feature)

```text
specs/001-ui-data-extract-quality/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - technology decisions
├── data-model.md        # Phase 1 output - schema changes
├── quickstart.md        # Phase 1 output - implementation guide
├── contracts/           # Phase 1 output - API contracts
│   ├── preview-api.yaml # File preview endpoints
│   └── extraction-api.yaml # Enhanced extraction endpoints
└── checklists/
    └── requirements.md  # Spec quality validation (already complete)
```

### Source Code (repository root)

```text
# Existing structure (web application)
backend/
├── core/
│   ├── models.py              # [MODIFY] Add per-field confidence columns
│   └── config.py              # [EXISTING] Configuration
├── brain/
│   ├── extractor.py           # [MODIFY] Format-specific extraction strategies
│   ├── schemas.py             # [MODIFY] Add per-field confidence to schema
│   └── validator.py           # [EXISTING] Validation framework
├── ingestion/
│   ├── orchestrator.py        # [MODIFY] Add parallel processing support
│   ├── pdf_processor.py       # [MODIFY] Enhanced PDF text/image detection
│   ├── excel_processor.py     # [MODIFY] Column header mapping for Excel
│   ├── image_processor.py     # [MODIFY] Image preprocessing options
│   └── file_preview.py        # [NEW] File preview utilities
├── interface/
│   ├── api/
│   │   └── routes/
│   │       ├── invoices.py    # [MODIFY] Add preview endpoints
│   │       └── quality.py     # [NEW] Quality metrics endpoints
│   └── dashboard/
│       ├── app.py             # [MODIFY] Enhanced filters and quality view
│       ├── components/
│       │   ├── file_preview.py   # [NEW] File preview components
│       │   ├── quality_metrics.py # [NEW] Quality dashboard
│       │   ├── inline_editor.py   # [NEW] Inline field editing
│       │   └── charts.py      # [MODIFY] Add quality trend charts
│       └── utils/
│           └── confidence_display.py # [NEW] Confidence visualization

tests/
├── unit/
│   ├── test_extraction_strategies.py  # [NEW] Format-specific extraction tests
│   ├── test_file_preview.py           # [NEW] File preview unit tests
│   └── test_parallel_processing.py    # [NEW] Parallel orchestrator tests
├── integration/
│   ├── test_quality_api.py            # [NEW] Quality metrics endpoint tests
│   └── test_preview_workflow.py       # [NEW] End-to-end preview tests
└── contract/
    └── test_preview_api.py             # [NEW] API contract tests

alembic/versions/
└── 002_add_field_confidence.py        # [NEW] Migration for per-field confidence
```

**Structure Decision**: Web application structure (backend + interface). The existing modular architecture (core, brain, ingestion, interface) is preserved. New modules are added for file preview, quality metrics, and inline editing. Database migration adds per-field confidence tracking without breaking existing columns.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. All principles can be satisfied within the existing architecture. The feature adds new capabilities without introducing unnecessary complexity.

## Phase 0: Research & Technology Decisions

See [research.md](./research.md) for detailed technology evaluations and decisions.

**Key Decisions Summary**:
1. **File Preview**: Use Streamlit native components (st.image, st.dataframe) + base64 encoding for PDF preview
2. **Format-Specific Extraction**: Enhance existing extraction prompts with format-specific guidance rather than separate extractors
3. **Parallel Processing**: Use asyncio.gather with semaphore limiting instead of external queue systems
4. **Per-Field Confidence**: Store as separate columns (vendor_confidence, invoice_number_confidence, etc.) rather than JSONB for query performance
5. **UI Framework**: Continue using Streamlit with enhanced components (no React/Vue.js needed)

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for complete schema design.

**Key Changes**:
- Add per-field confidence columns to `extracted_data` table
- Add `file_preview_metadata` JSONB column to `invoices` table for caching preview data
- Add indexes on confidence columns for filtering and sorting
- Add `processing_metadata` JSONB column to track parallel processing statistics

### API Contracts

See [contracts/](./contracts/) directory for OpenAPI specifications:
- `preview-api.yaml`: File preview endpoints (GET /api/v1/invoices/{id}/preview)
- `extraction-api.yaml`: Enhanced extraction endpoints with quality metrics

### Implementation Guide

See [quickstart.md](./quickstart.md) for step-by-step implementation instructions with code examples.

## Implementation Phases

### Phase 2: Task Breakdown (via `/speckit.tasks`)

Task breakdown will be generated in the next phase using `/speckit.tasks` command. Expected task categories:

1. **Database Migration Tasks** (2-3 tasks)
   - Create migration for per-field confidence columns
   - Add indexes for quality filtering
   - Backfill confidence scores for existing data

2. **Backend Enhancement Tasks** (8-10 tasks)
   - Implement file preview utilities
   - Add format-specific extraction strategies
   - Implement parallel processing orchestrator
   - Create quality metrics API endpoints
   - Add per-field confidence tracking

3. **Dashboard UI Tasks** (6-8 tasks)
   - Create file preview components
   - Build quality metrics dashboard
   - Implement inline editing with autocomplete
   - Add confidence visualization and filtering
   - Create quality trend charts

4. **Testing Tasks** (5-6 tasks)
   - Write unit tests for extraction strategies
   - Write integration tests for preview workflow
   - Write contract tests for new API endpoints
   - Performance testing for parallel processing

5. **Documentation Tasks** (2-3 tasks)
   - Update API documentation
   - Create user guide for quality features
   - Document configuration options

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PDF preview memory usage exceeds 512MB for large files | High | Implement file size limits (max 10MB for preview), use lazy loading, add memory monitoring |
| Parallel processing causes database connection pool exhaustion | High | Configure connection pool size appropriately, use semaphore to limit concurrency (default: 20) |
| Per-field confidence tracking increases extraction latency | Medium | Calculate confidence scores asynchronously, cache results, add timeout limits |
| Excel column header mapping fails for non-standard layouts | Medium | Implement fallback to positional detection, add manual column mapping UI |
| Existing invoices lack per-field confidence data | Low | Backfill migration script to reprocess or set default values, add "confidence unknown" indicator |

## Performance Benchmarks

| Metric | Current Baseline | Target | Measurement Method |
|--------|------------------|--------|-------------------|
| Critical field extraction accuracy | ~60% (many NULL) | 85%+ | Count non-NULL critical fields / total invoices |
| Excel extraction accuracy | Unknown | 95% | Manual review of 100 sample Excel invoices |
| File preview load time | N/A (not implemented) | <2s for <10MB files | Measure Streamlit component render time |
| Parallel processing throughput | 1 invoice/15s = 4/min | 20 concurrent = ~80/min | Process 100 invoice batch, measure completion time |
| Dashboard quality page load | N/A (not implemented) | <3s for 1000+ invoices | Measure query execution + render time |
| Memory per invoice | ~300MB | <512MB | Monitor container memory during processing |

## Success Criteria Mapping

| Success Criteria (from spec.md) | Implementation Approach |
|----------------------------------|------------------------|
| SC-001: Confidence scores displayed within 2s | Index confidence columns, optimize queries, cache dashboard data |
| SC-002: 85% critical field accuracy | Enhanced extraction prompts, format-specific strategies, validation feedback loop |
| SC-003: 95% Excel accuracy | Column header detection, cell position mapping, pandas integration |
| SC-004: Filter quality issues in <10s | Add database indexes, pre-compute quality flags, optimize filters |
| SC-005: Edit/save in <30s per invoice | Inline editing with immediate DB updates, validation on save |
| SC-006: Quality metrics load in <3s for 1000+ invoices | Aggregate queries with indexes, caching, efficient chart rendering |
| SC-007: Bulk export 100 invoices in <10s | Streaming export, efficient serialization, background job option |
| SC-008: 40% STP rate improvement | Measure baseline, track NULL field reduction, calculate improvement |
| SC-009: <15s processing for 95% of files | Optimize extraction calls, parallel processing, timeout handling |
| SC-010: Plain language UI labels | User-friendly terminology, tooltips, help text for all metrics |
| SC-011: 20 concurrent without degradation | Semaphore limiting, connection pooling, memory monitoring |
| SC-012: 50% reduction in "failed" status | Enhanced error handling, retry logic, format-specific processing |

## Next Steps

1. Review and approve this plan
2. Run `/speckit.tasks` to generate detailed task breakdown
3. Begin implementation starting with database migration (Phase 2)
4. Follow TDD approach: write tests first, then implement features
5. Monitor performance benchmarks throughout development
6. Update documentation as implementation progresses
