#!/usr/bin/env python3
"""
image_scraper.py – **strict hero‑only** version
==============================================
Reads ``sku_links_limited.txt`` (tab‑separated ``SKU    URL``) and writes a
single row per SKU to ``product_images.txt`` containing **only the principal
product image** – no Facebook pixels, no tiny icons, no gallery thumbnails.

Heuristic
---------
1. **Use the page’s OpenGraph photo** (``<meta property="og:image">``) if it
   exists – that tag is almost always the hero shot.
2. If the tag is missing, inspect every ``<img>`` in DOM order and take the
   first element that passes *all* of these checks:

   • **looks_like_product(src)** – src URL must end with ``jpg/png/webp`` and
     must *not* be on any of the skip hosts (facebook.com, gstatic, etc.).

   • **Visible size** – natural width **and** height ≥ ``MIN_DIM`` (100 px by
     default).  This skips 1×1 tracking pixels and small logos even if they’re
     loaded early in the markup.

Nothing else changed: same CMD‑line behaviour, same output format.
"""

import os
import sys
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

INPUT_FILE = "files/sku_links_limited.txt"
OUTPUT_FILE = "files/product_images.txt"
CHROMEDRIVER = "chromedriver.exe"  # adjust if not on PATH
HEADLESS = True  # flip to False to debug visually
MIN_DIM = 100  # px – minimum natural width & height
IMG_EXT_RE = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)
SKIP_HOSTS = (
    "facebook.com",
    "google.",
    "gstatic.com",
    "twitter.com",
    "doubleclick.net",
)


# ─── Selenium bootstrap ────────────────────────────────────────────────────


def init_driver():
    opts = Options()
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--ignore-certificate-errors")
    return webdriver.Chrome(service=Service(CHROMEDRIVER), options=opts)


# ─── Helpers ───────────────────────────────────────────────────────────────


def extract_meta(soup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop})
    return tag["content"].strip() if tag and tag.get("content") else None


def looks_like_product(src: str) -> bool:
    """Filter out tracking pixels, logos, social sprites, etc."""
    if not src or src.startswith("data:"):
        return False
    if any(h in src for h in SKIP_HOSTS):
        return False
    return bool(IMG_EXT_RE.search(src))


def extract_name_and_hero(driver: webdriver.Chrome, url: str) -> tuple[str, str]:
    """Return (name, hero_image_url). Hero is the first valid picture we trust."""
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Name – og:title or first <h1>
    name = extract_meta(soup, "og:title") or (
        soup.h1.get_text(strip=True) if soup.h1 else ""
    )

    # 1️⃣  OpenGraph image wins
    hero = extract_meta(soup, "og:image")
    if hero:
        return name, hero

    # 2️⃣  Fallback: first good‑looking <img>
    for img in driver.find_elements("tag name", "img"):
        src = img.get_attribute("src") or img.get_attribute("data-src") or ""
        if not looks_like_product(src):
            continue
        try:
            w = driver.execute_script("return arguments[0].naturalWidth", img)
            h = driver.execute_script("return arguments[0].naturalHeight", img)
        except Exception:
            w = h = 0
        if w >= MIN_DIM and h >= MIN_DIM:
            return name, src

    return name, ""  # nothing decent found


# ─── Main driver ───────────────────────────────────────────────────────────


def main():
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"❌ '{INPUT_FILE}' not found.")

    rows: list[tuple[str, str]] = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for ln in f:
            parts = ln.strip().split("\t", 1)
            if len(parts) == 2:
                rows.append(tuple(parts))
    if not rows:
        sys.exit(f"❌ '{INPUT_FILE}' is empty or malformed.")

    driver = init_driver()

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out:
        wr = csv.writer(out, delimiter="\t")
        wr.writerow(["SKU", "Name", "Image_URL"])

        for sku, url in rows:
            print(f"• {sku} → {url}")
            try:
                name, img = extract_name_and_hero(driver, url)
            except Exception as e:
                print(f"  ⚠️  failed: {e}")
                name, img = "", ""
            wr.writerow([sku, name, img])

    driver.quit()
    print(f"✅ Done – wrote '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
