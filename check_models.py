"""
check_models.py
===============
Lists models available on Nebius Token Factory and prints the Nemotron IDs.

Usage:  python check_models.py
Needs NEBIUS_API_KEY in the environment or .env.
"""

import sys
import requests

from config import NEBIUS_API_KEY, NEBIUS_BASE_URL, is_placeholder


def main() -> int:
    if is_placeholder(NEBIUS_API_KEY):
        print("NEBIUS_API_KEY is not set.")
        return 1

    resp = requests.get(
        NEBIUS_BASE_URL.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {NEBIUS_API_KEY}"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"HTTP {resp.status_code}: {resp.text[:500]}")
        return 1

    ids = sorted(m.get("id", "") for m in resp.json().get("data", []))
    nemotron = [i for i in ids if "nemotron" in i.lower()]
    print(f"{len(ids)} models available; {len(nemotron)} Nemotron:")
    for i in nemotron:
        print(f"  {i}")
    if not nemotron:
        print("No Nemotron models found. All IDs:")
        for i in ids:
            print(f"  {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
