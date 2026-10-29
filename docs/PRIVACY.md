# Privacy and Data Retention

## Principles
Collect minimum data. Explain optional fields. Never collect full card numbers, CVV, PIN, OTP, or issuer passwords. Do not train on user spending data by default. Do not send user data to a model provider without clear disclosure and an approved data policy. Use synthetic data in tests.

## Data classes
Account/profile, portfolio references, scenarios/calculations, uploaded imports, AI sessions, source content, audit records, logs, backups.

## User controls
Plan for export, scenario deletion, account deletion, and opt-out controls for optional assistant history/notifications.

## Deletion
Delete user-owned records/files according to policy. Document backup expiry and any audit retention exceptions. Do not promise instant removal from immutable backups if the system cannot provide it.

## Logging
Never log secrets, payment credentials, raw statements, or unnecessary transaction-level details.

## Compliance
Qualified review of applicable Indian privacy, consumer protection, financial services, retention, vendor, and source-licensing requirements is required before launch. This is not legal advice.
