# Tasks: Switchable OCR Providers

**Input**: Design documents from `/specs/001-ocr-switch-options/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create OCR package structure in `core/ocr/__init__.py` and `ingestion/ocr/__init__.py`
- [ ] T002 [P] Add OCR provider configuration defaults in `core/config.py`
- [ ] T003 [P] Add OCR provider configuration schema in `core/configuration_models.py` and validation in `core/configuration_validation.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Add OCR Provider/OCR Result/OCR Comparison models to `core/models.py`
- [ ] T005 Create Alembic migration in `alembic/versions/` for OCR tables
- [ ] T006 [P] Implement provider registry in `core/ocr/registry.py` and wire into `core/module_registry.py`
- [ ] T007 [P] Implement OCR provider adapters (PaddleOCR, DeepSeek CPU-only) in `core/ocr/providers.py`
- [ ] T008 Implement OCR orchestration service in `core/ocr/service.py`
- [ ] T009 [P] Implement OCR persistence helpers in `core/ocr/repository.py`
- [ ] T010 Define OCR API schemas in `interface/api/schemas.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Choose an OCR provider per run (Priority: P1) 🎯 MVP

**Goal**: Allow users to select an OCR provider for a run and record provider metadata in results.

**Independent Test**: Process a single invoice with an explicit provider and verify the result is labeled with that provider.

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

- [ ] T011 [P] [US1] Contract test for `POST /ocr/run` in `tests/contract/test_ocr_run_api.py`
- [ ] T012 [P] [US1] Contract test for `GET /ocr/results/{result_id}` in `tests/contract/test_ocr_results_api.py`
- [ ] T013 [P] [US1] Integration test for provider selection in `tests/integration/test_ocr_run_provider_selection.py`
- [ ] T014 [P] [US1] Unit test for default provider selection in `tests/unit/test_ocr_provider_selection.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement OCR run endpoint in `interface/api/routes/ocr.py`
- [ ] T016 [US1] Register OCR router in `interface/api/routes/__init__.py` and `interface/api/main.py`
- [ ] T017 [US1] Add provider selection logic in `core/ocr/service.py`
- [ ] T018 [US1] Persist OCR results with provider metadata in `core/ocr/repository.py`
- [ ] T019 [US1] Add structured logging and error handling for run flow in `core/ocr/service.py`

**Checkpoint**: User Story 1 fully functional and testable independently

---

## Phase 4: User Story 2 - Compare two OCR providers on the same input (Priority: P2)

**Goal**: Run a single-invoice comparison across two providers and return side-by-side results with partial failure handling.

**Independent Test**: Compare an invoice with two providers and receive side-by-side results, with partial success handled.

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [ ] T020 [P] [US2] Contract test for `POST /ocr/compare` in `tests/contract/test_ocr_compare_api.py`
- [ ] T021 [P] [US2] Contract test for `GET /ocr/comparisons/{comparison_id}` in `tests/contract/test_ocr_comparisons_api.py`
- [ ] T022 [P] [US2] Integration test for comparison workflow in `tests/integration/test_ocr_comparison.py`
- [ ] T023 [P] [US2] Unit test for partial failure handling in `tests/unit/test_ocr_comparison_failure.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement comparison orchestration in `ingestion/ocr/compare.py`
- [ ] T025 [US2] Persist comparison records in `core/ocr/repository.py`
- [ ] T026 [US2] Add comparison endpoints to `interface/api/routes/ocr.py`
- [ ] T027 [US2] Add side-by-side comparison response models in `interface/api/schemas.py`

**Checkpoint**: User Stories 1 and 2 independently functional

---

## Phase 5: User Story 3 - Set default and allowed providers (Priority: P3)

**Goal**: Allow admin-only configuration of enabled providers and default provider.

**Independent Test**: Update default and enabled providers as admin and verify default behavior applies on runs.

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [ ] T028 [P] [US3] Contract test for `GET /ocr/providers` in `tests/contract/test_ocr_providers_api.py`
- [ ] T029 [P] [US3] Contract test for `PATCH /ocr/providers/default` in `tests/contract/test_ocr_default_provider_api.py`
- [ ] T030 [P] [US3] Contract test for `PATCH /ocr/providers/enabled` in `tests/contract/test_ocr_enabled_providers_api.py`
- [ ] T031 [P] [US3] Integration test for admin-only provider config in `tests/integration/test_ocr_provider_admin.py`
- [ ] T032 [P] [US3] Unit test for provider registry updates in `tests/unit/test_ocr_provider_registry.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement provider list and config endpoints in `interface/api/routes/ocr.py`
- [ ] T034 [US3] Enforce admin-only access in `interface/api/dependencies.py`
- [ ] T035 [US3] Persist provider configuration in `core/configuration_service.py`
- [ ] T036 [US3] Apply provider config updates in `core/ocr/registry.py`

**Checkpoint**: All user stories independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Document OCR provider switching in `docs/ocr_providers.md`
- [ ] T038 Validate quickstart steps in `specs/001-ocr-switch-options/quickstart.md`
- [ ] T039 [P] Add performance coverage for OCR flows in `tests/integration/test_ocr_performance.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, but shares OCR services
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration

### Parallel Opportunities

- All tasks marked [P] can run in parallel (different files, no dependencies)
- After Foundational phase, user stories can proceed in parallel if staffing allows

---

## Parallel Example: User Story 1

```bash
Task: "Contract test for POST /ocr/run in tests/contract/test_ocr_run_api.py"
Task: "Contract test for GET /ocr/results/{result_id} in tests/contract/test_ocr_results_api.py"
Task: "Integration test for provider selection in tests/integration/test_ocr_run_provider_selection.py"
Task: "Unit test for default provider selection in tests/unit/test_ocr_provider_selection.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently
3. Add User Story 2 → Test independently
4. Add User Story 3 → Test independently
5. Finish Polish phase
