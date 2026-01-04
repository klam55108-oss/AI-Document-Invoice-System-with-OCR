# Implementation Tasks: E-Invoice Implementation Scaffold

**Feature**: E-Invoice Implementation Scaffold  
**Created**: 2024-12-19  
**Based on**: [spec.md](./spec.md), [plan.md](./plan.md), [data-model.md](./data-model.md)

## Overview

This document breaks down the implementation into actionable, dependency-ordered tasks organized by user story. Each task is independently executable and includes specific file paths.

**Total Tasks**: 67  
**User Stories**: 5  
**Parallel Opportunities**: 13 tasks marked with [P]

## Implementation Strategy

**MVP Scope**: User Stories 1-3 (Setup, File Ingestion, Basic Validation)  
**Incremental Delivery**: Each user story phase is independently testable and deployable.

## Dependencies

**Story Completion Order**:
1. Setup Phase (T001-T010) → Must complete first
2. Foundational Phase (T011-T020) → Blocks all user stories
3. US1: Developer Setup (T021-T028) → Enables development workflow
4. US2: File Ingestion (T029-T040) → Enables invoice processing
5. US3: Validation Framework (T041-T047) → Enables data validation
6. US4: API Endpoints (T048-T056) → Enables API access
7. US5: Review Dashboard (T057-T062) → Enables UI review
8. Polish Phase (T063-T067) → Cross-cutting improvements

**Parallel Execution Examples**:
- T012 [P] and T013 [P] can run in parallel (different files)
- T029 [P], T030 [P], T031 [P] can run in parallel (different processors)
- T048 [P] and T049 [P] can run in parallel (different route files)

---

## Phase 1: Setup

**Goal**: Initialize project structure, dependencies, and development environment

**Independent Test Criteria**: Project can be cloned, dependencies installed, and basic structure verified

### Tasks

- [X] T001 Create project root directory structure per plan.md in /Users/william.jiang/my-apps/ai-einvoicing
- [X] T002 Create core/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/core/__init__.py
- [X] T003 Create ingestion/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/__init__.py
- [X] T004 Create brain/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/brain/__init__.py
- [X] T005 Create interface/ directory structure with api/ and dashboard/ subdirectories in /Users/william.jiang/my-apps/ai-einvoicing/interface/
- [X] T006 Create interface/api/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/__init__.py
- [X] T007 Create interface/api/routes/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/__init__.py
- [X] T008 Create interface/dashboard/ directory with __init__.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/__init__.py
- [X] T009 Create data/ directory with .gitkeep in /Users/william.jiang/my-apps/ai-einvoicing/data/.gitkeep
- [X] T010 Create tests/ directory structure with unit/, integration/, fixtures/ subdirectories in /Users/william.jiang/my-apps/ai-einvoicing/tests/

---

## Phase 2: Foundational

**Goal**: Establish core infrastructure that blocks all user stories (database, encryption, logging)

**Independent Test Criteria**: Database connection works, encryption utilities functional, logging configured

### Tasks

- [X] T011 Create pyproject.toml with project metadata and dependencies in /Users/william.jiang/my-apps/ai-einvoicing/pyproject.toml
- [X] T012 [P] Create docker-compose.yml for PostgreSQL with pgvector and pgqueuer in /Users/william.jiang/my-apps/ai-einvoicing/docker-compose.yml
- [X] T013 [P] Create .env.example template with database and encryption configuration in /Users/william.jiang/my-apps/ai-einvoicing/.env.example
- [X] T014 Create core/database.py with async SQLAlchemy engine and session factory in /Users/william.jiang/my-apps/ai-einvoicing/core/database.py
- [X] T015 Create core/models.py with SQLAlchemy models (Invoice, ExtractedData, ValidationResult, ProcessingJob) in /Users/william.jiang/my-apps/ai-einvoicing/core/models.py
- [X] T016 Create core/encryption.py with file encryption utilities using cryptography library in /Users/william.jiang/my-apps/ai-einvoicing/core/encryption.py
- [X] T017 Create core/logging.py with structured logging configuration in /Users/william.jiang/my-apps/ai-einvoicing/core/logging.py
- [X] T018 Create Alembic configuration and initial migration script in /Users/william.jiang/my-apps/ai-einvoicing/alembic.ini
- [X] T019 Create alembic/versions/ directory and initial migration in /Users/william.jiang/my-apps/ai-einvoicing/alembic/versions/
- [X] T020 Create .gitignore file excluding venv, .env, __pycache__, etc. in /Users/william.jiang/my-apps/ai-einvoicing/.gitignore

---

## Phase 3: User Story 1 - Developer Setup and Environment

**Goal**: Developer can set up environment, install dependencies, and verify installation

**Independent Test Criteria**: Developer can clone repo, create venv, install dependencies, run health check

**Related FRs**: FR-1 (Project Structure), FR-2 (Dependency Management), FR-9 (Local Development Support)

### Tasks

- [X] T021 [US1] Create README.md with setup instructions referencing quickstart.md in /Users/william.jiang/my-apps/ai-einvoicing/README.md
- [X] T022 [US1] Create interface/api/main.py with FastAPI app initialization and health check endpoint in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/main.py
- [X] T023 [US1] Create interface/api/routes/health.py with GET /health route handler in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/health.py
- [X] T024 [US1] Create interface/api/schemas.py with Pydantic models for health response in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/schemas.py
- [X] T025 [US1] Update interface/api/main.py to include health route and configure CORS in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/main.py
- [X] T026 [US1] Create pytest configuration in pytest.ini or pyproject.toml for test discovery in /Users/william.jiang/my-apps/ai-einvoicing/pytest.ini
- [X] T027 [US1] Create tests/unit/test_health.py with health endpoint test in /Users/william.jiang/my-apps/ai-einvoicing/tests/unit/test_health.py
- [X] T028 [US1] Create setup script or instructions for virtual environment activation in /Users/william.jiang/my-apps/ai-einvoicing/scripts/setup.sh

---

## Phase 4: User Story 2 - File Ingestion and Processing

**Goal**: System can discover, identify, and process invoice files (PDF, Excel, Images) with hash-based versioning

**Independent Test Criteria**: System discovers files in data/, calculates SHA-256 hash, processes at least one format end-to-end, stores metadata in database

**Related FRs**: FR-4 (File Ingestion Foundation), FR-5 (Data Extraction Interface)

### Tasks

- [X] T029 [P] [US2] Create ingestion/file_discovery.py with async file discovery in data/ directory in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/file_discovery.py
- [X] T030 [P] [US2] Create ingestion/file_hasher.py with SHA-256 hash calculation utility in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/file_hasher.py
- [X] T031 [P] [US2] Create ingestion/pdf_processor.py with Docling-based PDF processing in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/pdf_processor.py
- [X] T032 [US2] Create ingestion/excel_processor.py with Pandas-based Excel/CSV processing in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/excel_processor.py
- [X] T033 [US2] Create ingestion/image_processor.py placeholder for future image processing in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/image_processor.py
- [X] T034 [US2] Create ingestion/orchestrator.py with file processing orchestration and version tracking in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/orchestrator.py
- [X] T035 [US2] Create brain/schemas.py with Pydantic models for ExtractedData in /Users/william.jiang/my-apps/ai-einvoicing/brain/schemas.py
- [X] T036 [US2] Create brain/extractor.py with basic data extraction logic mapping raw text to structured data in /Users/william.jiang/my-apps/ai-einvoicing/brain/extractor.py
- [X] T037 [US2] Update core/models.py to add file hash and version tracking to Invoice model in /Users/william.jiang/my-apps/ai-einvoicing/core/models.py
- [X] T038 [US2] Create database migration for file hash and version fields in /Users/william.jiang/my-apps/ai-einvoicing/alembic/versions/
- [X] T039 [US2] Create tests/integration/test_file_ingestion.py with end-to-end file processing test in /Users/william.jiang/my-apps/ai-einvoicing/tests/integration/test_file_ingestion.py
- [X] T040 [US2] Create tests/unit/test_file_hasher.py with hash calculation tests in /Users/william.jiang/my-apps/ai-einvoicing/tests/unit/test_file_hasher.py

---

## Phase 5: User Story 3 - Validation Framework

**Goal**: System validates invoice data for mathematical consistency (e.g., subtotal + tax = total)

**Independent Test Criteria**: System validates invoice math, stores validation results, identifies errors clearly

**Related FRs**: FR-6 (Validation Framework Foundation)

### Tasks

- [X] T041 [US3] Create brain/validator.py with validation rule framework and math check implementation in /Users/william.jiang/my-apps/ai-einvoicing/brain/validator.py
- [X] T042 [US3] Implement math_check_subtotal_tax validation rule in brain/validator.py in /Users/william.jiang/my-apps/ai-einvoicing/brain/validator.py
- [X] T043 [US3] Update core/models.py ValidationResult model with rule_name, status, error_message fields in /Users/william.jiang/my-apps/ai-einvoicing/core/models.py
- [X] T044 [US3] Create database migration for validation_results table in /Users/william.jiang/my-apps/ai-einvoicing/alembic/versions/
- [X] T045 [US3] Integrate validation into ingestion/orchestrator.py processing pipeline in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/orchestrator.py
- [X] T046 [US3] Create tests/unit/test_validator.py with validation rule tests in /Users/william.jiang/my-apps/ai-einvoicing/tests/unit/test_validator.py
- [X] T047 [US3] Create tests/integration/test_validation_pipeline.py with end-to-end validation test in /Users/william.jiang/my-apps/ai-einvoicing/tests/integration/test_validation_pipeline.py

---

## Phase 6: User Story 4 - API Endpoints

**Goal**: System provides REST API endpoints for querying processed invoices with structured JSON envelope

**Independent Test Criteria**: API responds to health check, lists invoices with pagination, returns invoice details with validation results

**Related FRs**: FR-7 (API Endpoints Foundation)

### Tasks

- [X] T048 [P] [US4] Create interface/api/routes/invoices.py with invoice route handlers in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/invoices.py
- [X] T049 [P] [US4] Update interface/api/schemas.py with invoice request/response models and envelope structure in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/schemas.py
- [X] T050 [US4] Implement GET /api/v1/invoices endpoint with pagination and filtering in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/invoices.py
- [X] T051 [US4] Implement GET /api/v1/invoices/{invoice_id} endpoint with full invoice details in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/invoices.py
- [X] T052 [US4] Implement POST /api/v1/invoices/process endpoint to trigger file processing in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/routes/invoices.py
- [X] T053 [US4] Update interface/api/main.py to register invoice routes and configure response models in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/main.py
- [X] T054 [US4] Create tests/integration/test_api_invoices.py with API endpoint tests in /Users/william.jiang/my-apps/ai-einvoicing/tests/integration/test_api_invoices.py
- [X] T055 [US4] Create tests/unit/test_api_schemas.py with schema validation tests in /Users/william.jiang/my-apps/ai-einvoicing/tests/unit/test_api_schemas.py
- [X] T056 [US4] Verify OpenAPI documentation auto-generation at /docs endpoint in /Users/william.jiang/my-apps/ai-einvoicing/interface/api/main.py

---

## Phase 7: User Story 5 - Review Dashboard

**Goal**: Developer can view processed invoices, extracted data, and validation results in Streamlit dashboard

**Independent Test Criteria**: Dashboard starts, displays invoice list, shows invoice details with validation status, highlights errors

**Related FRs**: FR-8 (Review Dashboard Foundation)

### Tasks

- [X] T057 [US5] Create interface/dashboard/app.py with Streamlit application entry point in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/app.py
- [X] T058 [US5] Implement invoice list view with status indicators in interface/dashboard/app.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/app.py
- [X] T059 [US5] Implement invoice detail view with extracted data display in interface/dashboard/app.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/app.py
- [X] T060 [US5] Implement validation error highlighting in dashboard interface/dashboard/app.py in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/app.py
- [X] T061 [US5] Create database query utilities for dashboard data retrieval in /Users/william.jiang/my-apps/ai-einvoicing/interface/dashboard/queries.py
- [X] T062 [US5] Create tests/integration/test_dashboard.py with dashboard rendering tests in /Users/william.jiang/my-apps/ai-einvoicing/tests/integration/test_dashboard.py

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Complete error handling, logging, encryption integration, and documentation

**Independent Test Criteria**: Error handling works, logs are structured, files are encrypted, documentation is complete

**Related FRs**: FR-10 (Error Handling and Logging), FR-9 (Encryption)

### Tasks

- [X] T063 Integrate error handling with fail-fast and continuation logic in ingestion/orchestrator.py in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/orchestrator.py
- [X] T064 Integrate structured logging throughout core modules with sensitive data filtering in /Users/william.jiang/my-apps/ai-einvoicing/core/logging.py
- [X] T065 Integrate file encryption into file storage workflow in ingestion/orchestrator.py in /Users/william.jiang/my-apps/ai-einvoicing/ingestion/orchestrator.py
- [X] T066 Update ProcessingJob model to track execution_type (async_coroutine vs cpu_process) in /Users/william.jiang/my-apps/ai-einvoicing/core/models.py
- [X] T067 Create comprehensive project documentation in README.md with links to quickstart.md and API docs in /Users/william.jiang/my-apps/ai-einvoicing/README.md

---

## Task Summary

**Total Tasks**: 67

**By Phase**:
- Phase 1 (Setup): 10 tasks
- Phase 2 (Foundational): 10 tasks
- Phase 3 (US1 - Developer Setup): 8 tasks
- Phase 4 (US2 - File Ingestion): 12 tasks
- Phase 5 (US3 - Validation): 7 tasks
- Phase 6 (US4 - API): 9 tasks
- Phase 7 (US5 - Dashboard): 6 tasks
- Phase 8 (Polish): 5 tasks

**By User Story**:
- US1: 8 tasks
- US2: 12 tasks
- US3: 7 tasks
- US4: 9 tasks
- US5: 6 tasks

**Parallel Opportunities**: 13 tasks marked with [P]

**MVP Scope** (Phases 1-5): 47 tasks covering setup, infrastructure, file ingestion, and validation

---

## Notes

- All file paths are absolute as required
- Tasks follow strict format: `- [ ] T### [P?] [Story?] Description with file path`
- Each user story phase is independently testable
- Dependencies are clearly marked in phase order
- Parallel execution opportunities are identified with [P] marker

