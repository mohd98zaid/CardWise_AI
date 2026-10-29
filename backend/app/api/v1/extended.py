from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.ai.assistant import answer_from_sources
from app.api.deps import get_current_user, require_admin
from app.core.config import settings
from app.core.ratelimit import rate_limit_auth
from app.core.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    session_expiry,
    verify_password,
)
from app.db.database import get_db
from app.db.models import (
    AuditEvent,
    CalculationRun,
    CalculationTraceStep,
    CardVariant,
    ExportJob,
    Reminder,
    Rule,
    RuleTestCase,
    Scenario,
    ScenarioAllocation,
    ScenarioSpend,
    SessionToken,
    Source,
    User,
    UserCard,
)
from app.domain.calculator.engine import calculate_reward
from app.domain.calculator.models import CalculationInput
from app.domain.optimizer import choose_best_cards
from app.domain.rules.models import CashbackRule, PointsRule
from app.domain.scenarios.models import (
    AllocationInput,
    AssistantRequest,
    AuthResponse,
    LoginRequest,
    OptimizerRequest,
    PortfolioCardUpdate,
    RegisterRequest,
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
    ScenarioCalculationRequest,
    ScenarioCreate,
    ScenarioResponse,
    ScenarioUpdate,
    SpendInput,
    UserResponse,
)

router = APIRouter(prefix="/api/v1")
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
private_router = APIRouter(prefix="/api/v1", tags=["private"])
admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        timezone=user.timezone,
        preferred_currency=user.preferred_currency,
    )


def issue_token(user: User, db: Session) -> AuthResponse:
    raw_token, token_hash = new_session_token()
    db.add(
        SessionToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=session_expiry(settings.session_ttl_hours),
        )
    )
    db.commit()
    return AuthResponse(access_token=raw_token, user=user_response(user))


@auth_router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(rate_limit_auth),
) -> AuthResponse:
    email = request.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    # SYNTHETIC-MVP-ONLY: Admin role is assigned by hardcoded email.
    # Replace with a proper provisioning process before any real deployment.
    # See docs/SECURITY_THREAT_MODEL.md for the risk register entry.
    role = "admin" if email == "admin@cardwise.local" else "user"
    user = User(email=email, password_hash=hash_password(request.password), role=role)
    db.add(user)
    db.flush()
    response = issue_token(user, db)
    db.add(AuditEvent(actor_id=user.id, action="register", entity_type="user", entity_id=user.id))
    db.commit()
    return response


@auth_router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(rate_limit_auth),
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == request.email.strip().lower()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return issue_token(user, db)


@auth_router.post("/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> None:
    if authorization and authorization.startswith("Bearer "):
        token_hash = hash_session_token(authorization.removeprefix("Bearer ").strip())
        db.execute(delete(SessionToken).where(SessionToken.token_hash == token_hash))
        db.commit()


@private_router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return user_response(user)


@private_router.delete("/me", status_code=204)
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    db.execute(delete(CalculationRun).where(CalculationRun.user_id == user.id))
    db.execute(delete(Reminder).where(Reminder.user_id == user.id))
    db.execute(delete(ExportJob).where(ExportJob.user_id == user.id))
    db.execute(delete(UserCard).where(UserCard.user_id == user.id))
    db.execute(delete(SessionToken).where(SessionToken.user_id == user.id))
    db.delete(user)
    db.commit()


@private_router.patch("/me/preferences", response_model=UserResponse)
def update_preferences(
    preferences: dict[str, str],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    if "timezone" in preferences:
        user.timezone = preferences["timezone"]
    if "preferred_currency" in preferences:
        if preferences["preferred_currency"] != "INR":
            raise HTTPException(
                status_code=422, detail="Only INR is supported in the synthetic MVP"
            )
        user.preferred_currency = preferences["preferred_currency"]
    db.commit()
    db.refresh(user)
    return user_response(user)


def spend_response(item: ScenarioSpend) -> SpendInput:
    return SpendInput(
        category=item.category,
        channel=item.channel,
        amount=item.amount,
        transaction_count=item.transaction_count,
        is_fixed=item.is_fixed,
        cap_usage=item.cap_usage,
        cap_knowledge_state=item.cap_knowledge_state,
        point_value_per_point=item.point_value_per_point,
    )


def scenario_response(scenario: Scenario) -> ScenarioResponse:
    return ScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        scenario_date=scenario.scenario_date,
        currency=scenario.currency,
        revision=scenario.revision,
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
        spend=[spend_response(item) for item in scenario.spend],
    )


def owned_scenario(scenario_id: str, user: User, db: Session) -> Scenario:
    scenario = db.scalar(
        select(Scenario).where(Scenario.id == scenario_id, Scenario.user_id == user.id)
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@private_router.get("/me/scenarios", response_model=list[ScenarioResponse])
def list_scenarios(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ScenarioResponse]:
    scenarios = db.scalars(
        select(Scenario)
        .where(Scenario.user_id == user.id)
        .order_by(Scenario.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [scenario_response(item) for item in scenarios]


@private_router.post("/me/scenarios", response_model=ScenarioResponse, status_code=201)
def create_scenario(
    request: ScenarioCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioResponse:
    scenario = Scenario(
        user_id=user.id,
        name=request.name,
        scenario_date=request.scenario_date,
        currency=request.currency,
    )
    db.add(scenario)
    db.flush()
    for item in request.spend:
        db.add(
            ScenarioSpend(
                scenario_id=scenario.id,
                category=item.category,
                channel=item.channel,
                amount=item.amount,
                transaction_count=item.transaction_count,
                is_fixed=item.is_fixed,
                cap_usage=item.cap_usage,
                cap_knowledge_state=item.cap_knowledge_state,
                point_value_per_point=item.point_value_per_point,
            )
        )
    db.commit()
    db.refresh(scenario)
    return scenario_response(scenario)


@private_router.get("/me/scenarios/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ScenarioResponse:
    return scenario_response(owned_scenario(scenario_id, user, db))


@private_router.patch("/me/scenarios/{scenario_id}", response_model=ScenarioResponse)
def update_scenario(
    scenario_id: str,
    request: ScenarioUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioResponse:
    scenario = owned_scenario(scenario_id, user, db)
    if request.name is not None:
        scenario.name = request.name
    if request.scenario_date is not None:
        scenario.scenario_date = request.scenario_date
    if request.spend is not None:
        scenario.spend.clear()
        for item in request.spend:
            scenario.spend.append(
                ScenarioSpend(
                    category=item.category,
                    channel=item.channel,
                    amount=item.amount,
                    transaction_count=item.transaction_count,
                    is_fixed=item.is_fixed,
                    cap_usage=item.cap_usage,
                    cap_knowledge_state=item.cap_knowledge_state,
                    point_value_per_point=item.point_value_per_point,
                )
            )
    scenario.revision += 1
    scenario.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(scenario)
    return scenario_response(scenario)


@private_router.delete("/me/scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    scenario = owned_scenario(scenario_id, user, db)
    db.delete(scenario)
    db.commit()


@private_router.post(
    "/me/scenarios/{scenario_id}/duplicate", response_model=ScenarioResponse, status_code=201
)
def duplicate_scenario(
    scenario_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ScenarioResponse:
    original = owned_scenario(scenario_id, user, db)
    duplicate = Scenario(
        user_id=user.id,
        name=f"{original.name} copy",
        scenario_date=original.scenario_date,
        currency=original.currency,
    )
    db.add(duplicate)
    db.flush()
    for item in original.spend:
        db.add(
            ScenarioSpend(
                scenario_id=duplicate.id,
                category=item.category,
                channel=item.channel,
                amount=item.amount,
                transaction_count=item.transaction_count,
                is_fixed=item.is_fixed,
                cap_usage=item.cap_usage,
                cap_knowledge_state=item.cap_knowledge_state,
                point_value_per_point=item.point_value_per_point,
            )
        )
    db.commit()
    db.refresh(duplicate)
    return scenario_response(duplicate)


@private_router.put("/me/scenarios/{scenario_id}/allocations")
def replace_allocations(
    scenario_id: str,
    allocations: list[AllocationInput],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    scenario = owned_scenario(scenario_id, user, db)
    spend_by_id = {item.id: item for item in scenario.spend}
    totals: dict[str, Decimal] = {}
    for item in allocations:
        if item.spend_id not in spend_by_id:
            raise HTTPException(
                status_code=422,
                detail=f"Spend bucket {item.spend_id} does not belong to this scenario",
            )
        if db.get(CardVariant, item.card_variant_id) is None:
            raise HTTPException(
                status_code=422, detail="Allocation references an unknown card variant"
            )
        totals[item.spend_id] = totals.get(item.spend_id, Decimal("0")) + item.amount
    for spend_id, spend_item in spend_by_id.items():
        if totals.get(spend_id, Decimal("0")) != spend_item.amount:
            raise HTTPException(
                status_code=422,
                detail="Allocations must preserve total planned spend per bucket",
            )
    db.query(ScenarioAllocation).filter(ScenarioAllocation.scenario_id == scenario.id).delete()
    for item in allocations:
        db.add(
            ScenarioAllocation(
                scenario_id=scenario.id,
                spend_id=item.spend_id,
                card_variant_id=item.card_variant_id,
                amount=item.amount,
                allocation_type=item.allocation_type,
            )
        )
    db.commit()
    return {
        "scenario_id": scenario.id,
        "allocations": [item.model_dump(mode="json") for item in allocations],
    }


@private_router.get("/me/cards")
def list_portfolio(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    rows = db.execute(
        select(UserCard, CardVariant)
        .join(CardVariant, CardVariant.id == UserCard.card_variant_id)
        .where(UserCard.user_id == user.id)
    ).all()
    return [
        {
            "id": row.id,
            "card_variant_id": row.card_variant_id,
            "nickname": row.nickname,
            "status": row.status,
            "display_name": variant.display_name,
        }
        for row, variant in rows
    ]


@private_router.post("/me/cards", status_code=201)
def add_portfolio_card(
    card_variant_id: str,
    nickname: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if db.get(CardVariant, card_variant_id) is None:
        raise HTTPException(status_code=404, detail="Card variant not found")
    existing = db.scalar(
        select(UserCard).where(
            UserCard.user_id == user.id, UserCard.card_variant_id == card_variant_id
        )
    )
    if existing is not None:
        return {
            "id": existing.id,
            "card_variant_id": existing.card_variant_id,
            "status": existing.status,
        }
    item = UserCard(user_id=user.id, card_variant_id=card_variant_id, nickname=nickname)
    db.add(item)
    db.commit()
    return {"id": item.id, "card_variant_id": item.card_variant_id, "status": item.status}


@private_router.patch("/me/cards/{card_id}")
def update_portfolio_card(
    card_id: str,
    request: PortfolioCardUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    item = db.scalar(select(UserCard).where(UserCard.id == card_id, UserCard.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Portfolio card not found")
    if request.nickname is not None:
        item.nickname = request.nickname
    if request.status is not None:
        item.status = request.status
    db.commit()
    return {
        "id": item.id,
        "card_variant_id": item.card_variant_id,
        "nickname": item.nickname,
        "status": item.status,
    }


@private_router.delete("/me/cards/{card_id}", status_code=204)
def delete_portfolio_card(
    card_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = db.scalar(select(UserCard).where(UserCard.id == card_id, UserCard.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Portfolio card not found")
    db.delete(item)
    db.commit()


def rule_for_card(card_id: str, db: Session) -> CashbackRule | PointsRule:
    row = db.scalar(select(Rule).where(Rule.card_variant_id == card_id))
    if row is None:
        raise HTTPException(status_code=422, detail="No supported rule exists for this card")
    rule_data = {
        "schema_version": row.schema_version,
        "rule_id": row.id,
        "card_variant_id": row.card_variant_id,
        "rule_type": row.rule_type,
        "parameters": row.parameters,
        "effective_from": row.effective_from,
        "effective_to": row.effective_to,
        "verification_status": row.verification_status,
        "evidence_ids": row.evidence_ids or [],
        "notes": row.notes,
    }
    return (
        PointsRule.model_validate(rule_data)
        if row.rule_type == "points_rate"
        else CashbackRule.model_validate(rule_data)
    )


@private_router.post("/scenarios/{scenario_id}/calculate")
def calculate_scenario(
    scenario_id: str,
    request: ScenarioCalculationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    scenario = owned_scenario(scenario_id, user, db)
    results: list[dict[str, object]] = []
    for card_id in request.card_variant_ids:
        rule = rule_for_card(card_id, db)
        card_results = []
        for item in scenario.spend:
            calculation = calculate_reward(
                CalculationInput(
                    card_variant_id=card_id,
                    amount=item.amount,
                    currency=scenario.currency,
                    scenario_date=scenario.scenario_date,
                    category=item.category,
                    channel=item.channel,
                    prior_cap_consumed=item.cap_usage,
                    cap_knowledge_state=item.cap_knowledge_state,
                    point_value_per_point=item.point_value_per_point,
                ),
                rule,
            )
            card_results.append(calculation.model_dump(mode="json"))
        total = sum(
            (
                Decimal(value["estimated_net_value"])
                for value in card_results
                if value["estimated_net_value"] is not None
            ),
            Decimal("0"),
        )
        results.append(
            {"card_variant_id": card_id, "estimated_net_value": str(total), "buckets": card_results}
        )
    payload = {"scenario_id": scenario.id, "revision": scenario.revision, "results": results}
    run = CalculationRun(
        user_id=user.id,
        scenario_id=scenario.id,
        input_snapshot={"scenario_revision": scenario.revision},
        result=payload,
        engine_version="calculator-0.1.0",
        manifest_hash="scenario",
        status="complete",
    )
    db.add(run)
    db.flush()
    payload["calculation_run_id"] = run.id
    run.result = payload
    for card_result in results:
        for bucket in card_result["buckets"]:
            for step in bucket["trace"]:
                db.add(
                    CalculationTraceStep(
                        calculation_run_id=run.id,
                        sequence_number=step["sequence"],
                        rule_id=step.get("rule_id"),
                        step_type=step["step_type"],
                        input_json=step["input"],
                        output_json=step["output"],
                        reason=step["reason"],
                        evidence_ids=step.get("evidence_ids", []),
                    )
                )
    db.commit()
    return payload


@private_router.post("/calculations/compare")
def compare_scenario(
    request: ScenarioCalculationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if request.scenario_id is None:
        raise HTTPException(status_code=422, detail="scenario_id is required for comparison")
    return calculate_scenario(request.scenario_id, request, user, db)


@private_router.get("/calculations/{calculation_id}")
def get_calculation(
    calculation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    run = db.scalar(
        select(CalculationRun).where(
            CalculationRun.id == calculation_id,
            CalculationRun.user_id == user.id,
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return {
        "id": run.id,
        "status": run.status,
        "result": run.result,
        "engine_version": run.engine_version,
        "manifest_hash": run.manifest_hash,
    }


@private_router.get("/calculations/{calculation_id}/trace")
def get_calculation_trace(
    calculation_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    run = db.scalar(
        select(CalculationRun).where(
            CalculationRun.id == calculation_id,
            CalculationRun.user_id == user.id,
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Calculation not found")
    steps = db.scalars(
        select(CalculationTraceStep)
        .where(CalculationTraceStep.calculation_run_id == run.id)
        .order_by(CalculationTraceStep.sequence_number)
    ).all()
    return {
        "id": run.id,
        "trace": [
            {
                "sequence": step.sequence_number,
                "rule_id": step.rule_id,
                "step_type": step.step_type,
                "input": step.input_json,
                "output": step.output_json,
                "reason": step.reason,
                "evidence_ids": step.evidence_ids,
            }
            for step in steps
        ],
    }


@private_router.post("/optimizer/run")
def run_optimizer(
    request: OptimizerRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    scenario = owned_scenario(request.scenario_id, user, db)
    owned_ids = {
        item.card_variant_id
        for item in db.scalars(select(UserCard).where(UserCard.user_id == user.id)).all()
    }
    requested_ids = [card_id for card_id in request.card_variant_ids if card_id in owned_ids]
    if not requested_ids:
        raise HTTPException(status_code=422, detail="Optimizer requires at least one owned card")
    cards = [(card_id, rule_for_card(card_id, db)) for card_id in requested_ids]
    spend = [
        {
            "amount": item.amount,
            "category": item.category,
            "channel": item.channel,
            "scenario_date": scenario.scenario_date,
            "cap_usage": item.cap_usage,
            "cap_state": item.cap_knowledge_state,
        }
        for item in scenario.spend
    ]
    result = choose_best_cards(spend, cards)
    result["scenario_id"] = scenario.id
    result["owned_card_variant_ids"] = requested_ids
    return result


@private_router.post("/reminders", response_model=ReminderResponse, status_code=201)
def create_reminder(
    request: ReminderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ReminderResponse:
    reminder = Reminder(
        user_id=user.id, label=request.label, due_at=request.due_at, timezone=request.timezone
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return ReminderResponse(
        id=reminder.id,
        label=reminder.label,
        due_at=reminder.due_at,
        timezone=reminder.timezone,
        status=reminder.status,
    )


@private_router.get("/reminders", response_model=list[ReminderResponse])
def list_reminders(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ReminderResponse]:
    reminders = db.scalars(
        select(Reminder).where(Reminder.user_id == user.id).order_by(Reminder.due_at)
    ).all()
    return [
        ReminderResponse(
            id=item.id,
            label=item.label,
            due_at=item.due_at,
            timezone=item.timezone,
            status=item.status,
        )
        for item in reminders
    ]


@private_router.patch("/reminders/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: str,
    request: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReminderResponse:
    reminder = db.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if request.label is not None:
        reminder.label = request.label
    if request.due_at is not None:
        reminder.due_at = request.due_at
    if request.status is not None:
        reminder.status = request.status
    db.commit()
    return ReminderResponse(
        id=reminder.id,
        label=reminder.label,
        due_at=reminder.due_at,
        timezone=reminder.timezone,
        status=reminder.status,
    )


@private_router.delete("/reminders/{reminder_id}", status_code=204)
def delete_reminder(
    reminder_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    reminder = db.scalar(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == user.id)
    )
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()


@private_router.post("/exports", response_model=dict[str, object], status_code=201)
def create_export(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict[str, object]:
    scenarios = db.scalars(select(Scenario).where(Scenario.user_id == user.id)).all()
    portfolio_rows = db.execute(
        select(UserCard, CardVariant)
        .join(CardVariant, CardVariant.id == UserCard.card_variant_id)
        .where(UserCard.user_id == user.id)
    ).all()
    reminders_rows = db.scalars(
        select(Reminder).where(Reminder.user_id == user.id)
    ).all()
    payload = {
        "schema_version": 1,
        "user": {"id": user.id, "email": user.email, "timezone": user.timezone,
                 "preferred_currency": user.preferred_currency, "role": user.role},
        "portfolio": [
            {"card_variant_id": uc.card_variant_id, "nickname": uc.nickname, "status": uc.status,
             "display_name": cv.display_name}
            for uc, cv in portfolio_rows
        ],
        "scenarios": [scenario_response(item).model_dump(mode="json") for item in scenarios],
        "reminders": [
            {"id": r.id, "label": r.label, "due_at": r.due_at.isoformat(),
             "timezone": r.timezone, "status": r.status}
            for r in reminders_rows
        ],
        "exported_at": datetime.now(UTC).isoformat(),
        "note": "This export contains user-owned records from the CardWise local database only.",
    }
    job = ExportJob(
        user_id=user.id, expires_at=session_expiry(settings.export_expiry_hours), payload=payload
    )
    db.add(job)
    db.commit()
    return {"id": job.id, "expires_at": job.expires_at, "status": job.status, "data": payload}


@private_router.get("/exports/{export_id}")
def get_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    job = db.scalar(
        select(ExportJob).where(ExportJob.id == export_id, ExportJob.user_id == user.id)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Export not found")
    if job.expires_at < datetime.now(UTC):
        job.status = "expired"
        db.commit()
        raise HTTPException(status_code=410, detail="Export has expired")
    return {"id": job.id, "expires_at": job.expires_at, "status": job.status, "data": job.payload}


@private_router.delete("/exports/{export_id}", status_code=204)
def delete_export(
    export_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    job = db.scalar(
        select(ExportJob).where(ExportJob.id == export_id, ExportJob.user_id == user.id)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Export not found")
    db.delete(job)
    db.commit()


@private_router.post("/assistant/ask")
def ask_assistant(
    request: AssistantRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = answer_from_sources(request.question, db.scalars(select(Source)).all())
    result["user_id"] = user.id
    return result


@admin_router.get("/rules")
def list_rules(
    _: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "card_variant_id": item.card_variant_id,
            "verification_status": item.verification_status,
            "review_status": item.review_status,
            "evidence_ids": item.evidence_ids,
        }
        for item in db.scalars(select(Rule)).all()
    ]


@admin_router.get("/review-queue")
def review_queue(
    _: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "entity_type": "rule",
            "reason": "rule awaiting review"
            if item.review_status in {"draft", "in_review"}
            else "published",
            "review_status": item.review_status,
        }
        for item in db.scalars(select(Rule)).all()
    ]


@admin_router.get("/audit")
def audit_events(
    _: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    return [
        {
            "id": event.id,
            "actor_id": event.actor_id,
            "action": event.action,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "created_at": event.created_at,
        }
        for event in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc())).all()
    ]


@admin_router.post("/sources", status_code=201)
def create_source(
    source: dict[str, str],
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    required = {"id", "title", "canonical_url", "excerpt"}
    if not required.issubset(source):
        raise HTTPException(
            status_code=422, detail="Source requires id, title, canonical_url, and excerpt"
        )
    if db.get(Source, source["id"]) is not None:
        raise HTTPException(status_code=409, detail="Source already exists")
    item = Source(
        id=source["id"],
        title=source["title"],
        source_type=source.get("source_type", "synthetic"),
        canonical_url=source["canonical_url"],
        excerpt=source["excerpt"],
        status=source.get("status", "under_review"),
        rights_status=source.get("rights_status", "synthetic_only"),
    )
    db.add(item)
    db.add(
        AuditEvent(
            actor_id=user.id, action="source_created", entity_type="source", entity_id=item.id
        )
    )
    db.commit()
    return {"id": item.id, "status": item.status}


@admin_router.post("/rules", status_code=201)
def create_rule(
    rule: CashbackRule,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if db.get(CardVariant, rule.card_variant_id) is None:
        raise HTTPException(status_code=422, detail="Rule references an unknown card variant")
    if db.get(Rule, rule.rule_id) is not None:
        raise HTTPException(status_code=409, detail="Rule already exists")
    missing_sources = [
        source_id for source_id in rule.evidence_ids if db.get(Source, source_id) is None
    ]
    if missing_sources:
        raise HTTPException(
            status_code=422, detail=f"Unknown evidence IDs: {', '.join(missing_sources)}"
        )
    row = Rule(
        id=rule.rule_id,
        card_variant_id=rule.card_variant_id,
        rule_type=rule.rule_type,
        schema_version=rule.schema_version,
        parameters=rule.model_dump(mode="json")["parameters"],
        effective_from=rule.effective_from,
        effective_to=rule.effective_to,
        verification_status="draft",
        review_status="draft",
        evidence_ids=rule.evidence_ids,
        notes=rule.notes,
    )
    db.add(row)
    db.add(
        AuditEvent(actor_id=user.id, action="rule_created", entity_type="rule", entity_id=row.id)
    )
    db.commit()
    return {"id": row.id, "verification_status": row.verification_status}


@admin_router.post("/rules/{rule_id}/review")
def review_rule(
    rule_id: str, decision: str, user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, str]:
    if decision not in {"approved", "rejected", "changes_requested"}:
        raise HTTPException(status_code=422, detail="Invalid review decision")
    rule = db.get(Rule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.review_status = decision
    db.add(
        AuditEvent(
            actor_id=user.id, action=f"rule_{decision}", entity_type="rule", entity_id=rule_id
        )
    )
    db.commit()
    return {"rule_id": rule_id, "review_status": decision}


@admin_router.post("/rules/{rule_id}/publish")
def publish_rule(
    rule_id: str, user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, str]:
    rule = db.get(Rule, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    has_tests = db.scalar(select(RuleTestCase).where(RuleTestCase.rule_id == rule_id)) is not None
    if not rule.evidence_ids or rule.review_status != "approved" or not has_tests:
        raise HTTPException(
            status_code=422,
            detail="Publication requires evidence, an approved review, and regression tests",
        )
    typed_rule = rule_for_card(rule.card_variant_id, db)
    test_cases = db.scalars(select(RuleTestCase).where(RuleTestCase.rule_id == rule_id)).all()
    failed_cases: list[str] = []
    for case in test_cases:
        try:
            case_input = CalculationInput.model_validate(
                case.input_json
                | {
                    "card_variant_id": rule.card_variant_id,
                    "currency": "INR",
                    "scenario_date": rule.effective_from,
                }
            )
            result = calculate_reward(case_input, typed_rule).model_dump(mode="json")
            for key, expected in case.expected_json.items():
                if result.get(key) != expected:
                    failed_cases.append(case.case_name)
        except Exception:
            failed_cases.append(case.case_name)
    if failed_cases:
        raise HTTPException(
            status_code=422,
            detail=f"Regression tests failed: {', '.join(sorted(set(failed_cases)))}",
        )
    rule.verification_status = "verified"
    rule.review_status = "published"
    db.add(
        AuditEvent(actor_id=user.id, action="rule_published", entity_type="rule", entity_id=rule_id)
    )
    db.commit()
    return {"rule_id": rule_id, "verification_status": rule.verification_status}
