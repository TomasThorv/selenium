#!/usr/bin/env python3
"""
sku_search_async.py (dual‑progress edition)
==========================================

▶ **Two live progress bars**

* **Domain requests** (top bar): ticks every time *any* site query finishes –
  you immediately see the script working even with thousands of SKUs.
* **SKUs completed** (bottom bar): advances once a whole SKU (all its domain
  searches) is done.

Run with:

    $ python sku_search_async.py

Input  : `files/skus.txt` (one SKU per line)
Output : `files/sku_search_results.csv`

Dependencies:

    pip install "httpx[http2]" beautifulsoup4 tqdm
"""
from __future__ import annotations

import asyncio
import csv
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Iterable, List, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm
from tqdm.asyncio import tqdm_asyncio  # type: ignore

# --------------------------------------------------------------------------- #
# CONFIGURATION                                                               #
# --------------------------------------------------------------------------- #
INPUT_FILE: Path = Path("files/skus.txt")
OUTPUT_FILE: Path = Path("files/sku_search_results.csv")

ALLOWED_DOMAINS: List[str] = [
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

SEARCH_URL: str = "https://duckduckgo.com/lite?q={query}"
TITLE_SELECTOR: str = "a.result-link"

TIMEOUT_SECS: int = 10  # per‑request timeout
CONCURRENT_QUERIES: int = 50  # global parallel requests
MAX_LINKS_PER_SKU: int = 2  # stop after this many matches per SKU
FUZZY_MATCH: bool = False  # True → substring match; False → word‑boundaries

# --------------------------------------------------------------------------- #
# GLOBAL PROGRESS BAR (updated from every task)                               #
# --------------------------------------------------------------------------- #
_domain_bar: Optional[tqdm] = None  # will become a real bar in _gather_all

# --------------------------------------------------------------------------- #
# NETWORK HELPERS                                                             #
# --------------------------------------------------------------------------- #


async def _fetch(session: httpx.AsyncClient, url: str) -> str | None:
    try:
        r = await session.get(url)
        r.raise_for_status()
        return r.text
    except (httpx.HTTPError, httpx.TimeoutException):
        return None


async def _search_domain(
    session: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    sku: str,
    domain: str,
    regex: re.Pattern,
) -> str | None:
    """Return first valid link for *sku* on *domain*, else None."""
    global _domain_bar
    query = f"site:{domain} {sku}"
    url = SEARCH_URL.format(query=urllib.parse.quote_plus(query))

    async with sem:
        html = await _fetch(session, url)

    link: str | None = None
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select(TITLE_SELECTOR):
            href = a.get("href", "")
            if (
                href.startswith("http")
                and domain in href
                and regex.search(href.lower())
            ):
                link = href
                print(f"[{sku}] ✓ {domain}")
                break
    # tick the domain‑level bar regardless of outcome
    if _domain_bar is not None:
        _domain_bar.update(1)
    return link


async def _links_for_sku(
    session: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    sku: str,
) -> List[str]:
    regex = (
        re.compile(re.escape(sku.lower()))
        if FUZZY_MATCH
        else re.compile(rf"\b{re.escape(sku.lower())}\b")
    )
    tasks = [
        asyncio.create_task(_search_domain(session, sem, sku, d, regex))
        for d in ALLOWED_DOMAINS
    ]
    found: List[str] = []
    for coro in asyncio.as_completed(tasks):
        link = await coro
        if link:
            found.append(link)
            if len(found) == MAX_LINKS_PER_SKU:
                for t in tasks:
                    t.cancel()
                break
    print(f"[{sku}] ⇒ {len(found)} link(s) found")
    return found


async def _gather_all(skus: Iterable[str]) -> Dict[str, List[str]]:
    """Gather links for every SKU while showing two progress bars."""
    global _domain_bar

    total_domains = len(skus) * len(ALLOWED_DOMAINS)
    _domain_bar = tqdm(total=total_domains, desc="Domain requests", unit="req")

    sem = asyncio.Semaphore(CONCURRENT_QUERIES)
    timeout = httpx.Timeout(TIMEOUT_SECS)
    async with httpx.AsyncClient(
        follow_redirects=True, timeout=timeout, http2=True
    ) as s:
        coros = [_links_for_sku(s, sem, sku) for sku in skus]
        # bottom bar (SKUs completed)
        results = await tqdm_asyncio.gather(*coros, desc="SKUs done", unit="sku")

    _domain_bar.close()
    return dict(zip(skus, results))


# --------------------------------------------------------------------------- #
# I/O UTILITIES                                                               #
# --------------------------------------------------------------------------- #


def _load_skus() -> List[str]:
    if not INPUT_FILE.exists():
        sys.exit(f"Input file not found: {INPUT_FILE}")
    skus = [
        l.strip()
        for l in INPUT_FILE.read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    if not skus:
        sys.exit("No SKUs in input file.")
    return skus


def _write_csv(res: Dict[str, List[str]]) -> None:
    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sku"] + [f"link{i+1}" for i in range(MAX_LINKS_PER_SKU)])
        for sku, links in res.items():
            w.writerow([sku] + links)
    print(f"📄 CSV saved → {OUTPUT_FILE.absolute()}")


# --------------------------------------------------------------------------- #
# MAIN                                                                        #
# --------------------------------------------------------------------------- #


def main() -> None:
    skus = _load_skus()
    print(
        f"🔍 {len(skus):,} SKU(s) × {len(ALLOWED_DOMAINS)} domain(s) = {len(skus)*len(ALLOWED_DOMAINS):,} requests …"
    )
    res = asyncio.run(_gather_all(skus))
    _write_csv(res)


if __name__ == "__main__":
    main()
