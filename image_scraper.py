import os
import sys
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

INPUT_FILE = "sku_links.txt"
OUTPUT_FILE = "product_images.txt"


def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return driver


def extract_meta(soup, prop):
    tag = soup.find("meta", attrs={"property": prop})
    return tag["content"].strip() if tag and tag.get("content") else None


def extract_name_and_image(driver, url):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # Name: og:title or first <h1>
    name = extract_meta(soup, "og:title") or (
        soup.h1.get_text(strip=True) if soup.h1 else ""
    )

    # Image: og:image or first <img>
    image = extract_meta(soup, "og:image") or None
    if not image:
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            image = img_tag["src"].strip()
    return name, image or ""


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        print(f"Error: '{INPUT_FILE}' is empty.")
        sys.exit(1)

    driver = init_driver()
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile, delimiter="\t")
        writer.writerow(["SKU", "Name", "Image_URL"])
        for line in lines:
            try:
                sku, url = line.split("\t", 1)
            except ValueError:
                print(f"Skipping invalid line: {line}")
                continue
            print(f"Processing {sku} -> {url}")
            try:
                name, image_url = extract_name_and_image(driver, url)
            except Exception as e:
                print(f"  Failed to fetch: {e}")
                name, image_url = "", ""
            writer.writerow([sku, name, image_url])

    driver.quit()
    print(f"Done. Output written to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
