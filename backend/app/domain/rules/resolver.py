"""Shared rule resolver with effective-dating and publication enforcement."""

from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Rule as RuleRow
from app.domain.rules.models import CashbackRule, PointsRule


def resolve_rule_for_card(
    card_variant_id: str,
    scenario_date: date,
    db: Session,
    *,
    allow_draft: bool = False,
) -> CashbackRule | PointsRule:
    """Resolve the authoritative active rule for a card variant on a given scenario date.

    Enforces:
    - Rule must belong to the requested card variant.
    - Rule must be active on scenario_date (effective_from <= scenario_date <= effective_to).
    - Rule must be approved/published (unless allow_draft=True for admin test paths).
    - Detects missing, expired, future, and conflicting/overlapping active rules.
    """
    # 1. Base query for this card variant
    query = select(RuleRow).where(RuleRow.card_variant_id == card_variant_id)
    if not allow_draft:
        query = query.where(RuleRow.review_status.in_(["published", "approved"]))

    candidate_rules = db.scalars(query).all()

    if not candidate_rules:
        # Check if rules exist in other review states (e.g., draft or under review)
        all_rules = db.scalars(
            select(RuleRow).where(RuleRow.card_variant_id == card_variant_id)
        ).all()
        if all_rules and not allow_draft:
            raise HTTPException(
                status_code=404,
                detail=f"No published rule exists for card variant '{card_variant_id}'.",
            )
        raise HTTPException(
            status_code=404,
            detail=f"No rule exists for card variant '{card_variant_id}'.",
        )

    # 2. Check for invalid date ranges on candidate rules
    for r in candidate_rules:
        if r.effective_to is not None and r.effective_to < r.effective_from:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Rule '{r.id}' has an invalid effective date range "
                    "(effective_to < effective_from)."
                ),
            )

    # 3. Filter rules active on scenario_date
    matching = [
        r
        for r in candidate_rules
        if r.effective_from <= scenario_date
        and (r.effective_to is None or r.effective_to >= scenario_date)
    ]

    if not matching:
        expired = [
            r
            for r in candidate_rules
            if r.effective_to is not None and scenario_date > r.effective_to
        ]
        future = [r for r in candidate_rules if scenario_date < r.effective_from]
        if expired and not future:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Rule for card variant '{card_variant_id}' has expired before "
                    f"{scenario_date.isoformat()}."
                ),
            )
        if future and not expired:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Rule for card variant '{card_variant_id}' is not effective until "
                    f"{future[0].effective_from.isoformat()}."
                ),
            )
        raise HTTPException(
            status_code=404,
            detail=(
                f"No active rule covers card variant '{card_variant_id}' on "
                f"{scenario_date.isoformat()}."
            ),
        )

    # 4. Check for conflicting overlapping active rules
    if len(matching) > 1:
        # If multiple rules are active on the exact same date for the same card
        distinct_types = {r.rule_type for r in matching}
        if len(matching) > len(distinct_types) or len(distinct_types) > 1:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Conflicting active rules found for card variant '{card_variant_id}' on "
                    f"{scenario_date.isoformat()}."
                ),
            )

    # 5. Select the most recently effective active rule
    selected = sorted(matching, key=lambda r: r.effective_from, reverse=True)[0]

    rule_dict: dict[str, Any] = {
        "schema_version": selected.schema_version,
        "rule_id": selected.id,
        "card_variant_id": selected.card_variant_id,
        "rule_type": selected.rule_type,
        "parameters": selected.parameters,
        "effective_from": selected.effective_from,
        "effective_to": selected.effective_to,
        "verification_status": selected.verification_status,
        "evidence_ids": selected.evidence_ids or [],
        "notes": selected.notes or "",
    }

    if selected.rule_type == "points_rate":
        return PointsRule.model_validate(rule_dict)
    return CashbackRule.model_validate(rule_dict)
