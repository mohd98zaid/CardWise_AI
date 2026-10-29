from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CalculationStatus = Literal[
    "verified_estimate",
    "estimated",
    "partial",
    "needs_input",
    "cannot_calculate",
    "excluded",
]
KnowledgeState = Literal["known", "unknown"]


class CalculationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_variant_id: str = Field(min_length=1)
    amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    scenario_date: date
    category: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    prior_cap_consumed: Decimal | None = Field(default=None, ge=Decimal("0"))
    cap_knowledge_state: KnowledgeState = "unknown"
    point_value_per_point: Decimal | None = Field(default=None, ge=Decimal("0"))


class TraceStep(BaseModel):
    sequence: int
    step_type: str
    reason: str
    input: dict[str, str | None]
    output: dict[str, str | None]
    rule_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class CalculationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CalculationStatus
    card_variant_id: str
    eligible_spend: Decimal
    excluded_spend: Decimal
    exclusion_reason: str | None = None
    gross_reward: Decimal | None = None
    reward_units: Decimal | None = None
    reward_unit: str = "INR"
    point_value_per_unit: Decimal | None = None
    cap_amount: Decimal | None = None
    cap_consumed_before: Decimal | None = None
    cap_remaining_before: Decimal | None = None
    estimated_reward: Decimal | None = None
    possible_reward_min: Decimal | None = None
    possible_reward_max: Decimal | None = None
    fee_allocation: Decimal = Decimal("0.00")
    estimated_net_value: Decimal | None = None
    currency: str
    verification_status: str
    warnings: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    trace: list[TraceStep]
    engine_version: str
    manifest_hash: str
