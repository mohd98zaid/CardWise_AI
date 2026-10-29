import pytest
from pydantic import ValidationError

from app.domain.rules.models import CashbackRateParameters


def test_cap_requires_period() -> None:
    with pytest.raises(ValidationError):
        CashbackRateParameters(
            rate_percent="5",
            cap_amount="500",
            eligible_categories=["online_shopping"],
            eligible_channels=["online_card"],
        )
