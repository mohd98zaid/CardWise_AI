from datetime import date
from decimal import Decimal

from app.domain.calculator.engine import calculate_cashback
from app.domain.calculator.models import CalculationInput
from app.services.catalogue import catalogue


def request(**overrides: object) -> CalculationInput:
    values: dict[str, object] = {
        "card_variant_id": "synthetic-variant",
        "amount": "8000.00",
        "currency": "INR",
        "scenario_date": date(2026, 1, 15),
        "category": "online_shopping",
        "channel": "online_card",
        "prior_cap_consumed": "0.00",
        "cap_knowledge_state": "known",
    }
    values.update(overrides)
    return CalculationInput.model_validate(values)


def test_applies_rate_without_exceeding_cap() -> None:
    result = calculate_cashback(request(), catalogue.get_cashback_rule("synthetic-variant"))

    assert result.status == "estimated"
    assert result.gross_reward == Decimal("400.00")
    assert result.estimated_reward == Decimal("400.00")
    assert result.estimated_net_value == Decimal("400.00")
    assert result.manifest_hash
    assert len(result.trace) == 4


def test_cap_boundary_limits_reward() -> None:
    result = calculate_cashback(
        request(amount="20000.00", prior_cap_consumed="450.00"),
        catalogue.get_cashback_rule("synthetic-variant"),
    )

    assert result.gross_reward == Decimal("1000.00")
    assert result.estimated_reward == Decimal("50.00")
    assert result.cap_remaining_before == Decimal("50.00")


def test_unknown_cap_usage_does_not_become_zero() -> None:
    result = calculate_cashback(
        request(prior_cap_consumed=None, cap_knowledge_state="unknown"),
        catalogue.get_cashback_rule("synthetic-variant"),
    )

    assert result.status == "needs_input"
    assert result.estimated_reward is None
    assert result.possible_reward_min == Decimal("0.00")
    assert result.possible_reward_max == Decimal("400.00")
    assert any("unknown" in warning.lower() for warning in result.warnings)


def test_excluded_spend_has_reason() -> None:
    result = calculate_cashback(
        request(category="dining"), catalogue.get_cashback_rule("synthetic-variant")
    )

    assert result.status == "excluded"
    assert result.estimated_reward == Decimal("0.00")
    assert result.exclusion_reason
    assert result.excluded_spend == Decimal("8000.00")
