# iArremate Scraper

This project extracts lot information from iArremate auction pages using Python and Playwright.

The main script is `scrape_iarremate_playwright.py`. It starts from an iArremate lot URL, fetches each lot page in sequence, and writes normalized auction-analysis data to JSON.

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
.venv/bin/python -m pip install --upgrade pip playwright beautifulsoup4 lxml pillow
```

Install the Playwright browser:

```bash
.venv/bin/python -m playwright install chromium
```

## Scrape All Lots

Pass the first lot URL:

```bash
.venv/bin/python scrape_iarremate_playwright.py https://www.iarremate.com/cukier_arte/038/1
```

The script derives the default JSON filename from the auction URL. For example:

```text
https://www.iarremate.com/selum-leiloes/027/1 -> selum-leiloes_027.json
```

You can still pass a custom output filename:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  custom_output.json
```

The script will start at lot `1`, then continue to lot `2`, `3`, and so on. If a lot number is missing, it checks the next three lot numbers before stopping.

## Scrape a Lot Range

Use `--start-lot` and `--end-lot` to scrape only part of an auction. Both options are optional.

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --start-lot 10 \
  --end-lot 20
```

This fetches lots `10` through `20`, inclusive.

You can also pass only one bound:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --start-lot 50
```

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --end-lot 25
```

## Testing a Small Run

For a quick test, use `--max-lots`:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --max-lots 3
```

## Download Images

Add `--download-images` to save images while scraping:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --download-images
```

The image folder is created inside `images/` and derived from the auction URL, using the same base name as the JSON file. For example:

```text
https://www.iarremate.com/selum-leiloes/027/1 -> images/selum-leiloes_027/
```

You can still pass a custom image folder:

```bash
.venv/bin/python scrape_iarremate_playwright.py \
  https://www.iarremate.com/cukier_arte/038/1 \
  --download-images images/cukier_arte_038
```

Images are saved as PNG files. Lot numbers from `1` through `99` are padded to three digits.

If a lot has one image, the filename is:

```text
001.png
```

If a lot has multiple images, filenames are:

```text
001-1.png
001-2.png
001-3.png
```

Lot `100` and above are not padded, for example `100.png` or `100-1.png`.

## Output Format

The JSON file is a single object with shared auction terms and a normalized lot array:

```json
{
  "terms_and_conditions": {
    "source_url": "https://www.iarremate.com/cukier_arte/038/1",
    "terms_text": "...",
    "payments_and_pickup_text": "...",
    "bid_confirmation_text": "..."
  },
  "buyer_premium": {
    "percent": 5,
    "applies_to_all_lots": true,
    "text": "A(s) obra(s) arrematada(s) será(ao) acrescida(s) da comissão do leiloeiro oficial, que é de 5%...",
    "source_section": "Pagamentos e retiradas"
  },
  "lots": []
}
```

Each item in `lots` uses this normalized schema:

- `lot_number`
- `url`
- `auction_house`
- `auction_name`
- `auction_id`
- `auction_date`
- `auction_location`
- `currency`
- `artist`
- `title`
- `medium`
- `dimensions`
- `year`
- `edition`
- `signature`
- `framed`
- `current_bid_brl`
- `estimate_low_brl`
- `estimate_high_brl`
- `bid_increment_brl`
- `status`
- `condition`
- `provenance`
- `certificate`
- `gallery_labels`
- `literature`
- `exhibition_history`
- `image_urls`
- `description_text`

## Notes

- The starting URL can point to any lot in the auction, but if you pass `--start-lot`, the script rewrites the URL to that lot number.
- `--end-lot` is inclusive.
- If a lot page is missing, the scraper checks the next three lot numbers before stopping.
- Brazilian currency values are converted into numbers, for example `1.670,00` becomes `1670`.
- Placeholder image URLs such as `noimage.png` are removed from `image_urls`.
- The scraper retries temporary Playwright navigation errors up to three times.
- During long scrapes, it checkpoints output every 25 lots.
