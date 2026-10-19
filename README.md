# Art Auction Intelligence Assistant

An auction research assistant for art collectors. The primary artifact is [AGENTS.md](AGENTS.md), which instructs a coding agent to implement, validate and deploy the service.

**Status: repository structure and placeholders only.** The application and deployment automation are not implemented.

## Customer problem

Collectors compare catalog descriptions, artist records, historical sales and acquisition costs before deciding which artworks deserve attention and how much to bid. The assistant brings those sources together into recommendations supported by evidence.

The intended workflow is to discover an auction, request catalog analysis, track progress, review ranked lots and inspect each valuation, maximum bid, source and uncertainty. The collector retains the purchase decision; automated bidding and payments are outside scope.

## Start here

- [AGENTS.md](AGENTS.md): business context, application requirements, architecture, execution contract and acceptance criteria.
- [SCAFFOLD.md](SCAFFOLD.md): placeholder behavior and repository conventions.
- [Integration inventory](docs/integrations.md): required providers and the previous scraper's historical source.
- [Storage contract](docs/storage.md): Azure Blob provisioning, local Azurite, identity and verification.
- [Execution documentation](docs/execution.md) and [operations documentation](docs/operations.md): locations for verified implementation runbooks.

## Required stack

| Responsibility | Technology |
|---|---|
| Service and assistant tools | Python, FastAPI and the official MCP SDK |
| Research orchestration and model access | LangGraph and LiteLLM |
| Background execution | Celery and RabbitMQ |
| Durable structured data | Azure Database for PostgreSQL Flexible Server |
| Evidence and reports | Azure Blob Storage in staging/production; Azurite locally |
| Local and production environments | Docker Compose and AKS |
| Provisioning and delivery | Terraform, Helm and GitHub Actions |
| Observability | OpenTelemetry |

The six planned MCP tools are `list_auctions`, `get_auction`, `analyze_auction`, `get_analysis_status`, `get_auction_analysis` and `get_lot_analysis`.

## Repository layout

```text
AGENTS.md                  Coding-agent instruction contract
Makefile                   Named execution entry points
src/auction_assistant/     Application and provider adapter placeholders
tests/                     Separate correctness and acceptance suites
scripts/                   Execution wrappers and shared safeguards
config/                    Environment, valuation and monitoring placeholders
migrations/                Database migration placeholders
infra/terraform/           Backend, platform module and environment roots
infra/policy/              Infrastructure and Kubernetes policy placeholders
deploy/helm/               Platform, application and migration charts
.github/workflows/         Disabled workflow placeholders
docs/                      Integration, execution and operations documentation
```

## Inspect the scaffold

```bash
make help
```

Other Make targets deliberately stop with exit code 2 until implemented. Chart templates stop Helm rendering, and workflow files use the `.yml.disabled` extension so GitHub Actions will not execute them.

No credentials, API endpoint paths, dependency locks or tool versions have been invented. Generate and verify those artifacts during implementation according to AGENTS.md.

The former standalone scraper project has been removed from the current tree. Its source and documentation remain recoverable in Git history through the links in the integration inventory.
