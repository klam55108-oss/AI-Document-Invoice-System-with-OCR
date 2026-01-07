# Tasks: UI and Multi-Format Data Extraction Quality Improvements

**Input**: Design documents from `/specs/001-ui-data-extract-quality/`  
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Web application structure: `core/`, `brain/`, `ingestion/`, `interface/` at repository root
- Tests: `tests/unit/`, `tests/integration/`, `tests/contract/`
- Database migrations: `alembic/versions/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure setup

- [X] T001 Review all planning documents (spec.md, plan.md, research.md, data-model.md, contracts/)
- [X] T002 Verify development environment: Python 3.12, PostgreSQL 17, all dependencies installed
- [X] T003 [P] Run baseline accuracy measurement script to establish current extraction metrics
- [X] T004 [P] Create task tracking board/system with all user stories and tasks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core database schema changes that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create Alembic migration file for per-field confidence columns in alembic/versions/002_add_per_field_confidence.py
- [X] T006 Add 7 confidence columns to extracted_data table (vendor_name_confidence, invoice_number_confidence, invoice_date_confidence, total_amount_confidence, subtotal_confidence, tax_amount_confidence, currency_confidence)
- [X] T007 [P] Add file_preview_metadata JSONB column to invoices table
- [X] T008 [P] Add processing_metadata JSONB column to invoices table
- [X] T009 Add CHECK constraints for confidence range validation (0.0-1.0) on all confidence columns
- [X] T010 [P] Create index idx_extracted_data_vendor_conf on extracted_data(vendor_name_confidence)
- [X] T011 [P] Create index idx_extracted_data_invoice_num_conf on extracted_data(invoice_number_confidence)
- [X] T012 [P] Create index idx_extracted_data_total_conf on extracted_data(total_amount_confidence)
- [X] T013 Create expression index idx_extracted_data_low_confidence for aggregate confidence filtering
- [X] T014 [P] Create index idx_invoices_batch_id on invoices((processing_metadata->>'parallel_batch_id'))
- [X] T015 Run migration: alembic upgrade head
- [X] T016 Verify migration success and index creation with database queries
- [X] T017 Update ExtractedData model in core/models.py to include 7 confidence columns with proper type hints
- [X] T018 [P] Update Invoice model in core/models.py to include file_preview_metadata and processing_metadata JSONB columns
- [X] T019 Update ExtractedDataSchema in brain/schemas.py to include per-field confidence scores with Pydantic validation
- [X] T020 Add model_validator to ExtractedDataSchema for calculating overall confidence from per-field scores

**Checkpoint**: Foundation ready - database schema updated, models synchronized, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Enhanced Extraction Quality Dashboard (Priority: P1) 🎯 MVP

**Goal**: Provide dashboard visibility into extraction quality with confidence scores, missing field indicators, quality filters, and format-specific metrics

**Independent Test**: Upload batch of 20 invoices with varying quality (Excel with headers, clear PDF, poor scan, CSV), verify dashboard displays confidence scores with color coding, allows filtering by quality issues, shows format-specific metrics

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

> **NOTE: Per Constitution Principle II, TDD is NON-NEGOTIABLE. Write these tests FIRST, ensure they FAIL before implementation. Test coverage must meet targets (80% core, 60% overall).**

- [ ] T021 [P] [US1] Create unit test for quality summary query in tests/unit/test_quality_queries.py
- [ ] T022 [P] [US1] Create unit test for quality by format aggregation in tests/unit/test_quality_queries.py
- [ ] T023 [P] [US1] Create unit test for confidence display utility functions in tests/unit/test_confidence_display.py
- [ ] T024 [P] [US1] Create integration test for quality metrics API endpoint in tests/integration/test_quality_api.py
- [ ] T025 [P] [US1] Create contract test for GET /api/v1/quality/metrics in tests/contract/test_quality_api.py
- [ ] T026 [US1] Run all User Story 1 tests and verify they FAIL (expected before implementation)

### Implementation for User Story 1

- [ ] T027 [P] [US1] Create quality_metrics.py queries module in interface/dashboard/queries/quality_metrics.py with get_quality_summary function
- [ ] T028 [P] [US1] Add get_quality_by_format function to interface/dashboard/queries/quality_metrics.py with file format grouping
- [ ] T029 [P] [US1] Add get_low_confidence_invoices function to interface/dashboard/queries/quality_metrics.py with confidence threshold filtering
- [ ] T030 [P] [US1] Create quality metrics API endpoint GET /api/v1/quality/metrics in interface/api/routes/quality.py
- [ ] T031 [P] [US1] Create confidence_display.py utility in interface/dashboard/utils/confidence_display.py with color-coded badge functions
- [ ] T032 [P] [US1] Add confidence score formatting and tooltip generation functions to interface/dashboard/utils/confidence_display.py
- [ ] T033 [P] [US1] Create quality_metrics.py component in interface/dashboard/components/quality_metrics.py with render_quality_dashboard function
- [ ] T034 [US1] Add summary metrics display (4 st.metric cards) to quality_metrics.py component
- [ ] T035 [US1] Add confidence by format bar chart using Plotly to quality_metrics.py component
- [ ] T036 [US1] Add missing fields breakdown visualization to quality_metrics.py component
- [ ] T037 [P] [US1] Enhance invoice list display in interface/dashboard/app.py to show confidence scores with color-coded badges
- [ ] T038 [P] [US1] Add confidence filter slider (0.0-1.0) to sidebar in interface/dashboard/app.py
- [ ] T039 [P] [US1] Add "Has Missing Fields" checkbox filter to sidebar in interface/dashboard/app.py
- [ ] T040 [US1] Add sortable confidence column to invoice list dataframe with proper formatting
- [ ] T041 [US1] Integrate quality metrics dashboard as new tab in interface/dashboard/app.py
- [ ] T042 [US1] Add quality issue highlighting (red/yellow/green badges) in invoice detail view for each extracted field
- [ ] T043 [US1] Run all User Story 1 tests and verify they PASS
- [ ] T044 [US1] Manual testing: Upload 20 invoices, verify quality dashboard displays correct metrics and filters work

**Checkpoint**: At this point, User Story 1 should be fully functional - quality dashboard visible, confidence scores displayed, filters working independently

---

## Phase 4: User Story 2 - Format-Specific Extraction Optimization (Priority: P1)

**Goal**: Improve extraction accuracy through format-specific strategies (Excel column mapping, PDF text detection, image preprocessing, CSV auto-detection) to achieve 85%+ critical field accuracy

**Independent Test**: Upload identical invoice content in 3 formats (Excel with headers, PDF with embedded text, scanned image), verify extraction accuracy >90% for Excel, >85% for PDF, >75% for image, and per-field confidence scores populated correctly

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [ ] T045 [P] [US2] Create unit test for Excel column header extraction in tests/unit/test_extraction_strategies.py
- [ ] T046 [P] [US2] Create unit test for PDF text vs image detection in tests/unit/test_extraction_strategies.py
- [ ] T047 [P] [US2] Create unit test for image OCR confidence propagation in tests/unit/test_extraction_strategies.py
- [ ] T048 [P] [US2] Create unit test for format hint generation in tests/unit/test_extraction_strategies.py
- [ ] T049 [P] [US2] Create unit test for field confidence calculation in tests/unit/test_extraction_strategies.py
- [ ] T050 [P] [US2] Create integration test for end-to-end Excel extraction accuracy in tests/integration/test_format_extraction.py
- [ ] T051 [P] [US2] Create integration test for end-to-end PDF extraction accuracy in tests/integration/test_format_extraction.py
- [ ] T052 [US2] Run all User Story 2 tests and verify they FAIL (expected before implementation)

### Implementation for User Story 2

- [ ] T053 [P] [US2] Add format hint generation function _generate_format_hints to brain/extractor.py with Excel/CSV, PDF, image-specific logic
- [ ] T054 [P] [US2] Add field confidence calculation function _calculate_field_confidences to brain/extractor.py with OCR, validation-based, and format-boost strategies
- [ ] T055 [US2] Enhance extract_invoice_data function in brain/extractor.py to accept metadata parameter and include format hints in LLM prompt
- [ ] T056 [US2] Add per-field confidence calculation call to extract_invoice_data after extraction completes
- [ ] T057 [P] [US2] Enhance process_excel function in ingestion/excel_processor.py to detect column headers with pandas
- [ ] T058 [P] [US2] Add column mapping metadata to process_excel return value (map "Vendor" → vendor_name, "Invoice #" → invoice_number, etc.)
- [ ] T059 [P] [US2] Enhance process_pdf function in ingestion/pdf_processor.py to detect text layer vs scanned image
- [ ] T060 [P] [US2] Add has_text_layer boolean to process_pdf metadata return value
- [ ] T061 [P] [US2] Enhance process_image function in ingestion/image_processor.py to include OCR word-level confidence scores
- [ ] T062 [P] [US2] Add ocr_confidences dictionary to process_image metadata (map extracted text to confidence scores)
- [ ] T063 [US2] Update process_invoice_file in ingestion/orchestrator.py to pass format metadata to extract_invoice_data
- [ ] T064 [US2] Update extracted_record in orchestrator to populate all 7 per-field confidence columns
- [ ] T065 [US2] Add extraction prompt enhancements for Excel/CSV structured data format (column headers, cell positions)
- [ ] T066 [US2] Add extraction prompt enhancements for PDF text vs scanned differentiation
- [ ] T067 [US2] Add extraction prompt enhancements for image OCR error correction (O vs 0, I vs 1)
- [ ] T068 [US2] Run all User Story 2 tests and verify they PASS
- [ ] T069 [US2] Manual testing: Process 10 Excel invoices, verify >90% accuracy and high confidence scores
- [ ] T070 [US2] Manual testing: Process 10 PDF invoices (mix of text and scanned), verify >85% accuracy overall
- [ ] T071 [US2] Manual testing: Process 10 image invoices, verify >75% accuracy and OCR confidence propagation
- [ ] T072 [US2] Run accuracy measurement script post-implementation, compare to baseline, verify improvement

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - quality dashboard shows improved accuracy metrics and format-specific confidence

---

## Phase 5: User Story 3 - Interactive Data Correction Workflow (Priority: P2)

**Goal**: Enable users to correct extraction errors inline with autocomplete suggestions, immediate database updates, and validation recalculation within 2 seconds

**Independent Test**: Open invoice with incorrect vendor name, click edit, verify autocomplete shows previous vendors, correct field, save, verify database updates and validation reruns within 2 seconds

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [ ] T073 [P] [US3] Create unit test for autocomplete vendor query in tests/unit/test_inline_editing.py
- [ ] T074 [P] [US3] Create unit test for extracted data update validation in tests/unit/test_inline_editing.py
- [ ] T075 [P] [US3] Create integration test for correction workflow end-to-end in tests/integration/test_correction_workflow.py
- [ ] T076 [P] [US3] Create contract test for PATCH /api/v1/invoices/{id}/extracted-data in tests/contract/test_extraction_api.py
- [ ] T077 [US3] Run all User Story 3 tests and verify they FAIL (expected before implementation)

### Implementation for User Story 3

- [ ] T078 [P] [US3] Create inline_editor.py component in interface/dashboard/components/inline_editor.py with render_inline_editor function
- [ ] T079 [P] [US3] Add get_vendor_suggestions query to interface/dashboard/queries/quality_metrics.py (SELECT DISTINCT vendor_name)
- [ ] T080 [P] [US3] Add get_invoice_number_suggestions query to interface/dashboard/queries/quality_metrics.py (SELECT DISTINCT invoice_number)
- [ ] T081 [US3] Implement field editing UI with st.text_input and st.selectbox for autocomplete in inline_editor.py
- [ ] T082 [US3] Add save button with async API call to update extracted data in inline_editor.py
- [ ] T083 [US3] Add success/error message display after save in inline_editor.py
- [ ] T084 [P] [US3] Create PATCH /api/v1/invoices/{invoice_id}/extracted-data endpoint in interface/api/routes/invoices.py
- [ ] T085 [US3] Implement extracted data update logic in PATCH endpoint with Pydantic validation
- [ ] T086 [US3] Add automatic validation recalculation after data update in PATCH endpoint
- [ ] T087 [US3] Add correction_note field to update request and log corrections for feedback learning
- [ ] T088 [US3] Store user corrections in processing_metadata JSONB for future extraction improvement
- [ ] T089 [US3] Integrate inline_editor component into invoice detail view in interface/dashboard/app.py
- [ ] T090 [US3] Add "Edit" button next to each extracted field in detail view
- [ ] T091 [US3] Add suggested total calculation from line items when total_amount is missing
- [ ] T092 [US3] Run all User Story 3 tests and verify they PASS
- [ ] T093 [US3] Manual testing: Correct 5 invoices with different field errors, verify save completes in <2s and validation updates
- [ ] T094 [US3] Performance testing: Measure save latency under load (10 concurrent corrections), verify <2s p95

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - users can view quality, extraction is accurate, and corrections are easy

---

## Phase 6: User Story 4 - Bulk Quality Review and Export (Priority: P3)

**Goal**: Support bulk operations (multi-select, bulk export to CSV/Excel/JSON, bulk corrections) and quality trend visualization for high-volume invoice processing

**Independent Test**: Process 50 invoices, filter by "Extraction Issues", select 20 invoices, export to CSV with all fields and confidence scores, verify export completes in <10s and contains correct data

### Tests for User Story 4 (MANDATORY per Constitution) ⚠️

- [ ] T095 [P] [US4] Create unit test for bulk export data formatting in tests/unit/test_bulk_operations.py
- [ ] T096 [P] [US4] Create unit test for quality trend calculation in tests/unit/test_quality_trends.py
- [ ] T097 [P] [US4] Create integration test for bulk export workflow in tests/integration/test_bulk_export.py
- [ ] T098 [P] [US4] Create contract test for GET /api/v1/quality/trends in tests/contract/test_quality_api.py
- [ ] T099 [US4] Run all User Story 4 tests and verify they FAIL (expected before implementation)

### Implementation for User Story 4

- [ ] T100 [P] [US4] Create get_quality_trends query in interface/dashboard/queries/quality_metrics.py with time-series aggregation
- [ ] T101 [P] [US4] Add date range and granularity parameters (day/week/month) to get_quality_trends function
- [ ] T102 [P] [US4] Create GET /api/v1/quality/trends endpoint in interface/api/routes/quality.py with date filtering
- [ ] T103 [P] [US4] Add bulk export functions (CSV, Excel, JSON) to interface/dashboard/utils/export_utils.py
- [ ] T104 [US4] Implement export_to_csv function with pandas DataFrame serialization
- [ ] T105 [US4] Implement export_to_excel function with openpyxl/xlsxwriter
- [ ] T106 [US4] Implement export_to_json function with proper JSON serialization of Decimal types
- [ ] T107 [US4] Add quality trend line chart to quality_metrics.py component using Plotly
- [ ] T108 [US4] Add date range selector for trend chart in quality_metrics.py component
- [ ] T109 [US4] Add bulk selection checkbox UI to invoice list in interface/dashboard/app.py
- [ ] T110 [US4] Add "Bulk Export" button with format dropdown (CSV/Excel/JSON) in interface/dashboard/app.py
- [ ] T111 [US4] Implement bulk export handler that calls export utility functions
- [ ] T112 [US4] Add filtered summary statistics display (count, avg confidence, missing fields) when filters applied
- [ ] T113 [US4] Add bulk correction UI with pattern-based rules (optional, if time permits)
- [ ] T114 [US4] Run all User Story 4 tests and verify they PASS
- [ ] T115 [US4] Manual testing: Export 100 invoices to CSV, verify completes in <10s and data is correct
- [ ] T116 [US4] Manual testing: View quality trends over 3 months, verify chart displays correctly

**Checkpoint**: All user stories (1, 2, 3, 4) should now be independently functional and integrated

---

## Phase 7: Parallel Processing Enhancement (Cross-Cutting)

**Goal**: Enable parallel batch processing of multiple invoices to improve throughput from 4/min to ~80/min (20 concurrent)

**Independent Test**: Process batch of 20 invoices concurrently, verify completion time <20s total, all invoices processed successfully, memory usage <8GB

### Tests for Parallel Processing ⚠️

- [ ] T117 [P] Create unit test for semaphore limiting in tests/unit/test_parallel_processing.py
- [ ] T118 [P] Create unit test for batch metadata tracking in tests/unit/test_parallel_processing.py
- [ ] T119 [P] Create integration test for parallel batch processing in tests/integration/test_parallel_ingestion.py
- [ ] T120 [P] Create contract test for POST /api/v1/invoices/batch/process in tests/contract/test_extraction_api.py
- [ ] T121 Run all parallel processing tests and verify they FAIL (expected before implementation)

### Implementation for Parallel Processing

- [ ] T122 Add process_invoice_batch function to ingestion/orchestrator.py with asyncio.gather and semaphore limiting
- [ ] T123 Implement batch ID generation and tracking in process_invoice_batch
- [ ] T124 Add per-task session management (create new session per concurrent task)
- [ ] T125 Add processing_metadata updates with batch_id and concurrent_slot to each invoice
- [ ] T126 Add batch progress tracking and error handling with return_exceptions
- [ ] T127 [P] Create POST /api/v1/invoices/batch/process endpoint in interface/api/routes/invoices.py
- [ ] T128 [P] Create GET /api/v1/invoices/batch/{batch_id}/progress endpoint in interface/api/routes/invoices.py
- [ ] T129 Update scripts/process_invoices.py to support --batch flag with --max-concurrency parameter
- [ ] T130 Add batch processing UI to dashboard upload component (optional, can trigger from script)
- [ ] T131 Configure database connection pool size to 30 (20 workers + 10 API) in core/config.py
- [ ] T132 Run all parallel processing tests and verify they PASS
- [ ] T133 Performance testing: Process 20 invoices in parallel, verify <20s completion time
- [ ] T134 Load testing: Process 50 invoices in batches of 20, monitor memory usage <8GB
- [ ] T135 Stress testing: Process 100 invoices concurrently, verify system stability

**Checkpoint**: Parallel processing enabled and validated for high-throughput scenarios

---

## Phase 8: File Preview Components (Cross-Cutting)

**Goal**: Add file preview capability (PDF, CSV, Excel, images) to Invoice Detail tab with <2s load time for files <10MB

**Independent Test**: Open invoice detail for PDF, verify preview displays with embedded PDF viewer; open CSV invoice, verify tabular data displays; open image invoice, verify image renders

### Tests for File Preview ⚠️

- [ ] T136 [P] Create unit test for PDF preview generation in tests/unit/test_file_preview.py
- [ ] T137 [P] Create unit test for CSV preview generation in tests/unit/test_file_preview.py
- [ ] T138 [P] Create unit test for Excel preview generation in tests/unit/test_file_preview.py
- [ ] T139 [P] Create unit test for image preview generation in tests/unit/test_file_preview.py
- [ ] T140 [P] Create integration test for preview workflow end-to-end in tests/integration/test_preview_workflow.py
- [ ] T141 [P] Create contract test for GET /api/v1/invoices/{id}/preview in tests/contract/test_preview_api.py
- [ ] T142 Run all file preview tests and verify they FAIL (expected before implementation)

### Implementation for File Preview

- [ ] T143 [P] Create file_preview.py utility module in ingestion/file_preview.py with generate_preview_data function
- [ ] T144 [P] Implement _preview_pdf function with base64 encoding and pypdf metadata extraction
- [ ] T145 [P] Implement _preview_csv function with pandas and row limiting (max 100 rows)
- [ ] T146 [P] Implement _preview_excel function with pandas multi-sheet support
- [ ] T147 [P] Implement _preview_image function with base64 encoding and Pillow metadata
- [ ] T148 [US1] Create GET /api/v1/invoices/{invoice_id}/preview endpoint in interface/api/routes/invoices.py
- [ ] T149 [US1] Add preview caching logic using file_preview_metadata JSONB column
- [ ] T150 [US1] Add file size validation (reject files >10MB) in preview endpoint
- [ ] T151 [P] [US1] Create file_preview.py component in interface/dashboard/components/file_preview.py with render_file_preview function
- [ ] T152 [P] [US1] Implement _render_pdf_preview with base64 iframe embedding
- [ ] T153 [P] [US1] Implement _render_csv_preview with st.dataframe display
- [ ] T154 [P] [US1] Implement _render_excel_preview with st.dataframe display
- [ ] T155 [P] [US1] Implement _render_image_preview with st.image display
- [ ] T156 [US1] Integrate file_preview component into Invoice Detail tab in interface/dashboard/app.py
- [ ] T157 [US1] Add "File Preview" as second tab in detail view (after Extracted Data, before Validation)
- [ ] T158 [US1] Add loading spinner with progress indicator for preview generation
- [ ] T159 [US1] Run all file preview tests and verify they PASS
- [ ] T160 [US1] Manual testing: Preview PDF invoice, verify renders in <2s
- [ ] T161 [US1] Manual testing: Preview CSV with 1000 rows, verify first 100 display
- [ ] T162 [US1] Manual testing: Preview Excel with multiple sheets, verify first sheet displays
- [ ] T163 [US1] Manual testing: Preview large image (5MB), verify displays correctly
- [ ] T164 [US1] Performance testing: Preview 10MB PDF, verify completes in <2s

**Checkpoint**: File preview functional for all supported formats with caching and performance validation

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements, documentation, and validation that affect multiple user stories

- [ ] T165 [P] Update API documentation with new endpoints (preview, quality metrics, batch processing) in docs/api.md
- [ ] T166 [P] Create user guide for quality dashboard features in docs/user-guide-quality.md
- [ ] T167 [P] Document inline correction workflow in docs/user-guide-corrections.md
- [ ] T168 [P] Add configuration documentation for parallel processing settings in docs/configuration.md
- [ ] T169 Code cleanup: Remove debug logging, unused imports across all modified files
- [ ] T170 Code refactoring: Extract common query patterns to reusable utility functions
- [ ] T171 [P] Add additional unit tests to reach 80% coverage for core modules (brain/, ingestion/)
- [ ] T172 [P] Add additional unit tests to reach 60% overall coverage
- [ ] T173 Security review: Validate input sanitization in all new endpoints
- [ ] T174 Security review: Check file path traversal vulnerabilities in preview endpoints
- [ ] T175 Performance optimization: Add caching for expensive quality metric queries
- [ ] T176 Performance optimization: Optimize database indexes based on query execution plans
- [ ] T177 Run complete test suite: pytest tests/ -v --cov
- [ ] T178 Verify test coverage targets: 80% core modules, 60% overall
- [ ] T179 Run static analysis: ruff check . && mypy .
- [ ] T180 Fix any linter errors or type hint issues
- [ ] T181 Run quickstart.md validation: Follow quickstart guide step-by-step
- [ ] T182 Measure final extraction accuracy: Run accuracy measurement script
- [ ] T183 Compare baseline vs final metrics: Verify 85%+ accuracy and 40% STP improvement
- [ ] T184 Generate performance report: Document latency, throughput, memory usage metrics
- [ ] T185 Create deployment checklist based on quickstart.md deployment section
- [ ] T186 Update README.md with new quality features and usage instructions
- [ ] T187 Create changelog entry for feature release

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (database migration MUST complete first)
- **User Story 1 (Phase 3)**: Depends on Foundational phase - Can start immediately after migration
- **User Story 2 (Phase 4)**: Depends on Foundational phase - Can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational phase - Can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational phase - Can run in parallel with US1/US2/US3
- **Parallel Processing (Phase 7)**: Can run in parallel with user stories - Independent feature
- **File Preview (Phase 8)**: Integrates with US1 dashboard - Should complete after US1 core functionality
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: ✅ Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: ✅ Can start after Foundational (Phase 2) - Independent, but integrates with US1 dashboard metrics
- **User Story 3 (P2)**: ✅ Can start after Foundational (Phase 2) - Independent, uses US1 display components
- **User Story 4 (P3)**: ✅ Can start after Foundational (Phase 2) - Independent, extends US1 dashboard

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/schemas before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete and validated before moving to next priority

### Parallel Opportunities

**Foundational Phase** (after migration file created):
- T007-T008 (JSONB columns), T010-T012 (indexes) can run in parallel
- T017-T018 (model updates) can run in parallel after migration completes

**User Story 1**:
- All tests T021-T025 can run in parallel
- T027-T029 (query functions), T030 (API endpoint), T031-T032 (utilities) can all run in parallel
- T037-T039 (sidebar filters) can run in parallel

**User Story 2**:
- All tests T045-T051 can run in parallel
- T053-T054 (extraction helpers), T057-T058 (Excel), T059-T060 (PDF), T061-T062 (Image) can all run in parallel
- T069-T071 (manual testing) can run in parallel across formats

**User Story 3**:
- All tests T073-T076 can run in parallel
- T078-T080 (autocomplete queries), T084 (API endpoint) can run in parallel

**User Story 4**:
- All tests T095-T098 can run in parallel
- T100-T102 (trend queries), T103-T106 (export functions) can all run in parallel

**Parallel Processing**:
- All tests T117-T120 can run in parallel
- T127-T128 (API endpoints) can run in parallel

**File Preview**:
- All tests T136-T141 can run in parallel
- T144-T147 (preview functions), T151-T155 (render functions) can all run in parallel

**Polish Phase**:
- Documentation tasks T165-T168 can all run in parallel
- Test tasks T171-T172 can run in parallel
- Security reviews T173-T174 can run in parallel

---

## Parallel Example: User Story 1 (Enhanced Extraction Quality Dashboard)

```bash
# After Foundational Phase completes, launch all US1 tests together:
Task T021: "Create unit test for quality summary query in tests/unit/test_quality_queries.py"
Task T022: "Create unit test for quality by format aggregation in tests/unit/test_quality_queries.py"
Task T023: "Create unit test for confidence display utility functions in tests/unit/test_confidence_display.py"
Task T024: "Create integration test for quality metrics API endpoint in tests/integration/test_quality_api.py"
Task T025: "Create contract test for GET /api/v1/quality/metrics in tests/contract/test_quality_api.py"

# After tests fail, launch all backend components together:
Task T027: "Create quality_metrics.py queries module with get_quality_summary function"
Task T028: "Add get_quality_by_format function to quality_metrics.py"
Task T029: "Add get_low_confidence_invoices function to quality_metrics.py"
Task T030: "Create quality metrics API endpoint GET /api/v1/quality/metrics"
Task T031: "Create confidence_display.py utility with color-coded badge functions"
Task T032: "Add confidence score formatting functions"
```

---

## Parallel Example: User Story 2 (Format-Specific Extraction)

```bash
# Launch all format-specific processor enhancements in parallel:
Task T057: "Enhance process_excel function to detect column headers"
Task T058: "Add column mapping metadata to process_excel return"
Task T059: "Enhance process_pdf function to detect text layer vs scanned"
Task T060: "Add has_text_layer boolean to process_pdf metadata"
Task T061: "Enhance process_image function to include OCR confidence scores"
Task T062: "Add ocr_confidences dictionary to process_image metadata"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Enhanced Extraction Quality Dashboard)
4. Complete Phase 8: File Preview (integrates with US1)
5. **STOP and VALIDATE**: Test User Story 1 independently with file preview
6. Measure impact: Run accuracy baseline vs current, verify quality dashboard displays correctly
7. Deploy/demo if ready - this is a fully functional MVP!

**MVP Deliverable**: Dashboard with quality visibility, confidence scores, filtering, and file preview - addresses core user pain point

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + File Preview → Test independently → Deploy/Demo (MVP! 🎯)
3. Add User Story 2 (Format-Specific Extraction) → Test independently → Deploy/Demo (accuracy improvement)
4. Add User Story 3 (Inline Correction) → Test independently → Deploy/Demo (workflow efficiency)
5. Add User Story 4 (Bulk Operations) → Test independently → Deploy/Demo (high-volume support)
6. Add Parallel Processing → Test performance → Deploy/Demo (throughput improvement)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

1. Team completes Setup + Foundational together (MUST finish before splitting)
2. Once Foundational is done (database migration complete):
   - **Developer A**: User Story 1 + File Preview (MVP priority)
   - **Developer B**: User Story 2 (Format-Specific Extraction)
   - **Developer C**: Parallel Processing Enhancement
3. After initial stories complete:
   - **Developer A**: User Story 3 (Inline Correction)
   - **Developer B**: User Story 4 (Bulk Operations)
   - **Developer C**: Performance optimization and polish
4. Stories complete and integrate independently

---

## Task Summary

**Total Tasks**: 187  
**Task Distribution**:
- Setup (Phase 1): 4 tasks
- Foundational (Phase 2): 16 tasks (BLOCKING - includes database migration)
- User Story 1 - Enhanced Quality Dashboard (P1): 24 tasks (6 tests + 18 implementation)
- User Story 2 - Format-Specific Extraction (P1): 28 tasks (8 tests + 20 implementation)
- User Story 3 - Interactive Correction (P2): 22 tasks (5 tests + 17 implementation)
- User Story 4 - Bulk Operations (P3): 17 tasks (5 tests + 12 implementation)
- Parallel Processing (Cross-Cutting): 19 tasks (5 tests + 14 implementation)
- File Preview (Cross-Cutting): 29 tasks (7 tests + 22 implementation)
- Polish & Cross-Cutting: 28 tasks

**Parallel Opportunities Identified**: 78 tasks marked [P] for parallel execution  
**Test Coverage**: 36 test tasks (19% of total) across unit, integration, and contract tests

**Independent Test Criteria**:
- ✅ User Story 1: Upload 20 invoices, verify quality dashboard, confidence scores, filters
- ✅ User Story 2: Upload same invoice in 3 formats, verify >85% accuracy, confidence populated
- ✅ User Story 3: Correct 5 fields, verify save <2s, validation updates
- ✅ User Story 4: Export 50 invoices to CSV, verify <10s completion

**Suggested MVP Scope**: User Story 1 (Enhanced Quality Dashboard) + File Preview = 53 tasks  
**Estimated MVP Time**: 15-20 hours (with TDD approach)

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Per Constitution: Tests MUST be written first and MUST fail before implementation
- Target test coverage: 80% for core modules (brain/, ingestion/), 60% overall
- Verify tests fail before implementing → implement → verify tests pass → commit
- Stop at any checkpoint to validate story independently before proceeding
- Database migration (Phase 2) is CRITICAL - blocks all user story work
- File paths are exact - use these paths when implementing tasks
- Commit after each task or logical group of related tasks
- Use Git feature branches per user story for easier code review

