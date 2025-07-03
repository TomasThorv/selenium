#!/usr/bin/env python3
"""
image_scraper.py – minimal tweak: still reads the same
    <SKU>\t<product‑page URL>
file (``sku_links_limited.txt``) **but now writes one row per image**.

Logic change requested by user
-----------------------------
* Keep the *hero* image exactly as before.
* Also grab any other <img> elements whose **centre point is within a
  configurable pixel radius (default 400 px) of the hero’s centre**.  This
  spatial proximity check avoids the unrelated thumbnails further down the page.
* No other parts of the script were touched – same input file, same output file
  name, same command‑line usage.
"""

import os
import sys
import csv
import math
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

INPUT_FILE = "sku_links_limited.txt"
OUTPUT_FILE = "product_images.txt"
CHROMEDRIVER = "chromedriver.exe"  # change if not on PATH
HEADLESS = True  # flip to False to watch each page
RADIUS_PX = 400  # max distance from hero centre
MAX_IMAGES = 12  # cap per product (hero + 11 adjacents)


# ─── Selenium bootstrap ────────────────────────────────────────────────────


def init_driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    return webdriver.Chrome(service=Service(CHROMEDRIVER), options=options)


# ─── Helpers ───────────────────────────────────────────────────────────────


def extract_meta(soup, prop):
    tag = soup.find("meta", attrs={"property": prop})
    return tag["content"].strip() if tag and tag.get("content") else None


def distance(c1, c2):
    dx = c1[0] - c2[0]
    dy = c1[1] - c2[1]
    return math.hypot(dx, dy)


def extract_name_and_images(driver, url, radius_px=RADIUS_PX):
    """Return product name and list of nearby image URLs (hero first)."""
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Product name
    name = extract_meta(soup, "og:title") or (
        soup.h1.get_text(strip=True) if soup.h1 else ""
    )

    # Determine hero src and corresponding WebElement
    hero_src = extract_meta(soup, "og:image")
    hero_elem = None

    if hero_src:
        for img in driver.find_elements("tag name", "img"):
            src = img.get_attribute("src") or img.get_attribute("data-src") or ""
            if src == hero_src:
                hero_elem = img
                break

    if not hero_elem:
        # Fallback: first <img> on the page
        hero_elem = driver.find_element("tag name", "img")
        hero_src = hero_elem.get_attribute("src") or ""

    if not hero_src:
        return name, []

    hero_rect = hero_elem.rect  # dict with x,y,width,height
    hero_center = (
        hero_rect["x"] + hero_rect["width"] / 2,
        hero_rect["y"] + hero_rect["height"] / 2,
    )

    images = [hero_src]
    seen = {hero_src}

    for img in driver.find_elements("tag name", "img"):
        src = img.get_attribute("src") or img.get_attribute("data-src") or ""
        if not src or src in seen:
            continue
        rect = img.rect
        centre = (rect["x"] + rect["width"] / 2, rect["y"] + rect["height"] / 2)
        if distance(centre, hero_center) <= radius_px:
            images.append(src)
            seen.add(src)
            if len(images) >= MAX_IMAGES:
                break

    return name, images


# ─── Main driver ───────────────────────────────────────────────────────────


def main():
    if not os.path.exists(INPUT_FILE):
        sys.exit(f"❌ '{INPUT_FILE}' not found.")

    with open(INPUT_FILE, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        sys.exit(f"❌ '{INPUT_FILE}' is empty or malformed.")

    driver = init_driver()

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as out:
        wr = csv.writer(out, delimiter="\t")
        wr.writerow(["SKU", "Name", "Image_URL"])

        for line in lines:
            try:
                sku, url = line.split("\t", 1)
            except ValueError:
                print(f"Skipping malformed line: {line}")
                continue

            print(f"• {sku} → {url}")
            try:
                name, imgs = extract_name_and_images(driver, url)
            except Exception as e:
                print(f"  ⚠️  failed: {e}")
                continue

            for img_url in imgs:
                wr.writerow([sku, name, img_url])

    driver.quit()
    print(f"✅ Done – wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
