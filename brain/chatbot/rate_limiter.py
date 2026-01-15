"""Rate limiting for chatbot queries."""

from datetime import datetime, timedelta, UTC
from collections import defaultdict
from typing import Dict, List

from core.config import settings


class RateLimiter:
    """Sliding window rate limiter for chatbot queries."""

    def __init__(
        self, max_requests: int | None = None, window_seconds: int = 60
    ):
        """Initialize rate limiter."""
        self.max_requests = max_requests or settings.CHATBOT_RATE_LIMIT
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        """Check if a request is allowed for the given user."""
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old requests outside the window
        self.requests[user_id] = [
            req_time
            for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # Check if limit exceeded
        if len(self.requests[user_id]) >= self.max_requests:
            return False

        # Record this request
        self.requests[user_id].append(now)
        return True

    def get_retry_after(self, user_id: str) -> int:
        """Get seconds until the next request is allowed."""
        if not self.requests[user_id]:
            return 0

        # Find oldest request in current window
        oldest = min(self.requests[user_id])
        window_end = oldest + timedelta(seconds=self.window_seconds)
        now = datetime.now(UTC)

        if window_end > now:
            return int((window_end - now).total_seconds())
        return 0

