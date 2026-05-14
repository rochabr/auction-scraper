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
from io import BytesIO
import json
import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

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
    r"óleo sobre tela colada em cartão grosso",
    r"óleo sobre tela colada em cart[aã]o grosso",
    r"óleo sobre e colagem sobre madeira",
    r"acrílica sobre tela colada em eucatex",
    r"acrílica e alumínio sobre eucatex",
    r"acrílica, recortes e colagens sobre cartão",
    r"acrílica, recortes e colagens sobre cart[aã]o",
    r"acrílica e areia sobre tela",
    r"guache sobre papel colado em eucatex",
    r"nanquim e aquarela sobre papel",
    r"serigrafia sobre acrílico",
    r"serigrafia em acrílico",
    r"serigrafia sobre cartão",
    r"serigrafia sobre cart[aã]o",
    r"serigrafia objeto",
    r"serigrafia póstuma",
    r"monotipia sobre papel",
    r"giclée e gliter sobre tela",
    r"giclée e acrílica sobre tela",
    r"giclée sobre tela",
    r"giclee e gliter sobre tela",
    r"giclee e acrilica sobre tela",
    r"giclee sobre tela",
    r"têmpera sobre tela",
    r"tempera sobre tela",
    r"spray sobre aglomerado de madeira",
    r"vinil e colagens encerados sobre tela colada em madeira",
    r"vinil encerado sobre tela eucatex",
    r"vinil sobre tela",
    r"óleo e pastel sobre eucatex",
    r"óleo sobre e pastel eucatex",
    r"óleo sobre eucatex",
    r"óleo sobre madeira",
    r"pastel sobre papel",
    r"guache e pastel sobre papel",
    r"guache e giz de cera sobre papel",
    r"guache sobre cartão",
    r"guache sobre cart[aã]o",
    r"guache sobre pape colado em eucatex",
    r"acrílica sobre papel",
    r"acrílica sobre madeira nobre",
    r"acrílica sobre madeira",
    r"acrílica encerada sobre tela",
    r"acrílica sobre cartão",
    r"acrílica sobre cart[aã]o",
    r"aguada de nanquim",
    r"nanquim e aguada sobre papel",
    r"grafite e lápis de cor sobre papel",
    r"óleo sobre tela",
    r"óleo sobre juta",
    r"óleo s/tela",
    r"acrílica sobre tela",
    r"acrílica s/tela",
    r"acrilica sobre tela",
    r"acrílica e areia sobre tela",
    r"guache sobre papel",
    r"aquarela sobre papel",
    r"nanquim sobre papel",
    r"liquitex sobre papel",
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
    r"desenho a sanguínea",
    r"desenho crayon tr6es cores, papel canson cinza",
    r"desenho crayon tr[êe]s cores, papel canson cinza",
    r"desenho grafite",
    r"bronze",
    r"cerâmica",
    r"ceramica",
    r"fotografia",
    r"impressão",
    r"impressao",
    r"offset",
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
    r"AC\.I\.D\.",
    r"\bACID\b",
    r"A\.C\.D\.",
    r"A\.C\.I\.",
    r"A\.C\.I\.E\.",
    r"A\.C\.S\.E\.",
    r"A\.I\.C\.D\.",
    r"A\.I\.C\.E\.",
    r"A\.V\.",
    r"A\.\s*V\.",
    r"A\.C\.S\.",
    r"A\.C\.",
    r"\be V\.",
    r"A\.\s*Internamente a caneta",
    r"Internamente a caneta",
    r"a lápis",
    r"assinado(?:\(a\))?",
    r"assinada",
    r"assinado",
    r"datado(?:\(a\))?",
    r"datada",
    r"datado",
    r"\(?na matriz\)?",
    r"com etiqueta da assinatura",
    r"com assinatura",
    r"com chancela (?:do|da|de) [^. ,;]+(?: [^. ,;]+){0,4}",
    r"chancela (?:do|da|de) [^. ,;]+(?: [^. ,;]+){0,4}",
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
    parts = urlsplit(remove_query(url))
    path_parts = [part for part in parts.path.split("/") if part]
    if len(path_parts) >= 3 and path_parts[-1].isdigit():
        path_parts[-1] = str(lot_number)
    else:
        path_parts.append(str(lot_number))
    return urlunsplit((parts.scheme, parts.netloc, "/" + "/".join(path_parts), "", ""))


def lot_number_from_url(url: str) -> int | None:
    path_parts = [part for part in urlsplit(remove_query(url)).path.split("/") if part]
    if len(path_parts) >= 3 and path_parts[-1].isdigit():
        return int(path_parts[-1])
    return None


def auction_basename_from_url(url: str) -> str:
    parts = [part for part in urlsplit(remove_query(url)).path.split("/") if part]
    if len(parts) >= 3 and parts[-1].isdigit():
        gallery_slug, auction_id = parts[-3], parts[-2]
    elif len(parts) >= 2:
        gallery_slug, auction_id = parts[-2], parts[-1]
    else:
        return "iarremate_lots"

    gallery_slug = re.sub(r"[^A-Za-z0-9_-]+", "-", gallery_slug).strip("-_")
    auction_id = re.sub(r"[^A-Za-z0-9_-]+", "-", auction_id).strip("-_")
    return f"{gallery_slug}_{auction_id}" if gallery_slug and auction_id else "iarremate_lots"


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

    compact_text = re.sub(r"\s+", " ", normalized_text)
    source_text = None
    match = re.search(
        r"(?:\d+[ªa]\.?)?[^.]*?comiss[aãõ]o do leiloeiro oficial.*?(?=(?:\d+[ªa]\.)|$)",
        compact_text,
        flags=re.I,
    )
    if not match:
        match = re.search(r"[^.]*?comiss[aãõ]o do leiloeiro.*?(?=(?:\d+[ªa]\.)|$)", compact_text, flags=re.I)
    if match:
        source_text = normalize_space(match.group(0).strip(" .;"))

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


def description_after_artist(description: str | None) -> str | None:
    if not description:
        return None
    if " - " in description:
        return normalize_space(description.split(" - ", 1)[1])
    return normalize_space(description)


def strip_leading_artist_bio(text: str | None) -> str | None:
    rest = normalize_space(text)
    if not rest:
        return None
    rest = re.sub(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇÜÑ .'-]+(?:\s+\([^)]+\))?\s+", "", rest)
    return normalize_space(rest)


def medium_match(text: str | None) -> re.Match[str] | None:
    if not text:
        return None
    matches: list[re.Match[str]] = []
    for pattern in MEDIUM_PATTERNS:
        match = re.search(pattern, text, flags=re.I)
        if match:
            matches.append(match)
    if not matches:
        return None
    return min(matches, key=lambda match: (match.start(), -(match.end() - match.start())))


def parse_title(description: str | None, artist: str | None) -> tuple[str | None, str | None]:
    if not description:
        return None, None

    has_dash_format = " - " in description
    rest = description_after_artist(description) or description
    if rest == description and artist and fold_text(rest).startswith(fold_text(artist)):
        rest = rest[len(artist) :].lstrip(" -")
    rest = normalize_space(rest)

    medium = medium_match(rest)
    if has_dash_format and medium and medium.start() > 0:
        pre_medium = normalize_space(rest[: medium.start()].strip(" .,-"))
        if pre_medium:
            title = "Sem título" if fold_text(pre_medium).startswith("sem titulo") else pre_medium
            return title, normalize_space(rest[medium.start() :])

    stripped = strip_leading_artist_bio(description)
    medium = medium_match(stripped)
    if stripped and medium and medium.start() == 0:
        after_medium = normalize_space(stripped[medium.end() :].lstrip(" .,-"))
        quoted = re.search(r'"([^"]+)"', after_medium)
        if quoted:
            return normalize_space(quoted.group(1)), stripped
        sentences = [normalize_space(part.strip(" .,-")) for part in re.split(r"\.\s*", after_medium) if normalize_space(part.strip(" .,-"))]
        for sentence in sentences:
            if not re.search(r"^(?:d[ée]cada|datado|med(?:idas?)?)\\b", fold_text(sentence), flags=re.I):
                return sentence, stripped

    return None, None


def split_description(description: str | None, artist: str | None) -> tuple[str | None, str | None]:
    if not description:
        return None, None

    parsed_title, parsed_remainder = parse_title(description, artist)
    if parsed_title:
        return parsed_title, parsed_remainder

    rest = description_after_artist(description) or description
    if artist and rest == description and fold_text(rest).startswith(fold_text(artist)):
        rest = rest[len(artist) :].lstrip(" -")

    rest = normalize_space(rest)
    if not rest:
        return None, None

    medium = medium_match(rest)
    dash_match = re.search(r"\s+-\s+", rest)

    if dash_match and (medium is None or dash_match.start() < medium.start()):
        title = normalize_space(rest[: dash_match.start()].strip(" .,-"))
        remainder = normalize_space(rest[dash_match.end() :])
    elif medium:
        title = normalize_space(rest[: medium.start()].strip(" .,-"))
        remainder = normalize_space(rest[medium.start() :])
    else:
        comma_match = re.search(r",\s+", rest)
        period_match = re.search(r"\.\s+", rest)
        separators = [match for match in [comma_match, period_match] if match]
        separator = min(separators, key=lambda match: match.start()) if separators else None
        title = normalize_space(rest[: separator.start()].strip(" .,-")) if separator else rest
        remainder = normalize_space(rest[separator.end() :]) if separator else None

    if artist and fold_text(title) == fold_text(artist):
        return None, remainder
    if fold_text(title).startswith("sem titulo"):
        title = "Sem título"

    if not title:
        title = None
        remainder = None

    return title, remainder


def parse_medium(text: str | None) -> str | None:
    match = medium_match(text)
    return normalize_space(match.group(0)) if match else None


def parse_dimensions(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(
        r"\b\d+(?:[,.]\d+)?\s*x\s*\d+(?:[,.]\d+)?(?:\s*x\s*\d+(?:[,.]\d+)?)?\s*cm(?:\s*\([^)]*\))?",
        text,
        flags=re.I,
    )
    if not match:
        match = re.search(r"\b\d+(?:[,.]\d+)?\s*cm\s+de\s+di[âa]metro\b", text, flags=re.I)
    return normalize_space(match.group(0)) if match else None


def parse_year(text: str | None) -> str | None:
    if not text:
        return None
    datado = re.search(r"\bdatad[oa]\s*:?\s*((?:18|19|20)\d{2})\b", text, flags=re.I)
    if datado:
        return datado.group(1)
    any_decade = re.search(r"\bdécada\s+de\s+(?:18|19|20)\d0\b", text, flags=re.I)
    if any_decade:
        return normalize_space(any_decade.group(0))
    dimension = parse_dimensions(text)
    search_text = text
    if dimension:
        dim_index = fold_text(text).find(fold_text(dimension))
        if dim_index >= 0:
            search_text = text[dim_index + len(dimension) :]

    sem_data = re.search(r"\bsem data\b", search_text, flags=re.I)
    if sem_data:
        return normalize_space(sem_data.group(0))
    decade = re.search(r"\bdéc\.?\s*\d{2}\b", search_text, flags=re.I)
    if decade:
        return normalize_space(decade.group(0))
    year_range = re.search(r"\b((?:18|19|20)\d{2}\s*-\s*(?:18|19|20)\d{2})\b", search_text)
    if year_range:
        return normalize_space(year_range.group(1))
    year = re.search(r"\b(?:18|19|20)\d{2}\b", search_text)
    if year:
        return year.group(0)
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
        for match in re.finditer(pattern, text, flags=re.I):
            match_text = normalize_space(match.group(0))
            if re.fullmatch(r"\d{4}\s*-\s*\d{4}", match_text):
                continue
            matches.append((match.start(), match_text))

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

    matches: list[tuple[int, int, str]] = []
    for pattern in SIGNATURE_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.I):
            sentence_start = max(text.rfind(".", 0, match.start()), text.rfind(";", 0, match.start())) + 1
            sentence_end_candidates = [idx for idx in [text.find(".", match.end()), text.find(";", match.end())] if idx != -1]
            sentence_end = min(sentence_end_candidates) if sentence_end_candidates else len(text)
            sentence = text[sentence_start:sentence_end]
            match_text = normalize_space(match.group(0).strip("() "))
            if re.fullmatch(r"assinado(?:\(a\))?|assinada|assinado", match_text, flags=re.I) and re.search(
                r"certificado", sentence, flags=re.I
            ):
                continue
            if fold_text(match_text) == "na matriz":
                match_text = "na matriz"
            matches.append((match.start(), match.end(), match_text))

    ordered_matches: list[str] = []
    accepted_ranges: list[tuple[int, int]] = []
    seen: set[str] = set()
    for start, end, match_text in sorted(matches, key=lambda item: (item[0], -(item[1] - item[0]))):
        if any(start < accepted_end and end > accepted_start for accepted_start, accepted_end in accepted_ranges):
            continue
        if match_text and match_text not in seen:
            seen.add(match_text)
            accepted_ranges.append((start, end))
            ordered_matches.append(match_text)
    return "; ".join(ordered_matches) or None


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


def clean_leading_framing(value: str | None) -> str | None:
    text = normalize_space(value)
    if not text:
        return None
    text = re.sub(r"^(?:com|sem)\s+moldura\s*(?:e|,)?\s*", "", text, flags=re.I)
    return normalize_space(text.strip(" .;,")) or None


def parse_certificate(text: str | None) -> str | None:
    if not text:
        return None

    matches: list[str] = []
    patterns = [
        r"certificado de autenticidade emitido pelo artista",
        r"certificado emitido pelo artista",
        r"certificado de autenticidade assinado pelo próprio [^. ;,]+(?: [^. ;,]+){0,4}",
        r"certificado de autenticidade assinado pelo pr[óo]r?prio [^. ;,]+(?: [^. ;,]+){0,4}",
        r"certificado assinado pelo artista",
        r"certificado assinado pelo pr[óo]r?prio [^. ;,]+(?: [^. ;,]+){0,4}",
        r"certificado assinado pelo pr[óo]rpio [^. ;,]+(?: [^. ;,]+){0,4}",
        r"certificado assinado pelo [^. ;,]+(?: [^. ;,]+){0,4}",
        r"certificado de autenticidade [^. ;]+(?: [^. ;]+){0,8}",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            cleaned = clean_leading_framing(match.group(0))
            if cleaned:
                matches.append(cleaned)
    return "; ".join(dict.fromkeys(matches)) if matches else None


def parse_gallery_labels(text: str | None) -> str | None:
    if not text:
        return None

    patterns = [
        r"etiqueta\s+(?:da|do|de)\s+(?:Galeria|Gallery|Ateli[eê]|Atelier|Museu|Instituto|Institui[çc][aã]o|Funda[çc][aã]o|Cole[çc][aã]o|Exposi[çc][aã]o|Acervo)[^. ;,]*(?: [^. ;,]+){0,8}",
        r"(?:selo|carimbo)\s+(?:da|do|de)\s+(?:Galeria|Gallery|Ateli[eê]|Atelier|Museu|Instituto|Institui[çc][aã]o|Funda[çc][aã]o|Cole[çc][aã]o|Exposi[çc][aã]o|Acervo)[^. ;,]*(?: [^. ;,]+){0,8}",
        r"chancela\s+(?:da|do|de)\s+(?:Galeria|IAC|Instituto|Funda[çc][aã]o|Ateli[eê]|Atelier)[^. ;,]*(?: [^. ;,]+){0,8}",
    ]
    matches: list[tuple[int, str]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            cleaned = clean_leading_framing(match.group(0))
            if cleaned and not re.search(r"etiqueta\s+(?:da|de|do)?\s*assinatura", cleaned, flags=re.I):
                matches.append((match.start(), cleaned))

    ordered_matches: list[str] = []
    seen: set[str] = set()
    for _, match_text in sorted(matches, key=lambda item: item[0]):
        if match_text not in seen:
            seen.add(match_text)
            ordered_matches.append(match_text)
    return "; ".join(ordered_matches) if ordered_matches else None


def parse_provenance(text: str | None) -> str | None:
    return extract_phrase(
        text,
        [
            r"\bpertencia a\b",
            r"\bcole[çc][aã]o\b",
            r"\bproveni[eê]ncia\b",
            r"\brecebeu essa obra\b",
            r"\btroca com\b",
            r"\bacervo\b",
        ],
    )


def parse_exhibition_history(text: str | None) -> str | None:
    return extract_phrase(
        text,
        [
            r"\bobra (?:foi )?expost[ao]\b",
            r"\bexpost[ao] (?:na|no|em)\b",
            r"\bexibid[ao] (?:na|no|em)\b",
            r"\bparticipou (?:da|do|de)\b",
            r"\bBienal\b",
            r"\bSal[aã]o\b",
            r"\bmostra\b",
        ],
    )


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
        "estimate_low_brl": parse_brl(lot.get("estimate_low_brl")) if lot.get("estimate_low_brl") is not None else None,
        "estimate_high_brl": parse_brl(lot.get("estimate_high_brl")) if lot.get("estimate_high_brl") is not None else None,
        "bid_increment_brl": parse_brl(lot.get("bid_increment_brl")) if lot.get("bid_increment_brl") is not None else None,
        "status": normalize_space(str(lot.get("status"))) if lot.get("status") else None,
        "condition": parse_condition(description),
        "provenance": parse_provenance(description),
        "certificate": parse_certificate(description),
        "gallery_labels": parse_gallery_labels(description),
        "literature": extract_phrase(description, [r"\bbibliografia\b", r"\bliteratura\b", r"\bpublicad[ao]\b"]),
        "exhibition_history": parse_exhibition_history(description),
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


def write_outputs(lots: list[dict[str, Any]], output: Path, shared_info: dict[str, Any] | None = None) -> None:
    normalized = normalize_output(lots, shared_info)
    output.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")


def formatted_lot_number(value: Any) -> str:
    try:
        lot_number = int(value)
    except (TypeError, ValueError):
        return "unknown-lot"
    if 1 <= lot_number <= 99:
        return f"{lot_number:03d}"
    return str(lot_number)


def image_filename(lot: dict[str, Any], image_index: int, image_count: int) -> str:
    lot_number = formatted_lot_number(lot.get("lot_number"))
    suffix = f"-{image_index}" if image_count > 1 else ""
    return f"{lot_number}{suffix}.png"


def save_png_image(image_bytes: bytes, destination: Path) -> None:
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError(
            "Image downloads require Pillow. Install it with: "
            ".venv/bin/python -m pip install pillow"
        ) from error

    with Image.open(BytesIO(image_bytes)) as image:
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        image.save(destination, format="PNG")


def download_lot_images(lots: list[dict[str, Any]], image_dir: Path) -> int:
    image_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    for lot in lots:
        image_urls = lot.get("image_urls")
        if not isinstance(image_urls, list):
            continue
        image_count = len([url for url in image_urls if url])
        for index, image_url in enumerate(image_urls, start=1):
            if not image_url:
                continue
            request = Request(image_url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=60) as response:
                destination = image_dir / image_filename(lot, index, image_count)
                save_png_image(response.read(), destination)
                downloaded += 1

    return downloaded


def scrape(
    start_url: str,
    output: Path,
    max_lots: int | None,
    start_lot: int | None,
    end_lot: int | None,
    image_dir: Path | None,
) -> list[dict[str, Any]]:
    lots: list[dict[str, Any]] = []
    shared_info: dict[str, Any] | None = None
    current_lot_number = start_lot or lot_number_from_url(start_url) or 1
    missing_streak = 0

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

        while True:
            if max_lots is not None and len(lots) >= max_lots:
                break
            if end_lot is not None and current_lot_number > end_lot:
                break

            current_url = lot_url(start_url, current_lot_number)
            print(f"Fetching {current_url}", flush=True)

            response = None
            html = ""
            for attempt in range(1, 4):
                try:
                    response = page.goto(current_url, wait_until="domcontentloaded", timeout=60_000)
                except (PlaywrightTimeoutError, PlaywrightError) as error:
                    if attempt == 3:
                        print(f"Stopping: navigation failed at {current_url}: {error}", flush=True)
                        write_outputs(lots, output, shared_info)
                        browser.close()
                        return lots
                    print(f"Retrying {current_url} after navigation error ({attempt}/3)", flush=True)
                    page.wait_for_timeout(2_000)
                    continue

                try:
                    page.wait_for_selector(".esp_lote_selecionado, .descriptionTitle", timeout=15_000)
                except PlaywrightTimeoutError:
                    pass
                html = page.content()
                break

            if response and response.status >= 400:
                print(f"No lot data found at {current_url} (HTTP {response.status})", flush=True)
                lot = None
            else:
                if shared_info is None and html:
                    shared_info = extract_terms_and_buyer_premium(html, current_url)

                lot = extract_lot(html, current_url) if html else None
                if lot and lot["lot_number"] != current_lot_number:
                    print(
                        f"No lot data found at {current_url} "
                        f"(found lot {lot['lot_number']} instead)",
                        flush=True,
                    )
                    lot = None

            if not lot:
                missing_streak += 1
                if missing_streak >= 4:
                    print(
                        f"Stopping after {missing_streak} consecutive missing lots, "
                        f"ending at lot {current_lot_number}",
                        flush=True,
                    )
                    break
                current_lot_number += 1
                continue

            missing_streak = 0
            lots.append(lot)
            if len(lots) % 25 == 0:
                write_outputs(lots, output, shared_info)
            if end_lot is not None and lot["lot_number"] >= end_lot:
                break
            current_lot_number = lot["lot_number"] + 1

        browser.close()

    write_outputs(lots, output, shared_info)
    if image_dir is not None:
        normalized_lots = normalize_lots(lots)
        downloaded = download_lot_images(normalized_lots, image_dir)
        print(f"Downloaded {downloaded} images to {image_dir}", flush=True)
    return lots


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Starting iArremate lot URL, e.g. https://www.iarremate.com/cukier_arte/038/1")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Optional output JSON path. Defaults to {auction-slug}_{auction-id}.json",
    )
    parser.add_argument("--max-lots", type=int, default=None, help="Optional cap for testing")
    parser.add_argument("--start-lot", type=int, default=None, help="Optional first lot number to scrape")
    parser.add_argument("--end-lot", type=int, default=None, help="Optional last lot number to scrape, inclusive")
    parser.add_argument(
        "--download-images",
        nargs="?",
        const="",
        default=None,
        metavar="DIR",
        help="Download lot images. Defaults to images/{auction-slug}_{auction-id}/ when DIR is omitted.",
    )
    args = parser.parse_args()

    if args.start_lot is not None and args.start_lot < 1:
        parser.error("--start-lot must be 1 or greater")
    if args.end_lot is not None and args.end_lot < 1:
        parser.error("--end-lot must be 1 or greater")
    if args.start_lot is not None and args.end_lot is not None and args.start_lot > args.end_lot:
        parser.error("--start-lot must be less than or equal to --end-lot")

    default_name = auction_basename_from_url(args.url)
    output = Path(args.output) if args.output else Path(f"{default_name}.json")
    image_dir = None
    if args.download_images is not None:
        image_dir = Path(args.download_images) if args.download_images else Path("images") / default_name

    lots = scrape(args.url, output, args.max_lots, args.start_lot, args.end_lot, image_dir)
    print(f"Wrote {len(lots)} lots to {output}")


if __name__ == "__main__":
    main()
