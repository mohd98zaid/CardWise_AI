from app.ai.assistant import answer_from_sources
from app.db.models import Source


def test_assistant_abstains_without_domain_terms() -> None:
    result = answer_from_sources("hello there how are you doing today", [])
    assert result["abstained"] is True
    assert result["evidence_level"] == "insufficient_evidence"
    assert result["citations"] == []


def test_assistant_abstains_with_no_relevant_evidence() -> None:
    result = answer_from_sources(
        "What is the dining lounge cashback rate?",
        [
            Source(
                id="s1",
                title="Fuel Guide",
                canonical_url="https://example.com/fuel",
                excerpt="Only fuel transactions earn 1% waiver.",
                status="current",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is True
    assert result["evidence_level"] == "no_relevant_evidence"
    assert result["citations"] == []


def test_assistant_detects_stale_and_superseded_sources() -> None:
    result = answer_from_sources(
        "dining cashback rate",
        [
            Source(
                id="s-old",
                title="Old Dining Policy",
                canonical_url="https://example.com/old-dining",
                excerpt="Dining cashback was 10% under 2024 policy.",
                status="superseded",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is True
    assert result["evidence_level"] == "stale_evidence"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["status"] == "superseded"
    assert any("not current" in u.lower() for u in result["unknowns"])


def test_assistant_detects_conflicting_evidence() -> None:
    result = answer_from_sources(
        "utility bill cashback",
        [
            Source(
                id="s1",
                title="Exclusion document",
                canonical_url="https://example.com/s1",
                excerpt="Utility bill spend is excluded from all cashback.",
                status="current",
                rights_status="synthetic_only",
            ),
            Source(
                id="s2",
                title="Promotion document",
                canonical_url="https://example.com/s2",
                excerpt="Utility bill spend is eligible for 5% cashback.",
                status="current",
                rights_status="synthetic_only",
            ),
        ],
    )
    assert result["abstained"] is True
    assert result["evidence_level"] == "conflicting_evidence"
    assert len(result["citations"]) == 2
    assert any("contradictory" in str(result["answer"]).lower() for _ in [1])


def test_assistant_identifies_partial_evidence() -> None:
    # Query asks for multiple domain terms: dining, lounge, airport, fuel, cashback
    result = answer_from_sources(
        "What dining lounge airport fuel cashback benefits exist?",
        [
            Source(
                id="s-partial",
                title="Dining terms",
                canonical_url="https://example.com/dining",
                excerpt="Earn 5% dining cashback on weekend restaurant spends.",
                status="current",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is False
    assert result["evidence_level"] == "partial_evidence"
    assert any("partial" in u.lower() for u in result["unknowns"])
    assert result["citations"][0]["source_id"] == "s-partial"


def test_assistant_cites_current_matching_excerpt_with_synthetic_warning() -> None:
    result = answer_from_sources(
        "online shopping cashback",
        [
            Source(
                id="s-current",
                title="Cashback guide",
                canonical_url="https://example.com/cashback",
                excerpt="Online shopping cashback is 5% on partner platforms.",
                status="current",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is False
    assert result["evidence_level"] == "evidence_found"
    assert result["citations"][0]["source_id"] == "s-current"
    assert result["citations"][0]["url"] == "https://example.com/cashback"
    assert any("synthetic fixture" in u.lower() for u in result["unknowns"])


def test_assistant_handles_missing_canonical_url_gracefully() -> None:
    result = answer_from_sources(
        "online shopping cashback",
        [
            Source(
                id="s-no-url",
                title="Internal note",
                canonical_url="",
                excerpt="Online shopping cashback applies at 5%.",
                status="current",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is False
    assert result["citations"][0]["url"] is None
    assert result["citations"][0]["locator"] == ""
