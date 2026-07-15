"""Golden tests against real (trimmed) Picnic PML payloads in tests/fixtures/.

These fixtures were captured from the live DE storefront via
``scripts/capture_fixtures.py`` and trimmed to a few real nodes. They guard
against layout drift that hand-written mocks would miss.
"""

import json
from pathlib import Path

import pytest

from python_picnic_api2.models import (
    Article,
    Cart,
    Delivery,
    DeliverySlots,
    DeliverySummary,
    SearchResult,
    User,
    pml,
)

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
    assert article.price_per_unit == "€0.95/L"
    assert article.price == 95
    assert article.image_id.startswith("6a6e61db")
    assert article.description.startswith("Perfekt für den morgendlichen Kaffee")
    # Named color codes stripped, bold markdown kept.
    assert article.highlights == [
        "Lange **haltbar**", "**3,5%** Fettanteil", "**Ohne** Gentechnik"]


def test_product_details_category_ids_de_real():
    data = _load("product_details_page_de.json")
    assert Article.category_ids_from_page(data) == (24410, 19400, 19626)


def test_product_details_bundle_de_real():
    # Real Barilla bundle page (trimmed): the main container carries no price and
    # several product-page-bundle-item-<id> containers hold per-pack-size prices.
    data = _load("product_details_bundle_de.json")
    article = Article.from_page(data, "s1050481")
    assert article is not None
    assert article.name == "Barilla Spaghetti"
    assert article.product_name == "Spaghetti"
    assert article.producer == "Barilla"
    assert article.unit_quantity == "4 x 500g"
    assert article.price_per_unit == "€3.70/kg"
    # Price is scoped to the requested pack's bundle-item container (185, the
    # per-500g price), not the first PRICE on the page (199, a different pack).
    assert article.price == 185
    assert article.is_bundle is True
    assert article.bundle_variant_ids == ["s1018999", "s1050480", "s1115047"]


def test_search_page_nl_real():
    result = SearchResult.from_page(_load("search_page_nl.json"))
    assert len(result.items) >= 1
    first = result.items[0]
    assert first.id == "s1016222"
    assert first.name == "Picnic aromatico filterkoffie"
    assert isinstance(first.display_price, int)


def test_product_details_page_nl_real():
    data = _load("product_details_page_nl.json")
    article = Article.from_page(data, "s1016222")
    assert article is not None
    assert article.product_name == "Aromatico filterkoffie"
    assert article.producer == "Picnic"
    assert article.name == "Picnic Aromatico filterkoffie"
    assert article.unit_quantity == "500 gram"
    assert article.price == 799
    assert article.image_id.startswith("1be1d07e")
    assert article.description.startswith("Onze aromatische filterkoffie")
    assert article.highlights == ["**Volle** smaak", "Snelfiltermaling"]


def test_product_details_category_ids_nl_real():
    data = _load("product_details_page_nl.json")
    assert Article.category_ids_from_page(data) == (21738, 21887, 22600)


def test_product_details_multipack_nl_real():
    # Real NL multipack. NL returns prices as float (1035.0) where DE uses int
    # (95); the parser must coerce to integer cents and never leave price None.
    # It is an ordinary product, not a tiered bundle.
    data = _load("product_details_multipack_nl.json")
    article = Article.from_page(data, "s1017747")
    assert article is not None
    assert article.name == "Fanta Orange"
    assert article.producer == "Fanta"
    assert article.product_name == "Orange"
    assert article.unit_quantity == "4 x 1.5 liter"
    assert article.price_per_unit == "€1.73/l"
    assert article.price == 1035
    assert isinstance(article.price, int)
    assert article.is_bundle is False


def test_category_page_nl_real():
    # Mirrors client.get_category_by_ids: find the L3 sub-header, read its label.
    data = _load("category_page_nl.json")
    node = pml.find(data, id="vertical-article-tiles-sub-header-22600")
    assert node is not None
    assert pml.accessibility_label(node) == "Regular"


# The domain-JSON endpoints (user, cart, deliveries, slots) return clean JSON
# parsed into pydantic models. These fixtures were captured from the live DE
# storefront and scrubbed of personal data; they guard the models against drift.
def test_current_deliveries_de_real():
    deliveries = [DeliverySummary.from_api(d) for d in
                  _load("current_deliveries_de.json")]
    assert deliveries
    summary = deliveries[0]
    assert summary.status == "CURRENT"
    assert summary.slot.window_start
    assert summary.orders[0].total_price > 0
    # Summary orders carry totals but no line items.
    assert summary.orders[0].items == []


def test_delivery_detail_de_real():
    delivery = Delivery.from_api(_load("delivery_de.json"))
    assert delivery.type == "DELIVERY"
    assert delivery.status == "CURRENT"
    assert delivery.slot.window_start
    # orders -> order lines -> order articles
    order = delivery.orders[0]
    assert order.total_price > 0
    article = order.items[0].items[0]
    assert article.type == "ORDER_ARTICLE"
    assert article.name
    assert delivery.raw["type"] == "DELIVERY"


def test_user_de_real():
    user = User.from_api(_load("user_de.json"))
    assert user.address is not None
    assert user.subscriptions
    assert isinstance(user.total_deliveries, int)
    assert isinstance(user.consent_decisions, dict)


def test_cart_de_real():
    cart = Cart.from_api(_load("cart_de.json"))
    assert cart.type == "ORDER"
    assert isinstance(cart.total_price, int)
    assert cart.delivery_slots
    assert cart.delivery_slots[0].minimum_order_value == 4500
    assert cart.selected_slot is not None


def test_delivery_slots_de_real():
    slots = DeliverySlots.from_api(_load("delivery_slots_de.json"))
    assert slots.delivery_slots
    first = slots.delivery_slots[0]
    assert first.window_start and first.window_end
    assert first.is_available is True
