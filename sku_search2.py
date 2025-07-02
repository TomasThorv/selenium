#!/usr/bin/env python3
"""
sku_search_limited.py – Search each SKU in skus.txt by restricting to a predefined list of domains
────────────────────────────────────────────────────────────────────────────────────────────────
Reads SKUs from `skus.txt` and for each SKU performs a DuckDuckGo "site:domain SKU" search
on each allowed domain, collecting at most one link per site that exactly matches the SKU and
belongs to the approved domains list.

• Respects STRICT_SKU_MATCH: enforces exact SKU boundaries in URLs.
• Enforces strict domain matching: only links from ALLOWED_DOMAINS are considered.
• Writes results to `sku_links_limited.txt`.

Run:
    python sku_search_limited.py
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
CHROMEDRIVER = "chromedriver"  # executable name
TIMEOUT = 10  # seconds per search
SEARCH_URL = "https://duckduckgo.com/?q={query}&ia=web"
TITLE_SEL = "a[data-testid='result-title-a'], a.result__a"
HEADLESS = True  # set False to see browser
STRICT_SKU_MATCH = True  # enforce exact SKU boundaries in URL
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
    "sa.puma.com",
    "ae.puma.com",
    "br.puma.com",
    "soccerandrugby.com",
    "adsport.store",
]
OUTPUT_FILE = "sku_links_limited.txt"
# ──────────────────────────────────────────────────────────────────────────────


def normalize(domain: str) -> str:
    """Ensure domain is lowercase without 'www.' prefix"""
    d = domain.lower()
    if d.startswith("www."):
        d = d[4:]
    return d


# Pre-calculate normalized domain set
ALLOWED_NORMALIZED = {normalize(d) for d in ALLOWED_DOMAINS}

# Set up headless Chrome
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


def find_links_for(sku: str) -> list[str]:
    """Search SKU on each allowed domain and return at most one strict match per domain."""
    collected: dict[str, str] = {}
    sku_lower = sku.lower()
    sku_pattern = (
        re.compile(rf"\b{re.escape(sku_lower)}\b") if STRICT_SKU_MATCH else None
    )

    for domain in ALLOWED_DOMAINS:
        norm_domain = normalize(domain)
        query = f"site:{domain} {sku}"
        driver.get(SEARCH_URL.format(query=query))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SEL)))
        except TimeoutException:
            continue

        for a in driver.find_elements(By.CSS_SELECTOR, TITLE_SEL):
            href = a.get_attribute("href") or ""
            # strict domain match
            netloc = urlparse(href).netloc
            norm_netloc = normalize(netloc)
            if norm_netloc != norm_domain:
                continue
            # strict SKU match in URL
            if sku_pattern and not sku_pattern.search(href.lower()):
                continue
            # accept first valid link per domain
            collected[norm_domain] = href
            break

        time.sleep(0.2)

    return list(collected.values())


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("skus.txt").read_text().splitlines()
        if s.strip()
    ]
    print(
        f"🔍 Starting search for {len(skus)} SKUs across {len(ALLOWED_DOMAINS)} domains"
    )
    print(f"📋 Config: STRICT_SKU_MATCH={STRICT_SKU_MATCH}, TIMEOUT={TIMEOUT}s")
    print("─" * 60)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for i, sku in enumerate(skus, 1):
            print(f"[{i}/{len(skus)}] Processing SKU: {sku}", end=" ... ")
            links = find_links_for(sku)
            if links:
                for link in links:
                    out.write(f"{sku}\t{link}\n")
                print(f"✓ Found {len(links)} link(s)")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")
                print("❌ No matching results")

    print("─" * 60)
    print(f"✅ Search completed! Results saved to: {OUTPUT_FILE}")
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        driver.quit()
        print("\nInterrupted by user.")
