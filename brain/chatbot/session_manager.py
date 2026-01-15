"""Conversation session management for chatbot."""

from datetime import datetime, timedelta, UTC
from uuid import UUID, uuid4
from typing import Optional
from dataclasses import dataclass, field
from typing import List

from core.config import settings


@dataclass
class ChatMessage:
    """Represents a single message in a conversation."""

    message_id: UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class ConversationSession:
    """Represents an active conversation session."""

    session_id: UUID
    created_at: datetime
    last_activity: datetime
    messages: List[ChatMessage] = field(default_factory=list)

    def add_message(self, message: ChatMessage) -> None:
        """Add a message to the session and update activity."""
        self.messages.append(message)
        # Keep only last N messages (context window)
        max_messages = settings.CHATBOT_CONTEXT_WINDOW
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
        self.last_activity = datetime.now(UTC)

    def is_expired(self, timeout_seconds: int | None = None) -> bool:
        """Check if session has expired due to inactivity."""
        if timeout_seconds is None:
            timeout_seconds = settings.CHATBOT_SESSION_TIMEOUT
        elapsed = (datetime.now(UTC) - self.last_activity).total_seconds()
        return elapsed > timeout_seconds


class SessionManager:
    """Manages conversation sessions in memory."""

    def __init__(self, timeout_seconds: int | None = None):
        """Initialize session manager."""
        self.sessions: dict[UUID, ConversationSession] = {}
        self.timeout_seconds = timeout_seconds or settings.CHATBOT_SESSION_TIMEOUT

    def create_session(self) -> ConversationSession:
        """Create a new conversation session."""
        session_id = uuid4()
        now = datetime.now(UTC)
        session = ConversationSession(
            session_id=session_id,
            created_at=now,
            last_activity=now,
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: UUID) -> Optional[ConversationSession]:
        """Get an existing session or None if not found/expired."""
        session = self.sessions.get(session_id)
        if session and not session.is_expired(self.timeout_seconds):
            return session
        if session:
            # Remove expired session
            del self.sessions[session_id]
        return None

    def cleanup_expired(self) -> int:
        """Remove expired sessions and return count of removed sessions."""
        expired = [
            sid
            for sid, session in self.sessions.items()
            if session.is_expired(self.timeout_seconds)
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)

    def get_session_count(self) -> int:
        """Get current number of active sessions."""
        return len(self.sessions)


# Default shared instance
session_manager = SessionManager()


