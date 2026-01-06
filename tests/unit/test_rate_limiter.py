"""Unit tests for chatbot rate limiter."""

from datetime import datetime, timedelta
import time

import pytest

from brain.chatbot.rate_limiter import RateLimiter


def test_rate_limiter_allows_requests():
    """Test that rate limiter allows requests within limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    user_id = "test_user"

    # First 5 requests should be allowed
    for i in range(5):
        assert limiter.is_allowed(user_id) is True

    # 6th request should be denied
    assert limiter.is_allowed(user_id) is False


def test_rate_limiter_resets_after_window():
    """Test that rate limiter resets after time window."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)  # 1 second window

    user_id = "test_user"

    # Use up the limit
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is True
    assert limiter.is_allowed(user_id) is False

    # Wait for window to expire
    time.sleep(1.1)

    # Should be allowed again
    assert limiter.is_allowed(user_id) is True


def test_rate_limiter_per_user():
    """Test that rate limiting is per user."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    user1 = "user1"
    user2 = "user2"

    # User1 uses up limit
    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is True
    assert limiter.is_allowed(user1) is False

    # User2 should still be allowed
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is True
    assert limiter.is_allowed(user2) is False


def test_rate_limiter_sliding_window():
    """Test that rate limiter uses sliding window algorithm."""
    limiter = RateLimiter(max_requests=3, window_seconds=2)

    user_id = "test_user"

    # Make 3 requests
    assert limiter.is_allowed(user_id) is True
    time.sleep(0.5)
    assert limiter.is_allowed(user_id) is True
    time.sleep(0.5)
    assert limiter.is_allowed(user_id) is True

    # Should be at limit
    assert limiter.is_allowed(user_id) is False

    # Wait 1 second (oldest request should be outside window)
    time.sleep(1.1)

    # Should be allowed again (oldest request expired)
    assert limiter.is_allowed(user_id) is True


def test_get_retry_after():
    """Test retry_after calculation."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    user_id = "test_user"

    # No requests yet
    assert limiter.get_retry_after(user_id) == 0

    # Make requests
    limiter.is_allowed(user_id)
    time.sleep(0.1)
    limiter.is_allowed(user_id)

    # Should be at limit
    assert limiter.is_allowed(user_id) is False

    # Retry after should be positive (time until oldest request expires)
    retry_after = limiter.get_retry_after(user_id)
    assert retry_after > 0
    assert retry_after <= 60


def test_rate_limiter_default_settings():
    """Test rate limiter with default settings from config."""
    limiter = RateLimiter()

    user_id = "test_user"

    # Should allow requests up to default limit (20)
    for i in range(20):
        assert limiter.is_allowed(user_id) is True

    # 21st should be denied
    assert limiter.is_allowed(user_id) is False

