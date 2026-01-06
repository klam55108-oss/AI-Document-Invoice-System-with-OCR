"""Chatbot API routes for conversational invoice querying."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.logging import get_logger
from brain.chatbot.engine import ChatbotEngine
from brain.chatbot.session_manager import SessionManager
from brain.chatbot.rate_limiter import RateLimiter
from interface.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionResponse,
    SessionDetailResponse,
    ChatMessage,
    ErrorResponse,
    ErrorDetail,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

# Initialize components (singleton instances)
session_manager = SessionManager()
rate_limiter = RateLimiter()


@router.post("/chat", response_model=ChatResponse, status_code=200)
async def send_chat_message(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Send a chat message and receive a response."""
    try:
        # Validate session ID
        try:
            session_id = UUID(request.session_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid session ID format",
            )

        # Rate limiting
        user_id = str(session_id)  # Use session_id as user identifier
        if not rate_limiter.is_allowed(user_id):
            retry_after = rate_limiter.get_retry_after(user_id)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please wait before submitting more queries.",
                headers={"Retry-After": str(retry_after)},
            )

        # Get or create session
        conv_session = session_manager.get_session(session_id)
        if not conv_session:
            conv_session = session_manager.create_session()
            session_id = conv_session.session_id

        # Process chat message
        engine = ChatbotEngine(session)
        response_text = await engine.process_message(
            message=request.message,
            session=conv_session,
            language=request.language,
        )

        # Extract invoice IDs from last assistant message if available
        invoice_ids = []
        invoice_count = 0
        has_more = False

        if conv_session.messages:
            last_msg = conv_session.messages[-1]
            if last_msg.role == "assistant":
                invoice_ids = last_msg.metadata.get("invoice_ids", [])
                invoice_count = last_msg.metadata.get("invoice_count", 0)
                has_more = last_msg.metadata.get("has_more", False)

        return ChatResponse(
            message=response_text,
            session_id=str(conv_session.session_id),
            invoice_ids=[str(uid) for uid in invoice_ids],
            invoice_count=invoice_count,
            has_more=has_more,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat message processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message. Please try again.",
        )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session() -> SessionResponse:
    """Create a new conversation session."""
    try:
        session = session_manager.create_session()
        return SessionResponse(
            session_id=str(session.session_id),
            created_at=session.created_at,
        )
    except Exception as e:
        logger.error("Session creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session. Please try again.",
        )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str) -> SessionDetailResponse:
    """Get conversation session details."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    session = session_manager.get_session(session_uuid)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    # Convert messages to schema format
    messages = [
        ChatMessage(
            message_id=str(msg.message_id),
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp,
            metadata=msg.metadata,
        )
        for msg in session.messages
    ]

    return SessionDetailResponse(
        session_id=str(session.session_id),
        created_at=session.created_at,
        last_activity=session.last_activity,
        messages=messages,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def end_session(session_id: str) -> None:
    """End a conversation session."""
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format",
        )

    session = session_manager.get_session(session_uuid)
    if session:
        # Remove session
        del session_manager.sessions[session_uuid]

    return None
