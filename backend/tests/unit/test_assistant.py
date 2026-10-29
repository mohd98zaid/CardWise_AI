from app.ai.assistant import answer_from_sources
from app.db.models import Source


def test_assistant_abstains_without_current_evidence() -> None:
    result = answer_from_sources(
        "What is the travel benefit?",
        [
            Source(
                id="s",
                title="Synthetic",
                canonical_url="synthetic://s",
                excerpt="Online shopping fixture",
                status="under_review",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is True
    assert result["citations"] == []


def test_assistant_cites_a_current_matching_excerpt() -> None:
    result = answer_from_sources(
        "online cashback",
        [
            Source(
                id="s",
                title="Cashback guide",
                canonical_url="synthetic://s",
                excerpt="Online cashback applies in this fictional fixture",
                status="current",
                rights_status="synthetic_only",
            )
        ],
    )
    assert result["abstained"] is False
    assert result["citations"][0]["source_id"] == "s"  # type: ignore[index]
