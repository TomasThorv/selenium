#!/usr/bin/env python3
"""
Report all SKUs in sku_links.txt that have NO link from the given top sites.
"""

from urllib.parse import urlparse
from collections import defaultdict

# your list of “must-have” domains (normalized to start with www.)
TOP_SITES = {
    "www.solesense.com",
    "www.nike.com",
    "www.foot-store.com",
    "www.nike.ae",
    "www.soccervillage.com",
    "www.footy.com",
    "www.goat.com",
    "www.soccerpost.com",
    "www.bzronline.com",
    "www.kickscrew.com",
}


def normalize_netloc(netloc: str) -> str:
    netloc = netloc.lower()
    if not netloc:
        return ""
    # force a leading www.
    if not netloc.startswith("www."):
        netloc = "www." + netloc
    return netloc


def main():
    # group all observed netlocs by SKU
    sku_to_sites = defaultdict(set)

    with open("sku_links.txt", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t", 1)
            if len(parts) != 2:
                continue
            sku, url = parts
            if not url.startswith(("http://", "https://")):
                continue
            netloc = urlparse(url).netloc
            netloc = normalize_netloc(netloc)
            sku_to_sites[sku].add(netloc)

    # find SKUs missing all of the top sites
    missing = []
    for sku, sites in sku_to_sites.items():
        # does this SKU have *any* link from TOP_SITES?
        if not (sites & TOP_SITES):
            missing.append(sku)

    if not missing:
        print("All SKUs have at least one link from the top-8 sites.")
    else:
        print("SKUs missing all top-8 sites:")
        for sku in missing:
            print("  ", sku)


if __name__ == "__main__":
    main()
