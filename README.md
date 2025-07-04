# Selenium Toolkit for Product Scraping and Captcha Solving

This repository contains a collection of Selenium scripts used to search for product pages, scrape images, and handle captcha challenges. The scripts can be run individually or through the provided pipeline.

## Pipeline Overview

The typical workflow is:

1. **`sku_search_sites.py`** – Search each SKU from `skus.txt` across a restricted list of domains. Results are written to `sku_links_limited.txt` (at most two links per SKU).
2. **`image_scraper.py`** – Visit each link and extract the main product image. Output is a tab-separated file `product_images.txt` containing the SKU, product name, and image URL.
3. **`product_image_cleaner.py`** – Filter the scraped list, removing rows without an image or where the URL does not contain the SKU. The cleaned file is `filtered_images.txt`.
4. **`images_to_json.py`** – Convert the cleaned text file into `images.json` with the nested structure expected by downstream tools.
5. **`run_all.py`** – Convenience script that executes the above steps in sequence.

Run the full pipeline with:

```bash
python run_all.py
```

file_handler contains files for assessing the most common websites to contain the skus

requirements in requirements.txt
