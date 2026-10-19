# Presentation script — Art Auction Intelligence Assistant

Speaker notes for walking through [AGENTS.md](AGENTS.md). Use the spoken paragraphs as a starting point and adjust them to your own voice.
Aim for a five-to-seven-minute overview, then follow the interviewer's questions into the relevant section, command or file.

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
