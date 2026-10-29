# ADR-005: Full-Text Search Before Vector Search

- Status: accepted
- Date: 2026-10-26

## Context
Card terms include exact product names, rates, caps, exclusions, and section identifiers.

## Decision
Start with metadata-filtered full-text search. Add vector retrieval only if evaluation demonstrates a meaningful gain.

## Consequences
Simpler initial infrastructure; evaluation decides whether semantic retrieval is worth the complexity.
