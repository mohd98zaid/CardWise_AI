import re
from dataclasses import dataclass

from app.db.models import Source


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    locator: str
    status: str


STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only",
    "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "shouldn't", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "were", "weren't", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "won't", "would", "wouldn't", "you",
    "your", "yours", "yourself", "yourselves", "tell", "card", "cards", "give", "much", "many",
}

DOMAIN_TERMS = {
    "cashback", "reward", "rewards", "points", "multiplier", "cap", "lounge", "dining",
    "travel", "groceries", "utility", "utilities", "fuel", "surcharge", "milestone",
    "waiver", "fee", "annual", "quarterly", "monthly", "exclusion", "excluded", "limit",
    "rate", "hdfc", "axis", "icici", "sbi", "amex", "infinia", "regalia", "magnus",
    "atlas", "supercash", "aeroplan", "voucher", "redemption", "online", "offline",
    "spend", "spending", "benefit", "benefits", "eligibility",
}

DISCLAIMER = (
    "This is an evidence-grounded lexical lookup alpha tool. It retrieves indexed source excerpts "
    "and does not calculate rewards or override authoritative calculation engine rules."
)


def _terms(text: str) -> set[str]:
    raw = {term for term in re.findall(r"[a-z0-9_]+", text.casefold()) if len(term) > 2}
    return raw - STOPWORDS


def _detect_contradiction(candidates: list[Source]) -> bool:
    """Detect if top candidate excerpts express conflicting eligibility or exclusion claims."""
    if len(candidates) < 2:
        return False
    top_excerpts = [s.excerpt.casefold() for s in candidates[:3]]
    exclusion_markers = [
        "not eligible", "excluded", "exclusion", "no reward", "no cashback", "0% cashback",
    ]
    inclusion_markers = [
        "eligible for", "earns", "cashback of", "reward points on", "included", "applies",
    ]
    has_exclusion = any(any(k in exc for k in exclusion_markers) for exc in top_excerpts)
    has_inclusion = any(any(k in exc for k in inclusion_markers) for exc in top_excerpts)
    return has_exclusion and has_inclusion


def answer_from_sources(question: str, sources: list[Source]) -> dict[str, object]:
    """Provide a deterministic evidence-only answer when lexical evidence supports it."""
    question_terms = _terms(question)

    # Require non-empty question terms and domain-relevant keyword overlap
    if not question_terms or not (question_terms & DOMAIN_TERMS or len(question_terms) >= 2):
        return {
            "answer": (
                "I could not find sufficient card or rewards domain terms in your question "
                "to search verified sources."
            ),
            "abstained": True,
            "citations": [],
            "unknowns": ["Query did not meet minimum domain-term grounding criteria."],
            "model_version": "lexical-evidence-only-0.2.0",
            "prompt_version": "evidence-only-0.2.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    scored: list[tuple[int, Source]] = []
    for source in sources:
        if source.status != "current" or not source.excerpt:
            continue
        source_terms = _terms(f"{source.title} {source.excerpt}")
        matched = question_terms & source_terms
        if matched and (matched & DOMAIN_TERMS or len(matched) >= 2):
            scored.append((len(matched), source))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    matches = [s for _, s in scored]

    if not matches:
        return {
            "answer": "I could not verify this from the available sources.",
            "abstained": True,
            "citations": [],
            "unknowns": ["No current source excerpt supports the requested claim."],
            "model_version": "lexical-evidence-only-0.2.0",
            "prompt_version": "evidence-only-0.2.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    if _detect_contradiction(matches):
        return {
            "answer": (
                "Sources contain conflicting or contradictory evidence regarding this query. "
                "Please consult official issuer terms directly."
            ),
            "abstained": True,
            "citations": [
                Citation(s.id, s.title, s.canonical_url, s.status).__dict__ for s in matches[:2]
            ],
            "unknowns": ["Contradictory evidence detected among top-matching sources."],
            "model_version": "lexical-evidence-only-0.2.0",
            "prompt_version": "evidence-only-0.2.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    source = matches[0]
    citation = Citation(source.id, source.title, source.canonical_url, source.status)
    return {
        "answer": f"The available source says: {source.excerpt}",
        "abstained": False,
        "citations": [citation.__dict__],
        "unknowns": ["This evidence is synthetic and does not establish a real issuer term."],
        "model_version": "lexical-evidence-only-0.2.0",
        "prompt_version": "evidence-only-0.2.0",
        "assistant_type": "lexical_lookup_alpha",
        "disclaimer": DISCLAIMER,
    }
