from python_picnic_api2.models import Article, Category, SearchResult

PRODUCT_DETAILS_PAGE = {
    "body": {"child": {"child": {"children": [{
        "id": "product-details-page-root-main-container",
        "pml": {"component": {"children": [
            {"markdown": "#(#333333)Goede start halvarine#(#333333)"},
            {"markdown": "Blue Band"},
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
    assert article.producer == "Blue Band"
    assert article.raw is PRODUCT_DETAILS_PAGE


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
