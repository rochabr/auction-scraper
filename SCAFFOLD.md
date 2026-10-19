# Auction Intelligence Assistant scaffold

This repository contains the existing iArremate scraper and a placeholder layout for the Art Auction Intelligence Assistant described in [AGENTS.md](AGENTS.md).

The scraper, existing README, requirements and ignore rules are preserved. The added files are structural placeholders; application behavior, infrastructure provisioning and deployment are not implemented.

## Layout

- `src/auction_assistant/`: future service, six MCP tools, research graph, background jobs and provider adapters.
- `tests/`: unit, provider contract, integration, regression, historical evaluation and acceptance suites.
- `scripts/` and `Makefile`: named execution entry points. Only `make help` is informational; other targets stop with exit code 2.
- `config/`: policy and environment placeholders; no credentials or provider endpoint values.
- `infra/terraform/`: isolated backend, platform module and environment roots.
- `infra/policy/`: future infrastructure and Kubernetes policy checks.
- `deploy/helm/`: platform, application and migration charts. Templates deliberately stop Helm rendering until implemented.
- `.github/workflows/*.yml.disabled`: inert workflow placeholders. GitHub Actions will not run these files.
- `docs/`: integration inventory and future execution and operations documentation.

The existing integration entry point is `scrape_iarremate_playwright.py`; its current usage and output schema are documented in the original root README. Discover and verify the remaining provider contracts before implementation.

Do not interpret this scaffold as a working application or a verified deployment. Implement the contracts in AGENTS.md before enabling scripts or workflows. Generate dependency locks and select real tool versions during implementation; none are fabricated here.
