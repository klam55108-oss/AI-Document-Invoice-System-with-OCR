# Research: Invoice Chatbot Implementation

**Feature**: Invoice Chatbot  
**Date**: 2024-12-19  
**Status**: Complete

## LLM Model Selection: DeepSeek Chat

**Decision**: Use DeepSeek Chat model for conversational AI

**Rationale**:
- Cost-effective alternative to OpenAI GPT models
- Supports both English and Chinese languages (required by spec)
- Good performance for conversational tasks
- API-compatible interface similar to OpenAI
- Configuration via .env file aligns with existing project patterns

**Alternatives Considered**:
- **OpenAI GPT-4**: Higher cost, already used for extraction but user wants DeepSeek for chatbot
- **Anthropic Claude**: Higher cost, good quality but not specified by user
- **Local LLMs (Ollama)**: Free but requires local GPU resources, adds infrastructure complexity
- **OpenRouter**: Aggregator service but adds another dependency layer

**Implementation Notes**:
- Use `deepseek` Python SDK or OpenAI-compatible client
- Configure via environment variables: `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` (default: "deepseek-chat")
- Temperature setting: 0.0 for consistent responses (same as extraction model)
- Error handling: Graceful fallback with user-friendly messages
- Rate limiting: Respect DeepSeek API rate limits in addition to application-level limits

## Embedding Model Selection: Free Models

**Decision**: Use a free embedding model compatible with existing pgvector storage

**Rationale**:
- Cost reduction for high-volume similarity searches
- Existing pgvector storage already contains trained embeddings
- Free models provide sufficient quality for retrieval tasks
- Aligns with "Complexity Collapse" strategy (minimize external costs)

**Alternatives Considered**:
- **OpenAI text-embedding-3-small**: Low cost but not free, currently used
- **sentence-transformers (all-MiniLM-L6-v2)**: Free, 384 dimensions, good for English
- **BGE-small-en-v1.5**: Free, 384 dimensions, optimized for English
- **multilingual-e5-small**: Free, 384 dimensions, supports English and Chinese
- **OpenAI-compatible free APIs**: HuggingFace Inference API, but adds external dependency

**Implementation Notes**:
- **Recommended**: Use `sentence-transformers` library with `all-MiniLM-L6-v2` for English-only or `multilingual-e5-small` for English+Chinese
- Embedding dimension: 384 (matches smaller model standard, may need migration if existing embeddings are 1536)
- Local execution: Run embeddings locally using sentence-transformers (no API calls)
- Compatibility: Ensure new query embeddings match dimension of existing pgvector embeddings
- If existing embeddings are 1536 (OpenAI), consider:
  - Option A: Re-embed all existing data with new model (migration required)
  - Option B: Continue using OpenAI embeddings for queries (not free but compatible)
  - Option C: Use OpenAI-compatible free API that outputs 1536 dimensions

**Configuration**:
- Add to `.env`: `EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2` or `multilingual-e5-small`
- Add to `core/config.py`: `EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"`
- Load model once at startup, reuse for all queries

## pgvector Integration for RAG

**Decision**: Query existing pgvector embeddings using similarity search for invoice retrieval

**Rationale**:
- Existing infrastructure already has trained embeddings in pgvector
- Vector similarity search enables semantic query understanding
- No need to re-embed or migrate data
- Leverages "All-in-Postgres" architecture

**Implementation Notes**:
- Use `pgvector` Python client (`pgvector` package) for similarity search
- Query pattern: Embed user question → Find similar invoice embeddings → Retrieve invoice IDs → Query structured data
- Similarity threshold: Use cosine similarity, return top-k results (k=50 max per spec)
- Hybrid search: Combine vector similarity with structured filters (vendor, date, amount) when detected in query
- Index optimization: Ensure pgvector indexes exist on embedding columns for fast search

**Query Flow**:
1. User asks natural language question
2. Embed question using free embedding model
3. Vector similarity search in pgvector: `SELECT invoice_id, embedding <=> $1 AS distance FROM invoice_embeddings ORDER BY distance LIMIT 50`
4. Retrieve invoice details from `invoices` and `extracted_data` tables
5. Format results for LLM context
6. Generate response using DeepSeek Chat

## Session Management

**Decision**: Use in-memory session storage with optional Redis for production scaling

**Rationale**:
- Spec states sessions expire after 30 minutes of inactivity
- No requirement for persistent conversation history
- In-memory is simpler for MVP, Redis optional for horizontal scaling
- Reduces database load for ephemeral data

**Alternatives Considered**:
- **PostgreSQL storage**: Persistent but adds unnecessary database load for temporary data
- **Redis**: Good for production but adds infrastructure dependency
- **File-based storage**: Not suitable for concurrent access
- **Database with TTL**: Over-engineered for temporary session data

**Implementation Notes**:
- Use Python `dict` with session ID as key, session data as value
- Session data structure:
  ```python
  {
    "session_id": str,
    "user_id": str,  # Optional, if multi-user
    "messages": List[ChatMessage],  # Last 10 messages
    "last_activity": datetime,
    "created_at": datetime
  }
  ```
- Background task: Cleanup expired sessions every 5 minutes
- For production: Migrate to Redis with TTL for horizontal scaling
- Session ID: Generate UUID4 for each new conversation

## Rate Limiting Implementation

**Decision**: Use in-memory sliding window rate limiter with per-user tracking

**Rationale**:
- Spec requires 20 queries per minute per user
- Simple implementation for MVP
- No external dependencies
- Can migrate to Redis-based limiter for distributed systems

**Alternatives Considered**:
- **Token bucket algorithm**: More complex, not necessary for simple per-minute limit
- **Fixed window**: Simpler but allows bursts at window boundaries
- **Redis-based**: Good for distributed systems but adds dependency
- **Database-based**: Over-engineered, adds database load

**Implementation Notes**:
- Sliding window: Track timestamps of last 20 queries per user
- User identification: Use session ID or IP address (if no auth)
- Cleanup: Remove old timestamps beyond 1-minute window
- Response: Return HTTP 429 with `Retry-After` header when limit exceeded
- Error message: "Rate limit exceeded. Please wait before submitting more queries."

## Query Intent Classification

**Decision**: Use LLM-based intent classification with structured output

**Rationale**:
- Natural language queries require understanding user intent
- LLM can classify intent and extract structured parameters
- More flexible than rule-based classification
- Can handle ambiguous queries better

**Alternatives Considered**:
- **Rule-based classification**: Too rigid, doesn't handle variations well
- **Fine-tuned classifier**: Requires training data, over-engineered
- **Keyword matching**: Insufficient for natural language understanding

**Implementation Notes**:
- Use DeepSeek Chat with structured output (JSON) for intent classification
- Intent types:
  - `find_invoice`: Find specific invoice(s) by criteria
  - `aggregate_query`: Calculate totals, counts, averages
  - `list_invoices`: List invoices matching filters
  - `get_details`: Get detailed information about specific invoice
- Extract structured parameters: vendor, date range, amount range, invoice number, etc.
- Fallback: If classification fails, use general RAG retrieval

## Error Handling Strategy

**Decision**: Graceful degradation with user-friendly error messages

**Rationale**:
- Spec requires user-friendly error messages (FR-014)
- System should remain functional even if components fail
- Clear guidance helps users understand issues

**Implementation Notes**:
- LLM service failure: Show "I'm having trouble processing your request. Please try again in a moment."
- Database connection failure: Show "Unable to access invoice data. Please try again later."
- Rate limit exceeded: Show "You've asked too many questions. Please wait a minute before asking more."
- No results found: Show "I couldn't find any invoices matching your criteria. Try rephrasing your question."
- Ambiguous query: Show "I found multiple possible matches. Could you be more specific?" with list of options
- All errors logged with structured logging for debugging

## Integration with Existing Dashboard

**Decision**: Add chatbot as new tab in existing Streamlit dashboard

**Rationale**:
- Spec states integration into existing dashboard interface
- Streamlit has built-in chat components (`st.chat_message`, `st.chat_input`)
- Consistent with existing dashboard architecture
- No need for separate frontend application

**Implementation Notes**:
- Use Streamlit's `st.chat_message` and `st.chat_input` components
- Create new tab: "Chatbot" or "Ask Questions"
- Session state: Store conversation history in `st.session_state`
- API calls: Use FastAPI backend for chatbot processing (separate from Streamlit)
- Real-time updates: Streamlit's rerun mechanism for new messages
- Loading indicator: Show typing indicator while waiting for response

## Performance Optimization

**Decision**: Implement caching and async processing for query optimization

**Rationale**:
- Spec requires < 3s response time for 95% of queries
- Vector search and LLM calls can be slow
- Caching reduces redundant computations

**Implementation Notes**:
- Cache embedding results: Cache question embeddings for identical queries
- Cache LLM responses: Cache responses for identical questions (with TTL)
- Async processing: Use async/await for all I/O operations
- Parallel queries: When possible, run vector search and structured queries in parallel
- Connection pooling: Reuse database connections via asyncpg pool
- Batch operations: Process multiple invoice retrievals in single query when possible

