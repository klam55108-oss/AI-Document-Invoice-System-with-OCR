"""Unit tests for chatbot session manager."""

from datetime import datetime, timedelta
from uuid import UUID

import pytest

from brain.chatbot.session_manager import (
    SessionManager,
    ConversationSession,
    ChatMessage,
)


def test_create_session():
    """Test creating a new conversation session."""
    manager = SessionManager()
    session = manager.create_session()

    assert isinstance(session.session_id, UUID)
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_activity, datetime)
    assert len(session.messages) == 0
    assert session in manager.sessions.values()


def test_get_session():
    """Test retrieving an existing session."""
    manager = SessionManager()
    session = manager.create_session()
    session_id = session.session_id

    retrieved = manager.get_session(session_id)

    assert retrieved is not None
    assert retrieved.session_id == session_id
    assert retrieved == session


def test_get_session_not_found():
    """Test retrieving a non-existent session."""
    manager = SessionManager()
    fake_id = UUID("00000000-0000-0000-0000-000000000000")

    retrieved = manager.get_session(fake_id)

    assert retrieved is None


def test_add_message():
    """Test adding messages to a session."""
    manager = SessionManager()
    session = manager.create_session()

    message = ChatMessage(
        message_id=UUID("11111111-1111-1111-1111-111111111111"),
        role="user",
        content="Hello",
        timestamp=datetime.utcnow(),
    )

    session.add_message(message)

    assert len(session.messages) == 1
    assert session.messages[0] == message
    assert session.last_activity > session.created_at


def test_context_window_limit():
    """Test that context window limits message history."""
    manager = SessionManager(timeout_seconds=1800)
    session = manager.create_session()

    # Add more messages than context window (default is 10)
    for i in range(15):
        message = ChatMessage(
            message_id=UUID(f"{i:08d}-0000-0000-0000-000000000000"),
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            timestamp=datetime.utcnow(),
        )
        session.add_message(message)

    # Should only keep last 10 messages
    assert len(session.messages) == 10
    # First message should be message 5 (15 - 10 = 5)
    assert "Message 5" in session.messages[0].content
    # Last message should be message 14
    assert "Message 14" in session.messages[-1].content


def test_session_expiration():
    """Test session expiration after timeout."""
    manager = SessionManager(timeout_seconds=1)  # 1 second timeout
    session = manager.create_session()

    # Session should not be expired immediately
    assert not session.is_expired(timeout_seconds=1)

    # Simulate time passing (manually set last_activity to past)
    session.last_activity = datetime.utcnow() - timedelta(seconds=2)

    # Session should now be expired
    assert session.is_expired(timeout_seconds=1)


def test_get_session_expired():
    """Test that expired sessions are not returned."""
    manager = SessionManager(timeout_seconds=1)
    session = manager.create_session()
    session_id = session.session_id

    # Manually expire the session
    session.last_activity = datetime.utcnow() - timedelta(seconds=2)

    # Should not return expired session
    retrieved = manager.get_session(session_id)

    assert retrieved is None
    # Expired session should be removed
    assert session_id not in manager.sessions


def test_cleanup_expired():
    """Test cleanup of expired sessions."""
    manager = SessionManager(timeout_seconds=1)

    # Create multiple sessions
    session1 = manager.create_session()
    session2 = manager.create_session()
    session3 = manager.create_session()

    # Expire two sessions
    session1.last_activity = datetime.utcnow() - timedelta(seconds=2)
    session2.last_activity = datetime.utcnow() - timedelta(seconds=2)
    # session3 remains active

    # Cleanup should remove expired sessions
    removed_count = manager.cleanup_expired()

    assert removed_count == 2
    assert session1.session_id not in manager.sessions
    assert session2.session_id not in manager.sessions
    assert session3.session_id in manager.sessions


def test_multiple_messages_order():
    """Test that messages are added in correct order."""
    manager = SessionManager()
    session = manager.create_session()

    messages = []
    for i in range(5):
        message = ChatMessage(
            message_id=UUID(f"{i:08d}-0000-0000-0000-000000000000"),
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            timestamp=datetime.utcnow(),
        )
        messages.append(message)
        session.add_message(message)

    assert len(session.messages) == 5
    for i, msg in enumerate(session.messages):
        assert msg.content == f"Message {i}"

