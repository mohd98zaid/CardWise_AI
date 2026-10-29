from datetime import date
from decimal import Decimal

from app.domain.calculator.engine import calculate_points
from app.domain.calculator.models import CalculationInput
from app.domain.rules.models import PointsRule


def points_rule(point_value: str | None = "0.25") -> PointsRule:
    return PointsRule(
        schema_version=1,
        rule_id="synthetic-points-v1",
        card_variant_id="points-variant",
        rule_type="points_rate",
        parameters={
            "points_per_100": "2",
            "point_value": point_value,
            "eligible_categories": ["travel"],
            "eligible_channels": ["online_card"],
        },
        effective_from=date(2026, 1, 1),
        verification_status="draft",
    )


def points_request(point_value: str | None = None) -> CalculationInput:
    return CalculationInput(
        card_variant_id="points-variant",
        amount=Decimal("1000.00"),
        currency="INR",
        scenario_date=date(2026, 1, 15),
        category="travel",
        channel="online_card",
        point_value_per_point=point_value,
    )


def test_points_are_converted_only_with_a_value() -> None:
    result = calculate_points(points_request(), points_rule())

    assert result.status == "estimated"
    assert result.reward_units == Decimal("20.00")
    assert result.estimated_reward == Decimal("5.00")
    assert result.reward_unit == "points"


def test_points_without_valuation_need_input() -> None:
    result = calculate_points(points_request(), points_rule(None))

    assert result.status == "needs_input"
    assert result.reward_units == Decimal("20.00")
    assert result.estimated_net_value is None
