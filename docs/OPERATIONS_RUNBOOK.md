# Operations Runbook

## Routine checks
API latency/errors, database health, calculation statuses, pending rule reviews, stale/conflicting sources, AI citation failures, background jobs, backups and restore status.

## Incorrect rule
Identify affected version/time window; disable confident use if necessary; preserve evidence; draft correction; review/tests; publish new version or invalidate future use; identify affected calculations; refresh results; communicate material limitations; record prevention action.

## Security incident
Contain affected account/service, preserve evidence, rotate secrets, assess data impact, follow applicable notification requirements with qualified advice, restore safely, document root cause.

## AI incident
Disable assistant if needed while leaving calculator online. Preserve model/prompt/evidence versions, reproduce against evaluation data, correct retrieval/validation, never auto-edit rules from model output.

## Database incident
Follow tested restore/failover process. Validate manifest/rule consistency, authorization, audit data, and recovery point.

## Rollback
Stop rollout, restore compatible artifact, avoid destructive schema rollback without a tested migration, verify health/calculation/access isolation.
