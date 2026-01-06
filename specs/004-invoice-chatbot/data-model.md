# Data Model: Invoice Chatbot

**Feature**: Invoice Chatbot  
**Date**: 2024-12-19  
**Status**: Complete

## Overview

The chatbot feature introduces conversation session management and message storage. For MVP, sessions are stored in-memory with optional database persistence for production. The data model focuses on conversation context, query handling, and integration with existing invoice data.

## Entities

### ConversationSession

Represents an active conversation between a user and the chatbot, maintaining context for follow-up questions.

**Storage**: In-memory (dict-based) for MVP, optional PostgreSQL table for production

**Fields**:
- `session_id` (UUID, Primary Key): Unique identifier for the conversation session
- `user_id` (str, Optional): User identifier if authentication is implemented
- `created_at` (datetime): Timestamp when session was created
- `last_activity` (datetime): Timestamp of last message (for 30-minute expiration)
- `messages` (List[ChatMessage]): Last 10 messages in the conversation (maintained in memory)
- `metadata` (dict, Optional): Additional session metadata (e.g., language preference)

**State Transitions**:
```
created → active → expired (after 30 min inactivity)
                → terminated (user ends conversation)
```

**Validation Rules**:
- `session_id` must be unique
- `last_activity` must be >= `created_at`
- `messages` list must contain <= 10 messages (older messages removed)
- Session expires if `last_activity` is > 30 minutes ago

**Indexes** (if stored in database):
- Primary key on `session_id`
- Index on `last_activity` for expiration cleanup queries

### ChatMessage

Represents a single message in a conversation (user question or chatbot response).

**Storage**: Part of ConversationSession.messages list (in-memory)

**Fields**:
- `message_id` (UUID): Unique identifier for the message
- `session_id` (UUID, Foreign Key): Reference to ConversationSession
- `role` (str): "user" or "assistant"
- `content` (str): Message text content
- `timestamp` (datetime): When the message was created
- `metadata` (dict, Optional): Additional message metadata:
  - `query_intent` (str, Optional): Classified intent (find_invoice, aggregate_query, etc.)
  - `invoice_ids` (List[UUID], Optional): Invoice IDs referenced in response
  - `tokens_used` (int, Optional): LLM tokens consumed for this message
  - `response_time_ms` (int, Optional): Response generation time in milliseconds

**Validation Rules**:
- `role` must be one of: "user", "assistant"
- `content` must be non-empty string
- `timestamp` must be valid datetime
- `message_id` must be unique within session

**Relationships**:
- Many-to-One with ConversationSession (many messages belong to one session)

### QueryIntent (Logical Entity)

Represents the classified intent of a user query. Not stored as separate entity, but extracted during query processing.

**Fields** (extracted, not persisted):
- `intent_type` (str): One of:
  - `find_invoice`: Find specific invoice(s)
  - `aggregate_query`: Calculate totals, counts, averages
  - `list_invoices`: List invoices with filters
  - `get_details`: Get detailed information about invoice
  - `ambiguous`: Query needs clarification
- `parameters` (dict): Extracted structured parameters:
  - `vendor_name` (str, Optional)
  - `invoice_number` (str, Optional)
  - `date_range` (tuple[date, date], Optional)
  - `amount_range` (tuple[float, float], Optional)
  - `status` (str, Optional)
  - `aggregation_type` (str, Optional): "sum", "count", "average", "max", "min"
- `confidence` (float): Confidence score 0.0-1.0

**Usage**: Used internally by QueryHandler to route queries to appropriate handlers

### InvoiceReference (Logical Entity)

Represents a reference to one or more invoices in a query result. Not stored separately, but included in ChatMessage metadata.

**Fields** (in ChatMessage.metadata):
- `invoice_ids` (List[UUID]): Invoice IDs referenced in the response
- `invoice_count` (int): Number of invoices in result set
- `has_more` (bool): Whether more results exist beyond the 50-invoice limit

## Relationships

1. **ConversationSession → ChatMessage**: One-to-Many
   - One session contains many messages
   - Messages are stored in session's `messages` list (in-memory)
   - Only last 10 messages are retained per session

2. **ChatMessage → Invoice** (via metadata): Many-to-Many (logical)
   - Messages can reference multiple invoices
   - Invoice IDs stored in message metadata
   - Used for context in follow-up questions

## Database Schema (Optional - for Production)

If sessions are persisted to database:

```sql
-- Conversation sessions table
CREATE TABLE conversation_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    metadata JSONB,
    CONSTRAINT check_last_activity_after_created CHECK (last_activity >= created_at)
);

CREATE INDEX idx_conversation_sessions_last_activity 
    ON conversation_sessions(last_activity) 
    WHERE last_activity < NOW() - INTERVAL '30 minutes';

-- Chat messages table
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    metadata JSONB,
    CONSTRAINT check_content_not_empty CHECK (length(content) > 0)
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp DESC);
```

## Integration with Existing Models

### Invoice Model (Existing)
- No changes required
- Chatbot queries existing `invoices` and `extracted_data` tables
- Uses existing indexes for fast lookups

### ExtractedData Model (Existing)
- No changes required
- Chatbot uses extracted data for answering questions
- Vector embeddings already stored in pgvector (separate table or column)

## Data Flow

1. **User sends message**:
   - Create ChatMessage with role="user"
   - Add to ConversationSession.messages
   - Update session.last_activity

2. **Process query**:
   - Classify intent (QueryIntent)
   - Retrieve invoices (vector search + structured query)
   - Generate response (DeepSeek Chat)

3. **Store response**:
   - Create ChatMessage with role="assistant"
   - Include invoice_ids in metadata
   - Add to ConversationSession.messages
   - Trim messages list to last 10 if exceeds limit

4. **Session expiration**:
   - Background task checks last_activity
   - Remove sessions inactive > 30 minutes
   - Clear associated messages from memory

## Migration Strategy

**Phase 1 (MVP)**: In-memory storage only
- No database migration required
- Sessions stored in Python dict
- Simple cleanup task for expired sessions

**Phase 2 (Production)**: Optional database persistence
- Create migration: `004_add_chatbot_tables.py`
- Add conversation_sessions and chat_messages tables
- Migrate in-memory sessions to database (if needed)
- Update session manager to use database

## Data Integrity

1. **Session Expiration**: Automatic cleanup of expired sessions (30 minutes inactivity)
2. **Message Limit**: Maximum 10 messages per session (FIFO removal of oldest)
3. **Rate Limiting**: Enforced at application level (20 queries/minute per user)
4. **Referential Integrity**: If using database, CASCADE DELETE messages when session deleted

## Performance Considerations

1. **In-Memory Storage**: Fast access, no database queries for session data
2. **Message Trimming**: Keep only last 10 messages to limit memory usage
3. **Session Cleanup**: Background task runs every 5 minutes to remove expired sessions
4. **Vector Search**: Use pgvector indexes for fast similarity search
5. **Query Caching**: Cache embeddings and responses for identical queries

