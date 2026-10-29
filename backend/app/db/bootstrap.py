import json
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.db.database import Base, SessionLocal, engine
from app.db.models import CardVariant, Issuer, Rule, RuleTestCase, Source

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
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        issuer = db.scalar(select(Issuer).where(Issuer.name == "Synthetic Issuer"))
        if issuer is None:
            issuer = Issuer(name="Synthetic Issuer", official_domain="synthetic.example")
            db.add(issuer)
            db.flush()
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
            if db.get(Rule, fixture["rule_id"]) is None:
                db.add(
                    Rule(
                        id=fixture["rule_id"],
                        card_variant_id=fixture["card_variant_id"],
                        rule_type=fixture["rule_type"],
                        schema_version=fixture["schema_version"],
                        parameters=fixture["parameters"],
                        effective_from=date.fromisoformat(fixture["effective_from"]),
                        verification_status="draft",
                        review_status="draft",
                        evidence_ids=[source["id"]],
                        notes=fixture["notes"],
                    )
                )
            if (
                db.scalar(select(RuleTestCase).where(RuleTestCase.rule_id == fixture["rule_id"]))
                is None
            ):
                db.add(_test_case(fixture))
        db.commit()
