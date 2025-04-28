import unittest
from unittest.mock import patch

import pytest

from python_picnic_api2 import PicnicAPI
from python_picnic_api2.client import DEFAULT_URL
from python_picnic_api2.session import PicnicAuthError

PICNIC_HEADERS = {
    "x-picnic-agent": "30100;1.15.272-15295;",
    "x-picnic-did": "3C417201548B2E3B",
}


class TestClient(unittest.TestCase):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def setUp(self) -> None:
        self.session_patcher = patch("python_picnic_api2.client.PicnicAPISession")
        self.session_mock = self.session_patcher.start()
        self.client = PicnicAPI(username="test@test.nl", password="test")
        self.expected_base_url = DEFAULT_URL.format("nl", "15")

    def tearDown(self) -> None:
        self.session_patcher.stop()

    def test_login_credentials(self):
        self.session_mock().authenticated = False
        PicnicAPI(username="test@test.nl", password="test")
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/user/login",
            json={
                "key": "test@test.nl",
                "secret": "098f6bcd4621d373cade4e832627b4f6",
                "client_id": 30100,
            },
        )

    def test_login_auth_token(self):
        self.session_mock().authenticated = True
        PicnicAPI(
            username="test@test.nl",
            password="test",
            auth_token="a3fwo7f3h78kf3was7h8f3ahf3ah78f3",
        )
        self.session_mock().login.assert_not_called()

    def test_login_failed(self):
        response = {
            "error": {
                "code": "AUTH_INVALID_CRED",
                "message": "Invalid credentials.",
            }
        }
        self.session_mock().post.return_value = self.MockResponse(response, 200)

        client = PicnicAPI()
        with self.assertRaises(PicnicAuthError):
            client.login("test-user", "test-password")

    def test_get_user(self):
        response = {
            "user_id": "594-241-3623",
            "firstname": "Firstname",
            "lastname": "Lastname",
            "address": {
                "house_number": 25,
                "house_number_ext": "b",
                "postcode": "1234 AB",
                "street": "Dorpsstraat",
                "city": "Het dorp",
            },
            "phone": "+31123456798",
            "contact_email": "test@test.nl",
            "total_deliveries": 25,
            "completed_deliveries": 20,
        }
        self.session_mock().get.return_value = self.MockResponse(response, 200)

        user = self.client.get_user()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/user", headers=None
        )
        self.assertDictEqual(user, response)

    def test_search(self):
        self.client.search("test-product")
        self.session_mock().get.assert_called_with(
            self.expected_base_url
            + "/pages/search-page-results?search_term=test-product",
            headers=PICNIC_HEADERS,
        )

    def test_search_encoding(self):
        self.client.search("Gut&Günstig H-Milch")
        self.session_mock().get.assert_called_with(
            self.expected_base_url
            + "/pages/search-page-results?search_term=Gut%26G%C3%BCnstig%20H-Milch",
            headers=PICNIC_HEADERS,
        )

    def test_get_article_by_gtin(self):
        self.client.get_article_by_gtin("123456789")
        self.session_mock().get.assert_called_with(
            "https://picnic.app/nl/qr/gtin/123456789",
            headers=PICNIC_HEADERS,
            allow_redirects=False,
        )

    def test_get_cart(self):
        self.client.get_cart()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/cart", headers=None
        )

    def test_add_product(self):
        self.client.add_product("p3f2qa")
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/add_product",
            json={"product_id": "p3f2qa", "count": 1},
        )

    def test_add_multiple_products(self):
        self.client.add_product("gs4puhf3a", count=5)
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/add_product",
            json={"product_id": "gs4puhf3a", "count": 5},
        )

    def test_remove_product(self):
        self.client.remove_product("gs4puhf3a", count=5)
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/remove_product",
            json={"product_id": "gs4puhf3a", "count": 5},
        )

    def test_clear_cart(self):
        self.client.clear_cart()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/clear", json=None
        )

    def test_get_delivery_slots(self):
        self.client.get_delivery_slots()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/cart/delivery_slots", headers=None
        )

    def test_get_delivery(self):
        self.client.get_delivery("3fpawshusz3")
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/deliveries/3fpawshusz3", headers=None
        )

    def test_get_delivery_scenario(self):
        self.client.get_delivery_scenario("3fpawshusz3")
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/deliveries/3fpawshusz3/scenario",
            headers=PICNIC_HEADERS,
        )

    def test_get_delivery_position(self):
        self.client.get_delivery_position("3fpawshusz3")
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/deliveries/3fpawshusz3/position",
            headers=PICNIC_HEADERS,
        )

    def test_get_deliveries_summary(self):
        self.client.get_deliveries()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/deliveries/summary", json=[]
        )

    def test_get_deliveries(self):
        with pytest.raises(NotImplementedError):
            self.client.get_deliveries(summary=False)

    def test_get_current_deliveries(self):
        self.client.get_current_deliveries()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/deliveries/summary", json=["CURRENT"]
        )

    def test_get_categories(self):
        self.session_mock().get.return_value = self.MockResponse(
            {
                "type": "MY_STORE",
                "catalog": [
                    {"type": "CATEGORY", "id": "purchases", "name": "Besteld"},
                    {"type": "CATEGORY", "id": "promotions", "name": "Acties"},
                ],
                "user": {},
            },
            200,
        )

        categories = self.client.get_categories()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/my_store?depth=0", headers=None
        )

        self.assertDictEqual(
            categories[0],
            {"type": "CATEGORY", "id": "purchases", "name": "Besteld"},
        )

    def test_get_auth_exception(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"error": {"code": "AUTH_ERROR"}}, 400
        )

        with self.assertRaises(PicnicAuthError):
            self.client.get_user()

    def test_post_auth_exception(self):
        self.session_mock().post.return_value = self.MockResponse(
            {"error": {"code": "AUTH_ERROR"}}, 400
        )

        with self.assertRaises(PicnicAuthError):
            self.client.clear_cart()
