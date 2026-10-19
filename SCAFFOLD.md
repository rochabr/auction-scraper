# Scaffold conventions

This repository provides the file and folder structure described in [AGENTS.md](AGENTS.md). [README.md](README.md) describes the application and current status.

## Placeholder behavior

- Python modules and test files contain structural placeholders, not application behavior or passing tests.
- Operational scripts stop with exit code 2. `make help` only describes the scaffold.
- Helm templates deliberately reject rendering until implemented.
- Workflow files end in `.yml.disabled`; they do not activate GitHub Actions.
- Configuration contains no credentials or concrete provider endpoint paths. Storage is Azure Blob in staging/production and Azurite locally; see [docs/storage.md](docs/storage.md).
- Dependency locks and real tool versions must be generated and verified during implementation.

## Source ownership

Implement the contracts in AGENTS.md before enabling scripts, chart rendering or workflows. Update source artifacts and regenerate their outputs; do not present placeholders as verified implementation.

The previous standalone scraper and its requirements file are no longer in the working tree. [docs/integrations.md](docs/integrations.md) links to their historical implementation and usage documentation.
