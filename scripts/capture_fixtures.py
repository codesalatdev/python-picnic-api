"""Capture real Picnic responses as test fixtures.

Dev-only helper. Reads ``PICNIC_AUTH_TOKEN`` and ``COUNTRY_CODE`` from the
environment (or a local ``.env``), hits the API and writes the raw JSON to
``tests/fixtures/`` so parsers/models can be built and regression tested against
real, current payloads.

Two families of endpoints are captured:

- The ``/pages/*`` PML pages (product details, search, category). These return
  product/category *pages*, not account data, so there is no personal information
  to scrub.
- The domain-JSON endpoints (user, cart, delivery slots, deliveries). These *do*
  contain personal data (name, address, IBAN, ids), so pass ``--scrub`` to redact
  it before writing. Always review the output before committing.

Usage::

    PICNIC_AUTH_TOKEN=... COUNTRY_CODE=DE uv run python scripts/capture_fixtures.py \
        --article s1018620 --search kaffee --category 2000 3000 --scrub
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from python_picnic_api2 import PicnicAPI

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Keys whose values are personal/identifying and must be redacted for committed
# domain-JSON fixtures. Redaction keeps the value's type so models still parse.
_SENSITIVE_KEYS = {
    "user_id",
    "firstname",
    "lastname",
    "phone",
    "contact_email",
    "author",
    "id",
    "house_number",
    "house_number_ext",
    "postcode",
    "street",
    "city",
    "slot_id",
    "hub_id",
    "fc_id",
    "delivery_id",
    "redacted_iban",
    "bank_id",
    "state_token",
    "image_ids",
}


def _redact(value):
    """Return a type-preserving placeholder for a sensitive scalar/list."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return 0
    if isinstance(value, list):
        return ["REDACTED" for _ in value]
    return "REDACTED"


def _scrub(node):
    """Recursively redact sensitive keys in a captured payload (in place-ish)."""
    if isinstance(node, dict):
        return {
            key: _redact(val) if key in _SENSITIVE_KEYS else _scrub(val)
            for key, val in node.items()
        }
    if isinstance(node, list):
        return [_scrub(item) for item in node]
    return node


def _dump(name: str, data, country: str, scrub: bool = False) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    if scrub:
        data = _scrub(data)
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
    parser.add_argument("--scrub", action="store_true",
                        help="Redact personal data in the domain-JSON fixtures")
    args = parser.parse_args()

    token = os.getenv("PICNIC_AUTH_TOKEN")
    country = os.getenv("COUNTRY_CODE", "NL")
    if not token:
        raise SystemExit(
            "PICNIC_AUTH_TOKEN is required (export it or put it in .env)."
        )

    client = PicnicAPI(auth_token=token, country_code=country)

    # PML pages: capture the raw (pre-parse) payloads via the private request
    # helper so the fixtures contain the full PML tree, not the parsed models.
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

    # Domain-JSON endpoints. These carry personal data -> scrub before committing.
    _dump("user", client._get("/user"), country, scrub=args.scrub)
    _dump("cart", client._get("/cart"), country, scrub=args.scrub)
    _dump("delivery_slots", client._get("/cart/delivery_slots"), country,
          scrub=args.scrub)
    summary = client._post("/deliveries/summary", data=["CURRENT"])
    _dump("current_deliveries", summary, country, scrub=args.scrub)
    if summary:
        delivery_id = summary[0].get("delivery_id")
        if delivery_id:
            _dump("delivery", client._get(f"/deliveries/{delivery_id}"), country,
                  scrub=args.scrub)


if __name__ == "__main__":
    main()
