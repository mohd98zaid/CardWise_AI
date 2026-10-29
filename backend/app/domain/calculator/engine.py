import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal

from app.domain.calculator.models import CalculationInput, CalculationResult, TraceStep
from app.domain.rules.models import CashbackRule, PointsRule

ENGINE_VERSION = "calculator-0.1.0"
MONEY_QUANTUM = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def _manifest_hash(rule: CashbackRule | PointsRule) -> str:
    payload = json.dumps(rule.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _stringify(values: dict[str, Decimal | str | None]) -> dict[str, str | None]:
    return {key: None if value is None else str(value) for key, value in values.items()}


def _step(
    sequence: int,
    step_type: str,
    reason: str,
    input_values: dict[str, Decimal | str | None],
    output_values: dict[str, Decimal | str | None],
    rule: CashbackRule,
) -> TraceStep:
    return TraceStep(
        sequence=sequence,
        step_type=step_type,
        reason=reason,
        input=_stringify(input_values),
        output=_stringify(output_values),
        rule_id=rule.rule_id,
        evidence_ids=rule.evidence_ids,
    )


def calculate_cashback(request: CalculationInput, rule: CashbackRule) -> CalculationResult:
    """Evaluate one typed cashback rule without I/O or floating-point arithmetic."""
    manifest_hash = _manifest_hash(rule)
    params = rule.parameters
    trace: list[TraceStep] = []
    warnings: list[str] = []

    if request.card_variant_id != rule.card_variant_id:
        trace.append(
            _step(
                1,
                "variant_resolution",
                "The requested card variant does not match the rule variant.",
                {"requested_variant": request.card_variant_id},
                {"rule_variant": rule.card_variant_id},
                rule,
            )
        )
        return _base_result(request, "cannot_calculate", trace, warnings, rule, manifest_hash)

    if request.currency != "INR":
        warnings.append("Only INR is supported by this synthetic fixture.")
        trace.append(
            _step(
                1,
                "currency_validation",
                "Unsupported currency.",
                {"currency": request.currency},
                {},
                rule,
            )
        )
        return _base_result(request, "cannot_calculate", trace, warnings, rule, manifest_hash)

    if not rule.applies_on(request.scenario_date):
        warnings.append("No active rule covers the requested scenario date.")
        trace.append(
            _step(
                1,
                "effective_date",
                "The rule is outside its effective date range.",
                {"scenario_date": request.scenario_date.isoformat()},
                {
                    "effective_from": rule.effective_from.isoformat(),
                    "effective_to": rule.effective_to,
                },
                rule,
            )
        )
        return _base_result(request, "cannot_calculate", trace, warnings, rule, manifest_hash)

    eligible = (
        request.category in params.eligible_categories
        and request.channel in params.eligible_channels
    )
    trace.append(
        _step(
            1,
            "eligibility",
            "Category and channel are eligible."
            if eligible
            else "Category or channel is excluded.",
            {"category": request.category, "channel": request.channel, "amount": request.amount},
            {
                "eligible": str(eligible),
                "eligible_spend": request.amount if eligible else Decimal("0"),
            },
            rule,
        )
    )
    if not eligible:
        return CalculationResult(
            status="excluded",
            card_variant_id=request.card_variant_id,
            eligible_spend=Decimal("0.00"),
            excluded_spend=_money(request.amount),
            exclusion_reason=(
                "This synthetic rule does not cover the selected category and channel."
            ),
            estimated_reward=Decimal("0.00"),
            estimated_net_value=Decimal("0.00"),
            currency=request.currency,
            verification_status=rule.verification_status,
            warnings=["This is a synthetic fixture, not a verified issuer term."],
            evidence_ids=rule.evidence_ids,
            trace=trace,
            engine_version=ENGINE_VERSION,
            manifest_hash=manifest_hash,
        )

    eligible_spend = _money(request.amount)
    gross_reward = _money(eligible_spend * params.rate_percent / Decimal("100"))
    trace.append(
        _step(
            2,
            "earn_rate",
            "Applied the typed percentage rate to eligible spend.",
            {"eligible_spend": eligible_spend, "rate_percent": params.rate_percent},
            {"gross_reward": gross_reward},
            rule,
        )
    )

    if params.cap_amount is None:
        trace.append(
            _step(3, "cap", "No cap is defined by this rule.", {}, {"reward": gross_reward}, rule)
        )
        return _finalize(
            request,
            rule,
            trace,
            warnings,
            "estimated",
            gross_reward,
            None,
            None,
            None,
            manifest_hash,
        )

    cap = _money(params.cap_amount)
    if request.cap_knowledge_state == "unknown" or request.prior_cap_consumed is None:
        possible_max = min(gross_reward, cap)
        warnings.append("Prior cap usage is unknown; the result is shown as a range.")
        trace.append(
            _step(
                3,
                "cap",
                "Prior cap usage is unknown, so no single capped reward is claimed.",
                {"cap_amount": cap, "prior_cap_consumed": None},
                {"possible_reward_min": Decimal("0"), "possible_reward_max": possible_max},
                rule,
            )
        )
        return _finalize(
            request,
            rule,
            trace,
            warnings,
            "needs_input",
            None,
            cap,
            None,
            None,
            manifest_hash,
            possible_reward_min=Decimal("0.00"),
            possible_reward_max=possible_max,
        )

    consumed = _money(request.prior_cap_consumed)
    if consumed > cap:
        warnings.append(
            "Prior cap usage exceeds the rule cap; no reward remains under this assumption."
        )
    remaining = max(Decimal("0.00"), cap - consumed)
    estimated_reward = min(gross_reward, remaining)
    trace.append(
        _step(
            3,
            "cap",
            "Applied the remaining calendar-month cap.",
            {"cap_amount": cap, "prior_cap_consumed": consumed, "gross_reward": gross_reward},
            {"remaining_cap": remaining, "estimated_reward": estimated_reward},
            rule,
        )
    )
    return _finalize(
        request,
        rule,
        trace,
        warnings,
        "estimated",
        estimated_reward,
        cap,
        consumed,
        remaining,
        manifest_hash,
    )


def calculate_points(request: CalculationInput, rule: PointsRule) -> CalculationResult:
    manifest_hash = _manifest_hash(rule)
    params = rule.parameters
    trace: list[TraceStep] = []
    if request.card_variant_id != rule.card_variant_id or not rule.applies_on(
        request.scenario_date
    ):
        return _base_result(
            request,
            "cannot_calculate",
            trace,
            ["No points rule covers this card and date."],
            rule,
            manifest_hash,
        )
    eligible = (
        request.category in params.eligible_categories
        and request.channel in params.eligible_channels
    )
    trace.append(
        _step(
            1,
            "eligibility",
            "Points category and channel are eligible."
            if eligible
            else "Category or channel is excluded.",
            {"category": request.category, "channel": request.channel, "amount": request.amount},
            {"eligible": str(eligible)},
            rule,
        )
    )
    if not eligible:
        return CalculationResult(
            status="excluded",
            card_variant_id=request.card_variant_id,
            eligible_spend=Decimal("0.00"),
            excluded_spend=_money(request.amount),
            exclusion_reason="This points rule does not cover the selected category and channel.",
            estimated_reward=Decimal("0.00"),
            estimated_net_value=Decimal("0.00"),
            currency=request.currency,
            verification_status=rule.verification_status,
            reward_unit="points",
            warnings=[
                "Point value is an assumption and must be supplied to calculate currency value."
            ],
            evidence_ids=rule.evidence_ids,
            trace=trace,
            engine_version=ENGINE_VERSION,
            manifest_hash=manifest_hash,
        )
    units = _money(request.amount * params.points_per_100 / Decimal("100"))
    point_value = request.point_value_per_point or params.point_value
    trace.append(
        _step(
            2,
            "points_rate",
            "Applied points per ₹100 to eligible spend.",
            {"eligible_spend": request.amount, "points_per_100": params.points_per_100},
            {"reward_units": units, "point_value": point_value},
            rule,
        )
    )
    if point_value is None:
        return CalculationResult(
            status="needs_input",
            card_variant_id=request.card_variant_id,
            eligible_spend=_money(request.amount),
            excluded_spend=Decimal("0.00"),
            gross_reward=units,
            reward_units=units,
            reward_unit="points",
            point_value_per_unit=None,
            estimated_reward=None,
            estimated_net_value=None,
            currency=request.currency,
            verification_status=rule.verification_status,
            warnings=[
                "Point value is unknown; supply a valuation assumption to calculate currency value."
            ],
            evidence_ids=rule.evidence_ids,
            trace=trace,
            engine_version=ENGINE_VERSION,
            manifest_hash=manifest_hash,
        )
    value = _money(units * point_value)
    trace.append(
        _step(
            3,
            "point_conversion",
            "Converted points using the selected valuation assumption.",
            {"points": units, "point_value": point_value},
            {"value": value},
            rule,
        )
    )
    return CalculationResult(
        status="estimated",
        card_variant_id=request.card_variant_id,
        eligible_spend=_money(request.amount),
        excluded_spend=Decimal("0.00"),
        gross_reward=units,
        reward_units=units,
        reward_unit="points",
        point_value_per_unit=point_value,
        estimated_reward=value,
        estimated_net_value=value,
        currency=request.currency,
        verification_status=rule.verification_status,
        warnings=["Point value is an assumption, not a guaranteed redemption value."],
        evidence_ids=rule.evidence_ids,
        trace=trace,
        engine_version=ENGINE_VERSION,
        manifest_hash=manifest_hash,
    )


def calculate_reward(
    request: CalculationInput,
    rule: CashbackRule | PointsRule,
) -> CalculationResult:
    if isinstance(rule, PointsRule):
        return calculate_points(request, rule)
    return calculate_cashback(request, rule)


def _base_result(
    request: CalculationInput,
    status: str,
    trace: list[TraceStep],
    warnings: list[str],
    rule: CashbackRule,
    manifest_hash: str,
) -> CalculationResult:
    return CalculationResult(
        status=status,  # type: ignore[arg-type]
        card_variant_id=request.card_variant_id,
        eligible_spend=Decimal("0.00"),
        excluded_spend=Decimal("0.00"),
        currency=request.currency,
        verification_status=rule.verification_status,
        warnings=warnings + ["This is a synthetic fixture, not a verified issuer term."],
        evidence_ids=rule.evidence_ids,
        trace=trace,
        engine_version=ENGINE_VERSION,
        manifest_hash=manifest_hash,
    )


def _finalize(
    request: CalculationInput,
    rule: CashbackRule,
    trace: list[TraceStep],
    warnings: list[str],
    status: str,
    estimated_reward: Decimal | None,
    cap_amount: Decimal | None,
    cap_consumed: Decimal | None,
    cap_remaining: Decimal | None,
    manifest_hash: str,
    *,
    possible_reward_min: Decimal | None = None,
    possible_reward_max: Decimal | None = None,
) -> CalculationResult:
    if estimated_reward is not None:
        trace.append(
            _step(
                len(trace) + 1,
                "rounding_and_net_value",
                (
                    "No fee is allocated in this synthetic fixture; reward value equals "
                    "estimated net value."
                ),
                {"estimated_reward": estimated_reward, "fee": Decimal("0.00")},
                {"estimated_net_value": estimated_reward},
                rule,
            )
        )
    else:
        trace.append(
            _step(
                len(trace) + 1,
                "rounding_and_net_value",
                "Net value remains unknown while prior cap usage is unknown.",
                {"estimated_reward": None, "fee": Decimal("0.00")},
                {"estimated_net_value": None},
                rule,
            )
        )
    return CalculationResult(
        status=status,  # type: ignore[arg-type]
        card_variant_id=request.card_variant_id,
        eligible_spend=_money(request.amount),
        excluded_spend=Decimal("0.00"),
        gross_reward=_money(request.amount * rule.parameters.rate_percent / Decimal("100")),
        cap_amount=cap_amount,
        cap_consumed_before=cap_consumed,
        cap_remaining_before=cap_remaining,
        estimated_reward=estimated_reward,
        possible_reward_min=possible_reward_min,
        possible_reward_max=possible_reward_max,
        estimated_net_value=estimated_reward,
        currency=request.currency,
        verification_status=rule.verification_status,
        warnings=warnings + ["This is a synthetic fixture, not a verified issuer term."],
        evidence_ids=rule.evidence_ids,
        trace=trace,
        engine_version=ENGINE_VERSION,
        manifest_hash=manifest_hash,
    )
