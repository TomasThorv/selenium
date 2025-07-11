#!/usr/bin/env python3
"""
Count how many SKUs are in images.json.

The images.json file contains an array of objects, each with:
    - "sku": the SKU identifier
    - "images": array of image URLs

Usage:
    python count_skus_in_json.py
"""

import json
import os


def main():
    json_file = "files/images.json"

    # Check if file exists
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        return

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            print(f"❌ Expected JSON array, got {type(data).__name__}")
            return

        # Count SKUs
        sku_count = len(data)

        # Count unique SKUs (in case there are duplicates)
        unique_skus = set()
        total_images = 0

        for item in data:
            if isinstance(item, dict) and "sku" in item:
                unique_skus.add(item["sku"])
                if "images" in item and isinstance(item["images"], list):
                    total_images += len(item["images"])

        unique_sku_count = len(unique_skus)

        # Print results
        print(f"📊 SKU Count Results:")
        print(f"─" * 40)
        print(f"Total entries:     {sku_count}")
        print(f"Unique SKUs:       {unique_sku_count}")
        print(f"Total images:      {total_images}")
        print(
            f"Avg images/SKU:    {total_images/unique_sku_count:.1f}"
            if unique_sku_count > 0
            else "Avg images/SKU:    0"
        )

        if sku_count != unique_sku_count:
            duplicates = sku_count - unique_sku_count
            print(f"⚠️  Duplicate entries: {duplicates}")

        print(f"─" * 40)
        print(f"✅ File: {json_file}")

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")


if __name__ == "__main__":
    main()
