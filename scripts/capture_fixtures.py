"""Capture real Picnic PML responses as test fixtures.

Dev-only helper. Reads ``PICNIC_AUTH_TOKEN`` and ``COUNTRY_CODE`` from the
environment (or a local ``.env``), hits the ``/pages/*`` endpoints and writes the
raw JSON to ``tests/fixtures/`` so parsers/models can be built and regression
tested against real, current payloads.

These endpoints return product/category *pages*, not account data, so there is no
personal information to scrub. If you capture anything account-specific, review it
before committing.

Usage::

    PICNIC_AUTH_TOKEN=... COUNTRY_CODE=DE uv run python scripts/capture_fixtures.py \
        --article s1018620 --search kaffee --category 2000 3000
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from python_picnic_api2 import PicnicAPI

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"


def _dump(name: str, data: dict, country: str) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURES_DIR / f"{name}_{country.lower()}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {path.relative_to(FIXTURES_DIR.parent.parent)}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", default="s1018620",
                        help="Article id for the product-details page fixture")
    parser.add_argument("--search", default="kaffee",
                        help="Search term for the search-page fixture")
    parser.add_argument("--category", nargs=2, type=int, metavar=("L2", "L3"),
                        default=None,
                        help="L2 and L3 category ids for the category-page fixture")
    args = parser.parse_args()

    token = os.getenv("PICNIC_AUTH_TOKEN")
    country = os.getenv("COUNTRY_CODE", "NL")
    if not token:
        raise SystemExit(
            "PICNIC_AUTH_TOKEN is required (export it or put it in .env)."
        )

    client = PicnicAPI(auth_token=token, country_code=country)

    # Capture the raw (pre-parse) payloads via the private request helper so the
    # fixtures contain the full PML tree, not the parsed models.
    _dump(
        "product_details_page",
        client._get(
            f"/pages/product-details-page-root?id={args.article}"
            "&show_category_action=true",
            add_picnic_headers=True,
        ),
        country,
    )
    _dump(
        "search_page",
        client._get(
            f"/pages/search-page-results?search_term={args.search}",
            add_picnic_headers=True,
        ),
        country,
    )
    if args.category:
        l2, l3 = args.category
        _dump(
            "category_page",
            client._get(
                "/pages/L2-category-page-root"
                f"?category_id={l2}&l3_category_id={l3}",
                add_picnic_headers=True,
            ),
            country,
        )


if __name__ == "__main__":
    main()
