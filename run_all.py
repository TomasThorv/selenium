#!/usr/bin/env python3
"""
run_all.py – Simple script runner
Run sku_search2.py then image_scraper.py
"""

import subprocess
import sys


def main():
    print("Running SKU search...")
    result1 = subprocess.run([sys.executable, "sku_search2.py"])

    print("\nRunning image scraper...")
    result2 = subprocess.run([sys.executable, "image_scraper.py"])

    print("\nDone!")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
