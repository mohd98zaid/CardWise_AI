"""Simple in-memory sliding-window rate limiter for single-process dev server."""

import os
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 60
_MAX_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT", "10"))

# Each key maps to a list of timestamps (float) within the current window.
_request_log: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()


def reset_rate_limits() -> None:
    """Clear rate limiting state. Useful for test suites."""
    with _lock:
        _request_log.clear()


def _cleanup(ip: str, now: float) -> None:
    """Remove timestamps older than the window. Must be called with _lock held."""
    cutoff = now - _WINDOW_SECONDS
    _request_log[ip] = [t for t in _request_log[ip] if t > cutoff]
    if not _request_log[ip]:
        del _request_log[ip]


def rate_limit_auth(request: Request) -> None:
    """FastAPI dependency: enforce max requests per 60 s per client IP."""
    if _MAX_REQUESTS <= 0:
        return
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _lock:
        _cleanup(ip, now)
        count = len(_request_log.get(ip, []))
        if count >= _MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please wait a moment.",
                    "retryable": True,
                },
            )
        _request_log[ip].append(now)

