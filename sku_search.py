"""
Search each SKU in *skus.txt* with DuckDuckGo and write **every** result‑page
link whose URL *or* title *or* snippet contains the SKU (case‑insensitive,
ignoring punctuation) to *sku_links.txt*.

Adapts to both DuckDuckGo result layouts (“result__a” and new
"data-testid='result-title-a'" anchors).

• Up to TIMEOUT seconds per SKU.
• Prints progress; writes "NOT_FOUND" when no match.
• Needs Chrome/Chromium + chromedriver.

Run:
    python sku_search.py
"""

from __future__ import annotations

import pathlib, re, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ─── Configuration ────────────────────────────────────────────────────────────
CHROMEDRIVER = "chromedriver"  # change if the executable name differs
TIMEOUT = 10  # seconds allowed per SKU
SEARCH_URL = "https://duckduckgo.com/?q={query}&ia=web"
TITLE_SEL = "a[data-testid='result-title-a'], a.result__a"
HEADLESS = True  # flip to False if you want to see the UI
# ──────────────────────────────────────────────────────────────────────────────

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

SANITIZE = re.compile(r"[^a-z0-9]")


def _clean(s: str) -> str:
    return SANITIZE.sub("", s.lower())


def links_for(sku: str) -> list[str]:
    driver.get(SEARCH_URL.format(query=sku))

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TITLE_SEL)))
    except TimeoutException:
        return []

    needle_raw = sku.lower()
    needle_clean = _clean(sku)

    links: list[str] = []
    anchors = driver.find_elements(By.CSS_SELECTOR, TITLE_SEL)

    for a in anchors:
        href = a.get_attribute("href") or ""
        title = a.text or ""
        snippet = ""
        # Try to grab the snippet inside the same result block (best‑effort).
        try:
            snippet = (
                a.find_element(
                    By.XPATH,
                    "ancestor::*[self::article or contains(@class,'result')]//div[contains(@class,'snippet') or contains(@class,'result__snippet')]",
                ).text
                or ""
            )
        except NoSuchElementException:
            pass

        haystacks = [
            href.lower(),
            title.lower(),
            snippet.lower(),
            _clean(href),
            _clean(title),
            _clean(snippet),
        ]
        if any((needle_raw in h) or (needle_clean in h) for h in haystacks):
            links.append(href)

    return links


def main() -> None:
    skus = [
        s.strip()
        for s in pathlib.Path("skus.txt").read_text().splitlines()
        if s.strip()
    ]

    with open("sku_links.txt", "w", encoding="utf-8") as out:
        for sku in skus:
            try:
                matches = links_for(sku)
            except Exception as e:
                print(f"⚠️  {sku}: error {e}")
                out.write(f"{sku}\tERROR:{e}\n")
                continue

            if matches:
                for link in matches:
                    out.write(f"{sku}\t{link}\n")
            else:
                out.write(f"{sku}\tNOT_FOUND\n")

            print(f"✓ {sku}: {len(matches)} link(s) found")
            time.sleep(0.5)  # gentle pause to avoid rate‑limits

    driver.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        driver.quit()
        print("\nInterrupted by user.")
