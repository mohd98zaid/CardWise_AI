# API Specification

Prefix endpoints with `/api/v1`. Use Pydantic request/response models. Every private endpoint enforces authentication and ownership server-side.

## Auth/profile
`POST /auth/register`, `/auth/login`, `/auth/logout`, optional password-reset endpoints; `GET /me`; `PATCH /me/preferences`; `DELETE /me`.

## Catalogue
`GET /issuers`, `/cards`, `/cards/{id}`, `/card-variants/{id}`, `/card-variants/{id}/rules`, `/sources`, `/history`. Never expose drafts to ordinary users.

## Portfolio
`GET/POST /me/cards`; `PATCH/DELETE /me/cards/{id}`.

## Scenarios
`GET/POST /me/scenarios`; `GET/PATCH/DELETE /me/scenarios/{id}`; `POST /me/scenarios/{id}/duplicate`; `PUT /me/scenarios/{id}/spend`; `PUT /me/scenarios/{id}/allocations`.

## Calculation
`POST /calculations/estimate`, `/calculations/compare`, `/scenarios/{id}/calculate`; `GET /calculations/{id}` and `/calculations/{id}/trace`. Client reward values are never authoritative.

## Optimizer
`POST /optimizer/run`; `GET /optimizer/runs/{id}` and `/trace`.

## Assistant
`POST /assistant/ask`; session list/read/delete endpoints. Return answer, citations, dates, uncertainty, model and prompt versions. Assistant cannot publish rules.

## Admin
Source/rule create/update/validate/review/approve/reject/publish endpoints; review queue and audit event reads. Require roles and audit logs.

## Reminders/exports
Reminder CRUD; export create/status/delete. Exports expire.

## Errors
Consistent fields: `code`, `message`, `request_id`, optional `field_errors`, `retryable`, and documentation reference. Do not expose stack traces, secrets, SQL errors, or internal paths.
