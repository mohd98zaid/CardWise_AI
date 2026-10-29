from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    timezone: str
    preferred_currency: str


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(RegisterRequest):
    pass


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse


class SpendInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=80)
    channel: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(ge=Decimal("0"))
    transaction_count: int | None = Field(default=None, ge=1)
    is_fixed: bool = False
    cap_usage: Decimal | None = Field(default=None, ge=Decimal("0"))
    cap_knowledge_state: Literal["known", "unknown"] = "unknown"
    point_value_per_point: Decimal | None = Field(default=None, ge=Decimal("0"))


class PortfolioCardUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=120)
    status: Literal["active", "inactive", "closed", "unknown"] | None = None


class TaxonomyItem(BaseModel):
    code: str
    label: str
    description: str


class AllocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spend_id: str
    card_variant_id: str
    amount: Decimal = Field(ge=Decimal("0"))
    allocation_type: Literal["baseline", "proposed", "manual"] = "baseline"


class ScenarioCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    scenario_date: date
    currency: Literal["INR"] = "INR"
    spend: list[SpendInput] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    scenario_date: date | None = None
    spend: list[SpendInput] | None = None


class ScenarioResponse(BaseModel):
    id: str
    name: str
    scenario_date: date
    currency: str
    revision: int
    created_at: datetime
    updated_at: datetime
    spend: list[SpendInput]


class ScenarioCalculationRequest(BaseModel):
    card_variant_ids: list[str] = Field(min_length=1)
    scenario_id: str | None = None


class ReminderCreate(BaseModel):
    label: str = Field(min_length=1, max_length=200)
    due_at: datetime
    timezone: str = "Asia/Kolkata"


class ReminderResponse(ReminderCreate):
    id: str
    status: str


class ReminderUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    due_at: datetime | None = None
    status: Literal["active", "dismissed"] | None = None


class OptimizerRequest(BaseModel):
    scenario_id: str
    card_variant_ids: list[str] = Field(min_length=1)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    card_variant_id: str | None = None
