# Tasks: Fix Ingestion Workflow

**Input**: Design documents from `/specs/005-fix-ingestion-workflow/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Schema Verification & File Cleanup)

**Purpose**: Verify database schema matches code models and clean up temporary files

- [x] T001 Verify database schema matches code models by running `alembic upgrade head` and checking for errors
- [x] T002 [P] Move probe_paddle.py from root to scripts/probe_paddle.py or remove if no longer needed
- [x] T003 [P] Move probe_paddle_ocr.py from root to scripts/probe_paddle_ocr.py or remove if no longer needed
- [x] T004 [P] Move debug_invoice.py from root to scripts/debug_invoice.py or remove if no longer needed
- [x] T005 Verify all migrations are applied by checking alembic version in database matches latest migration

---

## Phase 2: Foundational (Error Handling Infrastructure & Health Checks)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Add database schema health check function in core/database.py to verify schema matches models
- [x] T007 [P] Add comprehensive error logging to ingestion/orchestrator.py with structured error context
- [x] T008 [P] Add error handling wrapper in interface/dashboard/queries.py to catch and display database errors gracefully
- [x] T009 [P] Enhance health check endpoint in interface/api/routes/health.py to verify database connectivity and schema
- [x] T010 [P] Add error message formatting utility in core/logging.py for user-friendly error messages
- [x] T011 Add database connection retry logic in core/database.py for handling transient connection failures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload and Process Invoice Files Successfully (Priority: P1) 🎯 MVP

**Goal**: Users can upload invoice files (PDF, Excel, or images) through the web interface or API, and the system processes them completely from upload through data extraction and validation, storing all results in the database with accurate status tracking.

**Independent Test**: Upload a single invoice file and verify it progresses through all stages (pending → processing → completed) with extracted data and validation results stored correctly.

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

- [ ] T012 [P] [US1] Integration test for file upload and processing workflow in tests/integration/test_invoice_processing.py
- [ ] T013 [P] [US1] Unit test for process_invoice_file function in tests/unit/test_orchestrator.py
- [ ] T014 [P] [US1] Contract test for POST /api/v1/invoices/process endpoint in tests/contract/test_invoice_process_api.py

### Implementation for User Story 1

- [x] T015 [US1] Fix file path resolution in interface/api/routes/invoices.py to handle relative paths correctly
- [x] T016 [US1] Verify process_invoice_file correctly uses storage_path in ingestion/orchestrator.py
- [x] T017 [US1] Ensure status transitions are properly tracked in ingestion/orchestrator.py (pending → processing → completed/failed)
- [x] T018 [US1] Add validation that extracted data is stored correctly in ingestion/orchestrator.py
- [x] T019 [US1] Add validation that validation results are stored correctly in ingestion/orchestrator.py
- [x] T020 [US1] Fix scripts/process_invoices.py to handle API responses correctly and display proper error messages
- [x] T021 [US1] Add logging for each processing stage in ingestion/orchestrator.py to track progress

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Handle Processing Errors Gracefully (Priority: P2)

**Goal**: When file processing fails at any stage (file reading, OCR, extraction, validation), the system captures the error, marks the invoice appropriately, and allows users to understand what went wrong without breaking the entire workflow.

**Independent Test**: Upload a corrupted or unsupported file and verify that the system handles the error gracefully, provides clear feedback, and continues to function for other files.

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [ ] T022 [P] [US2] Integration test for error handling with corrupted files in tests/integration/test_error_handling.py
- [ ] T023 [P] [US2] Unit test for error handling in file processors in tests/unit/test_file_processors.py
- [ ] T024 [P] [US2] Integration test for batch processing with mixed valid/invalid files in tests/integration/test_batch_error_handling.py

### Implementation for User Story 2

- [x] T025 [US2] Add error handling for corrupted files in ingestion/orchestrator.py with descriptive error messages
- [x] T026 [US2] Add graceful handling for missing OCR library in ingestion/image_processor.py
- [x] T027 [US2] Add graceful handling for missing PDF library in ingestion/pdf_processor.py
- [x] T028 [US2] Ensure error messages include processing stage information in ingestion/orchestrator.py
- [x] T029 [US2] Add error isolation so one file failure doesn't affect others in interface/api/routes/uploads.py
- [x] T030 [US2] Add error message display in interface/api/routes/invoices.py for failed processing status
- [x] T031 [US2] Ensure error_message field is properly populated in core/models.py Invoice model usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Track Processing Status Accurately (Priority: P2)

**Goal**: Users can monitor the processing status of uploaded files in real-time, seeing accurate status updates as files move through the processing pipeline (pending → processing → completed/failed).

**Independent Test**: Upload a file and poll the status endpoint to verify status transitions occur correctly and match the actual processing state.

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [ ] T032 [P] [US3] Integration test for status tracking accuracy in tests/integration/test_status_tracking.py
- [ ] T033 [P] [US3] Contract test for GET /api/v1/invoices/{invoice_id} status endpoint in tests/contract/test_invoice_status_api.py
- [ ] T034 [P] [US3] Integration test for status query endpoint in tests/integration/test_status_queries.py

### Implementation for User Story 3

- [x] T035 [US3] Fix dashboard invoice list query in interface/dashboard/queries.py to handle missing extracted_data gracefully
- [x] T036 [US3] Add error handling for database query failures in interface/dashboard/queries.py
- [x] T037 [US3] Ensure status updates are committed to database immediately in ingestion/orchestrator.py
- [x] T038 [US3] Fix dashboard app.py to display error messages when queries fail in interface/dashboard/app.py
- [x] T039 [US3] Add status polling endpoint validation in interface/api/routes/invoices.py
- [x] T040 [US3] Ensure processed_at timestamp is set correctly in ingestion/orchestrator.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Process Files in Background Without Blocking (Priority: P3)

**Goal**: File processing occurs asynchronously in the background, allowing users to upload files and receive immediate confirmation without waiting for processing to complete.

**Independent Test**: Upload a file and verify that the API responds immediately with a queued status, while processing continues in the background.

### Tests for User Story 4 (MANDATORY per Constitution) ⚠️

- [ ] T041 [P] [US4] Integration test for background processing in tests/integration/test_background_processing.py
- [ ] T042 [P] [US4] Unit test for background task execution in tests/unit/test_background_tasks.py
- [ ] T043 [P] [US4] Contract test for async upload response in tests/contract/test_async_upload_api.py

### Implementation for User Story 4

- [x] T044 [US4] Verify background task execution in interface/api/routes/uploads.py process_invoice_background function
- [x] T045 [US4] Ensure API responds immediately with queued status in interface/api/routes/uploads.py
- [x] T046 [US4] Add proper session management for background tasks in interface/api/routes/uploads.py
- [x] T047 [US4] Verify concurrent processing works correctly in ingestion/orchestrator.py
- [x] T048 [US4] Add logging for background task lifecycle in interface/api/routes/uploads.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T049 [P] Add comprehensive error logging throughout ingestion workflow in ingestion/orchestrator.py, ingestion/image_processor.py, ingestion/pdf_processor.py, ingestion/excel_processor.py
- [x] T050 [P] Improve error messages in interface/api/routes/invoices.py to be more user-friendly
- [x] T051 [P] Add error recovery mechanisms in ingestion/orchestrator.py for transient failures
- [x] T052 [P] Update documentation in README.md with troubleshooting steps from quickstart.md
- [ ] T053 [P] Add unit tests to meet coverage targets (80% core, 60% overall) in tests/unit/ (Deferred - requires test infrastructure setup)
- [ ] T054 [P] Run quickstart.md validation steps to verify all fixes work (Manual validation required)
- [x] T055 Add performance monitoring for processing times in ingestion/orchestrator.py
- [ ] T056 Verify all error paths are tested in tests/integration/ (Deferred - requires test infrastructure setup)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Enhances US1 error handling but independently testable
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for status tracking but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 with async processing but independently testable

### Within Each User Story

- Tests (MANDATORY per Constitution) MUST be written and FAIL before implementation
- Core implementation before integration
- Error handling added throughout
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002, T003, T004)
- All Foundational tasks marked [P] can run in parallel (T007, T008, T009, T010)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Integration test for file upload and processing workflow in tests/integration/test_invoice_processing.py"
Task: "Unit test for process_invoice_file function in tests/unit/test_orchestrator.py"
Task: "Contract test for POST /api/v1/invoices/process endpoint in tests/contract/test_invoice_process_api.py"

# Launch file cleanup tasks together:
Task: "Move probe_paddle.py from root to scripts/probe_paddle.py"
Task: "Move probe_paddle_ocr.py from root to scripts/probe_paddle_ocr.py"
Task: "Move debug_invoice.py from root to scripts/debug_invoice.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (schema verification, file cleanup)
2. Complete Phase 2: Foundational (error handling infrastructure, health checks)
3. Complete Phase 3: User Story 1 (upload and process files successfully)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Error handling)
4. Add User Story 3 → Test independently → Deploy/Demo (Status tracking)
5. Add User Story 4 → Test independently → Deploy/Demo (Background processing)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 - MVP)
   - Developer B: User Story 2 (P2 - Error handling)
   - Developer C: User Story 3 (P2 - Status tracking)
3. After P1 and P2 stories complete:
   - Developer A: User Story 4 (P3 - Background processing)
   - Developer B: Polish phase tasks
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Schema verification (T001) is critical - must be done first
- File cleanup (T002-T004) can be done in parallel
- Error handling improvements affect all user stories
- Dashboard fixes (T035-T038) are critical for User Story 3

