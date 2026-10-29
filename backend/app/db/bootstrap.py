import json
import logging
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.models import CardVariant, Issuer, Rule, RuleTestCase, Source
from app.services.admin import provision_admin_user

_logger = logging.getLogger("cardwise.bootstrap")

FIXTURES = (
    "synthetic-cashback-rule.json",
    "synthetic-points-rule.json",
)


def _fixture_source(fixture: dict[str, object]) -> dict[str, str]:
    if fixture["rule_type"] == "points_rate":
        return {
            "id": "synthetic-points-source",
            "title": "Synthetic points rule fixture",
            "url": "synthetic://cardwise/rules/travel-points",
            "excerpt": "Fictional points fixture; point value is a user assumption.",
        }
    return {
        "id": "synthetic-source",
        "title": "Synthetic cashback rule fixture",
        "url": "synthetic://cardwise/rules/online-cashback",
        "excerpt": "Fictional test fixture; not a real issuer offer.",
    }


def _card_details(fixture: dict[str, object]) -> dict[str, str]:
    if fixture["rule_type"] == "points_rate":
        return {
            "product_family": "Synthetic Travel Rewards Card",
            "display_name": "Synthetic Travel Rewards Card — Points",
            "network": "Synthetic Network",
            "description": "A fictional points card used for local testing only.",
        }
    return {
        "product_family": "Synthetic Rewards Card",
        "display_name": "Synthetic Rewards Card — Online Cashback",
        "network": "Synthetic Network",
        "description": "A fictional cashback card used for local testing only.",
    }


def _test_case(fixture: dict[str, object]) -> RuleTestCase:
    if fixture["rule_type"] == "points_rate":
        return RuleTestCase(
            rule_id=str(fixture["rule_id"]),
            case_name="eligible travel points",
            input_json={"amount": "1000.00", "category": "travel", "channel": "online_card"},
            expected_json={"gross_reward": "20.00", "reward_unit": "points"},
        )
    return RuleTestCase(
        rule_id=str(fixture["rule_id"]),
        case_name="eligible online spend under cap",
        input_json={
            "amount": "8000.00",
            "category": "online_shopping",
            "channel": "online_card",
        },
        expected_json={"gross_reward": "400.00", "cap_amount": "500.00"},
    )


def initialize_database() -> None:
    """Initialize database schemas and initial bootstrap fixtures."""
    # Only run create_all in development or test. Production schemas use Alembic migrations.
    if settings.app_env != "production":
        Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # 1. Provision initial administrator if configured via environment
        if settings.initial_admin_email and settings.initial_admin_password:
            provision_admin_user(
                db,
                settings.initial_admin_email,
                settings.initial_admin_password,
                role="admin",
            )

        # 2. Seed synthetic issuer
        issuer = db.scalar(select(Issuer).where(Issuer.name == "Synthetic Issuer"))
        if issuer is None:
            issuer = Issuer(name="Synthetic Issuer", official_domain="synthetic.example")
            db.add(issuer)
            db.flush()

        # 3. Seed synthetic card variants, sources, and published rules
        fixture_dir = Path(__file__).resolve().parents[3] / "rule-data" / "fixtures"
        for filename in FIXTURES:
            fixture = json.loads((fixture_dir / filename).read_text(encoding="utf-8"))
            card_details = _card_details(fixture)
            if db.get(CardVariant, fixture["card_variant_id"]) is None:
                db.add(
                    CardVariant(
                        id=fixture["card_variant_id"],
                        issuer_id=issuer.id,
                        valid_from=date.fromisoformat(fixture["effective_from"]),
                        **card_details,
                    )
                )
            source = _fixture_source(fixture)
            if db.get(Source, source["id"]) is None:
                db.add(
                    Source(
                        id=source["id"],
                        title=source["title"],
                        canonical_url=source["url"],
                        excerpt=source["excerpt"],
                    )
                )

            # Synthetic baseline rules are published and visibly marked as synthetic
            existing_rule = db.get(Rule, fixture["rule_id"])
            if existing_rule is None:
                db.add(
                    Rule(
                        id=fixture["rule_id"],
                        card_variant_id=fixture["card_variant_id"],
                        rule_type=fixture["rule_type"],
                        schema_version=fixture["schema_version"],
                        parameters=fixture["parameters"],
                        effective_from=date.fromisoformat(fixture["effective_from"]),
                        verification_status="synthetic",
                        review_status="published",
                        evidence_ids=[source["id"]],
                        notes=fixture["notes"],
                    )
                )
            else:
                # Ensure synthetic rules remain published & marked synthetic
                if existing_rule.review_status == "draft":
                    existing_rule.review_status = "published"
                    existing_rule.verification_status = "synthetic"

            if (
                db.scalar(select(RuleTestCase).where(RuleTestCase.rule_id == fixture["rule_id"]))
                is None
            ):
                db.add(_test_case(fixture))

        # 4. Seed an explicit draft fixture for admin review/testing workflow
        draft_rule_id = "synthetic-draft-cashback-v2"
        if db.get(Rule, draft_rule_id) is None:
            db.add(
                Rule(
                    id=draft_rule_id,
                    card_variant_id="synthetic-variant",
                    rule_type="cashback_rate",
                    schema_version=1,
                    parameters={
                        "rate_percent": "6.0",
                        "cap_amount": "600.00",
                        "cap_period": "calendar_month",
                        "eligible_categories": ["online_shopping"],
                        "eligible_channels": ["online_card"],
                    },
                    effective_from=date(2027, 1, 1),
                    effective_to=None,
                    verification_status="draft",
                    review_status="draft",
                    evidence_ids=["synthetic-source"],
                    notes="Proposed future revision awaiting administrative review.",
                )
            )
            if db.scalar(select(RuleTestCase).where(RuleTestCase.rule_id == draft_rule_id)) is None:
                db.add(
                    RuleTestCase(
                        rule_id=draft_rule_id,
                        case_name="eligible online spend under cap",
                        input_json={
                            "amount": "1000.00",
                            "category": "online_shopping",
                            "channel": "online_card",
                        },
                        expected_json={"gross_reward": "60.00", "cap_amount": "600.00"},
                    )
                )

        db.commit()
