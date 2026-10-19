# Integration inventory

## Existing scraper

- Source: `scrape_iarremate_playwright.py` at repository root.
- Existing usage, command options and output schema: root `README.md`.
- Preserve its source and dependencies while adding typed adapters.

## Provider contracts to discover

- iarrematelegacy.com: historical realized sales API.
- catalogodasartes.com: artist API and cited context.

Document actual authentication, schemas, pagination, quotas and secret references during implementation. This scaffold supplies no endpoint paths or credential values. Live connectivity has not been tested.
