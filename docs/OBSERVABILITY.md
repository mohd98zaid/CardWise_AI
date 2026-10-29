# Observability

## Logs
Include timestamp, severity, request ID, operation, latency, error code, engine version, and manifest ID where relevant. Never log passwords/tokens, full card numbers, CVV/PIN/OTP, raw statements, or unnecessary financial detail.

## Metrics
Request count/latency/errors, calculation status distribution, `needs_input`/`partial`/`cannot_calculate` rates, rules awaiting review, stale-source count, publication failures, citation validation failures, empty retrieval rate, job retries/lag, database saturation.

## Health
Liveness, readiness, database check, worker heartbeat if used. AI health is separate; AI outage must not make the core calculator unavailable.

## Alerts
Set thresholds after baseline measurements. Prioritize security incidents, 5xx spikes, database outage, failed backups, critical rule conflicts, and calculation regressions.

## Privacy
Use aggregated metrics; never use transaction descriptions or raw user inputs as metric labels.
