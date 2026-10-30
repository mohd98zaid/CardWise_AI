"""Comprehensive regression test suite for feature audit, rule governance,
and functional workflows in CardWise AI.
"""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.ratelimit import reset_rate_limits
from app.db.database import SessionLocal
from app.main import app
from app.services.admin import provision_admin_user


def authenticated_client(
    email: str | None = None, role: str = "user"
) -> tuple[TestClient, dict[str, str]]:
    reset_rate_limits()
    client = TestClient(app)
    address = email or f"{uuid4().hex}@example.com"
    if role == "admin":
        with SessionLocal() as db:
            provision_admin_user(db, address, "password123", role="admin")
        response = client.post(
            "/api/v1/auth/login",
            json={"email": address, "password": "password123"},
        )
    else:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": address, "password": "password123"},
        )
        if response.status_code == 409:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": address, "password": "password123"},
            )
    assert response.status_code in {200, 201}
    return client, {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_create_both_cashback_and_points_rules() -> None:
    admin_client, admin_headers = authenticated_client(role="admin")
    variant_id = "synthetic-variant"

    # 1. Admin creates a points rule
    points_rule_id = f"test-points-rule-{uuid4().hex[:8]}"
    points_payload = {
        "schema_version": 1,
        "rule_id": points_rule_id,
        "card_variant_id": variant_id,
        "rule_type": "points_rate",
        "parameters": {
            "points_per_100": "4.0",
            "point_value": "0.25",
            "eligible_categories": ["dining", "online_shopping"],
            "eligible_channels": ["online_card", "pos_card"],
        },
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "verification_status": "draft",
        "evidence_ids": ["synthetic-source"],
        "notes": "Admin points rule creation test",
    }
    resp = admin_client.post("/api/v1/admin/rules", headers=admin_headers, json=points_payload)
    assert resp.status_code == 201
    assert resp.json()["id"] == points_rule_id

    # Test the draft points rule via the admin test endpoint
    test_calc = admin_client.post(
        f"/api/v1/admin/rules/{points_rule_id}/test",
        headers=admin_headers,
        json={
            "card_variant_id": variant_id,
            "currency": "INR",
            "scenario_date": "2026-06-01",
            "amount": "1000.00",
            "category": "dining",
            "channel": "pos_card",
        },
    )
    assert test_calc.status_code == 200
    assert test_calc.json()["status"] in {"estimated", "calculated"}
    # 1000 spend * 4 points/100 = 40 points; 40 * 0.25 = 10.00
    assert Decimal(test_calc.json()["estimated_reward"]) == Decimal("10.00")

    # 2. Admin creates a cashback rule
    cashback_rule_id = f"test-cashback-rule-{uuid4().hex[:8]}"
    cashback_payload = {
        "schema_version": 1,
        "rule_id": cashback_rule_id,
        "card_variant_id": variant_id,
        "rule_type": "cashback_rate",
        "parameters": {
            "rate_percent": "5.0",
            "cap_amount": "500.00",
            "cap_period": "calendar_month",
            "eligible_categories": ["online_shopping"],
            "eligible_channels": ["online_card"],
        },
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "verification_status": "draft",
        "evidence_ids": ["synthetic-source"],
        "notes": "Admin cashback rule creation test",
    }
    resp = admin_client.post("/api/v1/admin/rules", headers=admin_headers, json=cashback_payload)
    assert resp.status_code == 201
    assert resp.json()["id"] == cashback_rule_id


def test_public_card_rules_hides_draft_and_unapproved_rules() -> None:
    client = TestClient(app)
    admin_client, admin_headers = authenticated_client(role="admin")
    variant_id = "synthetic-variant"

    draft_rule_id = f"draft-rule-{uuid4().hex[:8]}"
    payload = {
        "schema_version": 1,
        "rule_id": draft_rule_id,
        "card_variant_id": variant_id,
        "rule_type": "cashback_rate",
        "parameters": {
            "rate_percent": "1.0",
            "eligible_categories": ["other"],
            "eligible_channels": ["pos_card"],
        },
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "verification_status": "draft",
        "evidence_ids": ["synthetic-source"],
        "notes": "Should remain draft and invisible to public catalogue",
    }
    admin_client.post("/api/v1/admin/rules", headers=admin_headers, json=payload)

    # Public catalogue rules query
    pub_resp = client.get(f"/api/v1/card-variants/{variant_id}/rules")
    assert pub_resp.status_code == 200
    rule_ids = [r["id"] for r in pub_resp.json()]
    assert draft_rule_id not in rule_ids


def test_public_sources_endpoint_filters_non_current_sources() -> None:
    client = TestClient(app)
    admin_client, admin_headers = authenticated_client(role="admin")

    under_review_source_id = f"src-under-review-{uuid4().hex[:8]}"
    source_payload = {
        "id": under_review_source_id,
        "title": "Under review policy doc",
        "canonical_url": "https://example.com/under-review",
        "excerpt": "Preliminary unverified rewards structure.",
        "status": "under_review",
    }
    resp = admin_client.post("/api/v1/admin/sources", headers=admin_headers, json=source_payload)
    assert resp.status_code == 201

    # Public sources check
    sources_resp = client.get("/api/v1/sources")
    assert sources_resp.status_code == 200
    source_ids = [s["id"] for s in sources_resp.json()]
    assert under_review_source_id not in source_ids


def test_optimizer_validation_rejects_unowned_cards() -> None:
    user_client, user_headers = authenticated_client()

    # User creates a scenario
    sc_resp = user_client.post(
        "/api/v1/me/scenarios",
        headers=user_headers,
        json={
            "name": "Shopping Plan",
            "scenario_date": "2026-06-01",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "5000.00",
                }
            ],
        },
    )
    assert sc_resp.status_code == 201
    scenario_id = sc_resp.json()["id"]

    # Attempt to optimize without owning the card
    opt_resp = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": scenario_id,
            "card_variant_ids": ["synthetic-variant"],
        },
    )
    assert opt_resp.status_code == 422
    assert "not in user portfolio" in opt_resp.json()["detail"]


def test_optimizer_fixed_allocations_and_duplication() -> None:
    user_client, user_headers = authenticated_client()
    variant_id = "synthetic-variant"

    # Add card to user portfolio
    add_resp = user_client.post(
        f"/api/v1/me/cards?card_variant_id={variant_id}",
        headers=user_headers,
    )
    assert add_resp.status_code == 201

    # Create scenario with one fixed bucket and one non-fixed bucket
    sc_resp = user_client.post(
        "/api/v1/me/scenarios",
        headers=user_headers,
        json={
            "name": "Fixed allocation scenario",
            "scenario_date": "2026-06-01",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "2000.00",
                    "is_fixed": True,
                    "cap_knowledge_state": "known",
                    "cap_usage": "0.00",
                },
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "3000.00",
                    "is_fixed": False,
                    "cap_knowledge_state": "known",
                    "cap_usage": "0.00",
                },
            ],
        },
    )
    assert sc_resp.status_code == 201
    scenario = sc_resp.json()
    scenario_id = scenario["id"]
    spend1_id = scenario["spend"][0]["id"]
    spend2_id = scenario["spend"][1]["id"]

    # 1. Attempt optimizer before allocating baseline card to fixed bucket -> 422
    opt_resp = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": scenario_id,
            "card_variant_ids": [variant_id],
        },
    )
    assert opt_resp.status_code == 422
    assert "requires an assigned baseline card allocation" in opt_resp.json()["detail"]

    # 2. Persist allocations
    alloc_resp = user_client.put(
        f"/api/v1/me/scenarios/{scenario_id}/allocations",
        headers=user_headers,
        json=[
            {
                "spend_id": spend1_id,
                "card_variant_id": variant_id,
                "amount": "2000.00",
                "allocation_type": "baseline",
            },
            {
                "spend_id": spend2_id,
                "card_variant_id": variant_id,
                "amount": "3000.00",
                "allocation_type": "baseline",
            },
        ],
    )
    assert alloc_resp.status_code == 200

    # 3. Now run optimizer -> succeeds and preserves fixed card
    opt_success = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": scenario_id,
            "card_variant_ids": [variant_id],
        },
    )
    assert opt_success.status_code == 200
    res = opt_success.json()
    assert res["total_spend_preserved"] is True
    assert res["plan_status"] == "optimal"
    assert len(res["allocations"]) == 2
    assert res["allocations"][0]["proposed_card_variant_id"] == variant_id

    # 4. Duplicate scenario and verify allocations are preserved
    dup_resp = user_client.post(
        f"/api/v1/me/scenarios/{scenario_id}/duplicate",
        headers=user_headers,
    )
    assert dup_resp.status_code in {200, 201}
    duplicate = dup_resp.json()
    dup_id = duplicate["id"]
    assert len(duplicate["spend"]) == 2

    # Running optimizer on duplicated scenario succeeds directly because allocations were duplicated
    dup_opt = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": dup_id,
            "card_variant_ids": [variant_id],
        },
    )
    assert dup_opt.status_code == 200
    assert dup_opt.json()["plan_status"] == "optimal"


def test_optimizer_unknown_cap_state_discloses_uncertainty_and_bounds() -> None:
    user_client, user_headers = authenticated_client()
    variant_id = "synthetic-variant"

    user_client.post(f"/api/v1/me/cards?card_variant_id={variant_id}", headers=user_headers)

    # Spend with unknown prior cap usage on a capped card
    sc_resp = user_client.post(
        "/api/v1/me/scenarios",
        headers=user_headers,
        json={
            "name": "Unknown cap scenario",
            "scenario_date": "2026-06-01",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "10000.00",
                    "cap_knowledge_state": "unknown",
                }
            ],
        },
    )
    scenario_id = sc_resp.json()["id"]

    opt_resp = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": scenario_id,
            "card_variant_ids": [variant_id],
        },
    )
    assert opt_resp.status_code == 200
    res = opt_resp.json()
    assert res["has_cap_uncertainty"] is True
    assert res["plan_status"] == "uncertain"
    assert "conservative_proposed_value" in res
    assert Decimal(res["conservative_proposed_value"]) <= Decimal(res["proposed_value"])
    assert any("uncertainty" in w.lower() for w in res["warnings"])


def test_scenario_update_preserves_spend_ids_and_increments_revision() -> None:
    user_client, user_headers = authenticated_client()
    variant_id = "synthetic-variant"

    user_client.post(f"/api/v1/me/cards?card_variant_id={variant_id}", headers=user_headers)

    # 1. Create a multi-bucket scenario
    create_resp = user_client.post(
        "/api/v1/me/scenarios",
        headers=user_headers,
        json={
            "name": "Multi-bucket baseline",
            "scenario_date": "2026-06-01",
            "currency": "INR",
            "spend": [
                {
                    "category": "dining",
                    "channel": "pos_card",
                    "amount": "1500.00",
                    "cap_knowledge_state": "known",
                },
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "3000.00",
                    "cap_knowledge_state": "known",
                },
            ],
        },
    )
    assert create_resp.status_code in {200, 201}
    scenario = create_resp.json()
    scenario_id = scenario["id"]
    initial_revision = scenario["revision"]
    assert len(scenario["spend"]) == 2
    spend_0_id = scenario["spend"][0]["id"]
    spend_1_id = scenario["spend"][1]["id"]
    assert spend_0_id is not None
    assert spend_1_id is not None

    # 2. Update scenario preserving spend_0_id, modifying amount, and adding a third bucket
    patch_resp = user_client.patch(
        f"/api/v1/me/scenarios/{scenario_id}",
        headers=user_headers,
        json={
            "name": "Multi-bucket updated",
            "spend": [
                {
                    "id": spend_0_id,
                    "category": "dining",
                    "channel": "pos_card",
                    "amount": "2000.00",
                    "cap_knowledge_state": "known",
                },
                {
                    "id": spend_1_id,
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "3500.00",
                    "cap_knowledge_state": "known",
                },
                {
                    "category": "groceries",
                    "channel": "pos_card",
                    "amount": "1200.00",
                    "cap_knowledge_state": "known",
                },
            ],
        },
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["name"] == "Multi-bucket updated"
    assert updated["revision"] == initial_revision + 1
    assert len(updated["spend"]) == 3

    # Check preserved IDs
    updated_ids = {s["id"] for s in updated["spend"]}
    assert spend_0_id in updated_ids
    assert spend_1_id in updated_ids

    # Check modified amount
    spend_0_updated = next(s for s in updated["spend"] if s["id"] == spend_0_id)
    assert Decimal(spend_0_updated["amount"]) == Decimal("2000.00")

    # 3. Optimizer succeeds on the updated scenario
    opt_resp = user_client.post(
        "/api/v1/optimizer/run",
        headers=user_headers,
        json={
            "scenario_id": scenario_id,
            "card_variant_ids": [variant_id],
        },
    )
    assert opt_resp.status_code == 200
    res = opt_resp.json()
    assert res["search_mode"] == "exhaustive"
    assert res["is_heuristic"] is False


def test_optimizer_reports_heuristic_search_mode_when_combinations_exceed_threshold() -> None:
    from unittest.mock import patch

    user_client, user_headers = authenticated_client()
    variant_id = "synthetic-variant"
    user_client.post(f"/api/v1/me/cards?card_variant_id={variant_id}", headers=user_headers)

    sc_resp = user_client.post(
        "/api/v1/me/scenarios",
        headers=user_headers,
        json={
            "name": "Combinations test",
            "scenario_date": "2026-06-01",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "1000.00",
                    "cap_knowledge_state": "known",
                },
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "2000.00",
                    "cap_knowledge_state": "known",
                },
            ],
        },
    )
    scenario_id = sc_resp.json()["id"]

    # Patch COMBINATION_LIMIT to 0 so any combinations (>0) triggers greedy_heuristic
    with patch("app.domain.optimizer.COMBINATION_LIMIT", 0):
        opt_resp = user_client.post(
            "/api/v1/optimizer/run",
            headers=user_headers,
            json={
                "scenario_id": scenario_id,
                "card_variant_ids": [variant_id],
            },
        )
        assert opt_resp.status_code == 200
        res = opt_resp.json()
        assert res["search_mode"] == "greedy_heuristic"
        assert res["is_heuristic"] is True
        assert res["plan_status"] == "heuristic"
        assert any("heuristic" in w.lower() for w in res["warnings"])


def test_reminder_patch_and_export_lifecycle() -> None:
    user_client, user_headers = authenticated_client()

    # 1. Create reminder
    rem_resp = user_client.post(
        "/api/v1/reminders",
        headers=user_headers,
        json={"label": "Pay credit card bill", "due_at": "2026-11-05T12:00:00Z"},
    )
    assert rem_resp.status_code in {200, 201}
    reminder_id = rem_resp.json()["id"]

    # 2. Update reminder status and label
    patch_rem = user_client.patch(
        f"/api/v1/reminders/{reminder_id}",
        headers=user_headers,
        json={"label": "Pay bill immediately", "status": "completed"},
    )
    assert patch_rem.status_code == 200
    assert patch_rem.json()["label"] == "Pay bill immediately"
    assert patch_rem.json()["status"] == "completed"

    # 3. Create export
    exp_resp = user_client.post("/api/v1/exports", headers=user_headers)
    assert exp_resp.status_code in {200, 201}
    export_id = exp_resp.json()["id"]

    # 4. Fetch export
    get_exp = user_client.get(f"/api/v1/exports/{export_id}", headers=user_headers)
    assert get_exp.status_code == 200
    exp_data = get_exp.json()
    assert exp_data["id"] == export_id
    assert "data" in exp_data

    # 5. Delete export
    del_exp = user_client.delete(f"/api/v1/exports/{export_id}", headers=user_headers)
    assert del_exp.status_code == 204

    # 6. Verify 404 after deletion
    get_del = user_client.get(f"/api/v1/exports/{export_id}", headers=user_headers)
    assert get_del.status_code == 404

