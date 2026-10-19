# Execution contract

This file specifies the implementation required by AGENTS.md. Operational scripts remain blocked until implemented and verified.

## Required source artifacts

Brace notation lists separate generated files. Existing provider assets must be discovered and reused.

| Path | Owner and purpose |
|---|---|
| `src/auction_assistant/{api,mcp_server,services,graph,workers,valuation,config}.py` | Interfaces, services, graph, jobs, valuation and configuration. |
| `src/auction_assistant/adapters/{iarremate,historical_sales,artists,blob_storage}.py` | Scraper/API adapters and the Azure Blob client. |
| `migrations/env.py`, `migrations/versions/`, `alembic.ini` | Alembic migrations. |
| `pyproject.toml`, `uv.lock`, `.tool-versions`, `Dockerfile`, `compose.yaml`, `compose.test.yaml` | Locked builds and runtime; isolated test services. |
| `config/environments/{local,staging,production}.yaml`, `config/environment.schema.json` | Verified identities, locations, secret references, limits and schema; no secrets. |
| `config/{auth,models,runtime,valuation-policy,observability,retention,verification,alerts}.yaml`, `config/schemas/` | Versioned policy/defaults and per-file JSON Schemas; environment files supply verified references. |
| `tests/{unit,contracts,integration,regression,evaluation,acceptance}/` | Test suites defined in section 7. |
| `scripts/lib/common.sh`, scripts listed in section 1, `Makefile` | Shared safeguards, execution implementations and command interface. |
| `docs/{integrations,execution,operations,storage,platform,security,valuation}.md` | Integration, execution, platform, security, valuation and recovery contracts. |

## Required Terraform and Helm artifacts

| Artifact | Required contents and owner |
|---|---|
| `infra/terraform/bootstrap/` | Dedicated Azure Blob `azurerm` state backend, Entra/OIDC access, native locking and reviewed migration. |
| `infra/terraform/modules/platform/` | AKS, ACR, identities, PostgreSQL Flexible Server, networking, Key Vault, Azure OpenAI, monitoring and backups. `storage.tf` owns Blob resources. |
| `infra/terraform/environments/{staging,production}/` | Each root contains `main.tf`, `versions.tf`, `backend.tf`, `variables.tf`, `outputs.tf`, `.terraform.lock.hcl`, nonsecret `backend.hcl`. |
| `infra/policy/{terraform,kubernetes}.rego` | Enforce exposure, encryption, privilege and destructive-change rules. |
| `deploy/helm/auction-platform/{Chart.yaml,Chart.lock,values.yaml,values-staging.yaml,values-production.yaml}` | RabbitMQ cluster, configuration and telemetry; separate pinned controller releases per `docs/platform.md`. |
| `deploy/helm/auction-assistant/{Chart.yaml,values.yaml,values.schema.json,values-staging.yaml,values-production.yaml}` | Application release and validated environment values. |
| `deploy/helm/auction-assistant/templates/` | `api-deployment.yaml`, `worker-deployment.yaml`, `service.yaml`, `gateway.yaml`, `httproute.yaml`, `certificate.yaml`, `secretproviderclass.yaml`, `scaledobject.yaml`, `triggerauthentication.yaml`, `serviceaccount.yaml`, `networkpolicy.yaml`, `hpa.yaml`, `pdb.yaml`. |
| `deploy/helm/auction-migrations/{Chart.yaml,values.yaml,templates/job.yaml}` | Migration release: same image digest and exclusive database lock. |
| `deploy/helm/auction-platform/templates/otel-collector.yaml` | Collector pipelines; load `config/alerts.yaml` through the monitoring integration. |
| `.github/workflows/{ci,build,infra,release}.yml` | Checks; build and publish; protected plan and apply; serialized deployment and verification. |

## Operation deadlines

Checks/build: 30m; Terraform: 60m; each platform controller/release: 20m; migrations/app: 10m each; smoke: 15m; load: 25m including analysis completion; recovery: 4h. Bound retries within the applicable deadline; preserve diagnostics on timeout. An analysis has a separate 900s deadline from durable submission, including queue time.

## Source ownership and entry points

- Makefile forwards ENV, RUN_DIR, RELEASE, PLAN_MANIFEST, PHASE, SUITE, TEST_PATH, QUALIFICATION_MANIFEST and RELEASE_REVISION explicitly to the named scripts. Scripts validate arguments, not shell-evaluated configuration.
- scripts/lib/common.sh enforces input schemas, fresh run IDs, identity/hash checks, authorization, prerequisites, redaction and append-only evidence.
- scripts/validate.sh validates every config file against config/schemas/<basename>.schema.json; environment files use config/environment.schema.json. Validate cross-file references, enum/range checks and production bans.
- Render from these sources; record source hashes and the effective-config hash in the release/deployment manifests. Do not duplicate policy constants in shell, application code or workflows.
- scripts/bootstrap.sh resolves compatible supported releases from official sources, pins tools/images/charts/actions/operators, generates locks and config schemas, then validates them before use. Subsequent runs verify locks without updating them.
- Never generate upstream hashes or version IDs from guesses. deploy/platform-sources.yaml is incomplete until verified pins are committed.
- test.sh owns five non-live suites; verify.sh owns live smoke, load, recovery and evidence-only qualification. No required suite may silently skip.

## Target prerequisites and evidence

| Target | Required behavior and evidence |
|---|---|
| `doctor` | `PHASE=preflight`: schema, verified identity/references, provider contracts and CI network reachability; runtime adds service probes. Permit absent not-yet-provisioned resources only during declared first provisioning. |
| `infra-bootstrap` | Require an authorized bootstrap plan; create/import only the state backend, protect local bootstrap state and verify migration/locking. See `docs/execution.md`. |
| `security` | Require `RELEASE`. Run pinned Gitleaks, Bandit, pip-audit, Trivy and Checkov; bind reports to the digest. Block high or critical findings except scoped, approved, expiring exceptions. |
| `local-up/down` | Up requires `RELEASE`: healthy dependencies → migrate → app/workers. Down preserves volumes. Record health or shutdown. |
| `configure-cluster` | Use scoped short-lived access; verify Azure identity, cluster, namespace and RBAC. |
| `deploy-dependencies` | Require `RELEASE` and reviewed values; install platform chart and verify quorum, storage and telemetry. |
| `migrate` | Require `RELEASE`, verified backups and schema compatibility. Run a unique migration release; record Job success, Alembic revision and logs. |
| `deploy` | Require `RELEASE` and verified package, digest and values; record readiness, manifest and Helm revision. |
| `rollback` | Require `RELEASE_REVISION` and schema compatibility; restore it and verify smoke. |

## Backend bootstrap: scripts/infra.sh --action bootstrap

make infra-bootstrap uses infra/terraform/bootstrap/ only. It must not create application infrastructure.
If the dedicated state account/container already exists, inventory/import it; never replace it to complete bootstrap. Initial bootstrap requires an already authorized connected workstation/runner with access to the management and private data planes; fail with that precise connectivity blocker if it is unavailable.

1. Confirm ENV, Azure tenant/subscription, backend ownership, approved bootstrap plan and network access. Use Entra/OIDC, not account keys.
2. Initialize the isolated bootstrap root with protected local state under .private/bootstrap/<env>/. Never use a circular backend dependency.
3. Save/authorize the bootstrap plan with the same plan/hash rules as infrastructure apply, then apply precisely that plan.
4. Require StorageV2 dedicated state account, private Blob access/DNS, encryption, versioning, 30-day soft delete and restricted container RBAC. Use separate staging/production state keys. No application identity can read state.
5. Export nonsecret backend settings into reviewed backend.hcl; enable use_azuread_auth and CI OIDC. Native Blob leases provide locking.
6. Back up local bootstrap state, migrate it to a separate bootstrap state key only after authorization, verify state parity and lock contention, then protect retained recovery copies. Never print state or backend tokens.
7. Emit bootstrap evidence and the verified backend reference. A rerun must detect existing state and return an idempotent result.

## Private CI execution

Use ephemeral GitHub self-hosted Linux runners on Azure VMs in a dedicated CI subnet with private DNS/route access to AKS API, state/data private endpoints and ACR. Terraform owns network/runner resources; bootstrap runner registration using a designated secret reference. Destroy runner instances after one trusted job; do not destroy shared infrastructure.
Use OIDC for Azure authentication, separate plan/apply/release identities and protected environments. Never dispatch untrusted PRs or fork code to private runners; ci.yml uses unprivileged GitHub-hosted runners.
Before plan/apply/deploy, doctor verifies DNS, TCP/TLS reachability and least-privilege access, without printing tokens. Check GitHub/control-plane egress and the verified provider allowlist.
For first provisioning, preflight may report named absent resources as pending; actual runtime probes become mandatory after provisioning. Missing credentials, invalid identifiers and inaccessible pre-existing dependencies always fail.

## Release and deployment manifests

build.sh emits OCI/chart packages, SBOM/provenance and release.json containing version, digest, chart hashes, schema and test evidence. publish.sh requires trusted CI, RELEASE and passing checks, signs the unchanged digests and emits published-release.json with registry/signature references.
deployment-manifest.json records target identity, source revision, effective configuration/values hashes and previous Helm revision/release. Bind every verification report to that manifest. AKS requires the published manifest; local execution accepts the candidate. Never rebuild during staging-to-production promotion.

## Immutable bundle handoff and production authorization

AGENTS.md section 6 is the required end-to-end sequence. Its command blocks use these explicit interfaces:
- publish.sh writes RUN_DIR/published-release.json and packages the candidate/release reports, locks, chart packages, SBOM/provenance, signatures and approved staging/production configuration hashes. CI retains the complete immutable bundle, not just the manifest.
- Workflow jobs restore the selected bundle under a verified absolute RELEASE_BUNDLE path, preserve expected relative paths, and set RELEASE to its published-release.json. Check out exactly the source revision in that manifest before bootstrap/validate; never accept a changed workspace or rebuild the bundle.
- Preserve one environment RUN_DIR and its plan/deployment evidence across serialized infra.yml/release.yml jobs. Carry PLAN_MANIFEST as the exact saved-plan reference; reauthorization is required after any input/state change.
- verify.sh --suite qualification is an evidence-only staging gate after smoke, load, recovery and the final smoke of the original staging deployment. No cloud mutation occurs in this aggregation step.
- Emit RUN_DIR/qualification.json with release ID/commit/digest/chart hashes, candidate environment config/policy hashes, staging deployment/schema/Helm references, source/lock hashes, all required report hashes/outcomes/counts/times, and trusted CI run/provenance. Require recovery/load thresholds and nonempty reports; reject missing/skipped/stale/mixed-release evidence.
- CI stores/attests the qualification report and its supporting evidence immutably. Production restores it and passes QUALIFICATION_MANIFEST to doctor.sh via --qualification-manifest.
- doctor.sh preflight verifies trusted provenance, report hashes/outcomes, release identity, approved production-config hash and valid authorization before any production apply/dependency/migration/deploy. Runtime rechecks the same identity/release binding.
- Stage and production environment IDs differ; each must match its own reviewed config and saved plan. Both use identical application/chart artifacts and policy versions. Never compare unrelated environment-specific IDs as if they must be equal.
- common.sh requires successful production preflight evidence and the qualification hash for every mutating production wrapper; directly invoking infra.sh/migrate.sh/deploy.sh cannot bypass the promotion gate.
- Required checks: no qualification artifact, tampered report, different digest/chart/policy, changed reviewed production config, skipped recovery or wrong target identity => nonzero before mutation.
- Production smoke checks live MCP behavior, deployed artifacts and read-only cloud controls. It writes completion.json only after promotion, plan, backup, migration, deployment and smoke evidence pass; recovered rollback does not qualify the failed new release.
- Report failure immediately and retain partial evidence. Do not enable workflows or remove scaffold blockers merely to create passing reports.

## Platform prerequisites: scripts/dependencies.sh

Use docs/platform.md and deploy/platform-sources.yaml.
Establish the private cluster connection, validate namespace/cluster identities, then reconcile pinned CRDs/controllers before auction-platform and auction-assistant charts.
Controller/CRD changes require policy and compatibility checks; do not delete shared CRDs on rollback. Keep each object under one declared owner. Install a separately owned controller only if discovery confirms it is not already managed.
Wait for each controller before dependent custom resources. Verify broker quorum, persistent volumes, cert issuance, CSI mounts, KEDA and monitoring.

### Required commands inside the wrappers

- `validate.sh`: `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, `uv run --locked mypy src/`, Compose config checks and `terraform fmt -check -recursive`.
- Initialize and validate Terraform roots without backends for static checks. Lint and render all charts for both environments; run kubeconform and conftest.
- Resolve locked chart dependencies with `helm dependency build`. Package source charts and regenerate manifests into `RUN_DIR/rendered/`; never edit vendored charts or rendered output directly.
- `test.sh`: `uv run --locked pytest tests/unit/`, `tests/contracts/`, `tests/integration/`, `tests/regression/`, `tests/evaluation/` as selected; support `TEST_PATH` for a focused test.
- `infra.sh`: set `TF_ROOT=infra/terraform/environments/$ENV`; initialize with `terraform -chdir="$TF_ROOT" init -input=false -lockfile=readonly -backend-config=backend.hcl`.
- Generate nonsecret tfvars from validated configuration; run `terraform -chdir="$TF_ROOT" plan -input=false -var-file=<generated-tfvars> -out=<private-plan>`.
- Export restricted JSON with `terraform -chdir="$TF_ROOT" show -json <verified-saved-plan>`; evaluate `infra/policy/terraform.rego`; write `RUN_DIR/plan-manifest.json` with plan hash/location, source/config/lock hashes and Azure identity.
- Apply only after policy/authorization checks using `terraform -chdir="$TF_ROOT" apply -input=false <verified-saved-plan>`; never generate a replacement plan during apply.
- Keep tools, workspace and runner OS/architecture identical for plan/apply. Reject stale state, changed inputs or identities.
- `deploy.sh`: `helm upgrade --install auction-assistant <verified-chart-package> --namespace <verified-namespace> -f <base-values> -f <environment-values> --wait --rollback-on-failure --timeout 10m`.
- Pin compatible Helm 4 tooling; pass the release image digest explicitly. Never use mutable image tags or `--reuse-values`.
- `rollback.sh`: `helm rollback auction-assistant <verified-revision> --namespace <verified-namespace> --wait --timeout 10m`; then invoke smoke verification.
- Verify recoverable backups before migrating existing data. For an empty database, verify backups and point-in-time recovery are configured, then initialize the schema.
- On rollout or smoke failure, attempt one compatible app rollback and retain diagnostics. For a first installation, preserve data and verify recovery from the failed installation.

## Verification dispatch

- make test-integration: PostgreSQL/RabbitMQ/Azurite in a unique Compose test project, local authentication test keys and frozen authorized provider records. No live Azure or external provider requirement.
- make verify SUITE=smoke: live providers, all six MCP tools, citations, ownership, durable state, deployed digest and telemetry.
- On staging/production, additionally invoke tests/acceptance/test_cloud_controls.py against Azure: positive/negative Workload Identity and Blob access, private connectivity, model deployment/model-version match, MCP client OAuth flow, secret mounts and current certificate chain/expiry.
- In staging only, use disposable fixtures for Blob overwrite/version restore, unauthorized principals, certificate renewal and secret rotation/reload. Production performs read-only checks of those controls and requires the same qualified policy plus staging evidence.
- Never modify tenant-wide identity policy or production secrets/certificates during smoke. Delete only fixtures owned by the current run.
- make verify SUITE=load: enforce config/runtime.yaml's profile and 900s per-analysis wall-clock deadline, measured from durable submission, including queue time.
- make verify SUITE=recovery: docs/operations.md and isolated restore destination; keep the staging release RUN_DIR, use unique recovery subdirectories/resources, and require RPO/RTO plus restored functional checks. Return to the original staging deployment for final smoke.
- make verify SUITE=qualification: aggregate passing staging reports; produce qualification.json as specified above. The suite is invalid outside staging.
- Local smoke uses real authorized providers and a verified OAuth client configuration; it may not bypass identity or report cloud controls as locally proven.
