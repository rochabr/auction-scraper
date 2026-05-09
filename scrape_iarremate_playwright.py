#!/usr/bin/env python3
"""Scrape iArremate lot pages with Python + Playwright.

The output JSON is normalized into the auction-analysis schema.

Usage:
    .venv/bin/python scrape_iarremate_playwright.py \
        https://www.iarremate.com/cukier_arte/038/1 \
        iarremate_cukier_arte_038_lots.json

    .venv/bin/python scrape_iarremate_playwright.py \
        https://www.iarremate.com/cukier_arte/038/1 \
        iarremate_cukier_arte_038_lots_10_20.json \
        --start-lot 10 \
        --end-lot 20
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

NORMALIZED_COLUMNS = [
    "lot_number",
    "url",
    "auction_house",
    "auction_name",
    "auction_id",
    "auction_date",
    "auction_location",
    "currency",
    "artist",
    "title",
    "medium",
    "dimensions",
    "year",
    "edition",
    "signature",
    "framed",
    "current_bid_brl",
    "estimate_low_brl",
    "estimate_high_brl",
    "bid_increment_brl",
    "status",
    "condition",
    "provenance",
    "certificate",
    "gallery_labels",
    "literature",
    "exhibition_history",
    "image_urls",
    "description_text",
]

MEDIUM_PATTERNS = [
    r"óleo sobre tela",
    r"óleo s/tela",
    r"acrílica sobre tela",
    r"acrílica s/tela",
    r"acrilica sobre tela",
    r"guache sobre papel",
    r"aquarela sobre papel",
    r"nanquim sobre papel",
    r"técnica mista",
    r"tecnica mista",
    r"mista sobre papel",
    r"mista sobre tela",
    r"colagem",
    r"serigrafia",
    r"litografia",
    r"xilogravura",
    r"gravura em metal",
    r"gravura",
    r"desenho",
    r"escultura",
    r"resina pintada a mão",
    r"bronze",
    r"cerâmica",
    r"ceramica",
    r"fotografia",
    r"impressão",
    r"impressao",
]

CONDITION_PATTERNS = [
    r"no estado",
    r"com manchas?",
    r"manchas?",
    r"rasgos?",
    r"amarelamento",
    r"perdas?",
    r"restauros?",
    r"craquelê",
    r"craquele",
    r"avarias?",
    r"oxidação",
    r"oxidacao",
    r"foxing",
    r"pequenas avarias?",
    r"pequenas perdas?",
]

SIGNATURE_PATTERNS = [
    r"A\.C\.I\.D\.",
    r"A\.C\.I\.E\.",
    r"A\.I\.C\.D\.",
    r"A\.I\.C\.E\.",
    r"A\.V\.",
    r"a lápis",
    r"assinado(?:\(a\))?",
    r"assinada",
    r"assinado",
    r"datado(?:\(a\))?",
    r"datada",
    r"datado",
    r"com etiqueta da assinatura",
    r"com assinatura",
]


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def fold_text(value: str | None) -> str:
    text = normalize_space(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


def first_text(root: Any, selector: str) -> str:
    node = root.select_one(selector)
    return normalize_space(node.get_text(" ", strip=True) if node else "")


def meta_content(soup: BeautifulSoup, selector: str) -> str:
    node = soup.select_one(selector)
    return normalize_space(node.get("content") if node else "")


def remove_query(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def next_lot_url(url: str, current_lot: int) -> str:
    return lot_url(url, current_lot + 1)


def lot_url(url: str, lot_number: int) -> str:
    bare = remove_query(url).rstrip("/")
    if re.search(r"/\d+$", bare):
        return re.sub(r"/\d+$", f"/{lot_number}", bare)
    return f"{bare}/{lot_number}"


def clean_label(value: str, label: str) -> str | None:
    cleaned = re.sub(rf"^{re.escape(label)}\s*:?\s*", "", value, flags=re.I).strip()
    return cleaned or None


def unique(values: list[str | None]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value:
            continue
        item = normalize_space(value)
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    urls: list[str | None] = [
        meta_content(soup, "meta[property='og:image']"),
        meta_content(soup, "meta[itemprop='image']"),
    ]

    for node in soup.select("#img_principal, #img_principal_mobile, .img_adicionais a, .img_adicionais img"):
        urls.extend(
            [
                node.get("data-zoom-image"),
                node.get("data-image"),
                node.get("src"),
                node.get("href"),
            ]
        )

    return unique([urljoin(base_url, url) for url in urls if url])


def extract_lot(html: str, url: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    root = soup.select_one(".esp_lote_selecionado") or soup

    title = meta_content(soup, "meta[property='og:title']") or normalize_space(
        soup.title.get_text(" ", strip=True) if soup.title else ""
    )
    lot_number_match = re.search(r"\bLote\s+(\d+)\b", title, flags=re.I)
    lot_number = int(lot_number_match.group(1)) if lot_number_match else None

    if lot_number is None:
        lot_heading = first_text(root, ".descriptionTitle h6.hide-in-mobile")
        lot_heading_match = re.search(r"\bLote\s+(\d+)\b", lot_heading, flags=re.I)
        lot_number = int(lot_heading_match.group(1)) if lot_heading_match else None

    description_node = root.select_one("div.nome .mob-limit") or root.select_one("div.nome p")
    if description_node:
        description_fragment = BeautifulSoup(str(description_node), "lxml")
        description_node = description_fragment.select_one(".mob-limit") or description_fragment.select_one("p")
        for button in description_node.select(".btn-more"):
            button.decompose()
        description_html = "".join(str(child) for child in description_node.children).strip()
        description_text = normalize_space(description_node.get_text(" ", strip=True))
        description_text = re.sub(r"\s*Saiba mais\s*$", "", description_text, flags=re.I).strip()
    else:
        description_html = ""
        description_text = ""

    if not lot_number or not description_text:
        return None

    canonical = soup.select_one("link[rel='canonical']")
    canonical_url = canonical.get("href") if canonical else url

    contact_email_text = first_text(root, ".contato_emails")
    emails = unique(re.findall(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", contact_email_text, flags=re.I))
    phone = clean_label(first_text(root, ".contato_telefones"), "Telefone")
    image_urls = extract_images(soup, url)

    exhibition_node = root.select_one(".datas_exposicao")
    if exhibition_node:
        exhibition_parts = [
            normalize_space(part)
            for part in exhibition_node.get_text("\n", strip=True).splitlines()
            if normalize_space(part)
        ]
    else:
        exhibition_parts = []

    return {
        "lot_number": lot_number,
        "url": urljoin(url, canonical_url),
        "page_title": title,
        "meta_description": meta_content(soup, "meta[name='description']"),
        "description_text": description_text,
        "description_html": description_html,
        "categories": [normalize_space(node.get_text(" ", strip=True)) for node in root.select(".categ a")],
        "artists": unique(
            [node.get_text(" ", strip=True) for node in root.select(".box-artista a, span.bio_art a, span.bio_art")]
        ),
        "gallery": first_text(root, ".nome_galeria"),
        "auction": first_text(root, ".nome_leilao"),
        "catalog_url": urljoin(url, root.select_one(".capa_catalogo a").get("href"))
        if root.select_one(".capa_catalogo a")
        else None,
        "auctioneer": clean_label(first_text(root, ".dados_leiloeiro"), "Leiloeiro"),
        "lot_auction_datetime": first_text(root, ".datas_leilao"),
        "exhibition": exhibition_parts[0] if exhibition_parts else "",
        "address": " ".join(exhibition_parts[1:]),
        "phone": phone,
        "emails": emails,
        "current_value_brl": first_text(root, ".val_atual .val") or None,
        "currency_quotes": [
            normalize_space(node.get_text(" ", strip=True))
            for node in root.select(".esp_cotacao div")
            if re.search(r"\([A-Z]{3}\)", node.get_text(" ", strip=True))
        ],
        "auction_info_text": normalize_space(first_text(root, ".inf_leilao")),
        "image_url": (image_urls or [None])[0],
        "image_urls": image_urls,
    }


def extract_terms_and_buyer_premium(html: str, url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    terms_text = first_text(soup, "#aba_pag_termos")
    payments_text = first_text(soup, "#aba_pag_pagamentos")
    bid_confirmation_text = first_text(soup, "#aceite_termos")
    buyer_premium = extract_buyer_premium(payments_text or terms_text)

    return {
        "terms_and_conditions": {
            "source_url": url,
            "terms_text": terms_text or None,
            "payments_and_pickup_text": payments_text or None,
            "bid_confirmation_text": bid_confirmation_text or None,
        },
        "buyer_premium": buyer_premium,
    }


def extract_buyer_premium(text: str | None) -> dict[str, Any]:
    normalized_text = normalize_space(text)
    if not normalized_text:
        return {
            "percent": None,
            "applies_to_all_lots": True,
            "text": None,
            "source_section": None,
        }

    phrases = re.split(r"(?<=[.;])\s+", normalized_text)
    source_text = None
    for phrase in phrases:
        if re.search(r"comiss[aã]o do leiloeiro oficial", phrase, flags=re.I):
            source_text = normalize_space(phrase.strip(" .;"))
            break
    if source_text is None:
        for phrase in phrases:
            if re.search(r"comiss[aã]o do leiloeiro", phrase, flags=re.I):
                source_text = normalize_space(phrase.strip(" .;"))
                break

    percent = None
    if source_text:
        match = re.search(r"(\d+(?:[,.]\d+)?)\s*%", source_text)
        if match:
            percent = parse_brl(match.group(1))

    return {
        "percent": percent,
        "applies_to_all_lots": True,
        "text": source_text,
        "source_section": "Pagamentos e retiradas" if source_text else None,
    }


def parse_brl(value: Any) -> float | int | None:
    text = normalize_space(str(value)) if value is not None else ""
    if not text:
        return None
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text:
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def parse_auction_id(catalog_url: Any) -> str | None:
    text = normalize_space(str(catalog_url)) if catalog_url is not None else ""
    if not text:
        return None
    path = urlsplit(text).path.rstrip("/")
    match = re.search(r"/([^/]+)$", path)
    return match.group(1) if match else None


def parse_auction_date(value: Any) -> str | None:
    text = normalize_space(str(value)) if value is not None else ""
    if not text:
        return None
    if re.search(r"(?:Z|[+-]\d{2}:\d{2})$", text):
        return text
    match = re.search(r"(\d{2})/(\d{2})/(\d{4})\s*(?:às|as)?\s*(\d{1,2}):(\d{2})h?", text, flags=re.I)
    if not match:
        return text
    day, month, year, hour, minute = match.groups()
    return f"{year}-{month}-{day}T{int(hour):02d}:{minute}:00"


def apply_auction_timezone(auction_date: str | None, auction_location: str | None) -> str | None:
    if not auction_date:
        return None
    if re.search(r"(?:Z|[+-]\d{2}:\d{2})$", auction_date):
        return auction_date
    if auction_location and re.search(r"s[ãa]o paulo.*\bsp\b", fold_text(auction_location), flags=re.I):
        return f"{auction_date}-03:00"
    return auction_date


def unique_image_urls(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []

    keys: list[tuple[str, str, str]] = []
    best_by_key: dict[tuple[str, str, str], tuple[int, str]] = {}
    for value in values:
        url = normalize_space(str(value)) if value is not None else ""
        if not url or "noimage.png" in url.lower():
            continue

        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query_without_size = [(key, val) for key, val in query if key.lower() not in {"w", "h"}]
        image_key = (parts.scheme, parts.netloc, parts.path, urlencode(query_without_size))
        query_map = {key.lower(): val for key, val in query}
        try:
            score = int(query_map.get("w", "0")) * int(query_map.get("h", "0"))
        except ValueError:
            score = 0

        if image_key not in best_by_key:
            keys.append(image_key)
            best_by_key[image_key] = (score, url)
        elif score > best_by_key[image_key][0]:
            best_by_key[image_key] = (score, url)

    return [best_by_key[key][1] for key in keys]


def normalize_artist(lot: dict[str, Any], description: str | None) -> str | None:
    artists = lot.get("artists")
    if isinstance(artists, list):
        clean_artists = [normalize_space(str(artist)) for artist in artists if normalize_space(str(artist))]
        if len(clean_artists) == 1:
            return clean_artists[0]
    if lot.get("artist"):
        return normalize_space(str(lot.get("artist")))
    if description and " - " in description:
        return normalize_space(description.split(" - ", 1)[0])
    return None


def split_description(description: str | None, artist: str | None) -> tuple[str | None, str | None]:
    if not description:
        return None, None

    rest = description
    if " - " in rest:
        first_part, after_artist = rest.split(" - ", 1)
        if not artist or fold_text(first_part) == fold_text(artist):
            rest = after_artist
    elif artist and fold_text(rest).startswith(fold_text(artist)):
        rest = rest[len(artist) :].lstrip(" -")

    rest = normalize_space(rest)
    if not rest:
        return None, None

    dash_match = re.search(r"\s+-\s+", rest)
    period_match = re.search(r"\.\s+", rest)
    separators = [match for match in [dash_match, period_match] if match]
    separator = min(separators, key=lambda match: match.start()) if separators else None

    if separator:
        title = normalize_space(rest[: separator.start()].rstrip("."))
        remainder = normalize_space(rest[separator.end() :])
    else:
        title = rest
        remainder = None

    return title, remainder


def parse_medium(text: str | None) -> str | None:
    if not text:
        return None
    for pattern in MEDIUM_PATTERNS:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return normalize_space(match.group(0))
    return None


def parse_dimensions(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(
        r"\b\d+(?:[,.]\d+)?\s*x\s*\d+(?:[,.]\d+)?(?:\s*x\s*\d+(?:[,.]\d+)?)?\s*cm\b",
        text,
        flags=re.I,
    )
    return normalize_space(match.group(0)) if match else None


def parse_year(text: str | None) -> str | None:
    if not text:
        return None
    sem_data = re.search(r"\bsem data\b", text, flags=re.I)
    if sem_data:
        return normalize_space(sem_data.group(0))
    decade = re.search(r"\bdéc\.?\s*\d{2}\b", text, flags=re.I)
    if decade:
        return normalize_space(decade.group(0))
    years = re.findall(r"\b(?:18|19|20)\d{2}\b", text)
    if len(years) == 1:
        return years[0]
    if len(years) > 1:
        return ", ".join(years)
    return None


def parse_edition(text: str | None) -> str | None:
    if not text:
        return None

    patterns = [
        r"\bP\.A\. ?(?:[IVXLC\d]+)?\b",
        r"\bH\.C\. ?(?:[IVXLC\d]+)?\b",
        r"\bP/E\b",
        r"\b\d+\s*-\s*\d+\b",
        r"\b\d+\s*/\s*\d+\b",
        r"\b[Ee]dição de [\d.]+ exemplares\b",
        r"\bsem numeração\b",
    ]
    matches: list[tuple[int, str]] = []
    for pattern in patterns:
        matches.extend((match.start(), normalize_space(match.group(0))) for match in re.finditer(pattern, text, flags=re.I))

    ordered_matches: list[str] = []
    seen: set[str] = set()
    for _, match_text in sorted(matches, key=lambda item: item[0]):
        if match_text and match_text not in seen:
            seen.add(match_text)
            ordered_matches.append(match_text)
    return "; ".join(ordered_matches) or None


def parse_signature(text: str | None) -> str | None:
    if not text:
        return None

    matches: list[str] = []
    for pattern in SIGNATURE_PATTERNS:
        matches.extend(normalize_space(match.group(0)) for match in re.finditer(pattern, text, flags=re.I))
    return "; ".join(dict.fromkeys(match for match in matches if match)) or None


def parse_framed(text: str | None) -> bool | None:
    if not text:
        return None
    if re.search(r"\bsem moldura\b", text, flags=re.I):
        return False
    if re.search(r"\bcom moldura\b", text, flags=re.I):
        return True
    return None


def parse_condition(text: str | None) -> str | None:
    if not text:
        return None

    phrases: list[str] = []
    for sentence in re.split(r"(?<=[.;])\s+", text):
        if any(re.search(pattern, sentence, flags=re.I) for pattern in CONDITION_PATTERNS):
            cleaned = normalize_space(sentence.strip(" .;"))
            if cleaned:
                phrases.append(cleaned)
    return "; ".join(dict.fromkeys(phrases)) if phrases else None


def extract_phrase(text: str | None, patterns: list[str]) -> str | None:
    if not text:
        return None

    phrases: list[str] = []
    for sentence in re.split(r"(?<=[.;])\s+", text):
        if any(re.search(pattern, sentence, flags=re.I) for pattern in patterns):
            cleaned = normalize_space(sentence.strip(" .;"))
            if cleaned:
                phrases.append(cleaned)
    return "; ".join(dict.fromkeys(phrases)) if phrases else None


def parse_gallery_labels(text: str | None) -> str | None:
    if not text:
        return None

    label_terms = [
        r"galeria",
        r"gallery",
        r"ateli[eê]",
        r"atelier",
        r"museu",
        r"instituto",
        r"institui[çc][aã]o",
        r"funda[çc][aã]o",
        r"cole[çc][aã]o",
        r"exposi[çc][aã]o",
        r"acervo",
    ]
    phrases: list[str] = []
    for sentence in re.split(r"(?<=[.;])\s+", text):
        has_label_word = re.search(r"\b(?:etiqueta|carimbo|selo)\b", sentence, flags=re.I)
        is_signature_label = re.search(r"\betiqueta\s+(?:da|de|do)?\s*assinatura\b", sentence, flags=re.I)
        has_institutional_term = any(re.search(pattern, sentence, flags=re.I) for pattern in label_terms)
        if has_label_word and not is_signature_label and has_institutional_term:
            cleaned = normalize_space(sentence.strip(" .;"))
            if cleaned:
                phrases.append(cleaned)
    return "; ".join(dict.fromkeys(phrases)) if phrases else None


def normalize_lot(lot: dict[str, Any]) -> dict[str, Any]:
    description = normalize_space(str(lot.get("description_text"))) if lot.get("description_text") is not None else None
    artist = normalize_artist(lot, description)
    title, remainder = split_description(description, artist)
    detail_text = remainder or description
    auction_location = (
        normalize_space(str(lot.get("address") or lot.get("auction_location")))
        if lot.get("address") or lot.get("auction_location")
        else None
    )
    auction_date = apply_auction_timezone(
        parse_auction_date(lot.get("lot_auction_datetime") or lot.get("auction_date")),
        auction_location,
    )

    normalized = {
        "lot_number": lot.get("lot_number"),
        "url": normalize_space(str(lot.get("url"))) if lot.get("url") is not None else None,
        "auction_house": normalize_space(str(lot.get("gallery") or lot.get("auction_house")))
        if lot.get("gallery") or lot.get("auction_house")
        else None,
        "auction_name": normalize_space(str(lot.get("auction") or lot.get("auction_name")))
        if lot.get("auction") or lot.get("auction_name")
        else None,
        "auction_id": parse_auction_id(lot.get("catalog_url")) or lot.get("auction_id"),
        "auction_date": auction_date,
        "auction_location": auction_location,
        "currency": "BRL",
        "artist": artist,
        "title": title,
        "medium": parse_medium(detail_text),
        "dimensions": parse_dimensions(detail_text),
        "year": parse_year(detail_text),
        "edition": parse_edition(detail_text),
        "signature": parse_signature(detail_text),
        "framed": parse_framed(description),
        "current_bid_brl": parse_brl(lot.get("current_value_brl") or lot.get("current_bid_brl")),
        "estimate_low_brl": None,
        "estimate_high_brl": None,
        "bid_increment_brl": None,
        "status": None,
        "condition": parse_condition(description),
        "provenance": extract_phrase(description, [r"\bproced[eê]ncia\b", r"\bproveni[eê]ncia\b"]),
        "certificate": extract_phrase(description, [r"\bcertificado\b", r"\bcertifica[çc][aã]o\b"]),
        "gallery_labels": parse_gallery_labels(description),
        "literature": extract_phrase(description, [r"\bbibliografia\b", r"\bliteratura\b", r"\bpublicad[ao]\b"]),
        "exhibition_history": extract_phrase(description, [r"\bexposi[çc][aã]o\b", r"\bexibido\b", r"\bexposta?\b"]),
        "image_urls": unique_image_urls(lot.get("image_urls")),
        "description_text": description,
    }
    return {key: normalized.get(key) for key in NORMALIZED_COLUMNS}


def normalize_lots(lots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [normalize_lot(lot) for lot in lots]
    return sorted(normalized, key=lambda lot: (lot["lot_number"] is None, lot["lot_number"]))


def empty_shared_info() -> dict[str, Any]:
    return {
        "terms_and_conditions": {
            "source_url": None,
            "terms_text": None,
            "payments_and_pickup_text": None,
            "bid_confirmation_text": None,
        },
        "buyer_premium": {
            "percent": None,
            "applies_to_all_lots": True,
            "text": None,
            "source_section": None,
        },
    }


def normalize_output(lots: list[dict[str, Any]], shared_info: dict[str, Any] | None = None) -> dict[str, Any]:
    shared = shared_info or empty_shared_info()
    default_buyer_premium = empty_shared_info()["buyer_premium"]
    buyer_premium = shared.get("buyer_premium") or default_buyer_premium
    buyer_premium = {
        "percent": buyer_premium.get("percent"),
        "applies_to_all_lots": buyer_premium.get("applies_to_all_lots", True),
        "text": buyer_premium.get("text"),
        "source_section": buyer_premium.get("source_section"),
    }
    return {
        "terms_and_conditions": shared.get("terms_and_conditions") or empty_shared_info()["terms_and_conditions"],
        "buyer_premium": buyer_premium,
        "lots": normalize_lots(lots),
    }


def write_csv(lots: list[dict[str, Any]], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NORMALIZED_COLUMNS)
        writer.writeheader()
        for lot in lots:
            row = {column: lot.get(column) for column in NORMALIZED_COLUMNS}
            row["image_urls"] = " | ".join(lot.get("image_urls", []))
            writer.writerow(row)


def write_outputs(lots: list[dict[str, Any]], output: Path, shared_info: dict[str, Any] | None = None) -> None:
    normalized = normalize_output(lots, shared_info)
    output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(normalized["lots"], output.with_suffix(".csv"))


def scrape(
    start_url: str,
    output: Path,
    max_lots: int | None,
    start_lot: int | None,
    end_lot: int | None,
) -> list[dict[str, Any]]:
    lots: list[dict[str, Any]] = []
    shared_info: dict[str, Any] | None = None
    visited: set[str] = set()
    current_url = lot_url(start_url, start_lot) if start_lot is not None else start_url
    expected_lot: int | None = start_lot

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="pt-BR",
            viewport={"width": 1440, "height": 1100},
        )
        page = context.new_page()
        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in {"image", "media", "font"}
            else route.continue_(),
        )

        while current_url not in visited:
            if max_lots is not None and len(lots) >= max_lots:
                break

            visited.add(current_url)
            print(f"Fetching {current_url}", flush=True)

            response = None
            for attempt in range(1, 4):
                try:
                    response = page.goto(current_url, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_selector(".esp_lote_selecionado, .descriptionTitle", timeout=15_000)
                    break
                except (PlaywrightTimeoutError, PlaywrightError) as error:
                    if attempt == 3:
                        print(f"Stopping: navigation failed at {current_url}: {error}", flush=True)
                        write_outputs(lots, output, shared_info)
                        browser.close()
                        return lots
                    print(f"Retrying {current_url} after navigation error ({attempt}/3)", flush=True)
                    page.wait_for_timeout(2_000)

            if response and response.status >= 400:
                print(f"Stopping: HTTP {response.status} at {current_url}", flush=True)
                break

            html = page.content()
            if shared_info is None:
                shared_info = extract_terms_and_buyer_premium(html, current_url)

            lot = extract_lot(html, current_url)
            if not lot:
                print(f"Stopping: no lot data found at {current_url}", flush=True)
                break

            if expected_lot is not None and lot["lot_number"] != expected_lot:
                print(f"Stopping: expected lot {expected_lot}, found lot {lot['lot_number']}", flush=True)
                break

            lots.append(lot)
            if len(lots) % 25 == 0:
                write_outputs(lots, output, shared_info)
            if end_lot is not None and lot["lot_number"] >= end_lot:
                break
            expected_lot = lot["lot_number"] + 1
            current_url = next_lot_url(current_url, lot["lot_number"])

        browser.close()

    write_outputs(lots, output, shared_info)
    return lots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Starting iArremate lot URL, e.g. https://www.iarremate.com/cukier_arte/038/1")
    parser.add_argument("output", nargs="?", default="iarremate_lots.json", help="Output JSON path")
    parser.add_argument("--max-lots", type=int, default=None, help="Optional cap for testing")
    parser.add_argument("--start-lot", type=int, default=None, help="Optional first lot number to scrape")
    parser.add_argument("--end-lot", type=int, default=None, help="Optional last lot number to scrape, inclusive")
    args = parser.parse_args()

    if args.start_lot is not None and args.start_lot < 1:
        parser.error("--start-lot must be 1 or greater")
    if args.end_lot is not None and args.end_lot < 1:
        parser.error("--end-lot must be 1 or greater")
    if args.start_lot is not None and args.end_lot is not None and args.start_lot > args.end_lot:
        parser.error("--start-lot must be less than or equal to --end-lot")

    lots = scrape(args.url, Path(args.output), args.max_lots, args.start_lot, args.end_lot)
    print(f"Wrote {len(lots)} lots to {args.output} and {Path(args.output).with_suffix('.csv')}")


if __name__ == "__main__":
    main()
