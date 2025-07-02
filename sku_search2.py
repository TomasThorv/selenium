"""
Search each SKU in skus.txt by restricting to a predefined list of domains:
for each SKU, perform a DuckDuckGo "site:domain SKU" search on each allowed domain,
collect all result links from those domains, and write them to sku_links_limited.txt.

• Gives each SKU up to TIMEOUT seconds per domain search.
• Prints progress and writes "NOT_FOUND" if no links found for that SKU across all domains.

Run:
    python sku_search_limited.py
"""

from __future__ import annotations
import pathlib, sys, time
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
]
OUTPUT_FILE = "sku_links_limited.txt"
# ──────────────────────────────────────────────────────────────────────────────

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


def normalize(domain: str) -> str:
    """Ensure domain is in lowercase without 'www.' prefix"""
    d = domain.lower()
    if d.startswith("www."):
        d = d[4:]
    return d


def find_links_for(sku: str) -> list[str]:
    """Search SKU on each allowed domain and collect matching links."""
    collected: list[str] = []
    for domain in ALLOWED_DOMAINS:
        query = f"site:{domain} {sku}"
        driver.get(SEARCH_URL.format(query=query))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SEL)))
        except TimeoutException:
            continue
        for a in driver.find_elements(By.CSS_SELECTOR, TITLE_SEL):
            href = a.get_attribute("href") or ""
            # check domain match
            netloc = urlparse(href).netloc.lower()
            if normalize(netloc) == domain:
                collected.append(href)
        time.sleep(0.2)
    # dedupe
    return list(dict.fromkeys(collected))


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("skus.txt").read_text().splitlines()
        if s.strip()
    ]
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for sku in skus:
            links = find_links_for(sku)
            if links:
                for link in links:
                    out.write(f"{sku}\t{link}\n")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")
            print(f"✓ {sku}: {len(links)} link(s) found")
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        driver.quit()
        print("\nInterrupted by user.")
