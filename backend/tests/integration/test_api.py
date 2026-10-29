from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.ratelimit import reset_rate_limits
from app.main import app


def authenticated_client(email: str | None = None) -> tuple[TestClient, dict[str, str]]:
    reset_rate_limits()
    client = TestClient(app)
    address = email or f"{uuid4().hex}@example.com"
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


def test_user_can_create_scenario_and_calculate() -> None:
    client, headers = authenticated_client()
    scenario = client.post(
        "/api/v1/me/scenarios",
        headers=headers,
        json={
            "name": "Online plan",
            "scenario_date": "2026-01-15",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "8000.00",
                    "cap_knowledge_state": "known",
                    "cap_usage": "0.00",
                }
            ],
        },
    )
    assert scenario.status_code == 201
    scenario_id = scenario.json()["id"]
    result = client.post(
        f"/api/v1/scenarios/{scenario_id}/calculate",
        headers=headers,
        json={"card_variant_ids": ["synthetic-variant"]},
    )
    assert result.status_code == 200
    assert result.json()["results"][0]["estimated_net_value"] == "400.00"


def test_scenarios_are_isolated_between_users() -> None:
    owner, owner_headers = authenticated_client()
    scenario = owner.post(
        "/api/v1/me/scenarios",
        headers=owner_headers,
        json={"name": "Private", "scenario_date": "2026-01-15", "currency": "INR"},
    )
    other, other_headers = authenticated_client()
    response = other.get(f"/api/v1/me/scenarios/{scenario.json()['id']}", headers=other_headers)
    assert response.status_code == 404


def test_rule_publication_requires_review_and_records_admin_action() -> None:
    client, headers = authenticated_client("admin@cardwise.local")
    review = client.post(
        "/api/v1/admin/rules/synthetic-online-cashback-v1/review?decision=approved",
        headers=headers,
    )
    assert review.status_code == 200
    published = client.post(
        "/api/v1/admin/rules/synthetic-online-cashback-v1/publish",
        headers=headers,
    )
    assert published.status_code == 200
    # Synthetic fixtures remain visibly synthetic even when published in test workflows
    assert published.json()["verification_status"] == "synthetic"


def test_catalogue_taxonomy_portfolio_and_persisted_trace() -> None:
    client, headers = authenticated_client()
    assert client.get("/api/v1/catalogue/cards").status_code == 200
    assert client.get("/api/v1/taxonomy/categories").json()
    assert client.get("/api/v1/taxonomy/channels").json()
    added = client.post(
        "/api/v1/me/cards?card_variant_id=synthetic-variant",
        headers=headers,
    )
    assert added.status_code == 201
    card_id = added.json()["id"]
    updated = client.patch(
        f"/api/v1/me/cards/{card_id}",
        headers=headers,
        json={"nickname": "Demo card", "status": "active"},
    )
    assert updated.status_code == 200
    scenario = client.post(
        "/api/v1/me/scenarios",
        headers=headers,
        json={
            "name": "Trace plan",
            "scenario_date": "2026-01-15",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "8000.00",
                    "cap_usage": "0.00",
                    "cap_knowledge_state": "known",
                }
            ],
        },
    )
    result = client.post(
        f"/api/v1/scenarios/{scenario.json()['id']}/calculate",
        headers=headers,
        json={"card_variant_ids": ["synthetic-variant"]},
    )
    assert result.status_code == 200
    trace = client.get(
        f"/api/v1/calculations/{result.json()['calculation_run_id']}/trace",
        headers=headers,
    )
    assert trace.status_code == 200
    assert trace.json()["trace"]
    runs = client.post(
        "/api/v1/calculations/compare",
        headers=headers,
        json={"scenario_id": scenario.json()["id"], "card_variant_ids": ["synthetic-variant"]},
    )
    assert runs.status_code == 200
    assert client.delete(f"/api/v1/me/cards/{card_id}", headers=headers).status_code == 204


def test_points_estimate_requires_or_uses_explicit_valuation() -> None:
    client = TestClient(app)
    unknown = client.post(
        "/api/v1/calculations/estimate",
        json={
            "card_variant_id": "synthetic-points-variant",
            "amount": "1000.00",
            "currency": "INR",
            "scenario_date": "2026-01-15",
            "category": "travel",
            "channel": "online_card",
        },
    )
    assert unknown.status_code == 200
    assert unknown.json()["status"] == "needs_input"
    valued = client.post(
        "/api/v1/calculations/estimate",
        json={
            "card_variant_id": "synthetic-points-variant",
            "amount": "1000.00",
            "currency": "INR",
            "scenario_date": "2026-01-15",
            "category": "travel",
            "channel": "online_card",
            "point_value_per_point": "0.25",
        },
    )
    assert valued.status_code == 200
    assert valued.json()["estimated_net_value"] == "5.00"


def test_logout_invalidates_token() -> None:
    client, headers = authenticated_client()
    me_resp = client.get("/api/v1/me", headers=headers)
    assert me_resp.status_code == 200

    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 204

    after_resp = client.get("/api/v1/me", headers=headers)
    assert after_resp.status_code == 401


def test_cross_user_calculation_isolation() -> None:
    user_a, headers_a = authenticated_client()
    user_b, headers_b = authenticated_client()

    scenario = user_a.post(
        "/api/v1/me/scenarios",
        headers=headers_a,
        json={
            "name": "Secret Plan",
            "scenario_date": "2026-01-15",
            "currency": "INR",
            "spend": [
                {
                    "category": "online_shopping",
                    "channel": "online_card",
                    "amount": "5000.00",
                    "cap_knowledge_state": "known",
                    "cap_usage": "0.00",
                }
            ],
        },
    )
    assert scenario.status_code == 201
    calc = user_a.post(
        f"/api/v1/scenarios/{scenario.json()['id']}/calculate",
        headers=headers_a,
        json={"card_variant_ids": ["synthetic-variant"]},
    )
    assert calc.status_code == 200
    calc_run_id = calc.json()["calculation_run_id"]

    # User B attempts to access calculation run and trace of User A
    leak_calc = user_b.get(f"/api/v1/calculations/{calc_run_id}", headers=headers_b)
    assert leak_calc.status_code == 404

    leak_trace = user_b.get(f"/api/v1/calculations/{calc_run_id}/trace", headers=headers_b)
    assert leak_trace.status_code == 404


def test_cross_user_export_isolation() -> None:
    user_a, headers_a = authenticated_client()
    user_b, headers_b = authenticated_client()

    export_res = user_a.post("/api/v1/exports", headers=headers_a)
    assert export_res.status_code == 201
    export_id = export_res.json()["id"]

    # User B attempts to fetch User A's export
    leak = user_b.get(f"/api/v1/exports/{export_id}", headers=headers_b)
    assert leak.status_code == 404


def test_user_account_deletion_cleans_up() -> None:
    client, headers = authenticated_client()
    me_resp = client.get("/api/v1/me", headers=headers)
    assert me_resp.status_code == 200

    del_resp = client.delete("/api/v1/me", headers=headers)
    assert del_resp.status_code == 204

    # Deleted account's token should no longer work
    check = client.get("/api/v1/me", headers=headers)
    assert check.status_code == 401


def test_health_and_readiness_endpoints() -> None:
    client = TestClient(app)
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    ready_resp = client.get("/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"
    assert ready_resp.json()["database"] == "connected"
