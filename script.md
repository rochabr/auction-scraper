# Presentation script — Art Auction Intelligence Assistant

Speaker notes for walking through [AGENTS.md](AGENTS.md). Use the spoken paragraphs as a starting point and adjust them to your own voice.
Allow approximately seven to nine minutes for the spoken paragraphs. The delivery walkthrough and best-practice callouts are optional discussion notes; do not read every table or command aloud.
These practices guide the design. The selected stack, valuation thresholds and recovery objectives remain project decisions to explain and validate.
AGENTS.md is the delivery contract; auxiliary configuration, scripts, Terraform and charts own implementation detail. This script explains both the decisions and how the agent must demonstrate completion.

## Opening

> I chose the consumer art auction market because collectors make purchase decisions using fragmented information. They need to understand the artwork, the artist, comparable transactions and total acquisition costs before deciding how much to bid.
>
> The Art Auction Intelligence Assistant brings that research together into recommendations supported by evidence. My deliverable is an AGENTS.md that tells a coding agent what to build, which integrations to use, how to deploy it and how to prove that it works.

Walk through the document as a chain: customer problem → agent boundaries → application behavior → architecture → deployment contract → execution → evidence of success.

## 1. Mission & Business Context

**Purpose and importance:** Establish the customer, the decision they need to make and the value of solving the problem. Define scope before discussing technology.

**Exercise fit:** Addresses the required real-world business problem, consumer-facing industry and expected business impact.

**Say:**

> A collector needs to decide which lots deserve attention and what maximum bid fits the evidence and their budget. Today, that requires reconciling catalog information, artist records, historical sales and fees across separate sources.
>
> The assistant analyzes a catalog and returns ranked lots, valuation ranges, acquisition costs and bidding limits with supporting evidence and explicit gaps. The collector retains the purchase decision. Automated bidding and payments are outside scope.
>
> I set an objective of reducing research time by 80%, measured against the same task and catalog researched manually. That is a target to validate. Valuation quality is measured separately on historical sales held out from calibration.

**Best practices to highlight:**

- **Customer-first design:** Start with the collector's decision, then justify each capability by how it improves that decision.
- **Measurable outcomes:** Compare research time against a manual baseline and evaluate valuation quality separately. An efficiency target does not establish accuracy.
- **Scope control and user authority:** Support research and bidding limits while keeping purchasing decisions with the collector.

**Point to:** Customer journey, scope and measurable outcomes. Explain that the hammer price excludes the buyer's premium, taxes and other costs.

## 2. Agent Operating Contract

**Purpose and importance:** Give the coding agent clear responsibilities, permissions and boundaries so it can work autonomously without inventing interfaces or weakening safeguards.

**Exercise fit:** Provides the operating context needed for autonomous implementation and connection to existing services.

**Say:**

> This section establishes what the agent can decide and what is already fixed. It can make routine implementation decisions, but it must use the selected stack, discover actual integration contracts, protect credentials and follow the prescribed execution path.
>
> The three integration responsibilities are explicit: iarremate.com supplies auction catalogs through the scraper, iarrematelegacy.com supplies historical sales, and catalogodasartes.com supplies artist information. The agent must verify their interfaces and authentication rather than invent endpoint paths.
>
> Existing authorization remains valid, while destructive or unauthorized actions stop at the affected stage. Retrieved content is treated as data so a catalog description cannot become an instruction to the coding agent.

**Best practices to highlight:**

- **Explicit agent instructions:** Name responsibilities, commands and boundaries so the agent can act with less ambiguity. This follows the project-specific guidance described by [AGENTS.md](https://agents.md/).
- **Least privilege and enforced authorization:** Instructions guide behavior; scoped identities and protected environments enforce permission boundaries. The Markdown file alone cannot enforce access control.
- **Prompt-injection defenses:** Treat catalog and provider content as untrusted input, with constrained tools and validated outputs. These controls reduce exposure; no individual control guarantees prevention. See [OWASP prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).
- **Discover and validate contracts:** Inspect existing interfaces and credential references before integration. Avoid inventing provider paths or presenting an adapter placeholder as a verified connection.

**Point to:** Integration inventory, authority boundaries and the rule requiring evidence for completion claims. The previous scraper source is available through the historical links in `docs/integrations.md`.

## 3. Application Specification

**Purpose and importance:** Turn the business objective into observable behavior, explicit interfaces and reproducible calculations.

**Exercise fit:** Supplies the functional detail and correctness rules the runtime agent needs to implement the service.

**Say:**

> This is the product contract. Six MCP tools cover auction discovery, catalog retrieval, starting analysis, checking progress and retrieving auction-level or lot-level results. Analysis runs asynchronously, so the collector receives a durable identifier and can return to the results later.
>
> Each recommendation must be traceable to source evidence. The model can help interpret supported attributes and explain results. Versioned Python functions calculate valuations, fees and maximum bids using Decimal arithmetic.
>
> The bid calculation starts from a conservative valuation bound, applies a safety margin and any budget, then finds the maximum hammer bid that fits the total acquisition cost. Unknown fees or insufficient comparable sales produce an explicit evidence gap and a constrained result.

**Best practices to highlight:**

- **Explicit tool contracts:** Typed input and output schemas make integrations easier to validate and consume. The [MCP tools specification](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) defines schema-based tool interfaces.
- **Idempotent requests:** The same caller and idempotency key should return the same analysis; changed payloads must be rejected. This applies the retry-safety pattern described in [Amazon Builders' Library](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/).
- **Deterministic critical calculations:** Keep price, fees, rounding and budget calculations in tested, versioned code. The chosen valuation formula and minimum sample are project policies that require calibration.
- **Provenance and explicit uncertainty:** Preserve source records and calculation inputs. Withhold unsupported recommendations so users can distinguish evidence gaps from low valuations.

**Point to:** The six-tool table, idempotency behavior, comparable-sale eligibility and total-acquisition-cost calculation. Emphasize that percentile ranges describe the sample; they are not statistical confidence intervals.

## 4. Technical Architecture & Engineering Standards

**Purpose and importance:** Assign each component one responsibility and give the agent an explicit repository map, dependency contract and implementation conventions.

**Exercise fit:** Addresses required libraries, technical dependencies, architecture decisions and sufficient implementation detail.

**Say:**

> FastAPI and the MCP SDK expose the service. LangGraph coordinates the research stages and checkpoints their progress. Celery and RabbitMQ deliver background work and handle retries, which keeps long analyses out of request handlers.
>
> LiteLLM controls access to verified Azure OpenAI deployments and enforces usage budgets. Azure Database for PostgreSQL owns durable job and result state, while Azure Blob Storage retains evidence and reports. Local Compose uses PostgreSQL, RabbitMQ and Azurite. OpenTelemetry connects requests, research stages and background tasks to the specified Azure monitoring destinations.
>
> These boundaries have costs: the graph, broker and workers add operational components. They support catalog-scale background processing, recovery and traceability. The repository map identifies the owning source files, and locked dependencies make builds reproducible. Detailed runtime and recommendation policy lives in versioned configuration, while AGENTS.md points the agent to its owning artifacts and required gates.

**Best practices to highlight:**

- **Separation of concerns:** Give interfaces, research orchestration, message delivery and valuation clear owners. Review the operational cost of every additional component.
- **Durable, repeatable task processing:** Persist progress and tolerate message redelivery with idempotent writes and bounded retries. [Celery's task guidance](https://docs.celeryq.dev/en/stable/userguide/tasks.html) discusses idempotency, acknowledgement and retry behavior; queue delivery alone does not guarantee exactly-once business effects.
- **Reproducible execution:** Pin dependencies and preserve input and policy versions so a result can be reconstructed. Reproducible calculations do not imply identical model wording on every run.
- **Observability across boundaries:** Correlate requests, graph stages and background work to investigate latency, failures and cost. [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/) explain how connected spans describe an operation across components.

**Point to:** Runtime topology, fixed platform choices and the repository map. Use `config/runtime.yaml` for numeric bounds and `docs/execution.md` for the full file inventory. Explain the distinction between graph progress and message delivery, including why processing must tolerate duplicate messages.

## 5. Infrastructure & Deployment Contract

**Purpose and importance:** Define the artifacts, identities and gates required to provision infrastructure and deploy a verified release consistently.

**Exercise fit:** Directly addresses production deployment, service dependencies, secure connections and the rationale for delivery choices.

**Say:**

> Terraform manages infrastructure, and Helm manages the platform, application and migration releases. Named Make targets invoke version-controlled scripts, so local execution and GitHub Actions use the same command interface.
>
> The release sequence is build, scan, then sign and publish. Staging and production use the same verified image digest and chart packages. Infrastructure changes apply the exact authorized saved plan, with checks for the environment, identity and input hashes.
>
> Platform choices are explicit: Entra External ID for customer identity, Key Vault for secrets, Azure OpenAI for models, Azure Monitor for telemetry, Envoy Gateway for routing, and KEDA for worker scaling. Versioned configuration and chart values own detailed settings. AGENTS.md names the decisions, entry points and mandatory gates.
>
> Storage is explicit: Azure Blob Storage in staging and production, provisioned with Terraform and accessed using AKS Workload Identity. Azurite supports local development. This keeps infrastructure in Azure or AKS and avoids operating a separate production object-storage cluster.
>
> Production controls include private data services, short-lived identities, secret injection, readiness checks and compatible database migrations. A staging qualification report is required before production mutation. A failed rollout can restore a compatible previous revision; first deployments use a separate recovery path.

**Best practices to highlight:**

- **Declarative infrastructure with one owner:** Terraform defines infrastructure and Helm defines workloads. Clear ownership reduces competing updates and makes proposed changes reviewable.
- **Review and apply the same plan:** Bind authorization to a saved Terraform plan, use remote state and locking, and reject changed inputs. This follows [HashiCorp's automation workflow](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).
- **Short-lived deployment credentials:** Use OIDC federation and scoped roles instead of repository-stored cloud keys. [GitHub's Azure OIDC guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure) describes the federated authentication approach.
- **Explicit Azure storage ownership:** Terraform provisions private Azure Blob resources, and AKS Workload Identity grants scoped data access. Azurite supports local development; real Azure tests prove cloud identity, networking and protection behavior. See [Blob SDK setup](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-python-get-started) and [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite).
- **Immutable releases and compatible recovery:** Promote the same verified digests and chart packages. Use compatible schema changes so an application rollback can preserve data; database reversal needs its own recovery decision.

**Point to:** Terraform roots, chart paths, config/runtime.yaml, config/valuation-policy.yaml, docs/platform.md, docs/security.md, script mappings, release manifests and the saved-plan contract. Explain the ownership boundary between Terraform resources and Helm resources.

## 6. Agent Execution Workflow

**Purpose and importance:** Give the agent one ordered path from discovery to verified production delivery, with commands, prerequisites, artifacts and an exit gate for every step.

**Exercise fit:** Demonstrates how the instructions guide autonomous implementation, testing and production deployment. This is where to show how the agent executes the specification.

**Say:**

> This section is the execution sequence. First, the agent discovers the existing assets and implements the required application, scripts, tests and infrastructure sources. It then validates, tests and runs the service locally.
>
> Trusted CI builds the authoritative release, scans it, signs it and publishes the complete bundle. Staging consumes that bundle, applies the exact authorized infrastructure plan, installs dependencies, runs migrations and deploys the service.
>
> Staging must pass smoke, load and recovery tests, followed by another smoke test of the original deployment. A qualification step checks those reports and binds them to the release in qualification.json. Missing or mismatched evidence blocks promotion.
>
> Production restores that same bundle and qualification report. It verifies authorization, plans and applies production infrastructure, migrates, deploys and runs smoke checks. It does not rebuild the release. Production smoke records completion only after every required gate passes.
>
> If rollout or smoke fails, the agent attempts one compatible recovery and retains diagnostics. Restoring the previous service does not make the failed new release successful.

**Optional delivery walkthrough — point to each numbered step:**

Use this table when asked how the agent actually builds, tests, deploys and promotes. It summarizes the complete command blocks in AGENTS.md; the wrappers' exact behavior lives in `docs/execution.md`.

| Step | What the agent executes | Evidence required before continuing | Best practice and benefit |
|---|---|---|---|
| **1. Discover and implement** | Locate existing integrations; create the app, six tools, tests, wrappers, schemas, Terraform and charts. | Verified contracts, resolved configuration/locks and implemented required sources. | Reuse verified assets; prevent invented interfaces and premature execution. |
| **2. Test and run locally** | `make bootstrap` → `doctor` → `validate` → `test` → `build` → `security` → `local-up` → runtime doctor → smoke. | Five non-live test suites, scans and authenticated local smoke; candidate `release.json`. | Catch correctness and integration failures before cloud deployment. |
| **3. Build and publish in trusted CI** | Checks on the selected commit; build → security → publish in `build.yml`. | Signed immutable image/chart references, SBOM/provenance, reports and `published-release.json`. | Establish one authoritative release; preserve its identity across environments. |
| **4. Deploy staging** | Verify bundle; bootstrap backend if needed; plan → authorized apply → configure cluster → dependencies → runtime doctor → migrate → deploy. | Exact plan/identity, healthy platform, migration success, deployed digest and Helm revision. | Separate infrastructure and workload ownership; apply the reviewed plan and respect dependency order. |
| **5. Qualify staging** | `make verify SUITE=smoke`, then `load`, `recovery`, final `smoke` and `make verify SUITE=qualification`. | Passing reports for the same release/configuration, aggregated in `qualification.json`. | Test recovery in isolation and verify the original service afterward; reject incomplete evidence. |
| **6. Promote to production** | Restore qualified bundle; doctor validates `QUALIFICATION_MANIFEST`; production plan/apply, dependencies, migration, deploy and smoke. | Trusted staging qualification, production authorization and passing production checks for identical application/chart artifacts. | Promote what staging tested; enforce the gate in scripts and protected workflows. |
| **7. Record delivery or recover** | Production smoke writes `completion.json`; rollout/smoke failure invokes one compatible recovery path. | Linked reports, commit/digest, plan, schema/Helm revisions, timestamps and any blockers. | Distinguish successful delivery, recovery of an older release and partial completion. |

**Best practices to highlight:**

- **Gated delivery:** Scripts must verify prerequisites before mutation. In production, both preflight and the shared wrapper enforce trusted staging qualification; a direct script invocation cannot bypass it.
- **Artifact identity:** `release.json` describes the candidate, `published-release.json` identifies signed published artifacts, `qualification.json` records staging eligibility, and `completion.json` records verified production delivery. Each artifact answers a different question.
- **Environment-specific authorization:** Staging and production use different identities, configuration and infrastructure plans. The application/image/chart artifacts and policy versions remain the qualified ones.
- **Progressive qualification:** Test locally, prove load/recovery in staging and use read-only cloud-control checks in production. No destructive production test is part of promotion.
- **Readiness plus functional verification:** Probes help control traffic and restarts; authenticated MCP smoke tests check customer-visible behavior. [Kubernetes probe guidance](https://kubernetes.io/docs/concepts/workloads/pods/probes/) distinguishes startup, readiness and liveness.
- **Honest recovery reporting:** A successful rollback protects service availability; it does not qualify the failed new release.

**Point to:** Section 6's seven steps and five shell blocks; `scripts/{infra,deploy,verify,doctor}.sh`, `scripts/lib/common.sh`, the Makefile and `docs/execution.md`. Show `QUALIFICATION_MANIFEST` in the production block and the absence of production build/publish commands.

**If asked why this is explicit enough:**

> Each step names an execution entry point, its required inputs and the result that permits the next step. AGENTS.md keeps that sequence visible; version-controlled auxiliary files define how the commands carry it out. Required checks must return nonzero when evidence is missing or a gate fails.

## 7. Acceptance Criteria & Definition of Done

**Purpose and importance:** Define observable completion conditions and the evidence needed to distinguish a generated repository from a successfully delivered service.

**Exercise fit:** Directly satisfies the requirement for acceptance criteria and verification of the implemented solution.

**Say:**

> Completion requires demonstrated outcomes. All six tools must work, the integrations must pass authorized live checks, and a 100-lot catalog must be accounted for through durable analysis.
>
> Calculations must reproduce from frozen evidence and policy versions. For example, the four-sale fixture must return a median of 250 and bounds of 175 and 325. Authorization, retries, recovery, staging qualification and production smoke must pass, with reports tied to the exact source revision and release.
>
> If an external gate blocks delivery, the agent reports partial completion and the precise remaining action. It cannot claim production success from file generation alone.

**Best practices to highlight:**

- **Behavioral acceptance criteria:** Require observable results such as complete lot accounting, authorization failures and reproducible calculations. File creation alone cannot establish delivery.
- **Recovery testing:** Exercise worker failure, redelivery, restoration and applicable rollback. State the conditions tested and measured recovery objectives rather than claiming all failures are covered.
- **Evidence-based completion:** Link check results to the exact commit, digest, plan and release. Keep targets, specified behavior and verified outcomes distinct, including the repository's current placeholder status.

**Point to:** Section 7's calculation fixtures, 100-lot smoke case, latency/load thresholds, recovery objectives and qualification gate. Explain that `qualification.json` permits promotion; `completion.json` establishes verified production delivery.

## Closing

> The document connects the collector's decision to a controlled engineering workflow. Each requirement has an owning component, an execution path and an observable result. That gives the coding agent enough direction to implement autonomously and gives a reviewer a way to assess completion.

## Presentation reminders

- Lead with the customer outcome, then explain the technical decision that supports it.
- Distinguish objectives, specified behavior and measured results. The repository currently contains placeholders; the assistant has not been implemented or deployed.
- Keep AGENTS.md as the primary assignment artifact. This file is a speaking guide.
- Use one example throughout: select an auction, request analysis, inspect a lot and explain its evidence and bidding limit.
- Treat existing integrations and authorized access as available inputs; describe how the agent discovers and validates their actual contracts.
- Explain trade-offs when asked: orchestration complexity, provider latency and quotas, sparse comparable sales, and the operating cost of the chosen production stack.
- Discuss incomplete evidence openly. Faster research is valuable, but it does not establish valuation accuracy or guarantee investment returns.
- Explain the ownership rule: AGENTS.md states outcomes and gates; config/policy files, scripts and chart values own implementation detail. Null real-world identifiers are discovery gates, not invented deployment values.
- If asked where the step-by-step process is, open Section 6 immediately. Walk through its seven numbered steps and explicit command blocks, then use the auxiliary files to explain one wrapper in detail.
- Explain that local builds support development; trusted CI publishes the authoritative bundle. Staging and production consume that bundle without rebuilding.
- Use the named scripts and charts to demonstrate execution detail. Avoid reading implementation tables line by line.
- When naming a best practice, point to its concrete requirement and explain the customer or operational benefit. Discuss the added cost or limitation when relevant.
- Describe these controls as requirements until they have been implemented and verified; the reference links support the practices, not a claim that the placeholder repository already enforces them.
