# Operations and recovery contract

This is the required runbook design. It is not evidence of an implemented or deployed service.

## Ownership and monitoring

config/retention.yaml owns data/backup retention and recovery objectives; config/observability.yaml owns destinations and signal pipelines; config/alerts.yaml owns thresholds and verified Azure Monitor Action Group/operational owner references.
Terraform provisions monitoring workspaces, Application Insights, metric/log collection, alerts/action-group references and protection policies. Use supported generally available ingestion: Python Azure Monitor OpenTelemetry distro for app traces/metrics; Azure Monitor Agent for redacted structured stdout logs; managed Prometheus scrapes broker/collector infrastructure metrics.
Do not assume preview-only native OTLP ingestion is production qualified. Local Collector debug output proves local signal creation only. Use one SDK/exporter per signal; avoid duplicate instrumentation.
Retain trace/log data 30 days; retain metrics for at least 90 days using the actual supported managed-service policy. Record effective retention/cost without promising unsupported deletion controls.
Dashboards in Azure Monitor Workbooks cover queue age, throughput, retries/redelivery, failures, numeric recommendation coverage, provider latency, input age, tokens, reserved/actual spend, storage and backup health. Never use user/analysis IDs as metric labels.
Smoke creates one identifiable safe test event and verifies its trace/log/metric and Action Group test notification. Use verified recipients already designated for operations; do not invent addresses or silently send arbitrary test messages.
If queue age is high, check broker quorum, worker capacity, provider quotas and failed tasks before scaling. Replay dead letters only with ownership/idempotency checks. If budgets or evidence fail, preserve results and report degraded explanations/evidence coverage.

## Backup and retention

- PostgreSQL Flexible Server: 35-day PITR, private access and a verified restore point; Azure owns scheduled managed backups.
- Evidence: Azure Backup vaulted Blob protection, daily recovery points retained 35 days, plus Blob versioning/30-day soft delete. Terraform backup.tf owns the vault/policy/protection identities; verify support for the chosen region, account, network and restore destination.
- Monitor the age of the latest completed recoverable point, not just the configured schedule. Daily scheduling alone does not prove RPO <=24h; a missed/late recovery point blocks the backup gate.
- Azure ZRS, Blob soft delete and versioning do not independently protect against every account-level failure. Verify vaulted restore separately.
- Retain analysis records/current evidence 365 days unless a verified hold applies. Daily cleanup may delete only owned expired objects/records, preserves referenced evidence, and logs counts without content.
- Do not purge a blob while retained database records still reference it. Versioned evidence remains immutable during an analysis's retention period.
- Operational owner and alert destination are required before production promotion.

## Recovery: scripts/verify.sh --suite recovery

1. Authorize an isolated staging restore run with fresh resources and no production/shared-data mutation. Record source environment, latest successful backup IDs/times, object inventory/hash manifest, database recovery point and test incident time.
2. Restore PostgreSQL to a new private server using verified Azure restore operations. Restore Blob backups to a new isolated account/container using the supported vaulted workflow; never overwrite active evidence.
3. Compute RPO from the newest verified recoverable state relative to incident time. Compute RTO from start of the recovery procedure to passing functional verification; include restore, reconciliation and redeployment time.
4. Reconcile every restored record with its evidence object/hash/version. Some service restore operations change version IDs; retain original lineage and record the verified restored mapping instead of fabricating IDs.
5. Choose a consistent recovery cut. Mark records newer than that cut unavailable/incomplete and resume or republish only idempotent work from PostgreSQL/outbox; explicitly report lost/unrecoverable coverage. Never serve a report with missing/mismatched evidence as valid.
6. Recreate RabbitMQ topology from reviewed declarations if needed; republish committed work from the outbox. Test worker loss/redelivery without duplicate business effects.
7. Deploy the qualified immutable release and compatible schema against restored data; run all six tools and integrity/ownership checks. Require RPO <=24h, RTO <=4h and complete accounting.
8. Record JUnit/JSON, backup IDs, timestamps, counts, restored hash mappings and failures. Remove only run-owned disposable resources after evidence retention; do not delete backup sources.
9. Run at least every 30 days in staging and after material recovery changes. Staging load/recovery must never target production.

## Application rollback and first installation

rollback.sh verifies the target Helm revision, image/chart signatures, configuration and database compatibility, then restores that exact bundle and reruns smoke. Keep data/PVCs and operators intact.
Do not reverse a database migration automatically. Use expand/contract and restore only under the isolated recovery procedure.
For first-install failures there is no previous app revision: retain diagnostics/data, correct the fault, redeploy the qualified bundle and verify functionality without declaring a nonexistent rollback successful.
