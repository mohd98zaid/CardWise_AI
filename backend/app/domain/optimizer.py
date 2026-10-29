from dataclasses import dataclass
from decimal import Decimal

from app.domain.calculator.engine import calculate_reward
from app.domain.calculator.models import CalculationInput
from app.domain.rules.models import CashbackRule, PointsRule

OPTIMIZER_VERSION = "enumeration-0.1.0"


@dataclass(frozen=True)
class AllocationCandidate:
    card_variant_id: str
    reward: Decimal


def choose_best_cards(
    spend: list[dict[str, object]],
    cards: list[tuple[str, CashbackRule | PointsRule]],
) -> dict[str, object]:
    """Transparent per-bucket enumeration for the bounded synthetic rule subset."""
    allocations: list[dict[str, object]] = []
    baseline_total = Decimal("0.00")
    proposed_total = Decimal("0.00")
    total_planned = Decimal("0.00")
    allocated_total = Decimal("0.00")
    excluded: list[dict[str, str]] = []
    for bucket in spend:
        amount = bucket["amount"]
        assert isinstance(amount, Decimal)
        total_planned += amount
        baseline_card = str(bucket.get("baseline_card") or "")
        candidates: list[AllocationCandidate] = []
        for card_id, rule in cards:
            result = calculate_reward(
                CalculationInput(
                    card_variant_id=card_id,
                    amount=amount,
                    currency="INR",
                    scenario_date=bucket["scenario_date"],
                    category=str(bucket["category"]),
                    channel=str(bucket["channel"]),
                    prior_cap_consumed=bucket.get("cap_usage"),
                    cap_knowledge_state=str(bucket.get("cap_state", "unknown")),
                ),
                rule,
            )
            if (
                result.status not in {"excluded", "cannot_calculate"}
                and result.estimated_net_value is not None
            ):
                candidates.append(AllocationCandidate(card_id, result.estimated_net_value))
        if not candidates:
            excluded.append(
                {
                    "category": str(bucket["category"]),
                    "reason": "No card has a known reward value under the supplied assumptions",
                }
            )
            continue
        selected = max(candidates, key=lambda candidate: candidate.reward)
        baseline = next(
            (candidate for candidate in candidates if candidate.card_variant_id == baseline_card),
            None,
        )
        baseline_reward = baseline.reward if baseline else Decimal("0.00")
        baseline_total += baseline_reward
        proposed_total += selected.reward
        allocated_total += amount
        allocations.append(
            {
                "category": bucket["category"],
                "channel": bucket["channel"],
                "amount": str(amount),
                "baseline_card_variant_id": baseline_card or None,
                "proposed_card_variant_id": selected.card_variant_id,
                "baseline_reward": str(baseline_reward),
                "proposed_reward": str(selected.reward),
            }
        )
    return {
        "method_version": OPTIMIZER_VERSION,
        "baseline_value": str(baseline_total),
        "proposed_value": str(proposed_total),
        "incremental_value": str(proposed_total - baseline_total),
        "total_spend_preserved": allocated_total == total_planned,
        "planned_spend": str(total_planned),
        "allocated_spend": str(allocated_total),
        "allocations": allocations,
        "excluded": excluded,
        "warnings": [
            (
                "Optimizer models each spending bucket independently. Shared monthly caps across "
                "multiple buckets are not tracked. If your card has a monthly reward cap, actual "
                "achievable reward may be lower than shown."
            )
        ],
    }
