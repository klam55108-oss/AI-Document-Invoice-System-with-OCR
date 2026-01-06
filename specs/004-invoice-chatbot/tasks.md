# Tasks: Invoice Chatbot

**Input**: Design documents from `/specs/004-invoice-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per Constitution Principle II (Testing Discipline), TDD is mandatory. Tests MUST be written before implementation. Test coverage targets: 80% for core chatbot modules, 60% overall. All tests MUST be categorized (unit, integration, contract).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **API Routes**: `interface/api/routes/` at repository root
- **Dashboard Components**: `interface/dashboard/components/`
- **Core Models**: `core/`
- **Brain/Chatbot**: `brain/chatbot/`
- **Tests**: `tests/integration/` and `tests/unit/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency verification, and directory structure

- [X] T001 [P] Verify dependencies in pyproject.toml: deepseek SDK (or OpenAI-compatible client), sentence-transformers>=2.2.0, pgvector>=0.2.0
- [X] T002 [P] Create brain/chatbot/ directory structure with __init__.py
- [X] T003 [P] Create interface/api/routes/chatbot.py file with router setup
- [X] T004 [P] Create interface/dashboard/components/chatbot.py file with component structure
- [X] T005 [P] Verify .env file has DEEPSEEK_API_KEY, DEEPSEEK_MODEL, EMBED_MODEL, CHATBOT_* variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Update core/config.py to add DeepSeek and embedding model configuration fields (DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_TEMPERATURE, EMBED_MODEL, CHATBOT_RATE_LIMIT, CHATBOT_SESSION_TIMEOUT, CHATBOT_MAX_RESULTS, CHATBOT_CONTEXT_WINDOW)
- [X] T007 [P] Create brain/chatbot/session_manager.py with ConversationSession and ChatMessage dataclasses and SessionManager class
- [X] T008 [P] Create brain/chatbot/rate_limiter.py with RateLimiter class implementing sliding window rate limiting
- [X] T009 [P] Create brain/chatbot/vector_retriever.py with VectorRetriever class for pgvector similarity search
- [X] T010 [P] Create brain/chatbot/query_handler.py with QueryHandler class for intent classification
- [X] T011 Create brain/chatbot/engine.py with ChatbotEngine class integrating all components (depends on T007, T008, T009, T010)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ask Questions About Specific Invoices (Priority: P1) 🎯 MVP

**Goal**: Enable users to ask natural language questions about specific invoices and receive immediate answers

**Independent Test**: Ask a question about a known invoice and verify the chatbot returns accurate information from the extracted data.

### Tests for User Story 1 (MANDATORY per Constitution) ⚠️

> **NOTE: Per Constitution Principle II, TDD is NON-NEGOTIABLE. Write these tests FIRST, ensure they FAIL before implementation.**

- [X] T012 [P] [US1] Create unit test for session manager in tests/unit/test_session_manager.py testing session creation, expiration, and message management
- [X] T013 [P] [US1] Create unit test for rate limiter in tests/unit/test_rate_limiter.py testing 20 queries/minute limit enforcement
- [X] T014 [P] [US1] Create unit test for vector retriever in tests/unit/test_vector_retriever.py testing pgvector similarity search (mock database)
- [X] T015 [P] [US1] Create unit test for query handler in tests/unit/test_query_handler.py testing intent classification (find_invoice, get_details)
- [X] T016 [P] [US1] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing POST /api/v1/chatbot/chat with invoice lookup query
- [X] T017 [P] [US1] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing rate limiting (429 response)
- [X] T018 [P] [US1] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing session creation and retrieval

### Implementation for User Story 1

- [X] T019 [P] [US1] Create chatbot API schemas in interface/api/schemas.py: ChatRequest, ChatResponse, SessionResponse, ChatMessage, ErrorResponse
- [X] T020 [US1] Implement POST /api/v1/chatbot/chat endpoint in interface/api/routes/chatbot.py with message processing and response generation
- [X] T021 [US1] Implement session management in interface/api/routes/chatbot.py creating/retrieving sessions and maintaining context
- [X] T022 [US1] Implement rate limiting check in interface/api/routes/chatbot.py enforcing 20 queries/minute with 429 response
- [X] T023 [US1] Implement query processing in brain/chatbot/engine.py processing user message, retrieving invoices, generating response
- [X] T024 [US1] Implement invoice retrieval in brain/chatbot/engine.py using vector search and structured queries to find matching invoices
- [X] T025 [US1] Implement response generation in brain/chatbot/engine.py using DeepSeek Chat to generate natural language responses
- [X] T026 [US1] Register chatbot router in interface/api/main.py with app.include_router(chatbot.router, prefix="/api/v1")
- [X] T027 [P] [US1] Create chatbot UI component in interface/dashboard/components/chatbot.py with Streamlit chat interface
- [X] T028 [US1] Implement chat message display in interface/dashboard/components/chatbot.py showing conversation history
- [X] T029 [US1] Implement chat input handling in interface/dashboard/components/chatbot.py sending messages to API and displaying responses
- [X] T030 [US1] Add chatbot tab to Streamlit dashboard in interface/dashboard/app.py creating new tab "Chatbot" or "Ask Questions"
- [X] T031 [US1] Integrate chatbot component in interface/dashboard/app.py rendering chatbot UI in the new tab

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can ask questions about specific invoices and receive answers.

---

## Phase 4: User Story 2 - Aggregate Analytics Queries (Priority: P2)

**Goal**: Enable users to ask aggregate questions about invoices (totals, counts, averages) and receive calculated answers

**Independent Test**: Ask aggregate questions about invoice data and verify the chatbot performs calculations correctly.

### Tests for User Story 2 (MANDATORY per Constitution) ⚠️

- [ ] T032 [P] [US2] Create unit test for query handler in tests/unit/test_query_handler.py testing aggregate_query intent classification
- [ ] T033 [P] [US2] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing aggregate queries (totals, counts, averages)
- [ ] T034 [P] [US2] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing date range filtering in aggregate queries

### Implementation for User Story 2

- [ ] T035 [US2] Implement aggregate query handling in brain/chatbot/query_handler.py classifying aggregate_query intent and extracting parameters
- [ ] T036 [US2] Implement aggregate calculation logic in brain/chatbot/engine.py performing totals, counts, averages across invoices
- [ ] T037 [US2] Implement date range filtering in brain/chatbot/engine.py filtering invoices by date range for aggregate queries
- [ ] T038 [US2] Implement vendor filtering in brain/chatbot/engine.py filtering invoices by vendor for aggregate queries
- [ ] T039 [US2] Implement result formatting in brain/chatbot/engine.py formatting aggregate results in natural language responses

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can ask both specific invoice questions and aggregate analytics queries.

---

## Phase 5: User Story 3 - Conversational Context and Follow-ups (Priority: P3)

**Goal**: Enable users to ask follow-up questions that reference previous answers without repeating context

**Independent Test**: Ask a question, then ask a follow-up that references the previous answer, and verify the chatbot maintains context correctly.

### Tests for User Story 3 (MANDATORY per Constitution) ⚠️

- [ ] T040 [P] [US3] Create unit test for session manager in tests/unit/test_session_manager.py testing context window (last 10 messages)
- [ ] T041 [P] [US3] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing follow-up questions with context
- [ ] T042 [P] [US3] Create integration test for chatbot API endpoint in tests/integration/test_chatbot_api.py testing session expiration (30 minutes)

### Implementation for User Story 3

- [ ] T043 [US3] Implement context window management in brain/chatbot/session_manager.py maintaining last 10 messages per session
- [ ] T044 [US3] Implement context injection in brain/chatbot/engine.py including conversation history in LLM prompts
- [ ] T045 [US3] Implement follow-up question resolution in brain/chatbot/engine.py resolving references to previous answers (e.g., "those", "it")
- [ ] T046 [US3] Implement session expiration cleanup in brain/chatbot/session_manager.py removing expired sessions (30 minutes inactivity)
- [ ] T047 [US3] Implement session expiration handling in interface/api/routes/chatbot.py creating new session when expired

**Checkpoint**: All user stories should now be independently functional. Users can have natural conversations with context maintained.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Implement error handling for LLM service failures in brain/chatbot/engine.py showing user-friendly error messages
- [ ] T049 [P] Implement error handling for database failures in brain/chatbot/engine.py showing user-friendly error messages
- [ ] T050 [P] Implement result limit handling in brain/chatbot/engine.py returning max 50 invoices with "has_more" indicator
- [ ] T051 [P] Implement ambiguous query handling in brain/chatbot/engine.py asking for clarification or listing options
- [ ] T052 [P] Implement multilingual support in brain/chatbot/engine.py supporting English and Chinese queries
- [ ] T053 [P] Add loading indicators in interface/dashboard/components/chatbot.py showing typing indicator while waiting for response
- [ ] T054 [P] Add error message display in interface/dashboard/components/chatbot.py showing user-friendly error messages
- [ ] T055 [P] Implement session cleanup background task in brain/chatbot/session_manager.py running periodic cleanup of expired sessions
- [ ] T056 [P] Add structured logging in brain/chatbot/engine.py logging queries, responses, and errors
- [ ] T057 [P] Add API endpoint for session management in interface/api/routes/chatbot.py: POST /sessions, GET /sessions/{id}, DELETE /sessions/{id}
- [ ] T058 [P] Additional unit tests to meet coverage targets (80% core, 60% overall) in tests/unit/
- [ ] T059 [P] Run quickstart.md validation testing all examples work correctly
- [ ] T060 [P] Documentation updates in README.md or docs/ for chatbot feature

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for query processing infrastructure
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 for session management

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core components before integration
- API endpoints before UI components
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, user stories should proceed sequentially (US1 → US2 → US3) due to dependencies
- All tests for a user story marked [P] can run in parallel
- Different components within a story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

