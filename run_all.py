#!/usr/bin/env python3
"""
run_all.py – Simple script runner
Run sku_search2.py then image_scraper.py then product_image_cleaner.py then images_to_json.py
"""

import subprocess
import sys


def main():
    print("Running SKU search...")
    result1 = subprocess.run([sys.executable, "scraping_process/sku_search_sites.py"])

    print("\nRunning image scraper...")
    result2 = subprocess.run([sys.executable, "scraping_process/image_scraper.py"])

    print("\nRunning product image cleaner...")
    result3 = subprocess.run(
        [sys.executable, "scraping_process/product_image_cleaner.py"]
    )

    print("\nRunning images to JSON...")
    result4 = subprocess.run([sys.executable, "scraping_process/images_to_json.py"])

    print("\nDone!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
