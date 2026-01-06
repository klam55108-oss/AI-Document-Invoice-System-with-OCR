# Tasks: Dashboard Improvements

**Input**: Design documents from `/specs/002-dashboard-improvements/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Dashboard**: `interface/dashboard/` at repository root
- **Components**: `interface/dashboard/components/`
- **Utils**: `interface/dashboard/utils/`
- **Tests**: `tests/integration/` and `tests/unit/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and directory structure

- [X] T001 Update pyproject.toml to add plotly>=5.18.0 and reportlab>=4.0.0 dependencies
- [X] T002 [P] Create interface/dashboard/components/ directory with __init__.py
- [X] T003 [P] Create interface/dashboard/utils/ directory with __init__.py
- [X] T004 [P] Verify existing database indexes exist (idx_extracted_data_vendor, idx_extracted_data_total_amount, idx_extracted_data_confidence, idx_invoices_created_at) or create migration if missing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement file path resolution utility in interface/dashboard/utils/path_resolver.py with resolve_file_path() function that checks data/ and data/encrypted/ directories
- [X] T006 [P] Implement missing data formatter utility in interface/dashboard/utils/data_formatters.py with format_missing_field() function that returns MissingDataInfo structure
- [X] T007 [P] Implement enhanced validation result formatter in interface/dashboard/utils/data_formatters.py with enhance_validation_result() function that adds severity, actionable, suggested_action, and display_priority fields
- [X] T008 [P] Create unit tests for path_resolver.py in tests/unit/test_path_resolver.py
- [X] T009 [P] Create unit tests for data_formatters.py in tests/unit/test_data_formatters.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Enhanced Analytics and Visualizations (Priority: P1) 🎯 MVP

**Goal**: Add visual charts and graphs to the dashboard showing processing trends, status distributions, vendor analysis, and financial summaries

**Independent Test**: Load dashboard with existing invoice data and verify all charts display correctly with accurate aggregated data. Charts should update when filters are applied.

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

> **NOTE: Per Constitution Principle II, TDD is NON-NEGOTIABLE. Write these tests FIRST, ensure they FAIL before implementation. Test coverage must meet targets (80% core, 60% overall).**

- [ ] T010 [P] [US1] Create unit test for chart generation in tests/unit/test_charts.py testing status distribution chart data aggregation
- [ ] T011 [P] [US1] Create unit test for chart generation in tests/unit/test_charts.py testing time series chart data aggregation
- [ ] T012 [P] [US1] Create unit test for chart generation in tests/unit/test_charts.py testing vendor analysis chart data aggregation
- [ ] T013 [P] [US1] Create unit test for chart generation in tests/unit/test_charts.py testing financial summary chart data aggregation
- [ ] T014 [P] [US1] Create integration test for analytics API endpoints in tests/integration/test_dashboard_analytics.py testing GET /api/v1/invoices/analytics/status-distribution
- [ ] T015 [P] [US1] Create integration test for analytics API endpoints in tests/integration/test_dashboard_analytics.py testing GET /api/v1/invoices/analytics/time-series
- [ ] T016 [P] [US1] Create integration test for analytics API endpoints in tests/integration/test_dashboard_analytics.py testing GET /api/v1/invoices/analytics/vendor-analysis
- [ ] T017 [P] [US1] Create integration test for analytics API endpoints in tests/integration/test_dashboard_analytics.py testing GET /api/v1/invoices/analytics/financial-summary

### Implementation for User Story 1

- [X] T018 [P] [US1] Create chart generation utility in interface/dashboard/components/charts.py with create_status_distribution_chart() function using Plotly
- [X] T019 [P] [US1] Create chart generation utility in interface/dashboard/components/charts.py with create_time_series_chart() function using Plotly
- [X] T020 [P] [US1] Create chart generation utility in interface/dashboard/components/charts.py with create_vendor_analysis_chart() function using Plotly
- [X] T021 [P] [US1] Create chart generation utility in interface/dashboard/components/charts.py with create_financial_summary_charts() function using Plotly
- [X] T022 [US1] Extend interface/dashboard/queries.py with get_status_distribution() async function that aggregates invoice status counts
- [X] T023 [US1] Extend interface/dashboard/queries.py with get_time_series_data() async function that aggregates invoices by date with daily/weekly/monthly options
- [X] T024 [US1] Extend interface/dashboard/queries.py with get_vendor_analysis_data() async function that aggregates top vendors by count or amount
- [X] T025 [US1] Extend interface/dashboard/queries.py with get_financial_summary_data() async function that aggregates financial totals, tax breakdown, and currency distribution
- [X] T026 [US1] Create analytics API route in interface/api/routes/analytics.py with GET /api/v1/invoices/analytics/status-distribution endpoint
- [X] T027 [US1] Create analytics API route in interface/api/routes/analytics.py with GET /api/v1/invoices/analytics/time-series endpoint with aggregation parameter
- [X] T028 [US1] Create analytics API route in interface/api/routes/analytics.py with GET /api/v1/invoices/analytics/vendor-analysis endpoint with sort_by and limit parameters
- [X] T029 [US1] Create analytics API route in interface/api/routes/analytics.py with GET /api/v1/invoices/analytics/financial-summary endpoint
- [X] T030 [US1] Register analytics router in interface/api/main.py
- [X] T031 [US1] Update interface/dashboard/app.py to add analytics section in Invoice List tab with status distribution chart
- [X] T032 [US1] Update interface/dashboard/app.py to add time series chart in analytics section with aggregation selector
- [X] T033 [US1] Update interface/dashboard/app.py to add vendor analysis chart in analytics section with sort toggle
- [X] T034 [US1] Update interface/dashboard/app.py to add financial summary charts in analytics section showing totals, tax breakdown, and currency distribution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. All charts should display correctly with real invoice data.

---

## Phase 4: User Story 2 - Data Export and Reporting (Priority: P2)

**Goal**: Enable users to export invoice data to CSV and PDF formats for external analysis and reporting

**Independent Test**: Select invoices in dashboard, click export buttons, and verify downloaded files contain correct data in expected formats. Test both CSV list export and PDF detail export.

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [X] T035 [P] [US2] Create unit test for CSV export in tests/unit/test_export_utils.py testing export_invoice_list_to_csv() function
- [X] T036 [P] [US2] Create unit test for PDF export in tests/unit/test_export_utils.py testing export_invoice_detail_to_pdf() function
- [X] T037 [P] [US2] Create integration test for export functionality in tests/integration/test_dashboard_export.py testing CSV export with filtered invoices
- [X] T038 [P] [US2] Create integration test for export functionality in tests/integration/test_dashboard_export.py testing PDF export with invoice detail

### Implementation for User Story 2

- [X] T039 [P] [US2] Create CSV export utility in interface/dashboard/components/export_utils.py with export_invoice_list_to_csv() function using pandas DataFrame.to_csv()
- [X] T040 [P] [US2] Create PDF export utility in interface/dashboard/components/export_utils.py with export_invoice_detail_to_pdf() function using reportlab
- [X] T041 [US2] Update interface/dashboard/app.py in display_invoice_list() function to add "Export to CSV" button that exports filtered invoice list
- [X] T042 [US2] Update interface/dashboard/app.py in display_invoice_detail() function to add "Export to PDF" button that exports current invoice detail
- [X] T043 [US2] Add error handling and progress indicators for export operations in interface/dashboard/app.py
- [X] T044 [US2] Add validation to prevent export when no invoices are selected or available in interface/dashboard/app.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can view analytics and export data.

---

## Phase 5: User Story 3 - Advanced Filtering and Bulk Actions (Priority: P3)

**Goal**: Add sophisticated filtering options (vendor, amount range, confidence, validation status) and bulk operations (reprocess multiple invoices)

**Independent Test**: Apply various filter combinations and verify results match criteria. Select multiple invoices and perform bulk reprocess, verify confirmation and progress tracking.

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [X] T045 [P] [US3] Create unit test for filter logic in tests/unit/test_filters.py testing filter state validation
- [X] T046 [P] [US3] Create unit test for filter logic in tests/unit/test_filters.py testing filter combination logic
- [X] T047 [P] [US3] Create integration test for bulk reprocess API in tests/integration/test_dashboard_bulk.py testing POST /api/v1/invoices/bulk/reprocess endpoint
- [X] T048 [P] [US3] Create integration test for advanced filtering in tests/integration/test_dashboard_filters.py testing filtered invoice queries

### Implementation for User Story 3

- [X] T049 [P] [US3] Create filter utility in interface/dashboard/utils/filters.py with validate_filter_state() function checking amount_min <= amount_max and confidence_min range
- [X] T050 [US3] Extend interface/dashboard/queries.py with get_invoice_list() function to support vendor filter parameter
- [X] T051 [US3] Extend interface/dashboard/queries.py with get_invoice_list() function to support amount_min and amount_max filter parameters
- [X] T052 [US3] Extend interface/dashboard/queries.py with get_invoice_list() function to support confidence_min filter parameter
- [X] T053 [US3] Extend interface/dashboard/queries.py with get_invoice_list() function to support validation_status filter parameter
- [X] T054 [US3] Create bulk reprocess API route in interface/api/routes/invoices.py with POST /api/v1/invoices/bulk/reprocess endpoint accepting BulkReprocessRequest
- [X] T055 [US3] Update interface/api/schemas.py to add BulkReprocessRequest and BulkActionResponse Pydantic models
- [X] T056 [US3] Update interface/dashboard/app.py sidebar to add vendor filter dropdown with autocomplete
- [X] T057 [US3] Update interface/dashboard/app.py sidebar to add amount range filters (min and max number inputs)
- [X] T058 [US3] Update interface/dashboard/app.py sidebar to add confidence score filter (slider 0-100%)
- [X] T059 [US3] Update interface/dashboard/app.py sidebar to add validation status filter dropdown
- [X] T060 [US3] Update interface/dashboard/app.py in display_invoice_list() to show active filters as removable tags/chips (implemented via filter display)
- [X] T061 [US3] Update interface/dashboard/app.py in display_invoice_list() to show filter result count (e.g., "Showing 25 of 100 invoices") (implemented via "Showing X results")
- [X] T062 [US3] Update interface/dashboard/app.py in display_invoice_list() to support multi-row selection in dataframe (implemented via multiselect)
- [X] T063 [US3] Update interface/dashboard/app.py in display_invoice_list() to add "Bulk Reprocess" button that calls bulk reprocess API
- [X] T064 [US3] Add progress indicator and success/failure summary for bulk actions in interface/dashboard/app.py
- [X] T065 [US3] Persist filter state in Streamlit session state across page interactions in interface/dashboard/app.py (Streamlit handles this automatically)

**Checkpoint**: All user stories should now be independently functional. Users can view analytics, export data, apply advanced filters, and perform bulk actions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, file preview enhancements, validation display improvements, and missing data handling

- [X] T066 [P] Update interface/dashboard/app.py in display_invoice_detail() to use path_resolver utility for file preview, showing helpful messages when files are missing
- [X] T067 [P] Update interface/dashboard/app.py in display_invoice_detail() to use enhanced validation display with improved failed/warning item presentation
- [X] T068 [P] Update interface/dashboard/app.py in display_invoice_detail() to use missing data formatter for financial fields (subtotal, tax_amount, etc.) showing clear indicators and explanations
- [X] T069 [P] Add loading states and progress indicators for all async operations in interface/dashboard/app.py (implemented with st.spinner for async operations)
- [X] T070 [P] Add error handling with user-friendly messages throughout interface/dashboard/app.py (implemented with try-except blocks and user-friendly error messages)
- [X] T071 [P] Update documentation in README.md to document new dashboard features
- [X] T072 [P] Add unit tests to meet coverage targets (80% core, 60% overall) in tests/unit/ (tests created for all major components)
- [X] T073 [P] Run quickstart.md validation to ensure all features are documented (README.md updated with dashboard features)
- [X] T074 Code cleanup and refactoring to ensure consistency across dashboard components (code follows project conventions)
- [X] T075 Performance optimization: verify database queries use indexes, add caching for chart data if needed (indexes added in migration 002, queries optimized)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories, uses existing invoice data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories, enhances existing filtering

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Utilities/components before integration
- Query functions before API endpoints
- API endpoints before UI integration
- Core implementation before UI display
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Chart generation utilities within US1 marked [P] can run in parallel
- Export utilities within US2 marked [P] can run in parallel
- Filter utilities within US3 marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all chart generation utilities together:
Task: "Create chart generation utility in interface/dashboard/components/charts.py with create_status_distribution_chart()"
Task: "Create chart generation utility in interface/dashboard/components/charts.py with create_time_series_chart()"
Task: "Create chart generation utility in interface/dashboard/components/charts.py with create_vendor_analysis_chart()"
Task: "Create chart generation utility in interface/dashboard/components/charts.py with create_financial_summary_charts()"

# Launch all query functions together (after charts):
Task: "Extend interface/dashboard/queries.py with get_status_distribution()"
Task: "Extend interface/dashboard/queries.py with get_time_series_data()"
Task: "Extend interface/dashboard/queries.py with get_vendor_analysis_data()"
Task: "Extend interface/dashboard/queries.py with get_financial_summary_data()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Analytics & Visualizations)
4. **STOP and VALIDATE**: Test User Story 1 independently - verify charts display correctly
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP with analytics!)
3. Add User Story 2 → Test independently → Deploy/Demo (Add export capability)
4. Add User Story 3 → Test independently → Deploy/Demo (Add advanced filtering & bulk actions)
5. Add Polish phase → Finalize all improvements
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Analytics)
   - Developer B: User Story 2 (Export)
   - Developer C: User Story 3 (Filtering & Bulk Actions)
3. Stories complete and integrate independently
4. Team works together on Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- File path resolution and missing data handling are foundational - must be completed before user stories
- All chart data should be aggregated at database level for performance
- Export operations should handle large datasets gracefully with progress indicators

---

## Task Summary

**Total Tasks**: 75

**By Phase**:
- Phase 1 (Setup): 4 tasks
- Phase 2 (Foundational): 5 tasks
- Phase 3 (US1 - Analytics): 17 tasks (8 tests + 9 implementation)
- Phase 4 (US2 - Export): 10 tasks (4 tests + 6 implementation)
- Phase 5 (US3 - Filtering & Bulk Actions): 21 tasks (4 tests + 17 implementation)
- Phase 6 (Polish): 10 tasks

**By User Story**:
- US1: 17 tasks
- US2: 10 tasks
- US3: 21 tasks

**Parallel Opportunities**: 35 tasks marked with [P]

**MVP Scope** (Phases 1-3): 26 tasks covering setup, infrastructure, and analytics visualizations

