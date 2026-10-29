from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32), default="user")
    status: Mapped[str] = mapped_column(String(32), default="active")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    preferred_currency: Mapped[str] = mapped_column(String(3), default="INR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    sessions: Mapped[list["SessionToken"]] = relationship(cascade="all, delete-orphan")
    scenarios: Mapped[list["Scenario"]] = relationship(cascade="all, delete-orphan")
    cards: Mapped[list["UserCard"]] = relationship(cascade="all, delete-orphan")


class SessionToken(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Issuer(Base):
    __tablename__ = "issuers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    market: Mapped[str] = mapped_column(String(8), default="IN")
    official_domain: Mapped[str] = mapped_column(String(255), default="synthetic.example")


class CardVariant(Base):
    __tablename__ = "card_variants"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"))
    product_family: Mapped[str] = mapped_column(String(160))
    display_name: Mapped[str] = mapped_column(String(200))
    network: Mapped[str] = mapped_column(String(80))
    market: Mapped[str] = mapped_column(String(8), default="IN")
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    valid_from: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(32), default="active")
    verification_status: Mapped[str] = mapped_column(String(32), default="synthetic")
    description: Mapped[str] = mapped_column(Text)


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(240))
    source_type: Mapped[str] = mapped_column(String(64), default="synthetic")
    canonical_url: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default="under_review")
    rights_status: Mapped[str] = mapped_column(String(32), default="synthetic_only")
    excerpt: Mapped[str] = mapped_column(Text)


class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    card_variant_id: Mapped[str] = mapped_column(ForeignKey("card_variants.id"), index=True)
    rule_type: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[int] = mapped_column(default=1)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="draft")
    review_status: Mapped[str] = mapped_column(String(32), default="draft")
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")


class RuleTestCase(Base):
    __tablename__ = "rule_test_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rules.id", ondelete="CASCADE"), index=True)
    case_name: Mapped[str] = mapped_column(String(160))
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    test_type: Mapped[str] = mapped_column(String(32), default="golden")


class UserCard(Base):
    __tablename__ = "user_cards"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    card_variant_id: Mapped[str] = mapped_column(ForeignKey("card_variants.id"))
    nickname: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    __table_args__ = (UniqueConstraint("user_id", "card_variant_id", name="uq_user_card_variant"),)


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    scenario_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    revision: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    spend: Mapped[list["ScenarioSpend"]] = relationship(cascade="all, delete-orphan")
    allocations: Mapped[list["ScenarioAllocation"]] = relationship(cascade="all, delete-orphan")


class ScenarioSpend(Base):
    __tablename__ = "scenario_spend"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(80))
    channel: Mapped[str] = mapped_column(String(80))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    transaction_count: Mapped[int | None] = mapped_column(nullable=True)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False)
    cap_usage: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    cap_knowledge_state: Mapped[str] = mapped_column(String(16), default="unknown")
    point_value_per_point: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)


class ScenarioAllocation(Base):
    __tablename__ = "scenario_allocations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), index=True
    )
    spend_id: Mapped[str] = mapped_column(ForeignKey("scenario_spend.id", ondelete="CASCADE"))
    card_variant_id: Mapped[str] = mapped_column(ForeignKey("card_variants.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    allocation_type: Mapped[str] = mapped_column(String(32), default="baseline")


class CalculationRun(Base):
    __tablename__ = "calculation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[str | None] = mapped_column(ForeignKey("scenarios.id"), nullable=True)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    result: Mapped[dict[str, Any]] = mapped_column(JSON)
    engine_version: Mapped[str] = mapped_column(String(80))
    manifest_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class CalculationTraceStep(Base):
    __tablename__ = "calculation_trace_steps"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    calculation_run_id: Mapped[str] = mapped_column(
        ForeignKey("calculation_runs.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column()
    rule_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    step_type: Mapped[str] = mapped_column(String(80))
    input_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    output_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(Text)
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list)


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(200))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    status: Mapped[str] = mapped_column(String(32), default="active")


class ExportJob(Base):
    __tablename__ = "export_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="ready")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(120))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
