"""Unit tests for security-related model validation."""

import pytest
from pydantic import ValidationError

from app.domain.scenarios.models import RegisterRequest


def test_password_too_short_raises_validation_error() -> None:
    """Passwords shorter than 8 characters must be rejected by the model."""
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", password="short")


def test_password_exactly_8_chars_is_valid() -> None:
    """A password of exactly 8 characters must be accepted."""
    req = RegisterRequest(email="user@example.com", password="exactly8")
    assert req.password == "exactly8"


def test_rate_limiter_blocks_excessive_requests() -> None:
    """Rate limiter should trigger HTTP 429 when max requests are exceeded."""
    from unittest.mock import Mock

    from fastapi import HTTPException

    from app.core.ratelimit import rate_limit_auth, reset_rate_limits

    reset_rate_limits()
    mock_request = Mock()
    mock_request.client.host = "192.168.1.100"

    # Make 10 requests (should succeed)
    for _ in range(10):
        rate_limit_auth(mock_request)

    # 11th request should raise 429
    with pytest.raises(HTTPException) as exc_info:
        rate_limit_auth(mock_request)
    assert exc_info.value.status_code == 429
    reset_rate_limits()

