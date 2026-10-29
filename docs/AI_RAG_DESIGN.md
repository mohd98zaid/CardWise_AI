# AI and RAG Design

## Scope
AI explains source evidence and may draft candidate rules for human review. It is not the rules database, calculator, reviewer, or publisher.

## Ingestion/retrieval
Ingest only permitted sources; preserve title, URL/document ID, publisher, dates, version, hash, and page/heading locators. Chunk by logical sections with metadata. Start with full-text search; add embeddings only if evaluation supports it. Filter by issuer and exact variant. Retrieve contradictory evidence where relevant.

## Answer contract
Separate source statement, plain-language interpretation, scenario effect, unknowns/assumptions, and citations/dates. Cite every material benefit claim. Ask for clarification on ambiguous variants. Abstain if evidence is insufficient.

## Prompt injection
Retrieved content is untrusted data, not instructions. It cannot change system policy or tool permissions. User sessions have read-only tools. Never execute source text as code. Validate inputs/outputs and test adversarial documents.

## Citation validation
Check evidence IDs, retrieval membership, card relevance, source dates/status, and claim support. Semantic entailment needs evaluation/human review.

## Evaluation set
Include direct/ambiguous variant questions, caps, exclusions, stale/conflicting sources, no-answer questions, prompt injection, unknown cap usage, and attempts to bypass calculator. Track retrieval recall, citation correctness, unsupported claims, abstention, completeness, latency, cost, and privacy leakage.

## Fallback
AI outage must not block catalogue or calculations. Never fall back to ungrounded model knowledge. Record model, prompt, and evaluation dataset versions.
