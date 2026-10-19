# Integration inventory

## iarremate.com

The previous standalone scraper has been removed from the current repository tree. Its implementation and usage documentation remain available in Git history:

- [Python scraper source](https://github.com/rochabr/auction-scraper/blob/bfcf9801c54a876b0219781cd653495c59995549/scrape_iarremate_playwright.py).
- [Usage and output schema](https://github.com/rochabr/auction-scraper/blob/bfcf9801c54a876b0219781cd653495c59995549/README.md).
- [Historical requirements](https://github.com/rochabr/auction-scraper/blob/bfcf9801c54a876b0219781cd653495c59995549/requirements.txt).

Review the available scraper implementation and its current contracts before integrating it through `src/auction_assistant/adapters/iarremate.py`. Do not treat the placeholder adapter as a working connection.

## API contracts to discover

| Provider | Required evidence |
|---|---|
| iarrematelegacy.com | Historical realized sales and comparable transaction records. |
| catalogodasartes.com | Artist identity, historical context and supporting citations. |

Document verified authentication, schemas, pagination, quotas, error behavior and secret references during implementation. No provider endpoint paths or credential values are supplied by this scaffold. Live connectivity has not been tested.
