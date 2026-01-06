# Tasks: Dataset Upload UI

**Input**: Design documents from `/specs/003-dataset-upload-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API Routes**: `interface/api/routes/` at repository root
- **Dashboard Components**: `interface/dashboard/components/`
- **Core Models**: `core/`
- **Ingestion**: `ingestion/`
- **Migrations**: `alembic/versions/`
- **Tests**: `tests/integration/` and `tests/unit/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency verification, and directory structure

- [X] T001 [P] Verify python-multipart>=0.0.12 dependency exists in pyproject.toml (required for FastAPI file uploads)
- [X] T002 [P] Create interface/api/routes/uploads.py file with router setup
- [X] T003 [P] Create interface/dashboard/components/upload.py file with component structure
- [X] T004 [P] Verify data/uploads/ directory exists or create it with proper permissions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database schema and model changes that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create database migration file alembic/versions/003_add_upload_metadata.py to add upload_metadata JSONB column to invoices table
- [X] T006 [P] Add GIN index on upload_metadata field in migration file alembic/versions/003_add_upload_metadata.py
- [X] T007 [P] Add indexes on upload_metadata->>'subfolder' and upload_metadata->>'group' in migration file alembic/versions/003_add_upload_metadata.py
- [X] T008 Run migration: alembic upgrade head to apply schema changes
- [X] T009 [P] Update core/models.py Invoice class to add upload_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True) field
- [X] T010 [P] Update ingestion/orchestrator.py process_invoice_file() function signature to accept optional upload_metadata parameter
- [X] T011 [P] Update ingestion/orchestrator.py process_invoice_file() to set upload_metadata when creating Invoice record if provided

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single File Upload and Processing (Priority: P1) 🎯 MVP

**Goal**: Enable users to upload individual invoice files through the Streamlit dashboard, with automatic processing and duplicate detection

**Independent Test**: Upload a single supported file (PDF, Excel, CSV, or image) through the UI and verify that the file is processed, appears in the invoice list, and contains extracted data. Test duplicate detection with warning dialog.

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

> **NOTE: Per Constitution Principle II, TDD is NON-NEGOTIABLE. Write these tests FIRST, ensure they FAIL before implementation. Test coverage must meet targets (80% core, 60% overall).**

- [X] T012 [P] [US1] Create unit test for file type validation in tests/unit/test_upload_component.py testing supported file types (PDF, Excel, CSV, images)
- [X] T013 [P] [US1] Create unit test for file size validation in tests/unit/test_upload_component.py testing 50MB limit enforcement
- [X] T014 [P] [US1] Create unit test for duplicate detection in tests/unit/test_upload_component.py testing hash-based duplicate detection
- [X] T015 [P] [US1] Create integration test for upload API endpoint in tests/integration/test_upload_api.py testing POST /api/v1/uploads with single file
- [X] T016 [P] [US1] Create integration test for upload API endpoint in tests/integration/test_upload_api.py testing file type validation and error responses
- [X] T017 [P] [US1] Create integration test for upload API endpoint in tests/integration/test_upload_api.py testing file size validation (50MB limit)
- [X] T018 [P] [US1] Create integration test for upload API endpoint in tests/integration/test_upload_api.py testing duplicate file detection and warning response
- [X] T019 [P] [US1] Create integration test for upload API endpoint in tests/integration/test_upload_api.py testing automatic processing integration after upload

### Implementation for User Story 1

- [X] T020 [P] [US1] Create upload API schemas in interface/api/schemas.py: UploadResponse, UploadItem, UploadMetadata, ErrorResponse (for uploads)
- [X] T021 [US1] Implement POST /api/v1/uploads endpoint in interface/api/routes/uploads.py with multipart/form-data file upload handling
- [X] T022 [US1] Implement file type validation in interface/api/routes/uploads.py validating against supported types (PDF, Excel, CSV, images)
- [X] T023 [US1] Implement file size validation in interface/api/routes/uploads.py enforcing 50MB limit per file
- [X] T024 [US1] Implement file storage logic in interface/api/routes/uploads.py saving files to data/uploads/ with original filename preserved
- [X] T025 [US1] Implement duplicate detection in interface/api/routes/uploads.py checking file hash against existing invoices
- [X] T026 [US1] Implement invoice record creation in interface/api/routes/uploads.py with upload_metadata containing subfolder, upload_source, uploaded_at
- [X] T027 [US1] Implement automatic processing trigger in interface/api/routes/uploads.py calling process_invoice_file() after file save
- [X] T028 [US1] Register upload router in interface/api/main.py with app.include_router(uploads.router)
- [X] T029 [P] [US1] Create upload UI component in interface/dashboard/components/upload.py with st.file_uploader for single file selection
- [X] T030 [US1] Implement file type filtering in interface/dashboard/components/upload.py using accept parameter for supported file types
- [X] T031 [US1] Implement client-side file size validation in interface/dashboard/components/upload.py checking 50MB limit before upload
- [X] T032 [US1] Implement upload submission in interface/dashboard/components/upload.py sending file to POST /api/v1/uploads endpoint
- [X] T033 [US1] Implement duplicate warning dialog in interface/dashboard/components/upload.py showing confirmation when duplicate detected
- [X] T034 [US1] Implement success confirmation message in interface/dashboard/components/upload.py displaying file name and processing status
- [X] T035 [US1] Add upload tab to Streamlit dashboard in interface/dashboard/app.py creating new tab "Upload Files" alongside existing tabs
- [X] T036 [US1] Integrate upload component in interface/dashboard/app.py rendering upload UI in the new tab

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can upload a single file, see duplicate warnings, and have files automatically processed.

---

## Phase 4: User Story 2 - Multiple File Upload (Priority: P2)

**Goal**: Enable users to upload multiple invoice files simultaneously with progress tracking for each file

**Independent Test**: Select multiple supported files and upload them together, then verify that all files are processed and appear in the invoice list. Test mixed file types (some supported, some unsupported) and verify partial success handling.

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [X] T037 [P] [US2] Create integration test for multiple file upload in tests/integration/test_upload_api.py testing POST /api/v1/uploads with multiple files
- [X] T038 [P] [US2] Create integration test for mixed file types in tests/integration/test_upload_api.py testing partial success when some files are unsupported
- [X] T039 [P] [US2] Create integration test for upload summary in tests/integration/test_upload_api.py testing response includes success/failed/skipped counts
- [X] T040 [P] [US2] Create unit test for progress tracking in tests/unit/test_upload_component.py testing progress indicators for multiple files

### Implementation for User Story 2

- [X] T041 [US2] Update POST /api/v1/uploads endpoint in interface/api/routes/uploads.py to handle multiple files in single request
- [X] T042 [US2] Implement batch processing logic in interface/api/routes/uploads.py processing each file independently and collecting results
- [X] T043 [US2] Implement upload summary generation in interface/api/routes/uploads.py calculating successful, failed, and skipped counts
- [X] T044 [US2] Update UploadResponse schema in interface/api/schemas.py to include total, successful, failed, skipped counts
- [X] T045 [US2] Update upload UI component in interface/dashboard/components/upload.py to enable accept_multiple_files=True in st.file_uploader
- [X] T046 [US2] Implement progress indicators in interface/dashboard/components/upload.py showing status for each file (uploading, processing, completed, failed)
- [X] T047 [US2] Implement upload summary display in interface/dashboard/components/upload.py showing success/failed/skipped counts after batch upload
- [X] T048 [US2] Implement partial success handling in interface/dashboard/components/upload.py displaying which files succeeded and which failed with error messages

**Checkpoint**: At this point, User Story 2 should be fully functional. Users can upload multiple files simultaneously and see progress for each file with a summary of results.

---

## Phase 5: User Story 3 - Upload Progress and Status Feedback (Priority: P3)

**Goal**: Provide real-time feedback during file upload and processing with progress bars, status updates, and notifications

**Independent Test**: Upload files and verify that progress indicators update correctly, status messages are accurate, and notifications appear at appropriate times. Test retry functionality for failed uploads.

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [X] T049 [P] [US3] Create integration test for upload status endpoint in tests/integration/test_upload_api.py testing GET /api/v1/uploads/{upload_id}/status
- [X] T050 [P] [US3] Create unit test for progress bar updates in tests/unit/test_upload_component.py testing progress bar updates during upload
- [X] T051 [P] [US3] Create unit test for status polling in tests/unit/test_upload_component.py testing status updates via API polling
- [X] T052 [P] [US3] Create unit test for retry functionality in tests/unit/test_upload_component.py testing retry button and failed upload retry

### Implementation for User Story 3

- [X] T053 [US3] Implement GET /api/v1/uploads/{upload_id}/status endpoint in interface/api/routes/uploads.py returning current processing status
- [X] T054 [US3] Create UploadStatusResponse schema in interface/api/schemas.py with invoice_id, file_name, processing_status, upload_metadata fields
- [X] T055 [US3] Implement upload progress bar in interface/dashboard/components/upload.py using st.progress() to show upload percentage
- [X] T056 [US3] Implement processing status display in interface/dashboard/components/upload.py showing status messages (uploading, processing, completed, failed)
- [X] T057 [US3] Implement status polling in interface/dashboard/components/upload.py polling GET /api/v1/uploads/{upload_id}/status every 2-5 seconds (manual refresh button)
- [X] T058 [US3] Implement success notification in interface/dashboard/components/upload.py displaying success message with link to view processed invoice
- [X] T059 [US3] Implement error notification in interface/dashboard/components/upload.py displaying error message with details about failure
- [X] T060 [US3] Implement retry button in interface/dashboard/components/upload.py allowing user to manually retry failed uploads (with guidance to re-upload)
- [X] T061 [US3] Implement upload history in interface/dashboard/components/upload.py showing status of recent uploads using session state
- [X] T062 [US3] Implement notification persistence in interface/dashboard/components/upload.py maintaining notifications across page navigation

**Checkpoint**: At this point, User Story 3 should be fully functional. Users see real-time progress, status updates, and can retry failed uploads.

---

## Phase 6: Metadata Display and Polish

**Purpose**: Display upload metadata in invoice detail view and final polish

- [X] T063 [P] Update interface/dashboard/app.py display_invoice_detail() function to show upload_metadata.subfolder as "Source Folder"
- [X] T064 [P] Update interface/dashboard/app.py display_invoice_detail() function to show upload_metadata.group as "Upload Group" (if present)
- [X] T065 [P] Update interface/dashboard/app.py display_invoice_detail() function to show upload_metadata.category as "Category" (if present)
- [X] T066 [P] Update interface/dashboard/app.py display_invoice_detail() function to show upload_metadata.upload_source to indicate upload method
- [X] T067 [P] Update interface/api/schemas.py InvoiceDetail schema to include upload_metadata field in response
- [X] T068 [P] Update interface/api/routes/invoices.py get_invoice() endpoint to include upload_metadata in response
- [X] T069 [P] Add error handling for network interruptions in interface/dashboard/components/upload.py with user-friendly error messages
- [X] T070 [P] Add filename sanitization in interface/api/routes/uploads.py to prevent path traversal attacks (remove ".." and "/")
- [X] T071 [P] Add logging for upload operations in interface/api/routes/uploads.py using structured logging
- [X] T072 [P] Verify all error messages are user-friendly and non-technical in interface/dashboard/components/upload.py
- [X] T073 [P] Add drag-and-drop support verification in interface/dashboard/components/upload.py (st.file_uploader supports this natively)

---

## Dependencies

### User Story Completion Order

1. **Phase 2 (Foundational)** → MUST complete before any user story
   - Database migration and model updates are prerequisites

2. **Phase 3 (US1 - Single File Upload)** → Can start after Phase 2
   - MVP functionality, enables basic upload workflow
   - Independent: Can be tested and deployed alone

3. **Phase 4 (US2 - Multiple File Upload)** → Depends on US1
   - Builds on single file upload functionality
   - Can be developed in parallel with US3 after US1 is complete

4. **Phase 5 (US3 - Progress and Status)** → Depends on US1
   - Enhances existing upload functionality
   - Can be developed in parallel with US2 after US1 is complete

5. **Phase 6 (Polish)** → Depends on all user stories
   - Final touches and metadata display
   - Can be developed in parallel with other polish tasks

### Parallel Execution Opportunities

**Within Phase 2 (Foundational)**:
- T006, T007, T009, T010, T011 can run in parallel (different aspects of same feature)

**Within Phase 3 (US1)**:
- Tests (T012-T019) can run in parallel
- T020, T029 can run in parallel (schemas and UI component structure)
- T022, T023, T024 can run in parallel (different validation aspects)

**Within Phase 4 (US2)**:
- Tests (T037-T040) can run in parallel
- T044, T045 can run in parallel (schema and UI updates)

**Within Phase 5 (US3)**:
- Tests (T049-T052) can run in parallel
- T055, T056, T057 can run in parallel (different UI components)

**Within Phase 6 (Polish)**:
- All tasks (T063-T073) can run in parallel (independent polish tasks)

**Cross-Phase Parallel**:
- Phase 4 and Phase 5 can run in parallel after Phase 3 is complete
- Phase 6 can start as soon as Phase 3 is complete (metadata display doesn't need US2 or US3)

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Recommended MVP**: Phase 2 (Foundational) + Phase 3 (US1 - Single File Upload)

This delivers:
- Core upload functionality
- Single file upload with validation
- Duplicate detection
- Automatic processing
- Basic success/error feedback

**Rationale**: US1 provides the core alternative workflow to the data/ folder method. US2 and US3 enhance the experience but are not required for basic functionality.

### Incremental Delivery

1. **Sprint 1**: Phase 2 (Foundational) - Database and model updates
2. **Sprint 2**: Phase 3 (US1) - Single file upload (MVP)
3. **Sprint 3**: Phase 4 (US2) - Multiple file upload
4. **Sprint 4**: Phase 5 (US3) - Progress and status feedback
5. **Sprint 5**: Phase 6 (Polish) - Metadata display and final touches

### Testing Strategy

- **Unit Tests**: Test individual components (file validation, duplicate detection, UI components)
- **Integration Tests**: Test API endpoints and full upload workflow
- **Manual Testing**: Test in Streamlit dashboard with real files

### Validation Checklist

Before considering any phase complete:
- [ ] All tests for that phase pass
- [ ] Code passes static analysis (ruff, mypy)
- [ ] Manual testing completed
- [ ] Error handling verified
- [ ] User-friendly error messages confirmed
- [ ] Performance targets met (if applicable)

---

## Summary

**Total Tasks**: 73
- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 7 tasks
- **Phase 3 (US1 - Single Upload)**: 17 tasks (8 tests + 9 implementation)
- **Phase 4 (US2 - Multiple Upload)**: 8 tasks (4 tests + 4 implementation)
- **Phase 5 (US3 - Progress/Status)**: 10 tasks (4 tests + 6 implementation)
- **Phase 6 (Polish)**: 11 tasks

**MVP Scope**: Phases 1-3 (28 tasks total)

**Parallel Opportunities**: Significant parallelization possible within phases and across US2/US3 after US1 completion

**Independent Test Criteria**:
- **US1**: Upload single file → verify processing → verify invoice appears in list
- **US2**: Upload multiple files → verify all processed → verify summary displayed
- **US3**: Upload file → verify progress updates → verify notifications appear

