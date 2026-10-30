import re
from dataclasses import asdict, dataclass

from app.db.models import Source


@dataclass(frozen=True)
class Citation:
    source_id: str
    title: str
    url: str | None
    locator: str
    source_type: str
    status: str
    rights_status: str
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        # Omit None url so frontend receives null or undefined cleanly
        return d


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
    "This is a local lexical evidence lookup (alpha). Answers are extracted directly from "
    "locally indexed source excerpts and may be incomplete or synthetic. They do not constitute "
    "financial advice, calculated guarantees, or official issuer statements."
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


def _build_citation(source: Source) -> dict[str, object]:
    url = (
        source.canonical_url.strip()
        if source.canonical_url and source.canonical_url.strip()
        else None
    )
    return Citation(
        source_id=source.id,
        title=source.title or "Untitled Source",
        url=url,
        locator=url or "",
        source_type=getattr(source, "source_type", "synthetic"),
        status=getattr(source, "status", "under_review"),
        rights_status=getattr(source, "rights_status", "synthetic_only"),
        excerpt=source.excerpt or "",
    ).to_dict()


def answer_from_sources(question: str, sources: list[Source]) -> dict[str, object]:
    """Provide a deterministic evidence-grounded response distinguishing confidence levels.

    Distinguishes:
    - evidence_found: Valid lexical match in current sources.
    - partial_evidence: Partial match or some question terms not covered.
    - conflicting_evidence: Contradictory inclusion/exclusion detected.
    - stale_evidence: Matches exist only in stale/superseded sources.
    - no_relevant_evidence: No sources matched.
    - insufficient_evidence: Question lacks domain grounding or is too brief.
    """
    question_terms = _terms(question)

    # 1. Minimum domain-term criteria: must contain card or rewards domain terms
    has_domain_terms = bool(question_terms & DOMAIN_TERMS)
    if not question_terms or not has_domain_terms:
        return {
            "answer": (
                "I could not find card or rewards domain terms in your question "
                "to match verified sources."
            ),
            "abstained": True,
            "evidence_level": "insufficient_evidence",
            "citations": [],
            "unknowns": ["Query did not meet minimum domain-term grounding criteria."],
            "model_version": "lexical-evidence-only-0.3.0",
            "prompt_version": "evidence-only-0.3.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    # 2. Score sources
    current_scored: list[tuple[int, set[str], Source]] = []
    stale_scored: list[tuple[int, set[str], Source]] = []

    for source in sources:
        if not source.excerpt:
            continue
        source_terms = _terms(f"{source.title} {source.excerpt}")
        matched = question_terms & source_terms
        if matched and (matched & DOMAIN_TERMS or len(matched) >= 2):
            if source.status == "current":
                current_scored.append((len(matched), matched, source))
            else:
                stale_scored.append((len(matched), matched, source))

    current_scored.sort(key=lambda pair: pair[0], reverse=True)
    stale_scored.sort(key=lambda pair: pair[0], reverse=True)

    # 3. Check if only stale/superseded sources matched
    if not current_scored and stale_scored:
        stale_matches = [s for _, _, s in stale_scored]
        citations = [_build_citation(s) for s in stale_matches[:2]]
        return {
            "answer": (
                "The available sources matching your query are stale, superseded, or under review. "
                "No current active source excerpt supports an answer."
            ),
            "abstained": True,
            "evidence_level": "stale_evidence",
            "citations": citations,
            "unknowns": [
                "Matching source(s) are not current. Current terms could not be established."
            ],
            "model_version": "lexical-evidence-only-0.3.0",
            "prompt_version": "evidence-only-0.3.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    # 4. Check if no sources matched at all
    if not current_scored:
        return {
            "answer": "I could not find relevant evidence in the current indexed sources.",
            "abstained": True,
            "evidence_level": "no_relevant_evidence",
            "citations": [],
            "unknowns": ["No current source excerpt supports the requested query."],
            "model_version": "lexical-evidence-only-0.3.0",
            "prompt_version": "evidence-only-0.3.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    current_matches = [s for _, _, s in current_scored]

    # 5. Check contradiction
    if _detect_contradiction(current_matches):
        return {
            "answer": (
                "Sources contain conflicting or contradictory evidence regarding this query. "
                "Please consult official issuer terms directly."
            ),
            "abstained": True,
            "evidence_level": "conflicting_evidence",
            "citations": [_build_citation(s) for s in current_matches[:2]],
            "unknowns": ["Contradictory evidence detected among top-matching sources."],
            "model_version": "lexical-evidence-only-0.3.0",
            "prompt_version": "evidence-only-0.3.0",
            "assistant_type": "lexical_lookup_alpha",
            "disclaimer": DISCLAIMER,
        }

    best_len, best_matched, top_source = current_scored[0]
    unmatched_query_terms = (question_terms & DOMAIN_TERMS) - best_matched

    unknowns: list[str] = []
    if getattr(top_source, "rights_status", "") == "synthetic_only" or getattr(
        top_source, "source_type", ""
    ) == "synthetic":
        unknowns.append(
            "Evidence is derived from a synthetic fixture and does not establish "
            "a real issuer term."
        )
    else:
        unknowns.append(
            "Evidence is extracted from local indexed text and has not been independently verified."
        )

    # Distinguish partial evidence vs evidence found
    if unmatched_query_terms and len(unmatched_query_terms) >= 2:
        evidence_level = "partial_evidence"
        missing_terms_str = ", ".join(sorted(unmatched_query_terms))
        unknowns.append(f"Partial coverage: source excerpt does not mention {missing_terms_str}.")
        answer_text = (
            f"The available source partially addresses your query: {top_source.excerpt}"
        )
    else:
        evidence_level = "evidence_found"
        answer_text = f"The available source states: {top_source.excerpt}"

    return {
        "answer": answer_text,
        "abstained": False,
        "evidence_level": evidence_level,
        "citations": [_build_citation(top_source)],
        "unknowns": unknowns,
        "model_version": "lexical-evidence-only-0.3.0",
        "prompt_version": "evidence-only-0.3.0",
        "assistant_type": "lexical_lookup_alpha",
        "disclaimer": DISCLAIMER,
    }
