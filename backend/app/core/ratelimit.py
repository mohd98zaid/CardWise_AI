"""In-memory sliding-window rate limiter with trusted proxy support.

NOTE: This limiter runs in-process memory. For production deployments with
multiple worker processes or replicas, enforce a single-worker process or
transition to a centralized Redis-backed token bucket store.
"""

import logging
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.core.config import settings

_WINDOW_SECONDS = 60
_logger = logging.getLogger("cardwise.ratelimit")

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


def get_client_ip(request: Request) -> str:
    """Resolve the client IP, honoring X-Forwarded-For only from trusted proxies."""
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip in settings.trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip
    return direct_ip


def rate_limit_auth(request: Request) -> None:
    """FastAPI dependency: enforce max requests per 60 s per client IP."""
    max_requests = settings.auth_rate_limit
    if max_requests <= 0:
        if settings.app_env == "production":
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "CONFIG_ERROR",
                    "message": "Rate limiter misconfigured in production.",
                },
            )
        return

    ip = get_client_ip(request)
    now = time.monotonic()
    with _lock:
        _cleanup(ip, now)
        count = len(_request_log.get(ip, []))
        if count >= max_requests:
            _logger.warning("auth_rate_limit_exceeded ip=%s count=%d", ip, count)
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please wait a moment.",
                    "retryable": True,
                },
            )
        _request_log[ip].append(now)
