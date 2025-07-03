#!/usr/bin/env python3
"""
Count most-frequent sites in sku_links.txt.

Each line in sku_links.txt is expected to be:
    <SKU><tab><URL or NOT_FOUND>

Usage:
    python count_sites.py
"""

from urllib.parse import urlparse
from collections import Counter

COUNTS = Counter()

with open("sku_links_limited.txt", encoding="utf-8") as fh:
    for line in fh:
        # keep lines that contain a URL
        parts = line.strip().split("\t", 1)
        if len(parts) < 2:
            continue
        url = parts[1]
        if not url.startswith(("http://", "https://")):
            continue  # skip NOT_FOUND or malformed entries

        # take the network-location part of the URL
        netloc = urlparse(url).netloc.lower()
        if not netloc:
            continue

        # normalise to a leading “www.” so everything looks like www.site.com
        if not netloc.startswith("www."):
            netloc = "www." + netloc

        COUNTS[netloc] += 1

# print results, highest-count first
for site, hits in COUNTS.most_common():
    print(f"{site}\t{hits}")
