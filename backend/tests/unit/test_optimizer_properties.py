"""Property and invariant tests for the portfolio optimizer."""

from datetime import date
from decimal import Decimal

from app.domain.optimizer import choose_best_cards
from app.domain.rules.models import CashbackRateParameters, CashbackRule
from app.services.catalogue import catalogue


def make_rule(variant_id: str, rate: Decimal, cap: Decimal = Decimal("500.00")) -> CashbackRule:
    return CashbackRule(
        schema_version=1,
        rule_id=f"rule-{variant_id}",
        card_variant_id=variant_id,
        rule_type="cashback_rate",
        parameters=CashbackRateParameters(
            rate_percent=rate,
            cap_amount=cap,
            cap_period="calendar_month",
            eligible_categories=["online_shopping"],
            eligible_channels=["online_card"],
        ),
        effective_from=date(2024, 1, 1),
        verification_status="draft",
        evidence_ids=[],
        notes="test rule",
    )


def test_optimizer_preserves_total_spend() -> None:
    spend = [
        {
            "amount": Decimal("5000.00"),
            "category": "online_shopping",
            "channel": "online_card",
            "scenario_date": date(2026, 1, 15),
            "cap_usage": Decimal("0.00"),
            "cap_state": "known",
        },
        {
            "amount": Decimal("3000.00"),
            "category": "online_shopping",
            "channel": "online_card",
            "scenario_date": date(2026, 1, 15),
            "cap_usage": Decimal("0.00"),
            "cap_state": "known",
        },
    ]
    cards = [("synthetic-variant", catalogue.get_cashback_rule("synthetic-variant"))]
    result = choose_best_cards(spend, cards)

    assert result["total_spend_preserved"] is True
    assert result["planned_spend"] == "8000.00"
    assert result["allocated_spend"] == "8000.00"
    assert len(result["allocations"]) == 2


def test_optimizer_warns_about_shared_caps() -> None:
    spend = [
        {
            "amount": Decimal("1000.00"),
            "category": "online_shopping",
            "channel": "online_card",
            "scenario_date": date(2026, 1, 15),
            "cap_usage": Decimal("0.00"),
            "cap_state": "known",
        }
    ]
    cards = [("synthetic-variant", catalogue.get_cashback_rule("synthetic-variant"))]
    result = choose_best_cards(spend, cards)

    assert any("shared" in w.lower() for w in result["warnings"])


def test_optimizer_identifies_excluded_spend() -> None:
    spend = [
        {
            "amount": Decimal("2000.00"),
            "category": "dining",  # not covered by synthetic rule
            "channel": "in_store_card",
            "scenario_date": date(2026, 1, 15),
            "cap_usage": Decimal("0.00"),
            "cap_state": "known",
        }
    ]
    cards = [("synthetic-variant", catalogue.get_cashback_rule("synthetic-variant"))]
    result = choose_best_cards(spend, cards)

    assert len(result["excluded"]) == 1
    assert result["excluded"][0]["category"] == "dining"
    assert result["total_spend_preserved"] is False


def test_adding_dominated_card_does_not_improve_objective() -> None:
    spend = [
        {
            "amount": Decimal("5000.00"),
            "category": "online_shopping",
            "channel": "online_card",
            "scenario_date": date(2026, 1, 15),
            "cap_usage": Decimal("0.00"),
            "cap_state": "known",
        }
    ]
    best_card = ("card-5pct", make_rule("card-5pct", Decimal("5.00")))
    dominated_card = ("card-2pct", make_rule("card-2pct", Decimal("2.00")))

    result_single = choose_best_cards(spend, [best_card])
    result_with_dominated = choose_best_cards(spend, [best_card, dominated_card])

    assert result_with_dominated["proposed_value"] == result_single["proposed_value"]
