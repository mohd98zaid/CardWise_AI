"""Deterministic portfolio optimizer with shared reward cap tracking."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from itertools import product
from typing import Any

from app.domain.rules.models import CashbackRule, PointsRule

OPTIMIZER_VERSION = "shared-cap-branch-bound-0.2.0"
MONEY_QUANTUM = Decimal("0.01")


def _money(val: Decimal) -> Decimal:
    return val.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class CardSpec:
    card_id: str
    rule: CashbackRule | PointsRule
    cap_amount: Decimal | None
    initial_consumed: Decimal
    is_cap_known: bool


@dataclass
class BucketEval:
    index: int
    amount: Decimal
    category: str
    channel: str
    scenario_date: Any
    baseline_card_id: str | None
    is_fixed: bool
    point_value: Decimal | None
    eligible_cards: list[str]
    gross_by_card: dict[str, Decimal]


def _card_gross_reward(
    amount: Decimal,
    category: str,
    channel: str,
    rule: CashbackRule | PointsRule,
    point_value_override: Decimal | None,
) -> Decimal | None:
    """Return gross reward for a bucket on a card if eligible, else None."""
    params = rule.parameters
    if category not in params.eligible_categories or channel not in params.eligible_channels:
        return None

    if isinstance(rule, CashbackRule):
        return amount * params.rate_percent / Decimal("100")
    elif isinstance(rule, PointsRule):
        points = amount * params.points_per_100 / Decimal("100")
        pval = point_value_override or params.point_value
        if pval is None:
            # Cannot calculate authoritative value without valuation assumption
            return None
        return points * pval
    return None


COMBINATION_LIMIT: int = 100_000


def choose_best_cards(
    spend: list[dict[str, object]],
    cards: list[tuple[str, CashbackRule | PointsRule]],
) -> dict[str, object]:
    """Optimize spending allocations across owned cards, enforcing shared caps."""
    warnings: list[str] = [
        "CardWise optimizer enforces shared monthly caps across all spend allocated to each card.",
        "Annual and joining fees are not modeled in monthly allocation optimizations.",
    ]

    card_specs: dict[str, CardSpec] = {}
    for card_id, rule in cards:
        cap_amt: Decimal | None = None
        if isinstance(rule, CashbackRule) and rule.parameters.cap_amount is not None:
            cap_amt = rule.parameters.cap_amount

        # Check if prior cap usage is specified in spend buckets
        known_consumed = Decimal("0.00")
        is_cap_known = True
        for b in spend:
            if b.get("baseline_card") == card_id or len(cards) == 1:
                if b.get("cap_state") == "unknown":
                    is_cap_known = False
                elif b.get("cap_usage") is not None:
                    usage = Decimal(str(b["cap_usage"]))
                    if usage > known_consumed:
                        known_consumed = usage

        if cap_amt is not None and not is_cap_known:
            warnings.append(
                f"Card '{card_id}' has a reward cap, but prior cap usage is unknown. "
                "Optimization calculates both upper-bound and conservative bounds."
            )

        card_specs[card_id] = CardSpec(
            card_id=card_id,
            rule=rule,
            cap_amount=cap_amt,
            initial_consumed=known_consumed,
            is_cap_known=is_cap_known,
        )

    total_planned = Decimal("0.00")
    buckets: list[BucketEval] = []
    excluded: list[dict[str, str]] = []

    for idx, b in enumerate(spend):
        amt = Decimal(str(b["amount"]))
        total_planned += amt
        cat = str(b["category"])
        chan = str(b["channel"])
        s_date = b.get("scenario_date")
        b_card = str(b.get("baseline_card") or "") or None
        is_fixed = bool(b.get("is_fixed", False))
        pval = Decimal(str(b["point_value_per_point"])) if b.get("point_value_per_point") else None

        eligible_cards: list[str] = []
        gross_map: dict[str, Decimal] = {}

        for card_id, rule in cards:
            gross = _card_gross_reward(amt, cat, chan, rule, pval)
            if gross is not None:
                eligible_cards.append(card_id)
                gross_map[card_id] = gross

        if not eligible_cards:
            excluded.append(
                {
                    "category": cat,
                    "channel": chan,
                    "amount": str(amt),
                    "reason": "No candidate card is eligible for this category and channel.",
                }
            )
            continue

        if is_fixed:
            if not b_card:
                excluded.append(
                    {
                        "category": cat,
                        "channel": chan,
                        "amount": str(amt),
                        "reason": "Fixed spending bucket requires an assigned baseline card.",
                    }
                )
                continue
            if b_card not in eligible_cards:
                excluded.append(
                    {
                        "category": cat,
                        "channel": chan,
                        "amount": str(amt),
                        "reason": (
                            f"Fixed card '{b_card}' is not eligible for this category/channel."
                        ),
                    }
                )
                continue
            eligible_cards = [b_card]

        buckets.append(
            BucketEval(
                index=idx,
                amount=amt,
                category=cat,
                channel=chan,
                scenario_date=s_date,
                baseline_card_id=b_card,
                is_fixed=is_fixed,
                point_value=pval,
                eligible_cards=eligible_cards,
                gross_by_card=gross_map,
            )
        )

    # If no bucket can be allocated
    if not buckets:
        return {
            "method_version": OPTIMIZER_VERSION,
            "plan_status": "infeasible",
            "search_mode": "exhaustive",
            "is_heuristic": False,
            "baseline_value": "0.00",
            "proposed_value": "0.00",
            "incremental_value": "0.00",
            "has_cap_uncertainty": False,
            "conservative_proposed_value": "0.00",
            "conservative_incremental_value": "0.00",
            "total_spend_preserved": False,
            "planned_spend": str(total_planned),
            "allocated_spend": "0.00",
            "allocations": [],
            "excluded": excluded,
            "warnings": warnings + ["No spending could be feasibly allocated."],
        }

    # Helper to compute total reward under shared caps given an assignment of buckets -> cards
    def evaluate_assignment(
        assignment: tuple[str, ...],
        *,
        conservative: bool = False,
    ) -> tuple[Decimal, dict[str, Decimal]]:
        card_gross: dict[str, Decimal] = {cid: Decimal("0.00") for cid in card_specs}
        for b_eval, card_id in zip(buckets, assignment, strict=True):
            card_gross[card_id] += b_eval.gross_by_card[card_id]

        total_reward = Decimal("0.00")
        card_rewards: dict[str, Decimal] = {}
        for cid, gross in card_gross.items():
            spec = card_specs[cid]
            if spec.cap_amount is not None:
                if conservative and not spec.is_cap_known:
                    cap_rem = Decimal("0.00")
                else:
                    cap_rem = max(Decimal("0.00"), spec.cap_amount - spec.initial_consumed)
                reward = min(gross, cap_rem)
            else:
                reward = gross
            reward_rounded = _money(reward)
            card_rewards[cid] = reward_rounded
            total_reward += reward_rounded
        return total_reward, card_rewards

    # 1. Evaluate baseline allocation
    baseline_assignment_list: list[str] = []
    for b in buckets:
        if b.baseline_card_id and b.baseline_card_id in b.eligible_cards:
            baseline_assignment_list.append(b.baseline_card_id)
        elif b.eligible_cards:
            baseline_assignment_list.append(b.eligible_cards[0])
        else:
            baseline_assignment_list.append(cards[0][0])
    baseline_assignment = tuple(baseline_assignment_list)
    baseline_total, _ = evaluate_assignment(baseline_assignment)

    # 2. Find optimal assignment across eligible cards
    # For small problems (cartesian product <= 100,000), search exhaustively
    possible_choices = [b.eligible_cards for b in buckets]
    total_combinations = 1
    for choices in possible_choices:
        total_combinations *= len(choices)

    best_assignment: tuple[str, ...] = baseline_assignment
    best_value: Decimal = Decimal("-1.00")
    search_mode: str = "exhaustive"
    is_heuristic: bool = False

    if total_combinations <= COMBINATION_LIMIT:
        for candidate in product(*possible_choices):
            val, _ = evaluate_assignment(candidate)
            if val > best_value:
                best_value = val
                best_assignment = candidate
    else:
        search_mode = "greedy_heuristic"
        is_heuristic = True
        warnings.append(
            f"Search space exceeded {COMBINATION_LIMIT:,} combinations ({total_combinations:,}); "
            "evaluated using greedy marginal heuristic. This allocation is an approximation "
            "and is not proven globally optimal."
        )
        # Greedy heuristic for larger problems: sort buckets by amount desc,
        # assign to card with highest marginal reward
        current_gross: dict[str, Decimal] = {cid: Decimal("0.00") for cid in card_specs}
        assignment_acc: list[str] = []
        for b in sorted(buckets, key=lambda x: x.amount, reverse=True):
            best_card = b.eligible_cards[0]
            best_marginal = Decimal("-1.00")
            for cid in b.eligible_cards:
                g = b.gross_by_card[cid]
                spec = card_specs[cid]
                old_gross = current_gross[cid]
                new_gross = old_gross + g
                old_capped = min(old_gross, spec.cap_amount) if spec.cap_amount else old_gross
                new_capped = min(new_gross, spec.cap_amount) if spec.cap_amount else new_gross
                marginal = new_capped - old_capped
                if marginal > best_marginal:
                    best_marginal = marginal
                    best_card = cid
            current_gross[best_card] += b.gross_by_card[best_card]
            assignment_acc.append(best_card)
        best_assignment = tuple(assignment_acc)
        best_value, _ = evaluate_assignment(best_assignment)

    proposed_total = best_value
    allocated_total = sum((b.amount for b in buckets), Decimal("0.00"))
    total_spend_preserved = (allocated_total == total_planned)

    allocations: list[dict[str, object]] = []
    for b, prop_card, base_card in zip(buckets, best_assignment, baseline_assignment, strict=True):
        allocations.append(
            {
                "category": b.category,
                "channel": b.channel,
                "amount": str(b.amount),
                "baseline_card_variant_id": base_card,
                "proposed_card_variant_id": prop_card,
                "baseline_reward": str(_money(b.gross_by_card[base_card])),
                "proposed_reward": str(_money(b.gross_by_card[prop_card])),
            }
        )

    has_cap_uncertainty = any(
        s.cap_amount is not None and not s.is_cap_known for s in card_specs.values()
    )
    conservative_proposed_total, _ = evaluate_assignment(best_assignment, conservative=True)
    conservative_baseline_total, _ = evaluate_assignment(baseline_assignment, conservative=True)

    if not total_spend_preserved:
        plan_status = "partial"
        warnings.append(
            f"Partial allocation: {len(excluded)} spending bucket(s) could not be "
            "allocated to any eligible card."
        )
    elif has_cap_uncertainty:
        plan_status = "uncertain"
        warnings.append(
            "Reward estimate has uncertainty: prior cap usage is unknown for one or more capped "
            f"cards. Upper-bound proposed reward is ₹{_money(proposed_total)}, while "
            f"conservative estimate is ₹{_money(conservative_proposed_total)}."
        )
    elif is_heuristic:
        plan_status = "heuristic"
    else:
        plan_status = "optimal"

    return {
        "method_version": OPTIMIZER_VERSION,
        "plan_status": plan_status,
        "search_mode": search_mode,
        "is_heuristic": is_heuristic,
        "baseline_value": str(_money(baseline_total)),
        "proposed_value": str(_money(proposed_total)),
        "incremental_value": str(_money(proposed_total - baseline_total)),
        "has_cap_uncertainty": has_cap_uncertainty,
        "conservative_proposed_value": str(_money(conservative_proposed_total)),
        "conservative_incremental_value": str(
            _money(conservative_proposed_total - conservative_baseline_total)
        ),
        "total_spend_preserved": total_spend_preserved,
        "planned_spend": str(total_planned),
        "allocated_spend": str(allocated_total),
        "allocations": allocations,
        "excluded": excluded,
        "warnings": warnings,
    }
