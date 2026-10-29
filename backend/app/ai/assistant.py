import re
from dataclasses import dataclass

from app.db.models import Source


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    locator: str
    status: str


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9_]+", text.casefold()) if len(term) > 2}


def answer_from_sources(question: str, sources: list[Source]) -> dict[str, object]:
    """Provide a deterministic evidence-only answer when lexical evidence supports it."""
    question_terms = _terms(question)
    ranked = sorted(
        sources,
        key=lambda source: len(question_terms & _terms(f"{source.title} {source.excerpt}")),
        reverse=True,
    )
    matches = [
        source for source in ranked if question_terms & _terms(f"{source.title} {source.excerpt}")
    ]
    if not matches or matches[0].status != "current":
        return {
            "answer": "I could not verify this from the available sources.",
            "abstained": True,
            "citations": [],
            "unknowns": ["No current source excerpt supports the requested claim."],
            "model_version": "lexical-evidence-only-0.1.0",
            "prompt_version": "evidence-only-0.1.0",
        }
    source = matches[0]
    citation = Citation(source.id, source.title, source.canonical_url, source.status)
    return {
        "answer": f"The available source says: {source.excerpt}",
        "abstained": False,
        "citations": [citation.__dict__],
        "unknowns": ["This evidence is synthetic and does not establish a real issuer term."],
        "model_version": "lexical-evidence-only-0.1.0",
        "prompt_version": "evidence-only-0.1.0",
    }
