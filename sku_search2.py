#!/usr/bin/env python3
"""
sku_search_limited.py – Search each SKU in **skus.txt** on a restricted list of
domains and write at most **two** product‑page links per SKU.

Changes in v0.4 (2025‑07‑03)
────────────────────────────
* New constant **`MAX_LINKS_PER_SKU = 2`**
* `find_links_for()` stops searching once that many links have been collected,
  so we no longer gather a long tail of results.
* Everything else – input file, output file, CLI flags – stays exactly the same.
"""

from __future__ import annotations

import pathlib, sys, time, re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ─── Configuration ────────────────────────────────────────────────────────────
CHROMEDRIVER = "chromedriver"  # executable name or full path
TIMEOUT = 10  # seconds per search/page load
SEARCH_URL = "https://duckduckgo.com/?q={query}&ia=web"
TITLE_SEL = "a[data-testid='result-title-a'], a.result__a"
HEADLESS = True  # flip to False to see browser
STRICT_SKU_MATCH = True  # enforce exact SKU boundaries in URL
MAX_LINKS_PER_SKU = 2  # ← new: stop after N links per SKU

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

OUTPUT_FILE = "sku_links_limited.txt"
# ──────────────────────────────────────────────────────────────────────────────


def normalize(domain: str) -> str:
    d = domain.lower()
    return d[4:] if d.startswith("www.") else d


ALLOWED_NORMALIZED = {normalize(d) for d in ALLOWED_DOMAINS}

# ─── Selenium bootstrap ───────────────────────────────────────────────────────
opts = webdriver.ChromeOptions()
if HEADLESS:
    opts.add_argument("--headless=new")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
try:
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)
except Exception as e:
    sys.exit(f"❌ Could not start Chrome: {e}")

wait = WebDriverWait(driver, TIMEOUT)

# ─── Search helper ────────────────────────────────────────────────────────────


def find_links_for(sku: str) -> list[str]:
    """Return up to *MAX_LINKS_PER_SKU* product links for *sku*."""
    collected: dict[str, str] = {}
    sku_lower = sku.lower()
    sku_regex = re.compile(rf"\b{re.escape(sku_lower)}\b") if STRICT_SKU_MATCH else None

    for domain in ALLOWED_DOMAINS:
        if len(collected) >= MAX_LINKS_PER_SKU:
            break  # we already have enough links ➜ stop searching

        query = f"site:{domain} {sku}"
        driver.get(SEARCH_URL.format(query=query))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SEL)))
        except TimeoutException:
            continue

        for a in driver.find_elements(By.CSS_SELECTOR, TITLE_SEL):
            href = a.get_attribute("href") or ""
            if not href.startswith("http"):
                continue
            if normalize(urlparse(href).netloc) != normalize(domain):
                continue
            if sku_regex and not sku_regex.search(href.lower()):
                continue
            collected[normalize(domain)] = href
            break  # one link per domain is enough

        time.sleep(0.2)  # politeness delay

    return list(collected.values())


# ─── Driver code ──────────────────────────────────────────────────────────────


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("skus.txt").read_text().splitlines()
        if s.strip()
    ]
    total = len(skus)

    print(f"🔍 Starting search for {total} SKUs across {len(ALLOWED_DOMAINS)} domains")
    print(
        f"📋 STRICT_SKU_MATCH={STRICT_SKU_MATCH}, MAX_LINKS_PER_SKU={MAX_LINKS_PER_SKU}"
    )
    print("─" * 60)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for idx, sku in enumerate(skus, 1):
            print(f"[{idx}/{total}] {sku}", end=" … ")
            links = find_links_for(sku)
            if links:
                for link in links:
                    out.write(f"{sku}\t{link}\n")
                print(f"✓ {len(links)} link(s)")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")
                print("❌ No results")

    print("─" * 60)
    print(f"✅ Done. Results → {OUTPUT_FILE}")
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        driver.quit()
        print("\nInterrupted by user.")
