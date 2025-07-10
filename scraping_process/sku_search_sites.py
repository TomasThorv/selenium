#!/usr/bin/env python3
"""
sku_search_sites.py – Search each SKU in ``skus.txt`` on a list of domains and
write the first few matching product links.  This version drops Selenium in
favour of ``requests`` + ``BeautifulSoup`` and processes multiple SKUs in
parallel.

Changes in v0.5 (2025‑07‑03)
───────────────────────────
* **No Selenium** – search result pages are fetched with ``requests``.
* **ThreadPoolExecutor** – several SKUs are searched concurrently.
* **Query cache** – repeated ``(sku, domain)`` searches reuse previous results.
"""

from __future__ import annotations

import pathlib
import sys
import re
from urllib.parse import urlparse
import concurrent.futures
import threading
import requests
from bs4 import BeautifulSoup

# ─── Configuration ────────────────────────────────────────────────────────────
TIMEOUT = 10  # seconds per request
SEARCH_URL = "https://duckduckgo.com/?q={query}&ia=web"
TITLE_SEL = "a[data-testid='result-title-a'], a.result__a"
STRICT_SKU_MATCH = True  # enforce exact SKU boundaries in URL
MAX_LINKS_PER_SKU = 4  # stop after N links per SKU
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}

ALLOWED_DOMAINS = [
    "solesense.com",
    "nike.com",
    "foot-store.com",
    "nike.ae",
    "soccervillage.com",
    "footy.com",
    "goat.com",
    "soccerpost.com",
    "kickscrew.com",
    "sportano.com",
    "puma.com",
    "soccerandrugby.com",
    "adsport.store",
    "mybrand.shoes",
    "u90soccer.com",
    "yoursportsperformance.com",
]

OUTPUT_FILE = "files/sku_links_limited.txt"
# ──────────────────────────────────────────────────────────────────────────────


def normalize(domain: str) -> str:
    d = domain.lower()
    return d[4:] if d.startswith("www.") else d


ALLOWED_NORMALIZED = {normalize(d) for d in ALLOWED_DOMAINS}

# ─── Query cache ─────────────────────────────────────────────────────────────
_cache: dict[tuple[str, str], str | None] = {}
_cache_lock = threading.Lock()

# ─── Search helper ────────────────────────────────────────────────────────────


def _search_domain(sku: str, domain: str, sku_regex: re.Pattern | None) -> str | None:
    """Return the first matching link for ``(sku, domain)`` or ``None``."""
    key = (sku, domain)
    with _cache_lock:
        if key in _cache:
            return _cache[key]

    query = f"site:{domain} {sku}"
    url = SEARCH_URL.format(query=query)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception:
        link = None
    else:
        soup = BeautifulSoup(resp.text, "html.parser")
        link = None
        for a in soup.select(TITLE_SEL):
            href = a.get("href", "")
            if not href.startswith("http"):
                continue
            if normalize(urlparse(href).netloc) != normalize(domain):
                continue
            if sku_regex and not sku_regex.search(href.lower()):
                continue
            link = href
            break

    with _cache_lock:
        _cache[key] = link
    return link


def find_links_for(sku: str) -> list[str]:
    """Return up to ``MAX_LINKS_PER_SKU`` product links for ``sku``."""
    collected: list[str] = []
    sku_lower = sku.lower()
    sku_regex = re.compile(rf"\b{re.escape(sku_lower)}\b") if STRICT_SKU_MATCH else None

    for domain in ALLOWED_DOMAINS:
        if len(collected) >= MAX_LINKS_PER_SKU:
            break
        link = _search_domain(sku, domain, sku_regex)
        if link:
            collected.append(link)

    return collected


# ─── Driver code ──────────────────────────────────────────────────────────────


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("files/skus.txt").read_text().splitlines()
        if s.strip()
    ]
    total = len(skus)

    print(f"🔍 Starting search for {total} SKUs across {len(ALLOWED_DOMAINS)} domains")
    print(
        f"📋 STRICT_SKU_MATCH={STRICT_SKU_MATCH}, MAX_LINKS_PER_SKU={MAX_LINKS_PER_SKU}"
    )
    print("─" * 60)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out, concurrent.futures.ThreadPoolExecutor() as ex:
        for idx, (sku, links) in enumerate(ex.map(lambda s: (s, find_links_for(s)), skus), 1):
            print(f"[{idx}/{total}] {sku}", end=" … ")
            if links:
                for link in links:
                    out.write(f"{sku}\t{link}\n")
                print(f"✓ {len(links)} link(s)")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")
                print("❌ No results")

    print("─" * 60)
    print(f"✅ Done. Results → {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
