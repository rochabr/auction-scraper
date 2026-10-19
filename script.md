# Presentation script — Art Auction Intelligence Assistant

Speaker notes for walking through [AGENTS.md](AGENTS.md). Use the spoken paragraphs as a starting point and adjust them to your own voice.
Aim for a five-to-seven-minute overview using the spoken paragraphs. Use the best-practice callouts as optional discussion cues; choose the ones relevant to the interviewer's question.
These practices guide the design. The selected stack, valuation thresholds and recovery objectives remain project decisions to explain and validate.

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
> LiteLLM centralizes authorized model access and usage controls. PostgreSQL owns durable job and result state, while S3-compatible storage retains larger evidence and report artifacts. OpenTelemetry connects the execution stages through traces and metrics.
>
> These boundaries have costs: the graph, broker and workers add operational components. They support catalog-scale background processing, recovery and traceability. The repository map identifies the owning source files, and locked dependencies make builds reproducible.

**Best practices to highlight:**

- **Separation of concerns:** Give interfaces, research orchestration, message delivery and valuation clear owners. Review the operational cost of every additional component.
- **Durable, repeatable task processing:** Persist progress and tolerate message redelivery with idempotent writes and bounded retries. [Celery's task guidance](https://docs.celeryq.dev/en/stable/userguide/tasks.html) discusses idempotency, acknowledgement and retry behavior; queue delivery alone does not guarantee exactly-once business effects.
- **Reproducible execution:** Pin dependencies and preserve input and policy versions so a result can be reconstructed. Reproducible calculations do not imply identical model wording on every run.
- **Observability across boundaries:** Correlate requests, graph stages and background work to investigate latency, failures and cost. [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/) explain how connected spans describe an operation across components.

**Point to:** Runtime topology, architecture decisions and repository map. Be ready to explain the distinction between graph progress and message delivery, including why processing must tolerate duplicate messages.

## 5. Infrastructure & Deployment Contract

**Purpose and importance:** Define the artifacts, identities and gates required to provision infrastructure and deploy a verified release consistently.

**Exercise fit:** Directly addresses production deployment, service dependencies, secure connections and the rationale for delivery choices.

**Say:**

> Terraform manages infrastructure, and Helm manages the platform, application and migration releases. Named Make targets invoke version-controlled scripts, so local execution and GitHub Actions use the same command interface.
>
> The release sequence is build, scan, then sign and publish. Staging and production use the same verified image digest and chart packages. Infrastructure changes apply the exact authorized saved plan, with checks for the environment, identity and input hashes.
>
> Production controls include private data services, short-lived identities, secret injection, readiness checks and compatible database migrations. A failed release can restore a compatible application revision while preserving data. First deployments have their own recovery path because no earlier revision exists.

**Best practices to highlight:**

- **Declarative infrastructure with one owner:** Terraform defines infrastructure and Helm defines workloads. Clear ownership reduces competing updates and makes proposed changes reviewable.
- **Review and apply the same plan:** Bind authorization to a saved Terraform plan, use remote state and locking, and reject changed inputs. This follows [HashiCorp's automation workflow](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).
- **Short-lived deployment credentials:** Use OIDC federation and scoped roles instead of repository-stored cloud keys. [GitHub's Azure OIDC guidance](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure) describes the federated authentication approach.
- **Immutable releases and compatible recovery:** Promote the same verified digests and chart packages. Use compatible schema changes so an application rollback can preserve data; database reversal needs its own recovery decision.

**Point to:** Terraform roots, chart paths, script mappings, release manifests and the saved-plan contract. Explain the ownership boundary between Terraform resources and Helm resources.

## 6. Agent Execution Workflow

**Purpose and importance:** Order implementation, validation and release work so each stage establishes the prerequisites for the next.

**Exercise fit:** Shows how a coding agent can carry the specification through implementation to verified production delivery.

**Say:**

> This section turns the contracts into a sequence. The agent discovers assets, creates the required artifacts, validates locally, qualifies the release in staging and promotes it through the protected production workflow.
>
> Every stage has prerequisites and evidence. A failed gate stops dependent work. The agent fixes the defect and reruns affected checks without bypassing policy or rebuilding a different release for production.
>
> Staging also exercises concurrent catalog analysis, worker recovery, backup restoration and applicable rollback behavior. Production promotion finishes with authenticated MCP smoke tests against the deployed release and authorized providers.

**Best practices to highlight:**

- **Gated delivery:** A stage must establish evidence before dependent work proceeds. Scripts and CI checks must enforce this rule; an instruction to stop is insufficient by itself.
- **Progressive qualification:** Verify locally, exercise recovery in staging, then promote the same release to production. Keep destructive qualification tests isolated from production data.
- **Readiness plus functional verification:** Probes help control traffic and restarts; authenticated MCP smoke tests verify customer-visible behavior. [Kubernetes probe guidance](https://kubernetes.io/docs/concepts/workloads/pods/probes/) distinguishes startup, readiness and liveness responsibilities.
- **Bounded work:** Deadlines, retry limits and spend budgets constrain failures and cost. Recovery must report an actionable blocker when those bounds are exhausted.

**Point to:** Local and staging command blocks, runtime checks and production promotion. Walk through one submission from `analyze_auction` to durable status and cited results, rather than reading every command aloud.

## 7. Acceptance Criteria & Definition of Done

**Purpose and importance:** Define observable completion conditions and the evidence needed to distinguish a generated repository from a successfully delivered service.

**Exercise fit:** Directly satisfies the requirement for acceptance criteria and verification of the implemented solution.

**Say:**

> Completion requires demonstrated outcomes. All six tools must work, the integrations must pass authorized live checks, and a 100-lot catalog must be accounted for through durable analysis.
>
> Calculations must reproduce from frozen evidence and policy versions. Authorization, retries, recovery, infrastructure gates and production smoke checks must pass. The completion report links those results to the source revision, image digest, infrastructure plan and deployed release.
>
> If an external gate blocks delivery, the agent reports partial completion and the precise remaining action. It cannot claim production success from file generation alone.

**Best practices to highlight:**

- **Behavioral acceptance criteria:** Require observable results such as complete lot accounting, authorization failures and reproducible calculations. File creation alone cannot establish delivery.
- **Recovery testing:** Exercise worker failure, redelivery, restoration and applicable rollback. State the conditions tested and measured recovery objectives rather than claiming all failures are covered.
- **Evidence-based completion:** Link check results to the exact commit, digest, plan and release. Keep targets, specified behavior and verified outcomes distinct, including the repository's current placeholder status.

**Point to:** Acceptance checklist and `completion.json` evidence requirements.

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
- Use the named scripts and charts to demonstrate execution detail. Avoid reading implementation tables line by line.
- When naming a best practice, point to its concrete requirement and explain the customer or operational benefit. Discuss the added cost or limitation when relevant.
- Describe these controls as requirements until they have been implemented and verified; the reference links support the practices, not a claim that the placeholder repository already enforces them.
