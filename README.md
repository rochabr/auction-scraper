# iArremate Scraper

This project extracts lot information from iArremate auction pages using Python and Playwright.

The main script is `scrape_iarremate_playwright.py`. It starts from an iArremate lot URL, fetches each lot page in sequence, and writes normalized auction-analysis data to both JSON and CSV.

## Requirements

- Python 3.9 or newer
- Playwright Chromium browser

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
```

Install the Python dependencies:

```bash
.venv/bin/python -m pip install --upgrade pip playwright beautifulsoup4 lxml
```

Install the Playwright browser:

```bash
.venv/bin/python -m playwright install chromium
```

## Scrape All Lots

Pass the first lot URL and an output JSON filename:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  iarremate_cukier_arte_038_lots.json
```

The script will start at lot `1`, then continue to lot `2`, `3`, and so on until the next page has no lot data.

It also creates a CSV next to the JSON file:

```text
iarremate_cukier_arte_038_lots.json
iarremate_cukier_arte_038_lots.csv
```

## Scrape a Lot Range

Use `--start-lot` and `--end-lot` to scrape only part of an auction. Both options are optional.

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  iarremate_cukier_arte_038_lots_10_20.json \
  --start-lot 10 \
  --end-lot 20
```

This fetches lots `10` through `20`, inclusive.

You can also pass only one bound:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  iarremate_cukier_arte_038_from_50.json \
  --start-lot 50
```

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  iarremate_cukier_arte_038_to_25.json \
  --end-lot 25
```

## Testing a Small Run

For a quick test, use `--max-lots`:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  test_lots.json \
  --max-lots 3
```

## Output Format

Each JSON record uses this normalized schema:

- `lot_number`
- `url`
- `auction_house`
- `auction_name`
- `auction_id`