"""Comprehensive calculation test matrix for the synthetic cashback rule.

Covers 20 cases exercising eligibility, caps, currencies, dates,
rounding, and determinism against the synthetic-cashback-rule fixture.
"""
from datetime import date
from decimal import Decimal

from app.domain.calculator.engine import calculate_cashback
from app.domain.calculator.models import CalculationInput
from app.domain.rules.models import CashbackRateParameters, CashbackRule
from app.services.catalogue import catalogue

# ---------------------------------------------------------------------------
# Shared fixture helpers
# ---------------------------------------------------------------------------

VARIANT_ID = "synthetic-variant"
# effective_from comes from rule-data/fixtures/synthetic-cashback-rule.json
EFFECTIVE_FROM = date(2026, 1, 1)
SCENARIO_IN_RANGE = date(2026, 1, 15)


def _rule() -> CashbackRule:
    """Return the live fixture rule (rate 5%, cap 500, online_shopping/online_card)."""
    rule = catalogue.get_cashback_rule(VARIANT_ID)
    assert rule is not None, "Synthetic rule must be present in catalogue"
    return rule


def _req(**overrides: object) -> CalculationInput:
    """Build a baseline CalculationInput with valid defaults, applying overrides."""
    defaults: dict[str, object] = {
        "card_variant_id": VARIANT_ID,
        "amount": Decimal("8000.00"),
        "currency": "INR",
        "scenario_date": SCENARIO_IN_RANGE,
        "category": "online_shopping",
        "channel": "online_card",
        "prior_cap_consumed": Decimal("0.00"),
        "cap_knowledge_state": "known",
    }
    defaults.update(overrides)
    return CalculationInput.model_validate(defaults)


def _modified_rule(**overrides: object) -> CashbackRule:
    """Clone the fixture rule with field overrides for edge-case testing."""
    base = _rule().model_dump()
    base.update(overrides)
    return CashbackRule.model_validate(base)


# ---------------------------------------------------------------------------
# Case 1 – Positive cashback, cap not reached
# ---------------------------------------------------------------------------

def test_case01_positive_cashback_gross_reward() -> None:
    """INR 8000 at 5%, cap not touched → gross and estimated reward = 400.00."""
    result = calculate_cashback(_req(), _rule())
    assert result.status == "estimated"
    assert result.gross_reward == Decimal("400.00")
    assert result.estimated_reward == Decimal("400.00")


# ---------------------------------------------------------------------------
# Case 2 – Zero reward for tiny eligible spend
# ---------------------------------------------------------------------------

def test_case02_tiny_eligible_spend_near_zero() -> None:
    """INR 0.01 at 5% → reward rounds to 0.00, status estimated."""
    result = calculate_cashback(_req(amount=Decimal("0.01")), _rule())
    assert result.status == "estimated"
    assert result.estimated_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 3 – Ineligible transaction category
# ---------------------------------------------------------------------------

def test_case03_ineligible_category_excluded() -> None:
    """dining category is not in eligible_categories → excluded status."""
    result = calculate_cashback(_req(category="dining"), _rule())
    assert result.status == "excluded"
    assert result.estimated_reward == Decimal("0.00")
    assert result.excluded_spend == Decimal("8000.00")


# ---------------------------------------------------------------------------
# Case 4 – Zero rate gives zero reward
# ---------------------------------------------------------------------------

def test_case04_zero_rate_gives_zero_reward() -> None:
    """A rule with rate_percent=0 should produce 0 reward for any eligible spend."""
    zero_rate_rule = CashbackRule(
        schema_version=1,
        rule_id="zero-rate-rule",
        card_variant_id=VARIANT_ID,
        rule_type="cashback_rate",
        parameters=CashbackRateParameters(
            rate_percent=Decimal("0"),
            cap_amount=None,
            cap_period=None,
            eligible_categories=["online_shopping"],
            eligible_channels=["online_card"],
        ),
        effective_from=EFFECTIVE_FROM,
        effective_to=None,
        verification_status="draft",
    )
    result = calculate_cashback(_req(), zero_rate_rule)
    assert result.status == "estimated"
    assert result.estimated_reward == Decimal("0.00")
    assert result.gross_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 5 – Monthly cap not reached
# ---------------------------------------------------------------------------

def test_case05_cap_not_reached() -> None:
    """INR 1000, no prior consumption → 5% = 50.00, well under 500 cap."""
    result = calculate_cashback(
        _req(amount=Decimal("1000.00"), prior_cap_consumed=Decimal("0.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.estimated_reward == Decimal("50.00")


# ---------------------------------------------------------------------------
# Case 6 – Monthly cap exactly reached (1 unit under, small transaction)
# ---------------------------------------------------------------------------

def test_case06_cap_almost_exhausted_caps_reward() -> None:
    """cap_consumed=499, spend=INR 20 → gross 1.00, cap remaining 1.00 → reward 1.00."""
    result = calculate_cashback(
        _req(amount=Decimal("20.00"), prior_cap_consumed=Decimal("499.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.gross_reward == Decimal("1.00")
    assert result.cap_remaining_before == Decimal("1.00")
    assert result.estimated_reward == Decimal("1.00")


# ---------------------------------------------------------------------------
# Case 7 – Monthly cap exceeded (prior_consumed > cap, large tx)
# ---------------------------------------------------------------------------

def test_case07_cap_exceeded_reward_zero() -> None:
    """cap_consumed=500 (= cap), INR 1000 → no remaining → reward 0."""
    result = calculate_cashback(
        _req(amount=Decimal("1000.00"), prior_cap_consumed=Decimal("500.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.estimated_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 8 – Cap already exhausted (prior == cap_amount)
# ---------------------------------------------------------------------------

def test_case08_cap_already_exhausted() -> None:
    """When prior_cap_consumed equals cap_amount, reward must be 0.00."""
    result = calculate_cashback(
        _req(prior_cap_consumed=Decimal("500.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.cap_remaining_before == Decimal("0.00")
    assert result.estimated_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 9 – Partial cap availability
# ---------------------------------------------------------------------------

def test_case09_partial_cap_availability() -> None:
    """cap_consumed=450, INR 8000 (gross 400) → capped to remaining 50.00."""
    result = calculate_cashback(
        _req(amount=Decimal("8000.00"), prior_cap_consumed=Decimal("450.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.cap_remaining_before == Decimal("50.00")
    assert result.estimated_reward == Decimal("50.00")


# ---------------------------------------------------------------------------
# Case 10 – Unknown cap usage → needs_input
# ---------------------------------------------------------------------------

def test_case10_unknown_cap_usage_needs_input() -> None:
    """Unknown cap → status needs_input, estimated_reward None, min=0 max>0."""
    result = calculate_cashback(
        _req(prior_cap_consumed=None, cap_knowledge_state="unknown"),
        _rule(),
    )
    assert result.status == "needs_input"
    assert result.estimated_reward is None
    assert result.possible_reward_min == Decimal("0.00")
    assert result.possible_reward_max is not None
    assert result.possible_reward_max > Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 11 – Minimum transaction amount (INR 0)
# ---------------------------------------------------------------------------

def test_case11_zero_amount_zero_reward() -> None:
    """INR 0 spend → eligible_spend 0, reward 0."""
    result = calculate_cashback(
        _req(amount=Decimal("0.00"), prior_cap_consumed=Decimal("0.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.eligible_spend == Decimal("0.00")
    assert result.estimated_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 12 – Unsupported payment channel
# ---------------------------------------------------------------------------

def test_case12_unsupported_channel_excluded() -> None:
    """online_shopping but channel=upi → excluded (not in eligible_channels)."""
    result = calculate_cashback(_req(channel="upi"), _rule())
    assert result.status == "excluded"
    assert result.excluded_spend == Decimal("8000.00")


# ---------------------------------------------------------------------------
# Case 13 – Both category and channel excluded
# ---------------------------------------------------------------------------

def test_case13_excluded_category_and_channel() -> None:
    """dining + upi (both ineligible) → excluded."""
    result = calculate_cashback(_req(category="dining", channel="upi"), _rule())
    assert result.status == "excluded"
    assert result.estimated_reward == Decimal("0.00")


# ---------------------------------------------------------------------------
# Case 14 – Rounding boundary (INR 1 → 0.05)
# ---------------------------------------------------------------------------

def test_case14_rounding_boundary_one_rupee() -> None:
    """INR 1 * 5% = 0.05 → should round to exactly 0.05."""
    result = calculate_cashback(
        _req(amount=Decimal("1.00"), prior_cap_consumed=Decimal("0.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.estimated_reward == Decimal("0.05")


# ---------------------------------------------------------------------------
# Case 15 – Rule not yet effective
# ---------------------------------------------------------------------------

def test_case15_rule_not_yet_effective() -> None:
    """scenario_date before effective_from → cannot_calculate."""
    result = calculate_cashback(
        _req(scenario_date=date(2025, 12, 31)),
        _rule(),
    )
    assert result.status == "cannot_calculate"
    assert any("active rule" in w.lower() or "date" in w.lower() for w in result.warnings)


# ---------------------------------------------------------------------------
# Case 16 – Expired rule (effective_to in the past)
# ---------------------------------------------------------------------------

def test_case16_expired_rule() -> None:
    """Rule with effective_to=2026-01-10 and scenario_date=2026-01-15 → cannot_calculate."""
    expired_rule = _modified_rule(effective_to=date(2026, 1, 10))
    result = calculate_cashback(_req(scenario_date=date(2026, 1, 15)), expired_rule)
    assert result.status == "cannot_calculate"


# ---------------------------------------------------------------------------
# Case 17 – Wrong currency
# ---------------------------------------------------------------------------

def test_case17_wrong_currency_cannot_calculate() -> None:
    """Non-INR currency → cannot_calculate."""
    result = calculate_cashback(_req(currency="USD"), _rule())
    assert result.status == "cannot_calculate"


# ---------------------------------------------------------------------------
# Case 18 – Wrong card_variant_id
# ---------------------------------------------------------------------------

def test_case18_wrong_variant_id_cannot_calculate() -> None:
    """Mismatched card_variant_id → cannot_calculate."""
    result = calculate_cashback(_req(card_variant_id="wrong-variant"), _rule())
    assert result.status == "cannot_calculate"


# ---------------------------------------------------------------------------
# Case 19 – Large amount well above cap
# ---------------------------------------------------------------------------

def test_case19_large_amount_capped_at_cap_amount() -> None:
    """INR 100000 at 5% = 5000 gross, but cap is 500 → reward = 500.00."""
    result = calculate_cashback(
        _req(amount=Decimal("100000.00"), prior_cap_consumed=Decimal("0.00")),
        _rule(),
    )
    assert result.status == "estimated"
    assert result.gross_reward == Decimal("5000.00")
    assert result.estimated_reward == Decimal("500.00")


# ---------------------------------------------------------------------------
# Case 20 – Same inputs are deterministic (manifest_hash stable)
# ---------------------------------------------------------------------------

def test_case20_same_inputs_deterministic() -> None:
    """Running calculate_cashback twice with identical inputs yields identical results."""
    req = _req()
    rule = _rule()
    result_a = calculate_cashback(req, rule)
    result_b = calculate_cashback(req, rule)
    assert result_a.manifest_hash == result_b.manifest_hash
    assert result_a.estimated_reward == result_b.estimated_reward
    assert result_a.status == result_b.status
