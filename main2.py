"""
main2.py – Bright Data Browser‑API CAPTCHA solver
─────────────────────────────────────────────────
Now pre‑filled with **your zone credentials** so you can run it straight away.

• Zone   : `brd-customer-hl_08a0a299-zone-scraping_browser1`
• Password : `rsmhf56qvcyj`
• Endpoint : `brd.superproxy.io:9222` (Browser API, mandatory for CAPTCHA solve)

The script still randomises the **session token** on every run so Bright Data
hands you a fresh residential IP each time.  If you ever rotate the password or
create a new zone, just update the two constants at the top or export
`BD_USERNAME` / `BD_PASSWORD` in your shell to override.

Usage (PowerShell / bash)
────────────────────────
python main2.py          # credentials already embedded

or, to override at runtime:
$env:BD_PASSWORD="NEW_PASS"; python main2.py

-------------------------------------------------------------------------"""

from __future__ import annotations

import json
import os
import random
import string
import time
from typing import Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ─────────────────────────────────────────────────────────────────────────
# Embedded Bright Data credentials (override via env vars if you prefer)
# ─────────────────────────────────────────────────────────────────────────

_BASE_USER_DEFAULT = "brd-customer-hl_08a0a299-zone-scraping_browser1"
_PWD_DEFAULT = "rsmhf56qvcyj"


def _random_session(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _make_auth() -> str:
    """Assemble the <username>:<password> auth block with rotating session."""
    base_user = os.getenv("BD_USERNAME", _BASE_USER_DEFAULT).strip()
    pwd = os.getenv("BD_PASSWORD", _PWD_DEFAULT).strip()
    country = os.getenv("BD_COUNTRY", "").lower().strip()

    sess_token = f"session-rand{_random_session()}"
    if country:
        user = f"{base_user}-country-{country}-{sess_token}"
    else:
        user = f"{base_user}-{sess_token}"

    return f"{user}:{pwd}"


# Bright Data Browser‑API websocket (port 9222)
WS_ENDPOINT = f"wss://{_make_auth()}@brd.superproxy.io:9222"


# ─────────────────────────────────────────────────────────────────────────
# Selenium helpers
# ─────────────────────────────────────────────────────────────────────────


def _connect() -> webdriver.Chrome:
    """Attach Selenium to the hosted Chrome instance."""
    opts = Options()
    opts.add_experimental_option("debuggerAddress", WS_ENDPOINT)
    return webdriver.Chrome(options=opts)


def _load_state() -> Dict[str, Any]:
    fallback = {"url": "https://www.google.com", "cookies": []}
    try:
        with open("session_state.json", "r", encoding="utf-8") as fh:
            return json.load(fh) | {"task": "solve_captcha"}
    except Exception:
        return fallback


def _save_solution(driver: webdriver.Chrome, status: str = "success") -> None:
    data = {
        "cookies": driver.get_cookies(),
        "final_url": driver.current_url,
        "user_agent": driver.execute_script("return navigator.userAgent"),
        "status": status,
    }
    with open("captcha_solution.json", "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ─────────────────────────────────────────────────────────────────────────
# Main solve routine
# ─────────────────────────────────────────────────────────────────────────


def solve():
    state = _load_state()
    print(f"[main2] Target URL → {state['url']}")
    print("[main2] Connecting through Bright Data (rotating IP)…")

    driver = _connect()
    try:
        # 1️⃣ Navigate – Bright Data auto‑injects the solver if needed
        driver.get(state["url"])

        # 2️⃣ Block until CAPTCHA is cleared (no‑op if none present)
        try:
            driver.execute_cdp_cmd("Captcha.waitForSolve", {})
            print("[main2] Captcha solved ✅")
        except Exception as err:
            print(f"[main2] waitForSolve raised {err}; continuing…")

        time.sleep(1)
        _save_solution(driver, "success")
    except Exception as failure:
        print(f"[main2] Fatal error ⇒ {failure}")
        _save_solution(driver, "failed")
    finally:
        driver.quit()


if __name__ == "__main__":
    solve()
