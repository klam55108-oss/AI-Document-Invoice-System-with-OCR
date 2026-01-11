# Quickstart: Invoice Chatbot

**Feature**: Invoice Chatbot  
**Date**: 2024-12-19  
**Status**: Implementation Guide

## Overview

This guide helps you quickly set up and test the invoice chatbot feature. The chatbot allows users to query trained invoice data using natural language, powered by DeepSeek Chat model and free embedding models.

## Prerequisites

1. **Existing Setup**: Invoice processing pipeline must be functional with trained embeddings in pgvector
2. **Python 3.12**: Ensure Python 3.12 is installed
3. **PostgreSQL with pgvector**: Database must have pgvector extension enabled
4. **Environment Variables**: Configure `.env` file with required settings

## Configuration

### 1. Environment Variables

Add the following to your `.env` file:

```bash
# DeepSeek Chat Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.0

# Embedding Model Configuration
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
# OR for multilingual support:
# EMBED_MODEL=sentence-transformers/paraphrase-multilingual-e5-small

# Chatbot Settings
CHATBOT_RATE_LIMIT=20  # queries per minute
CHATBOT_SESSION_TIMEOUT=1800  # 30 minutes in seconds
CHATBOT_MAX_RESULTS=50  # maximum invoices per response
CHATBOT_CONTEXT_WINDOW=10  # last 10 messages in context
```

### 2. Install Dependencies

Add required packages to `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "deepseek>=1.0.0",  # DeepSeek SDK (or use OpenAI-compatible client)
    "sentence-transformers>=2.2.0",  # For free embedding models
    "pgvector>=0.2.0",  # PostgreSQL vector extension client
]
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

## Project Structure

```
interface/
├── api/
│   ├── routes/
│   │   └── chatbot.py          # Chatbot API endpoints
│   └── schemas.py              # Updated with chatbot schemas
├── dashboard/
│   ├── components/
│   │   └── chatbot.py          # Streamlit chatbot UI component
│   └── app.py                  # Updated with chatbot tab
brain/
└── chatbot/
    ├── __init__.py
    ├── engine.py                # Main chatbot engine
    ├── session_manager.py       # Session management
    ├── query_handler.py         # Query intent classification
    ├── vector_retriever.py      # pgvector similarity search
    └── rate_limiter.py          # Rate limiting
```

## Implementation Steps

### Step 1: Create Chatbot Module Structure

```bash
mkdir -p brain/chatbot
touch brain/chatbot/__init__.py
touch brain/chatbot/engine.py
touch brain/chatbot/session_manager.py
touch brain/chatbot/query_handler.py
touch brain/chatbot/vector_retriever.py
touch brain/chatbot/rate_limiter.py
```

### Step 2: Update Configuration

Add to `core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # DeepSeek Chat
    DEEPSEEK_API_KEY: str | None = None
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_TEMPERATURE: float = 0.0
    
    # Embedding Model
    EMBED_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chatbot Settings
    CHATBOT_RATE_LIMIT: int = 20
    CHATBOT_SESSION_TIMEOUT: int = 1800
    CHATBOT_MAX_RESULTS: int = 50
    CHATBOT_CONTEXT_WINDOW: int = 10
```

### Step 3: Implement Core Components

#### 3.1 Session Manager (`brain/chatbot/session_manager.py`)

```python
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional
from dataclasses import dataclass, field
from typing import List

@dataclass
class ChatMessage:
    message_id: UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

@dataclass
class ConversationSession:
    session_id: UUID
    created_at: datetime
    last_activity: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    
    def add_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        # Keep only last 10 messages
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_seconds: int = 1800) -> bool:
        return (datetime.utcnow() - self.last_activity).total_seconds() > timeout_seconds

class SessionManager:
    def __init__(self, timeout_seconds: int = 1800):
        self.sessions: dict[UUID, ConversationSession] = {}
        self.timeout_seconds = timeout_seconds
    
    def create_session(self) -> ConversationSession:
        session_id = uuid4()
        now = datetime.utcnow()
        session = ConversationSession(
            session_id=session_id,
            created_at=now,
            last_activity=now
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: UUID) -> Optional[ConversationSession]:
        session = self.sessions.get(session_id)
        if session and not session.is_expired(self.timeout_seconds):
            return session
        if session:
            del self.sessions[session_id]
        return None
    
    def cleanup_expired(self) -> int:
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.timeout_seconds)
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)
```

#### 3.2 Rate Limiter (`brain/chatbot/rate_limiter.py`)

```python
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

class RateLimiter:
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[user_id].append(now)
        return True
    
    def get_retry_after(self, user_id: str) -> int:
        if not self.requests[user_id]:
            return 0
        
        oldest = min(self.requests[user_id])
        window_end = oldest + timedelta(seconds=self.window_seconds)
        now = datetime.utcnow()
        
        if window_end > now:
            return int((window_end - now).total_seconds())
        return 0
```

#### 3.3 Vector Retriever (`brain/chatbot/vector_retriever.py`)

```python
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorRetriever:
    def __init__(self, model_name: str, session: AsyncSession):
        self.model = SentenceTransformer(model_name)
        self.session = session
    
    async def search_similar(
        self,
        query_text: str,
        limit: int = 50,
        threshold: float = 0.7
    ) -> List[UUID]:
        # Embed query
        query_embedding = self.model.encode(query_text)
        query_vector = f"[{','.join(map(str, query_embedding))}]"
        
        # Vector similarity search in pgvector
        query = text("""
            SELECT invoice_id, embedding <=> :query_vector::vector AS distance
            FROM invoice_embeddings
            WHERE embedding <=> :query_vector::vector < :threshold
            ORDER BY distance
            LIMIT :limit
        """)
        
        result = await self.session.execute(
            query,
            {
                "query_vector": query_vector,
                "threshold": threshold,
                "limit": limit
            }
        )
        
        rows = result.fetchall()
        return [UUID(row[0]) for row in rows]
```

### Step 4: Create API Endpoints

Create `interface/api/routes/chatbot.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.database import get_session
from brain.chatbot.engine import ChatbotEngine
from brain.chatbot.session_manager import SessionManager
from brain.chatbot.rate_limiter import RateLimiter
from interface.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize components (in production, use dependency injection)
session_manager = SessionManager()
rate_limiter = RateLimiter()

@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session)
):
    # Rate limiting
    user_id = str(request.session_id)  # Use session_id as user identifier
    if not rate_limiter.is_allowed(user_id):
        retry_after = rate_limiter.get_retry_after(user_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Get or create session
    conv_session = session_manager.get_session(request.session_id)
    if not conv_session:
        conv_session = session_manager.create_session()
    
    # Process chat message
    engine = ChatbotEngine(session)
    response = await engine.process_message(
        message=request.message,
        session=conv_session,
        language=request.language
    )
    
    return response
```

### Step 5: Add Streamlit UI Component

Create `interface/dashboard/components/chatbot.py`:

```python
import streamlit as st
import httpx
from typing import List, Dict

def render_chatbot_tab():
    st.header("💬 Chat with Invoices")
    st.markdown("Ask questions about your invoices using natural language.")
    
    # Initialize session
    if "chatbot_session_id" not in st.session_state:
        # Create new session via API
        with httpx.Client() as client:
            response = client.post("http://localhost:${API_PORT}/api/v1/chatbot/sessions")
            if response.status_code == 201:
                st.session_state.chatbot_session_id = response.json()["session_id"]
            else:
                st.error("Failed to create chat session")
                return
    
    # Display chat history
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = []
    
    for message in st.session_state.chatbot_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your invoices..."):
        # Add user message
        st.session_state.chatbot_messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Show user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                with httpx.Client() as client:
                    response = client.post(
                        "http://localhost:${API_PORT}/api/v1/chatbot/chat",
                        json={
                            "message": prompt,
                            "session_id": st.session_state.chatbot_session_id
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.write(data["message"])
                        st.session_state.chatbot_messages.append({
                            "role": "assistant",
                            "content": data["message"]
                        })
                    elif response.status_code == 429:
                        st.error("Rate limit exceeded. Please wait a moment.")
                    else:
                        st.error("Failed to get response. Please try again.")
```

Update `interface/dashboard/app.py` to add chatbot tab:

```python
# Add import
from interface.dashboard.components.chatbot import render_chatbot_tab

# In main function, add new tab
tab1, tab2, tab3 = st.tabs(["Invoice List", "Invoice Detail", "Chatbot"])
# ... existing tabs ...
with tab3:
    render_chatbot_tab()
```

## Testing

### 1. Start Services

```bash
# Terminal 1: Start FastAPI
uvicorn interface.api.main:app --reload

# Terminal 2: Start Streamlit
streamlit run interface/dashboard/app.py
```

### 2. Test API Directly

```bash
# Create session
curl -X POST http://localhost:${API_PORT}/api/v1/chatbot/sessions

# Send message
curl -X POST http://localhost:${API_PORT}/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many images did you train from dataset jimeng folder, and list the total cost?",
    "session_id": "YOUR_SESSION_ID"
  }'
```

### 3. Test in Dashboard

1. Open http://localhost:${UI_PORT:-8501}
2. Navigate to "Chatbot" tab
3. Ask questions like:
   - "How many invoices are from Acme Corp?"
   - "What is the total spending in December 2024?"
   - "Show me invoices with validation issues"

## Troubleshooting

### Issue: DeepSeek API errors
- **Solution**: Verify `DEEPSEEK_API_KEY` is set correctly in `.env`
- Check API key has sufficient credits/quota

### Issue: Embedding model not loading
- **Solution**: Ensure `sentence-transformers` is installed
- First run will download model (may take time)

### Issue: No results from vector search
- **Solution**: Verify pgvector has trained embeddings
- Check embedding dimensions match (384 for MiniLM, 1536 for OpenAI)
- Verify `invoice_embeddings` table exists

### Issue: Rate limit errors
- **Solution**: Wait 60 seconds between batches of queries
- Adjust `CHATBOT_RATE_LIMIT` in `.env` if needed

## Next Steps

1. **Implement ChatbotEngine**: Core logic for processing messages
2. **Add Query Handler**: Intent classification and routing
3. **Integrate with Existing Data**: Connect to invoice queries
4. **Add Tests**: Unit and integration tests
5. **Production Deployment**: Add Redis for session storage, monitoring

## References

- [Specification](./spec.md)
- [Research](./research.md)
- [Data Model](./data-model.md)
- [API Contract](./contracts/openapi.yaml)

