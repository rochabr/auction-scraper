# Azure and Kubernetes platform contract

These are owning implementation contracts. Scripts/charts remain blocked until completed and validated. Use existing authorized resources where ownership permits; import instead of replacing them.

## Ownership and installation order

Terraform modules/platform owns Azure resources, AKS add-ons (Workload Identity, Key Vault CSI, KEDA, Azure Monitor agents), networking, managed PostgreSQL, ACR, Key Vault, Azure OpenAI, monitoring, Backup vault/protection, identities and scoped role assignments.
scripts/dependencies.sh owns separate cert-manager and Envoy Gateway Helm releases and the pinned official RabbitMQ Cluster Operator release manifest. Existing shared controllers stay with their verified owner.
auction-platform Helm owns the RabbitmqCluster resource, custom storage class, certificate issuer/configuration and OpenTelemetry collector. RabbitMQ Cluster Operator owns its generated StatefulSet, services and PVCs; never separately template those generated objects.
auction-assistant Helm owns the API/worker resources, Gateway/HTTPRoute/Certificate, SecretProviderClass and scaler resources.
Order: Terraform add-ons -> cert-manager -> Gateway API CRDs/Envoy Gateway -> RabbitMQ Cluster Operator -> auction-platform -> runtime checks -> migrations -> auction-assistant. Validate supported version combinations before any apply.

In deploy/platform-sources.yaml record verified upstream source/release, immutable digest or manifest hash, license and Kubernetes/API compatibility. Resolve versioned official artifacts during bootstrap; never use latest at execution.
For RabbitMQ operator, use its official release manifest, pin its content hash and image digests, mirror verified images to ACR, then apply the local verified manifest with server-side apply and a dedicated field manager. Record the object inventory and owner; no unmanaged download-and-execute.
CRD upgrades require compatibility checks and an explicit authorized step; Helm does not automatically upgrade CRDs in its crds/ directory. Never remove shared CRDs/controllers during application rollback.

## Routing, DNS and TLS

Choose Envoy Gateway with Gateway API, not legacy ingress-nginx. Use the official OCI Helm chart named in platform-sources. Do not render templates/ingress.yaml; gateway.yaml, httproute.yaml and certificate.yaml own the replacement.
Terraform discovers/imports the authorized Azure DNS zone; the application hostname and ACME account contact are required verified configuration, never invented. Terraform provisions a static Standard Azure public IP for the gateway and the corresponding DNS record; the Envoy service binds that exact IP through verified AKS annotations/RBAC. This removes a deployment/DNS dependency cycle. Do not let Terraform and a DNS controller manage the same record.
cert-manager issues and renews a public certificate with Let's Encrypt DNS-01 using scoped Azure DNS Workload Identity. TLS >=1.2; do not expose HTTP application traffic. Validate the certificate chain, hostname and expiry.
Gateway/backend settings must disable response buffering for Streamable HTTP, allow streaming for 900s, heartbeat every 15s and reconnect without repeating accepted analyses. Disable automatic retries of analysis submissions at the gateway; application idempotency governs retry behavior.
Enforce runtime.yaml body limits and per-user API limits. Apply request/idle timeout behavior using the pinned Gateway API/Envoy versions and prove a stream lasting beyond ordinary proxy defaults in staging.
Gateway replicas >=2, API replicas >=2, disruption budgets and topology spread. Explicitly configure service routing across API replicas for MCP sessions: use shared PostgreSQL session/event state with replay cursors; no process-local session requirement or unverified sticky-session dependency.

## Secrets, broker and persistence

Use docs/security.md for Azure Key Vault CSI mounts, separate runtime identities and rotation.
RabbitMQ: official Cluster Operator, supported pinned RabbitMQ image, three nodes across three available zones, quorum queues, publisher confirms, bounded delivery/dead-letter behavior, client TLS and encrypted inter-node communication.
Create an application vhost plus distinct producer/consumer and read-only scaler credentials; credentials remain in Key Vault/secret references. KEDA may inspect only required queue metrics; never grant administrator access to the worker.
The platform chart defines a custom Azure Disk CSI StorageClass with Premium_ZRS, Retain reclaim policy, WaitForFirstConsumer and expansion enabled; validate regional/SKU compatibility rather than silently downgrading. Request 32Gi per broker; warn at 70% disk usage and page at 85%. Maintain >=1GiB RabbitMQ disk free limit.
Operator persistence settings reference that storage class. Test rescheduling and PVC retention; a surviving disk is not a backup.
Initial broker resources per pod: requests 500m CPU/1Gi RAM, limits 2 CPU/2Gi RAM. Tune from staging evidence without changing qualified production values silently.
Do not restore RabbitMQ queue contents as authoritative analysis state: PostgreSQL/outbox/checkpoints drive republishing and idempotent resumption.

## Scaling and initial resources

API: HPA 2-6 replicas, CPU target 60%; requests 250m/512Mi, limits 1 CPU/1Gi.
Workers: KEDA RabbitMQ scaler with QueueLength mode, 10 ready messages per replica, polling 15s, cooldown 120s, 2-8 replicas. Each worker has concurrency 2/prefetch 1; requests 500m/1Gi, limits 2 CPU/2Gi. Bind scaler credentials through TriggerAuthentication; no competing standalone HPA on workers.
Use a 150s worker termination grace period and graceful task draining; late-ack work must redeliver safely.
AKS initial system pool: three nodes across supported zones; dedicated autoscaling user pool 3-6 nodes. Select a supported regional VM SKU with >=4 vCPU/16Gi and enough allocatable capacity for these requests plus controllers. Record the verified SKU/AKS version in environment values before plan approval; no fictional SKU or capacity claims.
PostgreSQL Flexible Server: General Purpose, minimum 2 vCore/8Gi, zone-redundant HA, 128Gi storage/autogrow and 35-day PITR. Confirm regional availability/quota and size from load evidence; enforce private connectivity and TLS.
These are starting allocations, not performance claims. Load/recovery qualification and cost review must pass for the effective sizes.

## Network and CI

Use private AKS API, private data endpoints and private DNS. For newly created AKS choose Azure CNI Overlay with Cilium network policy; retain compatible existing owned networking rather than replacing a cluster.
Default-deny pod ingress/egress with explicit DNS, database, broker, storage, identity, telemetry and verified provider traffic. Authorize outbound destinations from the discovered contracts and verified DNS/IP inventory; keep SSRF hostname/redirect/address checks in adapters.
Use ephemeral Azure VM GitHub runners in a dedicated CI subnet; docs/execution.md owns lifecycle and reachability gates. Public untrusted PR jobs cannot access that subnet or privileged identities.
No external managed service outside Azure is introduced for runtime data, secrets, models or monitoring. cert-manager and Envoy run on AKS; ACME certificate issuance is explicitly outbound and not a data-processing provider.

## Sources to verify when pinning

- RabbitMQ operator: https://www.rabbitmq.com/kubernetes/operator/install-operator
- RabbitMQ cluster configuration: https://www.rabbitmq.com/kubernetes/operator/using-operator
- Envoy Gateway: https://gateway.envoyproxy.io/docs/tasks/quickstart/
- Gateway timeouts: https://gateway.envoyproxy.io/docs/tasks/traffic/http-timeouts/
- cert-manager: https://cert-manager.io/docs/installation/helm/
- Azure DNS issuer: https://cert-manager.io/docs/configuration/acme/dns01/azuredns/
- AKS scaling: https://learn.microsoft.com/en-us/azure/aks/concepts-scale
- Azure Disk CSI: https://learn.microsoft.com/en-us/azure/aks/azure-disk-volume
