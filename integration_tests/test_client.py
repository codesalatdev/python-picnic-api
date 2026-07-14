import os
import time

import pytest
from dotenv import load_dotenv

from python_picnic_api2 import Article, PicnicAPI, SearchResult

load_dotenv()

auth_token = os.getenv("AUTH_TOKEN")
country_code = os.getenv("COUNTRY_CODE")

picnic = PicnicAPI(auth_token=auth_token, country_code=country_code)


@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    time.sleep(2)


def _get_amount(cart: dict, product_id: str):
    items = cart["items"][0]["items"]
    product = next((item for item in items if item["id"] == product_id), None)
    return product["decorators"][0]["quantity"]


def test_auth_token_valid():
    assert picnic.logged_in(), (
        "Auth token is invalid or expired — renew the PICNIC_AUTH_TOKEN secret"
    )


def test_get_user():
    response = picnic.get_user()
    assert isinstance(response, dict)
    assert "contact_email" in response


def test_search():
    response = picnic.search("kaffee")
    assert isinstance(response, SearchResult)
    assert isinstance(response.items, list)
    assert response.items[0].id


def test_get_article():
    response = picnic.get_article("s1018620")
    assert isinstance(response, Article)
    assert response.id == "s1018620"
    assert response.name == "Gut&Günstig H-Milch 3,5%"


def test_get_article_with_category_name():
    response = picnic.get_article("s1018620", add_category=True)
    assert isinstance(response, Article)
    assert response.category is not None
    assert response.category.name == "H-Milch"


def test_get_article_by_gtin():
    response = picnic.get_article_by_gtin("4311501044209")
    assert response.id == "s1018620"
    assert response.name == "Gut&Günstig H-Milch 3,5%"


def test_get_article_by_gtin_unknown():
    response = picnic.get_article_by_gtin("4311501040000")
    assert response is None


def test_get_cart():
    response = picnic.get_cart()
    assert isinstance(response, dict)
    assert "id" in response
    assert response["id"] == "shopping_cart"


def test_add_product():
    # need a clear cart for reproducibility
    picnic.clear_cart()
    response = picnic.add_product("s1018620", count=2)

    assert isinstance(response, dict)
    assert "items" in response
    assert any(
        item["id"] == "s1018620" for item in response["items"][0]["items"])
    assert _get_amount(response, "s1018620") == 2


def test_remove_product():
    # need a clear cart for reproducibility
    picnic.clear_cart()
    # add two milk to the cart so we can remove 1
    picnic.add_product("s1018620", count=2)

    response = picnic.remove_product("s1018620", count=1)
    amount = _get_amount(response, "s1018620")

    assert isinstance(response, dict)
    assert "items" in response
    assert amount == 1


def test_clear_cart():
    # need a clear cart for reproducibility
    picnic.clear_cart()
    # add two coffee to the cart so we can clear it
    picnic.add_product("s1018620", count=2)

    response = picnic.clear_cart()

    assert isinstance(response, dict)
    assert "items" in response
    assert len(response["items"]) == 0


def test_get_delivery_slots():
    response = picnic.get_delivery_slots()
    assert isinstance(response, dict)
    assert "delivery_slots" in response
    assert isinstance(response["delivery_slots"], list)


def test_get_deliveries():
    response = picnic.get_deliveries()

    assert isinstance(response, list)
    assert isinstance(response[0], dict)
    assert response[0]["status"] == "COMPLETED"


def test_get_delivery():
    # get a id to test against
    response = picnic.get_deliveries()
    deliveryId = response[0]["delivery_id"]

    response = picnic.get_delivery(deliveryId)
    assert isinstance(response, dict)
    assert response["status"] == "COMPLETED"
    assert response["id"] == deliveryId


def test_get_current_deliveries():
    response = picnic.get_current_deliveries()
    assert isinstance(response, list)
