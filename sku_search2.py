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
STRICT_SKU_MATCH = True  # Only return results that contain the exact SKU
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
    "www.soccerandrugby.com",
    "www.adsport.store",
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
    collected: dict[str, str] = {}  # domain -> best_link mapping

    for domain in ALLOWED_DOMAINS:
        query = f"site:{domain} {sku}"
        driver.get(SEARCH_URL.format(query=query))
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SEL)))
        except TimeoutException:
            continue

        # Find the best matching link for this domain
        best_link = None
        best_score = 0

        for a in driver.find_elements(By.CSS_SELECTOR, TITLE_SEL):
            href = a.get_attribute("href") or ""
            title = a.text.strip()

            # Check domain match
            netloc = urlparse(href).netloc.lower()
            if normalize(netloc) != domain:
                continue

            # Check if SKU appears in URL or title
            href_lower = href.lower()
            title_lower = title.lower()
            sku_lower = sku.lower()

            # Calculate relevance score
            score = 0

            # Exact SKU match in URL gets highest priority
            if sku_lower in href_lower:
                score += 10
                # Bonus for exact match boundaries (not part of another word)
                if (
                    f"/{sku_lower}" in href_lower
                    or f"-{sku_lower}" in href_lower
                    or f"={sku_lower}" in href_lower
                ):
                    score += 5
                # Bonus for SKU at end of URL
                if href_lower.endswith(sku_lower) or href_lower.endswith(
                    f"{sku_lower}/"
                ):
                    score += 3

            # SKU match in title
            if sku_lower in title_lower:
                score += 5
                # Bonus for exact word match in title
                if sku.lower() in title_lower.split():
                    score += 3

            # Only consider links that actually contain the SKU
            if score > 0 and score > best_score:
                best_link = href
                best_score = score

        # Add the best link for this domain if found
        if best_link:
            collected[domain] = best_link

        time.sleep(0.2)

    # Return list of best links (one per domain)
    return list(collected.values())


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("skus2.txt").read_text().splitlines()
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
                print(f"✓ Found {len(links)} unique link(s)")

                # Show which domains had results
                domains_found = []
                for link in links:
                    domain = normalize(urlparse(link).netloc)
                    if domain not in domains_found:
                        domains_found.append(domain)
                print(f"  📍 Domains: {', '.join(domains_found)}")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")
                print("❌ No matching results found")

    print("─" * 60)
    print(f"✅ Search completed! Results saved to: {OUTPUT_FILE}")
    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        driver.quit()
        print("\nInterrupted by user.")
