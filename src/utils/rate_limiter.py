"""Rate limiter for webhook requests."""

import time
import asyncio
from collections import deque


class RateLimiter:
    """Rate limiter using sliding window algorithm."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds (default 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()  # Store timestamps
        self._lock = asyncio.Lock()

    async def is_allowed(self) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
            - is_allowed: True if request allowed, False otherwise
            - retry_after_seconds: Seconds to wait before next request
        """
        if self.max_requests <= 0:
            return True, 0

        current_time = time.time()

        async with self._lock:
            # Remove timestamps outside the window
            while (
                self.requests and self.requests[0] < current_time - self.window_seconds
            ):
                self.requests.popleft()

            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(current_time)
                return True, 0
            else:
                # Calculate retry time
                oldest_request = self.requests[0]
                retry_after = int(oldest_request + self.window_seconds - current_time)
                return False, max(retry_after, 1)

    def get_usage(self) -> tuple[int, int]:
        """
        Get current rate limit usage.

        Returns:
            Tuple of (current_requests, max_requests)
        """
        current_time = time.time()

        # Remove timestamps outside the window
        while self.requests and self.requests[0] < current_time - self.window_seconds:
            self.requests.popleft()

        return len(self.requests), self.max_requests
