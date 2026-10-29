# ADR-003: Decimal Arithmetic and Manifests

- Status: accepted
- Date: 2026-10-26

## Context
Floating-point can introduce money errors and mutable rules undermine reproducibility.

## Decision
Use Decimal/numeric and persist input snapshots, rule manifest, engine version, and trace.

## Consequences
Results are auditable; rounding semantics must be explicit and tested.
