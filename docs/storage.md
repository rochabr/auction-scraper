# Azure storage implementation contract

This document defines the intended storage implementation. The repository contains placeholders; no storage resources or integration tests have been deployed or executed.

## Explicit choices

| Environment | Service | Access |
|---|---|---|
| Local development and isolated tests | Azurite in Docker Compose | Azure Blob SDK with local-only credentials supplied outside Git |
| Staging and production | Azure Blob Storage | Azure Blob SDK using AKS Workload Identity |

Use Standard StorageV2 with zone-redundant storage (ZRS) in an authorized region supporting it. Disable hierarchical namespace (HNS) so the account uses the required Blob versioning configuration. Enable versioning and 30-day soft delete for blobs and containers.

Versioning and redundancy address different failure modes. Meet the recovery objectives in AGENTS.md through tested restore procedures; local tests alone do not establish cloud recovery behavior.

## Owning artifacts

- `infra/terraform/modules/platform/storage.tf`: storage account, private containers, Blob private endpoint, private DNS and network links, and role assignments.
- `src/auction_assistant/adapters/blob_storage.py`: Blob storage adapter using `azure-storage-blob` and `azure-identity`.
- `compose.yaml`: pinned Azurite image and persistent local volume.
- `compose.test.yaml`: isolated Azurite test service and disposable test data.
- `config/environments/*.yaml`: validated service location and credential-reference settings.
- `tests/integration/test_storage.py`: isolated Azurite behavior tests only.
- `tests/acceptance/test_cloud_controls.py`: real-Azure identity, access, private connectivity and protection checks.
- `infra/terraform/modules/platform/backup.tf`, `config/retention.yaml`, `docs/operations.md`: vaulted backup, retention and restore/reconciliation.

Terraform owns managed Blob resources. Helm owns application workloads, service accounts and their workload identity bindings; the platform chart does not host a production object-storage service.

## Authentication and configuration

In AKS, use `azure.identity.WorkloadIdentityCredential` and grant Storage Blob Data Contributor at the required container scope. Bind the service account to the authorized Azure identity. Disable public network access and Shared Key authorization.

The AKS identity integration supplies `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` and `AZURE_FEDERATED_TOKEN_FILE`. Do not populate them with invented identifiers or tokens. Read the account URL and container name from Terraform outputs and validated configuration.

Local Azurite credentials are development-only and supplied through an ignored local environment or the designated secret mechanism. Reject local connection strings or account keys in staging and production.

Keep blobs private. Route artifact downloads through the authenticated FastAPI service, enforce resource ownership, and never expose account keys in responses or logs.

## Data behavior

Store source snapshots and reports as block blobs. Persist the object reference, content hash, ETag and Azure version ID with its analysis record. Use a null version ID locally when Azurite does not provide one; never invent a cloud version. Use versioned analysis keys so completed evidence is not silently overwritten.

Azurite and Azure expose different feature sets. Keep local tests within supported Blob operations; verify Azure identity, network restrictions, versioning and restoration against the real staging account.

## Verification

1. Run `make test-integration` against isolated Azurite: upload, read, list, delete, missing-object handling, exact byte/hash preservation and test isolation.
2. Run staging `make doctor PHASE=runtime`: verify the configured Blob location, private DNS/connectivity and workload identity.
3. Run staging `make verify SUITE=smoke`: verify authorized storage operations and denial for unauthorized access; check the evidence hash and saved version reference.
4. Run staging `make verify SUITE=recovery`: restore evidence in isolation and meet RPO ≤24 hours and RTO ≤4 hours without changing production data.
5. Record results in the named JUnit and JSON reports. Do not substitute local results for real-Azure security or protection checks.

## Primary references

- [Azure Blob Storage](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction)
- [Azure Blob SDK for Python](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-python-get-started)
- [WorkloadIdentityCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.workloadidentitycredential?view=azure-python)
- [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)
- [Blob versioning](https://learn.microsoft.com/en-us/azure/storage/blobs/versioning-overview)
- [Private endpoints](https://learn.microsoft.com/en-us/azure/storage/common/storage-private-endpoints)
