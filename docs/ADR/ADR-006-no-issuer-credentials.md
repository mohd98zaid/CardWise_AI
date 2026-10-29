# ADR-006: No Issuer Credentials in MVP

- Status: accepted
- Date: 2026-10-26

## Context
Issuer credentials and payment credentials add unnecessary security risk to a comparison tool.

## Decision
Do not collect full card numbers, CVV, PIN, OTP, or issuer login credentials. Use manual portfolio selection and scenario inputs.

## Consequences
Less automation but substantially less sensitive-data exposure. Future integrations need separate consent, vendor, security, and legal review.
