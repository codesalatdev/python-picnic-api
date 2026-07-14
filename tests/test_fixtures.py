"""Golden tests against real (trimmed) Picnic PML payloads in tests/fixtures/.

These fixtures were captured from the live DE storefront via
``scripts/capture_fixtures.py`` and trimmed to a few real nodes. They guard
against layout drift that hand-written mocks would miss.
"""

import json
from pathlib import Path

import pytest

from python_picnic_api2.models import Article, SearchResult

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    path = FIXTURES / name
    if not path.exists():
        pytest.skip(f"fixture {name} not captured")
    return json.loads(path.read_text(encoding="utf-8"))


def test_search_page_de_real():
    result = SearchResult.from_page(_load("search_page_de.json"))
    assert len(result.items) >= 1
    first = result.items[0]
    assert first.id
    assert first.name
    assert isinstance(first.display_price, int)
    # .raw preserves the untouched tile payload.
    assert first.raw["sellingUnit"]["id"] == first.id


def test_product_details_page_de_real():
    data = _load("product_details_page_de.json")
    article = Article.from_page(data, "s1018620")
    assert article is not None
    assert article.product_name == "H-Milch 3,5%"
    assert article.producer == "Gut&Günstig"
    assert article.name == "Gut&Günstig H-Milch 3,5%"
    assert article.unit_quantity == "1L"


def test_product_details_category_ids_de_real():
    data = _load("product_details_page_de.json")
    assert Article.category_ids_from_page(data) == (24410, 19400, 19626)


# The delivery endpoints still return raw dicts (no model yet). These fixtures
# were captured while a delivery was scheduled and guard the response shape for
# the upcoming Delivery model. Identifiers are scrubbed.
def test_current_deliveries_de_real_shape():
    deliveries = _load("current_deliveries_de.json")
    assert isinstance(deliveries, list) and deliveries
    delivery = deliveries[0]
    assert delivery["status"] == "CURRENT"
    assert delivery["delivery_id"]
    assert delivery["slot"]["window_start"]
    assert delivery["orders"][0]["total_price"] > 0


def test_delivery_detail_de_real_shape():
    delivery = _load("delivery_de.json")
    assert delivery["type"] == "DELIVERY"
    assert delivery["status"] == "CURRENT"
    # orders -> order lines -> order articles
    article = delivery["orders"][0]["items"][0]["items"][0]
    assert article["type"] == "ORDER_ARTICLE"
    assert article["id"] and article["name"]
