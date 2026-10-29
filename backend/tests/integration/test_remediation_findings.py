"""Integration tests validating the 14 review findings remediation."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.v1.extended import VALID_REVIEW_TRANSITIONS
from app.core.config import ConfigurationError, Settings
from app.core.ratelimit import get_client_ip, reset_rate_limits
from app.db.database import Base
from app.db.models import (
    AuditEvent,
    ExportJob,
    Rule,
    Source,
)
from app.domain.optimizer import choose_best_cards
from app.domain.rules.models import CashbackRateParameters, CashbackRule
from app.domain.rules.resolver import resolve_rule_for_card
from app.main import app
from app.services.admin import provision_admin_user


@pytest.fixture(autouse=True)
def _reset_limits() -> None:
    reset_rate_limits()


def get_token(
    client: TestClient,
    email: str = "testuser@example.com",
    password: str = "password123",
) -> tuple[str, dict[str, str]]:
    res = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    if res.status_code == 409:
        res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Finding 1: Privileged account provisioning
# ---------------------------------------------------------------------------
def test_finding_1_public_registration_never_grants_admin() -> None:
    from uuid import uuid4

    client = TestClient(app)
    email = f"user_{uuid4().hex[:8]}@cardwise.local"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "secureadminpass123",
        },
    )
    assert res.status_code == 201
    # Role must be "user", NOT "admin"
    assert res.json()["user"]["role"] == "user"

    # User cannot access admin endpoints
    headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    admin_res = client.get("/api/v1/admin/rules", headers=headers)
    assert admin_res.status_code == 403


def test_finding_1_admin_provisioning_service() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    with TestingSession() as db:
        user = provision_admin_user(db, "ops@cardwise.local", "SuperSecure123!", role="admin")
        assert user.role == "admin"
        assert user.email == "ops@cardwise.local"

        # Verify audit log
        event = db.scalar(select(AuditEvent).where(AuditEvent.entity_id == user.id))
        assert event is not None
        assert event.action == "provision_admin"


# ---------------------------------------------------------------------------
# Finding 2: Rule publication enforcement & state transitions
# ---------------------------------------------------------------------------
def test_finding_2_valid_review_transitions() -> None:
    assert "draft" in VALID_REVIEW_TRANSITIONS
    assert "published" in VALID_REVIEW_TRANSITIONS
    # Draft can transition to approved or in_review
    assert "approved" in VALID_REVIEW_TRANSITIONS["draft"]
    # Rejected cannot transition directly to published
    assert "published" not in VALID_REVIEW_TRANSITIONS["rejected"]


def test_finding_2_draft_rule_isolation_and_admin_test() -> None:
    client = TestClient(app)
    # Provision an admin
    from app.db.database import SessionLocal

    with SessionLocal() as db:
        provision_admin_user(db, "superadmin@cardwise.local", "AdminPass123!", role="admin")

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@cardwise.local", "password": "AdminPass123!"},
    )
    admin_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Admin tests draft rule directly via test endpoint
    test_calc = client.post(
        "/api/v1/admin/rules/synthetic-draft-cashback-v2/test",
        headers=admin_headers,
        json={
            "card_variant_id": "synthetic-variant",
            "amount": "1000.00",
            "currency": "INR",
            "scenario_date": "2027-02-01",
            "category": "online_shopping",
            "channel": "online_card",
        },
    )
    assert test_calc.status_code == 200
    assert Decimal(test_calc.json()["gross_reward"]) == Decimal("60.00")


# ---------------------------------------------------------------------------
# Finding 3: Effective-dated rule resolution
# ---------------------------------------------------------------------------
def test_finding_3_effective_dated_rule_resolver() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    with TestingSession() as db:
        # Create an expired rule
        db.add(
            Rule(
                id="rule-expired",
                card_variant_id="card-exp",
                rule_type="cashback_rate",
                schema_version=1,
                parameters={
                    "rate_percent": "5.0",
                    "eligible_categories": ["dining"],
                    "eligible_channels": ["pos_card"],
                },
                effective_from=date(2025, 1, 1),
                effective_to=date(2025, 6, 30),
                verification_status="verified",
                review_status="published",
                evidence_ids=["ev1"],
            )
        )
        db.commit()

        # Query on 2026-01-01 -> Expired (404)
        with pytest.raises(Exception) as excinfo:
            resolve_rule_for_card("card-exp", date(2026, 1, 1), db)
        assert excinfo.value.status_code == 404
        assert "expired before" in excinfo.value.detail

        # Query on 2024-01-01 -> Not yet effective (404)
        with pytest.raises(Exception) as excinfo2:
            resolve_rule_for_card("card-exp", date(2024, 1, 1), db)
        assert excinfo2.value.status_code == 404
        assert "not effective until" in excinfo2.value.detail


# ---------------------------------------------------------------------------
# Finding 4: Shared reward caps in the optimizer
# ---------------------------------------------------------------------------
def test_finding_4_optimizer_shared_caps_across_multiple_buckets() -> None:
    # Rule with monthly cap of 500.00
    rule = CashbackRule(
        schema_version=1,
        rule_id="shared-cap-rule",
        card_variant_id="card-shared",
        rule_type="cashback_rate",
        parameters=CashbackRateParameters(
            rate_percent=Decimal("10.0"),
            cap_amount=Decimal("500.00"),
            cap_period="calendar_month",
            eligible_categories=["dining", "online_shopping"],
            eligible_channels=["online_card", "pos_card"],
        ),
        effective_from=date(2026, 1, 1),
        verification_status="verified",
    )

    cards = [("card-shared", rule)]
    # Two buckets: 4,000 in dining (gross reward 400)
    # and 4,000 in online_shopping (gross reward 400).
    # Sum of gross rewards = 800.00, but monthly shared cap is 500.00!
    spend = [
        {
            "amount": Decimal("4000.00"),
            "category": "dining",
            "channel": "pos_card",
            "scenario_date": date(2026, 2, 1),
        },
        {
            "amount": Decimal("4000.00"),
            "category": "online_shopping",
            "channel": "online_card",
            "scenario_date": date(2026, 2, 1),
        },
    ]

    result = choose_best_cards(spend, cards)
    # Total proposed reward must NOT exceed shared monthly cap of 500.00!
    assert Decimal(result["proposed_value"]) <= Decimal("500.00")
    assert Decimal(result["proposed_value"]) == Decimal("500.00")
    assert result["total_spend_preserved"] is True
    assert result["plan_status"] == "optimal"


# ---------------------------------------------------------------------------
# Finding 5: Catalogue query efficiency
# ---------------------------------------------------------------------------
def test_finding_5_catalogue_search_and_pagination() -> None:
    client = TestClient(app)
    # Test offset and limit
    res1 = client.get("/api/v1/catalogue/cards?limit=1&offset=0")
    assert res1.status_code == 200
    items1 = res1.json()
    assert len(items1) <= 1

    # Search filter
    res_search = client.get("/api/v1/catalogue/cards?search=Synthetic")
    assert res_search.status_code == 200
    for card in res_search.json():
        assert (
            "synthetic" in card["display_name"].lower()
            or "synthetic" in card["description"].lower()
        )


# ---------------------------------------------------------------------------
# Finding 6: Readiness error disclosure
# ---------------------------------------------------------------------------
def test_finding_6_readiness_masks_internal_exceptions() -> None:
    client = TestClient(app)
    # Mock database session failure
    with patch("app.main.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = RuntimeError("FATAL: connection secret string exposed!")
        mock_session.return_value.__enter__.return_value = mock_db

        res = client.get("/ready")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "degraded"
        assert "FATAL" not in str(data)
        assert "secret" not in str(data)
        assert "request_id" in data


# ---------------------------------------------------------------------------
# Finding 7: Configuration and rate limiting
# ---------------------------------------------------------------------------
def test_finding_7_production_config_validation() -> None:
    # Production with sqlite raises ConfigurationError
    with pytest.raises(ConfigurationError, match="SQLite cannot be used"):
        s = Settings(
            app_env="production",
            database_url="sqlite:///./prod.db",
        )
        s.validate()

    # Production with zero rate limit raises ConfigurationError
    with pytest.raises(ConfigurationError, match="AUTH_RATE_LIMIT cannot be disabled"):
        s2 = Settings(
            app_env="production",
            database_url="postgresql://user:pass@localhost:5432/cardwise",
            auth_rate_limit=0,
        )
        s2.validate()


def test_finding_7_trusted_proxy_ip_resolution() -> None:
    class DummyRequest:
        def __init__(self, client_host: str, headers: dict[str, str]) -> None:
            self.client = MagicMock(host=client_host)
            self.headers = headers

    # Untrusted proxy attempting spoofing
    req_untrusted = DummyRequest(
        client_host="198.51.100.1",
        headers={"x-forwarded-for": "203.0.113.195"},
    )
    # Must use client_host, NOT the spoofed header
    assert get_client_ip(req_untrusted) == "198.51.100.1"


# ---------------------------------------------------------------------------
# Finding 9: Preference and datetime validation
# ---------------------------------------------------------------------------
def test_finding_9_timezone_and_preference_validation() -> None:
    client = TestClient(app)
    _, headers = get_token(client, "tzuser@example.com")

    # Invalid IANA timezone must return 422
    res_bad_tz = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={"timezone": "Invalid/Fake_Timezone"},
    )
    assert res_bad_tz.status_code == 422

    # Valid IANA timezone succeeds
    res_good_tz = client.patch(
        "/api/v1/me/preferences",
        headers=headers,
        json={"timezone": "Asia/Kolkata"},
    )
    assert res_good_tz.status_code == 200
    assert res_good_tz.json()["timezone"] == "Asia/Kolkata"


# ---------------------------------------------------------------------------
# Finding 12: Assistant grounding & domain overlap
# ---------------------------------------------------------------------------
def test_finding_12_assistant_abstains_on_non_domain_or_contradictory_queries() -> None:
    from app.ai.assistant import answer_from_sources

    sources = [
        Source(
            id="s1",
            title="Rewards guide",
            canonical_url="https://example.com/s1",
            excerpt="Utility bill payments are excluded from all cashback.",
            status="current",
            rights_status="synthetic_only",
        ),
        Source(
            id="s2",
            title="Rewards promotional offer",
            canonical_url="https://example.com/s2",
            excerpt="Utility bill payments are eligible for 5% cashback of max 500.",
            status="current",
            rights_status="synthetic_only",
        ),
    ]

    # Contradictory evidence query
    res = answer_from_sources("utility cashback", sources)
    assert res["abstained"] is True
    assert "conflicting or contradictory" in str(res["answer"]).lower()
    assert res["assistant_type"] == "lexical_lookup_alpha"
    assert "disclaimer" in res


# ---------------------------------------------------------------------------
# Finding 13: Privacy, account deletion cascade & expired export
# ---------------------------------------------------------------------------
def test_finding_13_expired_export_purges_payload() -> None:
    client = TestClient(app)
    from app.db.database import SessionLocal

    _, headers = get_token(client, "exportuser@example.com")
    exp_res = client.post("/api/v1/exports", headers=headers)
    assert exp_res.status_code == 201
    job_id = exp_res.json()["id"]

    # Manually expire the export job in DB
    with SessionLocal() as db:
        job = db.get(ExportJob, job_id)
        job.expires_at = datetime.now(UTC) - timedelta(hours=1)
        db.commit()

    # Getting expired export returns 410 Gone and purges data
    expired_res = client.get(f"/api/v1/exports/{job_id}", headers=headers)
    assert expired_res.status_code == 410

    with SessionLocal() as db:
        refreshed = db.get(ExportJob, job_id)
        assert refreshed.status == "expired"
        assert refreshed.payload == {}
