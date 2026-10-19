# Identity and secrets implementation contract

## Customer authorization

Microsoft Entra External ID is the customer identity provider. config/auth.yaml owns verified issuer, discovery metadata, resource audience, pre-registered client IDs and exact permitted redirect URIs. Do not infer a tenant or copy an ID from an unrelated app.
Use authorization-code flow with S256 PKCE and pre-registered clients; dynamic registration is not required. Expose MCP Protected Resource Metadata and authorization-server discovery for the pinned MCP revision. Validate the selected client's resource/audience behavior against Entra; a successful login alone is insufficient.
Do not claim generic MCP-client compatibility. Run an actual supported MCP client through discovery, consent, code exchange, token refresh, expiry and denied-access cases before release. If provider/client resource binding is incompatible, stop and report that integration issue; never accept a wrong-audience token or bypass verification.
Pin a supported JWT validation library such as PyJWT[crypto] in uv.lock. Verify signature, allowed algorithm, issuer, audience, expiry and subject; reject ID tokens, unsigned tokens and algorithm substitution. Refresh trusted JWKS once on unknown key ID, bounded by auth.yaml limits.
Map caller identity to (issuer, subject), never email or an input user_id. auctions.read authorizes discovery/read; auctions.analyze additionally authorizes submission. All analysis/status/result/artifact lookups include the owner predicate. Return safe denied/not-found responses without disclosing other users' resources.
Do not pass caller tokens to provider APIs or log them. Use separate runtime provider credentials.

## AKS Workload Identity and secrets

Terraform owns Key Vault private endpoint/DNS, purge protection, RBAC and federated identities; enable the AKS Key Vault Secrets Store CSI add-on.
auction-assistant/templates/secretproviderclass.yaml mounts only designated existing secrets as files; bind the service account to its identity. Use identity-based Blob/model access and database identity where supported; RabbitMQ/provider secrets use verified references.
Application and worker service accounts have distinct least-privilege roles. The CSI identity receives Key Vault Secrets User only on required scope; no administrator role for runtime.
Enable CSI rotation polling every 2m. Application configuration watches atomically replaced mounted files and recreates affected clients safely within 5m; if a library cannot reload, use a controlled rolling restart with readiness checks. Never treat a mounted subPath file as automatically refreshed.
Do not place secrets in Terraform variables/state, Helm values, Kubernetes ConfigMaps, artifacts or command arguments. Reference existing secret names/versions and use a separately authorized secret-provisioning process.
scripts/doctor.sh tests required references and access without printing values. Production forbids shared storage keys and long-lived cloud credentials.
Local development resolves secrets outside Git through a designated local secret file/OS credential store and authorized Azure developer identity. Offline tests use ephemeral signing keys and local-only service credentials; never use them to pass live authentication tests.

## Test ownership

tests/integration/test_auth.py: local signature/claims, expiry/key rotation, scopes, owner predicate, forged tokens and cross-user access.
tests/acceptance/test_cloud_controls.py: real MCP client OAuth/resource binding, scoped Azure identity, secret mounts and denied access. In staging, rotate a run-owned disposable secret and prove reload <=5m; production checks evidence/reference versions without rotation.
Verify TLS and caller authorization independently: a valid certificate does not prove token validation.

## Primary references

- MCP authorization: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- External ID: https://learn.microsoft.com/en-us/entra/external-id/customers/overview-customers-ciam
- AKS Key Vault CSI: https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver
- Azure model identity: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/managed-identity
