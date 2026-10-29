from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RuleType = Literal["cashback_rate", "points_rate"]
VerificationStatus = Literal[
    "draft", "in_review", "verified", "needs_review", "superseded", "expired", "synthetic"
]


class CashbackRateParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rate_percent: Decimal = Field(ge=Decimal("0"), le=Decimal("100"))
    cap_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    cap_period: Literal["calendar_month"] | None = None
    eligible_categories: list[str] = Field(min_length=1)
    eligible_channels: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cap_period(self) -> "CashbackRateParameters":
        if self.cap_amount is not None and self.cap_period is None:
            raise ValueError("cap_period is required when cap_amount is present")
        return self


class CashbackRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    rule_id: str = Field(min_length=1)
    card_variant_id: str = Field(min_length=1)
    rule_type: Literal["cashback_rate"]
    parameters: CashbackRateParameters
    effective_from: date
    effective_to: date | None = None
    verification_status: VerificationStatus
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def validate_dates(self) -> "CashbackRule":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self

    def applies_on(self, scenario_date: date) -> bool:
        return self.effective_from <= scenario_date and (
            self.effective_to is None or scenario_date <= self.effective_to
        )


class PointsRateParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points_per_100: Decimal = Field(ge=Decimal("0"))
    point_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    eligible_categories: list[str] = Field(min_length=1)
    eligible_channels: list[str] = Field(min_length=1)


class PointsRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    rule_id: str = Field(min_length=1)
    card_variant_id: str = Field(min_length=1)
    rule_type: Literal["points_rate"]
    parameters: PointsRateParameters
    effective_from: date
    effective_to: date | None = None
    verification_status: VerificationStatus
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""

    @model_validator(mode="after")
    def validate_dates(self) -> "PointsRule":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self

    def applies_on(self, scenario_date: date) -> bool:
        return self.effective_from <= scenario_date and (
            self.effective_to is None or scenario_date <= self.effective_to
        )


RuleModel = Annotated[CashbackRule | PointsRule, Field(discriminator="rule_type")]
