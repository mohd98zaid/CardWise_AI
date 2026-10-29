from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import CardVariant as CardVariantRow
from app.db.models import Issuer, Rule, Source
from app.domain.calculator.engine import calculate_reward
from app.domain.calculator.models import CalculationInput, CalculationResult
from app.domain.catalogue import CardVariant as CardVariantResponse
from app.domain.rules.models import CashbackRule, PointsRule
from app.domain.scenarios.models import TaxonomyItem
from app.domain.taxonomy import CATEGORIES, CHANNELS

router = APIRouter(prefix="/api/v1")


@router.get("/catalogue/cards", response_model=list[CardVariantResponse])
def list_cards(
    search: str | None = Query(default=None, min_length=1),
    network: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[CardVariantResponse]:
    rows = db.execute(
        select(CardVariantRow, Issuer).join(Issuer, Issuer.id == CardVariantRow.issuer_id)
    ).all()
    cards = [
        CardVariantResponse(
            id=row.id,
            issuer_name=issuer.name,
            product_family=row.product_family,
            display_name=row.display_name,
            network=row.network,
            market=row.market,
            currency=row.currency,
            valid_from=row.valid_from,
            status=row.status,
            verification_status=row.verification_status,
            description=row.description,
        )
        for row, issuer in rows
    ]
    if network:
        cards = [c for c in cards if c.network.casefold() == network.casefold()]
    if status:
        cards = [c for c in cards if c.status == status]
    if search:
        normalized = search.casefold()
        cards = [
            card
            for card in cards
            if normalized
            in " ".join(
                [card.issuer_name, card.product_family, card.display_name, card.network]
            ).casefold()
        ]
    return cards[offset : offset + limit]


@router.get("/catalogue/cards/{variant_id}", response_model=CardVariantResponse)
def get_card(variant_id: str, db: Session = Depends(get_db)) -> CardVariantResponse:
    row = db.scalar(select(CardVariantRow).where(CardVariantRow.id == variant_id))
    issuer = db.get(Issuer, row.issuer_id) if row is not None else None
    if row is None or issuer is None:
        raise HTTPException(status_code=404, detail="Card variant not found")
    return CardVariantResponse(
        id=row.id,
        issuer_name=issuer.name,
        product_family=row.product_family,
        display_name=row.display_name,
        network=row.network,
        market=row.market,
        currency=row.currency,
        valid_from=row.valid_from,
        status=row.status,
        verification_status=row.verification_status,
        description=row.description,
    )


@router.get("/taxonomy/categories", response_model=list[TaxonomyItem])
def list_categories() -> list[TaxonomyItem]:
    return CATEGORIES


@router.get("/taxonomy/channels", response_model=list[TaxonomyItem])
def list_channels() -> list[TaxonomyItem]:
    return CHANNELS


@router.get("/sources")
def list_sources(db: Session = Depends(get_db)) -> list[dict[str, str]]:
    return [
        {
            "id": source.id,
            "title": source.title,
            "source_type": source.source_type,
            "canonical_url": source.canonical_url,
            "status": source.status,
            "rights_status": source.rights_status,
            "excerpt": source.excerpt,
        }
        for source in db.scalars(select(Source)).all()
    ]


@router.get("/card-variants/{variant_id}/rules")
def list_card_rules(variant_id: str, db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [
        {
            "id": rule.id,
            "rule_type": rule.rule_type,
            "parameters": rule.parameters,
            "effective_from": rule.effective_from,
            "effective_to": rule.effective_to,
            "verification_status": rule.verification_status,
            "evidence_ids": rule.evidence_ids,
            "notes": rule.notes,
        }
        for rule in db.scalars(select(Rule).where(Rule.card_variant_id == variant_id)).all()
    ]


@router.post("/calculations/estimate", response_model=CalculationResult)
def estimate(request: CalculationInput, db: Session = Depends(get_db)) -> CalculationResult:
    row = db.scalar(
        select(Rule)
        .where(
            and_(
                Rule.card_variant_id == request.card_variant_id,
                Rule.effective_from <= request.scenario_date,
                or_(Rule.effective_to.is_(None), Rule.effective_to >= request.scenario_date),
            )
        )
        .order_by(Rule.effective_from.desc())
    )
    if row is None:
        raise HTTPException(
            status_code=404, detail="No active rule for this card on the requested date"
        )
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
    rule = (
        PointsRule.model_validate(rule_data)
        if row.rule_type == "points_rate"
        else CashbackRule.model_validate(rule_data)
    )
    return calculate_reward(request, rule)
