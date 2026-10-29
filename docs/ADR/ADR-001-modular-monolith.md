# ADR-001: Modular Monolith

- Status: accepted
- Date: 2026-10-26

## Context
The initial product has related domains but no measured need for separate deployments.

## Decision
Use one backend deployment with strict module boundaries.

## Consequences
Simpler development and transactions. Avoid circular dependencies; extract services only when scale or reliability evidence justifies it.
