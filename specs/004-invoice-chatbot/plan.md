# Implementation Plan: Invoice Chatbot

**Branch**: `004-invoice-chatbot` | **Date**: 2024-12-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-invoice-chatbot/spec.md`

## Summary

Implement a conversational chatbot interface integrated into the Streamlit dashboard that allows users to query trained invoice data using natural language. The chatbot uses DeepSeek Chat model for language understanding and generation, a free embedding model for vector similarity search, and leverages existing pgvector storage containing trained invoice embeddings. Users can ask questions about specific invoices, perform aggregate analytics queries, and engage in conversational follow-ups with context maintained across the last 10 messages. The system enforces rate limiting (20 queries/minute), returns maximum 50 results per query, and handles service failures gracefully.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI 0.115.0+, Streamlit 1.39.0+, SQLAlchemy 2.0.36+, LlamaIndex 0.11.0+, DeepSeek SDK, pgvector extension  
**Storage**: PostgreSQL with pgvector (existing trained embeddings), in-memory session storage (Redis or dict-based)  
**Testing**: pytest 8.3.0+, pytest-asyncio 0.24.0+  
**Target Platform**: Linux/macOS server (FastAPI), Web browser (Streamlit dashboard)  
**Project Type**: Web application (FastAPI backend + Streamlit frontend)  
**Performance Goals**: Query response < 3s for 95% of queries, interface acknowledgment < 500ms, support 50 concurrent sessions  
**Constraints**: p95 response time < 500ms (sync), < 2s (async initiation), memory < 512MB per request, rate limit 20 queries/minute per user, max 50 invoices per response  
**Scale/Scope**: 50 concurrent conversation sessions, queries across all trained invoices in pgvector, supports English and Chinese languages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with all constitution principles:

### I. Code Quality Standards
- [x] Type hints defined for all function signatures
- [x] Static analysis tools (ruff, mypy) configured and passing
- [x] Error handling strategy defined with structured logging
- [x] Security practices identified (input validation via Pydantic, rate limiting, parameterized queries)
- [x] Dependencies will be pinned with exact versions

### II. Testing Discipline
- [x] Test-driven development (TDD) approach confirmed
- [x] Test coverage targets defined (80% core chatbot logic, 60% overall)
- [x] Test categories identified (unit, integration, contract)
- [x] Async test patterns defined (pytest-asyncio)
- [x] CI/CD test automation planned

### III. User Experience Consistency
- [x] API response format standards defined (consistent error messages, user-friendly guidance)
- [x] Error message format and user guidance strategy defined
- [x] UI consistency patterns identified (Streamlit chat component integration)
- [x] Loading states and progress indicators planned (typing indicator, response streaming)

### IV. Performance Requirements
- [x] Latency targets defined (p95 < 500ms sync, < 2s async initiation, < 3s query response)
- [x] Database query optimization strategy identified (vector similarity search with pgvector, indexed queries)
- [x] Memory usage bounds defined (< 512MB per request, context window limited to 10 messages)
- [x] Caching strategy planned (session context caching, query result caching for repeated queries)
- [x] Async I/O patterns confirmed (async database queries, async LLM API calls)
- [x] Performance regression testing planned

## Project Structure

### Documentation (this feature)

```text
specs/004-invoice-chatbot/
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
│   │   └── chatbot.py          # New: Chatbot API endpoints (POST /chat, GET /chat/sessions)
│   └── schemas.py              # Updated: Add chatbot request/response schemas
├── dashboard/
│   ├── components/
│   │   └── chatbot.py           # New: Chatbot UI component for Streamlit
│   └── app.py                   # Updated: Add chatbot tab
brain/
├── chatbot/
│   ├── __init__.py
│   ├── engine.py                # New: Chatbot engine with DeepSeek integration
│   ├── session_manager.py      # New: Conversation session management
│   ├── query_handler.py         # New: Query intent classification and routing
│   ├── vector_retriever.py      # New: pgvector similarity search integration
│   └── rate_limiter.py          # New: Rate limiting implementation
core/
├── config.py                    # Updated: Add DeepSeek and embedding model config
└── models.py                   # Updated: Add ChatMessage and ConversationSession models (optional, may use in-memory)
alembic/
└── versions/
    └── 004_add_chatbot_tables.py  # New: Migration for chatbot tables (if persisting sessions)
tests/
├── integration/
│   └── test_chatbot_api.py      # New: Chatbot API integration tests
└── unit/
    ├── test_chatbot_engine.py   # New: Chatbot engine unit tests
    ├── test_query_handler.py    # New: Query handler unit tests
    └── test_rate_limiter.py     # New: Rate limiter unit tests
```

**Structure Decision**: Single project structure with FastAPI backend and Streamlit frontend. Chatbot functionality organized in new `brain/chatbot/` module following existing brain module pattern. New API route for chatbot endpoints. Optional database tables for session persistence (may use in-memory storage initially). Configuration extended to support DeepSeek and free embedding models via .env.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution principles are satisfied.
