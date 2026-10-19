# Execution contract

This file specifies the implementation required by AGENTS.md. Operational scripts remain blocked until implemented and verified.

## Operation deadlines

Checks/build: 30m; Terraform: 60m; each platform controller/release: 20m; migrations/app: 10m each; smoke: 15m; load: 25m including analysis completion; recovery: 4h. Bound retries within the applicable deadline; preserve diagnostics on timeout. An analysis has a separate 900s deadline from durable submission, including queue time.

## Source ownership and entry points

- Makefile forwards ENV, RUN_DIR, RELEASE, PLAN_MANIFEST, PHASE, SUITE, TEST_PATH and RELEASE_REVISION explicitly to the named scripts. Scripts validate arguments, not shell-evaluated configuration.
- scripts/lib/common.sh enforces input schemas, fresh run IDs, identity/hash checks, authorization, prerequisites, redaction and append-only evidence.
- scripts/validate.sh validates every config file against config/schemas/<basename>.schema.json; environment files use config/environment.schema.json. Validate cross-file references, enum/range checks and production bans.
- Render from these sources; record source hashes and the effective-config hash in the release/deployment manifests. Do not duplicate policy constants in shell, application code or workflows.
- scripts/bootstrap.sh resolves compatible supported releases from official sources, pins tools/images/charts/actions/operators, generates locks and config schemas, then validates them before use. Subsequent runs verify locks without updating them.
- Never generate upstream hashes or version IDs from guesses. deploy/platform-sources.yaml is incomplete until verified pins are committed.
- test.sh owns five non-live suites; verify.sh owns live smoke, load and recovery. No required suite may silently skip.

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
- make verify SUITE=recovery: docs/operations.md, isolated restore destination and a fresh RUN_DIR; require the specified RPO/RTO and final smoke.
- Local smoke uses real authorized providers and a verified OAuth client configuration; it may not bypass identity or report cloud controls as locally proven.
