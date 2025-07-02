#!/usr/bin/env python3
"""
Greedy cover: find a small set of domains (excluding ebay & amazon)
so every SKU in sku_links.txt is covered by at least one link.
"""

from urllib.parse import urlparse
from collections import defaultdict

# domains to ignore
EXCLUDE = {"www.ebay.com", "ebay.com", "www.amazon.com", "amazon.com"}


def normalize_netloc(netloc: str) -> str:
    n = netloc.lower()
    # drop port, credentials etc.
    n = n.split(":", 1)[0]
    # force www.
    if not n.startswith("www."):
        n = "www." + n
    return n


def main():
    # map each domain → set of SKUs it appears under
    domain_to_skus = defaultdict(set)
    all_skus = set()

    with open("sku_links.txt", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t", 1)
            if len(parts) != 2:
                continue
            sku, url = parts
            all_skus.add(sku)
            if not url.startswith(("http://", "https://")):
                continue
            netloc = urlparse(url).netloc
            dom = normalize_netloc(netloc)
            if dom in EXCLUDE:
                continue
            domain_to_skus[dom].add(sku)

    # greedy cover: pick the domain covering the most yet-uncovered SKUs
    covered = set()
    selected = []

    while covered != all_skus:
        # choose domain with largest number of uncovered SKUs
        best_dom, skus = max(
            domain_to_skus.items(),
            key=lambda item: len(item[1] - covered),
            default=(None, set()),
        )
        if not best_dom or not (skus - covered):
            # no further coverage possible
            break

        selected.append(best_dom)
        covered |= domain_to_skus[best_dom]
        # remove it from future consideration
        del domain_to_skus[best_dom]

    # report
    print("Selected domains (excluding ebay/amazon):")
    for dom in selected:
        print(f"  {dom}")
    missing = all_skus - covered
    if missing:
        print("\nWarning: the following SKUs had no links outside ebay/amazon:")
        for sku in missing:
            print(" ", sku)
    else:
        print("\nAll SKUs covered!")


if __name__ == "__main__":
    main()
