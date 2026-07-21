from python_picnic_api2.models import (
    Article,
    Cart,
    Category,
    Delivery,
    DeliverySlots,
    DeliverySummary,
    SearchResult,
    User,
)

PRODUCT_DETAILS_PAGE = {
    "body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Goede start halvarine#(#333333)",
             "textType": "HEADER1"},
            {"markdown": "Blue Band"},
            {"markdown": "#(#333333)250 gram#(#333333)"},
            {"markdown": "€5.16/kg"},
            {"type": "PRICE", "price": 149},
        ]}},
    }, {
        "type": "image_gallery", "image_id": "img-abc",
    }, {
        "id": "product-page-description",
        "pml": {"component": {"children": [
            {"markdown": "A tasty **spread**."},
        ]}},
    }, {
        "id": "product-page-highlights",
        "pml": {"component": {"children": [
            {"markdown": "#(GREEN1)Vegan#(GREEN1)"},
            {"markdown": "Low fat"},
        ]}},
    }, {
        "id": "category-button",
        "pml": {"component": {"onPress": {
            "target": "app.picnic://categories/1000/l2/2000/l3/3000"}}},
    }]}}}
}

SEARCH_PAGE = {
    "body": {"child": {"children": [
        {"type": "SELLING_UNIT_TILE", "sellingUnit": {
            "id": "s1019822", "name": "Lavazza", "display_price": 1799,
            "unit_quantity": "1kg", "sole_article_id": "10511523"}},
        {"type": "SELLING_UNIT_TILE", "sellingUnit": {
            "id": "s1018620", "name": "Milk", "display_price": 129}},
    ]}}
}


def test_article_from_page():
    article = Article.from_page(PRODUCT_DETAILS_PAGE, "p3f2qa")
    assert article.id == "p3f2qa"
    assert article.name == "Blue Band Goede start halvarine"
    assert article.product_name == "Goede start halvarine"
    assert article.producer == "Blue Band"
    assert article.unit_quantity == "250 gram"
    assert article.price_per_unit == "€5.16/kg"
    assert article.price == 149
    assert article.image_id == "img-abc"
    assert article.description == "A tasty **spread**."
    # Named color codes (#(GREEN1)…) are stripped, bold markdown is kept.
    assert article.highlights == ["Vegan", "Low fat"]
    # An ordinary product is not a bundle.
    assert article.is_bundle is False
    assert article.bundle_variant_ids == []
    assert article.raw is PRODUCT_DETAILS_PAGE


def test_article_from_page_unbranded_produce():
    # Fresh produce has no brand line and no price-per-unit; a positional read
    # used to put the quantity into `producer`. Roles must be assigned correctly.
    page = {"body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Bananen#(#333333)", "textType": "HEADER1"},
            {"markdown": "#(#333333)5 Stück#(#333333)"},
            {"type": "PRICE", "price": 149},
        ]}},
    }]}}}}
    article = Article.from_page(page, "s1020669")
    assert article.product_name == "Bananen"
    assert article.producer is None
    assert article.unit_quantity == "5 Stück"
    assert article.price_per_unit is None
    assert article.name == "Bananen"
    assert article.price == 149


def test_article_on_sale_prices():
    # On-sale layout: current price first, struck-through original (isCrossed)
    # second. `price` must be the current one, never the crossed original.
    page = {"body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Feine Butter#(#333333)", "textType": "HEADER1"},
            {"markdown": "Meggle"},
            {"color": "#b40117", "price": 143, "type": "PRICE"},
            {"color": "#c9c6c3", "price": 179, "isCrossed": True, "type": "PRICE"},
        ]}},
    }]}}}}
    article = Article.from_page(page, "s1146184")
    assert article.price == 143
    assert article.original_price == 179


def test_article_not_on_sale_has_no_original_price():
    article = Article.from_page(PRODUCT_DETAILS_PAGE, "p3f2qa")
    assert article.original_price is None


def test_article_bundle_price_scoped_to_matching_item():
    # Bundle/multipack pages list several pack sizes, each in its own
    # product-page-bundle-item-<id> container. The price must come from the
    # container matching the requested article, not the first PRICE on the page.
    page = {"body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Spaghetti#(#333333)", "textType": "HEADER1"},
            {"markdown": "Barilla"},
            {"markdown": "#(#333333)4 x 500g#(#333333)"},
        ]}},
    }, {
        "id": "product-page-bundle-item-s1018999",
        "pml": {"component": {"children": [
            {"price": 199, "type": "PRICE"}]}},
    }, {
        "id": "product-page-bundle-item-s1050481",
        "pml": {"component": {"children": [
            {"price": 185, "type": "PRICE"}]}},
    }]}}}}
    article = Article.from_page(page, "s1050481")
    assert article.price == 185
    assert article.unit_quantity == "4 x 500g"
    assert article.is_bundle is True
    # Sibling pack sizes only (the requested article is excluded).
    assert article.bundle_variant_ids == ["s1018999"]


def test_article_price_accepts_float_cents():
    # NL returns the price as a float (1035.0) where DE uses an int; it must
    # coerce to integer cents and never be left as None.
    page = {"body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Orange#(#333333)", "textType": "HEADER1"},
            {"markdown": "Fanta"},
            {"type": "PRICE", "price": 1035.0},
        ]}},
    }]}}}}
    article = Article.from_page(page, "s1017747")
    assert article.price == 1035
    assert isinstance(article.price, int)


def test_article_price_falls_back_to_any_price_key():
    # Even when the main price isn't a PRICE-type node, price must still parse.
    page = {"body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Wein#(#333333)", "textType": "HEADER1"},
            {"someWrapper": {"price": 499}},
        ]}},
    }]}}}}
    article = Article.from_page(page, "s1")
    assert article.price == 499


def test_article_from_page_unsupported_returns_none():
    assert Article.from_page({"body": {"child": {}}}, "p3f2qa") is None


def test_article_category_ids_from_page():
    assert Article.category_ids_from_page(PRODUCT_DETAILS_PAGE) == (1000, 2000, 3000)
    assert Article.category_ids_from_page({"body": {}}) is None


def test_search_result_from_page():
    result = SearchResult.from_page(SEARCH_PAGE)
    assert [item.id for item in result.items] == ["s1019822", "s1018620"]
    assert result.items[0].display_price == 1799
    assert result.items[0].sole_article_id == "10511523"
    assert result.items[0].raw["sellingUnit"]["id"] == "s1019822"


def test_search_result_empty():
    result = SearchResult.from_page({"body": {"child": {}}})
    assert result.items == []


def test_models_tolerate_unknown_fields():
    # extra="ignore": country/A-B variance must not break parsing.
    result = SearchResult.from_page({"body": {"child": {"children": [
        {"type": "SELLING_UNIT_TILE", "sellingUnit": {
            "id": "s1", "name": "X", "some_new_field": {"nested": True},
            "another_variant_key": [1, 2, 3]}},
    ]}}})
    assert result.items[0].id == "s1"
    assert result.items[0].name == "X"


def test_category_parse_deeplink():
    assert Category.parse_deeplink(
        "app.picnic://categories/1/l2/2/l3/3") == (1, 2, 3)
    assert Category.parse_deeplink("garbage") is None


def test_model_dump_excludes_raw():
    article = Article.from_page(PRODUCT_DETAILS_PAGE, "p3f2qa")
    assert "raw" not in article.model_dump()


# --- Domain-JSON models -----------------------------------------------------

USER_RESPONSE = {
    "user_id": "594-241-3623",
    "firstname": "Firstname",
    "lastname": "Lastname",
    "address": {"house_number": 25, "street": "Dorpsstraat", "city": "Het dorp"},
    "contact_email": "test@test.nl",
    "subscriptions": [{"list_id": "MISC", "subscribed": True, "name": "Emails"}],
    "household_details": {"adults": 2, "children": 0},
    "consent_decisions": {"POST_MAIL": True},
    "total_deliveries": 25,
    "completed_deliveries": 20,
}

DELIVERY_RESPONSE = {
    "type": "DELIVERY",
    "delivery_id": "d123",
    "status": "CURRENT",
    "slot": {"slot_id": "s1", "window_start": "2026-07-15T14:15:00.000+02:00"},
    "eta2": {"start": "2026-07-15T15:06:00.000+02:00", "end": "..."},
    "orders": [{
        "type": "ORDER",
        "id": "o1",
        "total_price": 4996,
        "transaction_info": {"payment_type": "DIRECT_DEBIT"},
        "items": [{
            "type": "ORDER_LINE",
            "id": "2528",
            "display_price": 169,
            "items": [{
                "type": "ORDER_ARTICLE",
                "id": "s1021945",
                "name": "Burger Buns",
                "price": 199,
                "decorators": [{"type": "QUANTITY", "quantity": 1}],
            }],
        }],
    }],
}


def test_user_from_api():
    user = User.from_api(USER_RESPONSE)
    assert user.user_id == "594-241-3623"
    assert user.firstname == "Firstname"
    assert user.address.city == "Het dorp"
    assert user.subscriptions[0].name == "Emails"
    assert user.household_details.adults == 2
    assert user.consent_decisions["POST_MAIL"] is True
    assert user.total_deliveries == 25
    assert user.raw is USER_RESPONSE
    assert "raw" not in user.model_dump()


def test_cart_from_api():
    response = {
        "type": "ORDER",
        "id": "shopping_cart",
        "total_count": 2,
        "total_price": 1234,
        "delivery_slots": [{"slot_id": "s1", "minimum_order_value": 4500}],
        "selected_slot": {"slot_id": "s1", "state": "IMPLICIT"},
        "items": [{
            "type": "ORDER_LINE", "id": "l1", "display_price": 199,
            "items": [{"type": "ORDER_ARTICLE", "id": "s1", "name": "Milk"}],
        }],
    }
    cart = Cart.from_api(response)
    assert cart.type == "ORDER"
    assert cart.total_count == 2
    assert cart.delivery_slots[0].minimum_order_value == 4500
    assert cart.selected_slot.state == "IMPLICIT"
    assert cart.items[0].items[0].name == "Milk"
    assert cart.raw is response


def test_delivery_from_api_order_tree():
    delivery = Delivery.from_api(DELIVERY_RESPONSE)
    assert delivery.delivery_id == "d123"
    assert delivery.status == "CURRENT"
    assert delivery.slot.slot_id == "s1"
    assert delivery.eta2.start.startswith("2026-07-15")
    order = delivery.orders[0]
    assert order.total_price == 4996
    assert order.transaction_info.payment_type == "DIRECT_DEBIT"
    article = order.items[0].items[0]
    assert article.id == "s1021945"
    assert article.name == "Burger Buns"
    assert article.decorators[0].type == "QUANTITY"
    assert "raw" not in delivery.model_dump()


def test_delivery_summary_from_api():
    response = {
        "delivery_id": "d1",
        "status": "COMPLETED",
        "slot": {"slot_id": "s1"},
        "orders": [{"type": "ORDER", "id": "o1", "total_price": 4996}],
    }
    summary = DeliverySummary.from_api(response)
    assert summary.delivery_id == "d1"
    assert summary.status == "COMPLETED"
    # Summary orders carry totals but no line items.
    assert summary.orders[0].total_price == 4996
    assert summary.orders[0].items == []


def test_delivery_slots_from_api():
    response = {
        "delivery_slots": [
            {"slot_id": "s1", "is_available": True},
            {"slot_id": "s2", "is_available": False},
        ],
        "selected_slot": {"slot_id": "s1", "state": "EXPLICIT"},
    }
    slots = DeliverySlots.from_api(response)
    assert [s.slot_id for s in slots.delivery_slots] == ["s1", "s2"]
    assert slots.selected_slot.slot_id == "s1"


def test_domain_models_tolerate_unknown_fields():
    # extra="ignore": country/A-B variance must not break parsing.
    cart = Cart.from_api({"type": "ORDER", "some_new_field": {"x": 1}})
    assert cart.type == "ORDER"
