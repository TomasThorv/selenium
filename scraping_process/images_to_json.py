#!/usr/bin/env python3
"""
images_to_json.py – Convert a cleaned, tab‑separated image list into the
nested‑JSON structure you showed.

Expected input (default: ``filtered_images.txt``)
================================================
```
SKU<TAB>Name<TAB>Image_URL
SKU<TAB>Name<TAB>Image_URL
...
```

• Lines with an empty URL should already have been filtered out by
  ``clean_image_list.py`` – but they’re skipped again here just in case.
• Duplicate image URLs for the same SKU are removed while preserving order.

Command‑line usage
==================
```
python images_to_json.py [input.tsv] [output.json]
```
Defaults:
    input  = filtered_images.txt
    output = images.json
"""

import sys, json
from pathlib import Path
from collections import OrderedDict

DEFAULT_IN = "files/filtered_images.txt"
DEFAULT_OUT = "files/images.json"


def build_mapping(lines: list[str]):
    """Return {sku: [img1, img2, ...]} preserving first‑seen order."""
    mapping: dict[str, list[str]] = OrderedDict()
    seen_per_sku: dict[str, set[str]] = {}

    for ln in lines:
        parts = ln.split("\t", 2)
        if len(parts) < 3:
            continue  # malformed
        sku, _name, url = (p.strip() for p in parts[:3])
        if not url:
            continue
        sku_key = sku.upper()  # normalise case for grouping
        if sku_key not in mapping:
            mapping[sku_key] = []
            seen_per_sku[sku_key] = set()
        if url not in seen_per_sku[sku_key]:
            mapping[sku_key].append(url)
            seen_per_sku[sku_key].add(url)
    return mapping


def main(argv: list[str]):
    in_path = Path(argv[1]) if len(argv) > 1 else Path(DEFAULT_IN)
    out_path = Path(argv[2]) if len(argv) > 2 else Path(DEFAULT_OUT)

    if not in_path.exists():
        sys.exit(f"❌ Input file '{in_path}' not found.")

    lines = in_path.read_text(encoding="utf-8").splitlines()
    mapping = build_mapping(lines)

    output = [
        {"sku": sku, "images": urls}
        for sku, urls in mapping.items()
        if urls  # skip SKUs left with no images
    ]

    out_path.write_text(json.dumps(output, indent=4), encoding="utf-8")
    print(f"✅ Wrote {len(output)} SKUs → '{out_path}'.")


if __name__ == "__main__":
    main(sys.argv)
