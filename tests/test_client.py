import unittest
from unittest.mock import patch

import pytest

from python_picnic_api2 import Category, PicnicAPI
from python_picnic_api2.client import DEFAULT_URL
from python_picnic_api2.session import (
    Picnic2FAError,
    Picnic2FARequired,
    PicnicAuthError,
)

PICNIC_HEADERS = {
    "x-picnic-agent": "30100;1.206.1-#15408",
    "x-picnic-did": "598F770380CA54B6",
}


class TestClient(unittest.TestCase):
    class MockResponse:
        def __init__(self, json_data, status_code, content=b"data"):
            self.json_data = json_data
            self.status_code = status_code
            self.content = content

        def json(self):
            return self.json_data

    def setUp(self) -> None:
        self.session_patcher = patch(
            "python_picnic_api2.client.PicnicAPISession")
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
            headers=PICNIC_HEADERS,
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
        self.assertEqual(user.user_id, "594-241-3623")
        self.assertEqual(user.firstname, "Firstname")
        self.assertEqual(user.address.city, "Het dorp")
        self.assertEqual(user.total_deliveries, 25)
        # .raw preserves the untouched payload.
        self.assertEqual(user.raw, response)

    def test_search(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"body": {"child": {"children": [{
                "type": "SELLING_UNIT_TILE",
                "sellingUnit": {
                    "id": "s1019822",
                    "name": "Lavazza",
                    "display_price": 1799,
                    "unit_quantity": "1kg",
                },
            }]}}},
            200,
        )
        result = self.client.search("test-product")
        self.session_mock().get.assert_called_with(
            self.expected_base_url
            + "/pages/search-page-results?search_term=test-product",
            headers=PICNIC_HEADERS,
        )
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].id, "s1019822")
        self.assertEqual(result.items[0].name, "Lavazza")
        self.assertEqual(result.items[0].display_price, 1799)

    def test_search_encoding(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"body": {"child": {}}}, 200
        )
        self.client.search("Gut&Günstig H-Milch")
        self.session_mock().get.assert_called_with(
            self.expected_base_url
            + "/pages/search-page-results?search_term=Gut%26G%C3%BCnstig%20H-Milch",
            headers=PICNIC_HEADERS,
        )

    def test_get_article(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"body": {"child": {"child": {"children": [{
                "id": "product-details-page-root-main-container",
                "pml": {
                    "component": {
                        "children": [
                            {
                                "markdown": "#(#333333)Goede start halvarine#(#333333)",
                            },
                            {
                                "markdown": "Blue Band",
                            },

                        ]
                    }
                }
            }]}}}},
            200
        )

        article = self.client.get_article("p3f2qa")
        self.session_mock().get.assert_called_with(
            "https://storefront-prod.nl.picnicinternational.com/api/15/pages/product-details-page-root?id=p3f2qa&show_category_action=true",
            headers=PICNIC_HEADERS,
        )

        self.assertEqual(article.id, "p3f2qa")
        self.assertEqual(article.name, "Blue Band Goede start halvarine")

    def test_get_article_with_category(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"body": {"child": {"child": {"children": [{
                "id": "product-details-page-root-main-container",
                "pml": {
                    "component": {
                        "children": [
                            {
                                "markdown": "#(#333333)Goede start halvarine#(#333333)",
                            },
                            {
                                "markdown": "Blue Band",
                            },

                        ]
                    }
                }
            },
                {
                "id": "category-button",
                "pml": {"component": {"onPress": {"target": "app.picnic://categories/1000/l2/2000/l3/3000"}}}
            }]}}}},
            200
        )

        category_patch = patch(
            "python_picnic_api2.client.PicnicAPI.get_category_by_ids")
        category_patch.start().return_value = Category(
            l2_id=2000, l3_id=3000, name="Test")

        article = self.client.get_article("p3f2qa", True)

        category_patch.stop()
        self.session_mock().get.assert_called_with(
            "https://storefront-prod.nl.picnicinternational.com/api/15/pages/product-details-page-root?id=p3f2qa&show_category_action=true",
            headers=PICNIC_HEADERS,
        )

        self.assertEqual(article.id, "p3f2qa")
        self.assertEqual(article.name, "Blue Band Goede start halvarine")
        self.assertEqual(article.category.l2_id, 2000)
        self.assertEqual(article.category.l3_id, 3000)
        self.assertEqual(article.category.name, "Test")

    def test_get_article_with_unsupported_structure(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"body": {"child": {"child": {"children": [{
                "id": "unsupported-root-container",
                "pml": {
                    "component": {
                        "children": [
                            {
                                "markdown": "#(#333333)Goede start halvarine#(#333333)",
                            },
                            {
                                "markdown": "Blue Band",
                            },

                        ]
                    }
                }
            }]}}}},
            200
        )

        article = self.client.get_article("p3f2qa")
        self.session_mock().get.assert_called_with(
            "https://storefront-prod.nl.picnicinternational.com/api/15/pages/product-details-page-root?id=p3f2qa&show_category_action=true",
            headers=PICNIC_HEADERS,
        )

        assert article is None

    def test_get_article_by_gtin(self):
        self.client.get_article_by_gtin("123456789")
        self.session_mock().get.assert_called_with(
            "https://picnic.app/nl/qr/gtin/123456789",
            headers=PICNIC_HEADERS,
            allow_redirects=False,
        )

    def test_get_cart(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"type": "ORDER", "id": "shopping_cart", "total_count": 3}, 200
        )
        cart = self.client.get_cart()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/cart",
            headers=PICNIC_HEADERS,
        )
        self.assertEqual(cart.type, "ORDER")
        self.assertEqual(cart.total_count, 3)

    def test_add_product(self):
        self.session_mock().post.return_value = self.MockResponse(
            {"type": "ORDER", "id": "shopping_cart"}, 200
        )
        cart = self.client.add_product("p3f2qa")
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/add_product",
            json={"product_id": "p3f2qa", "count": 1},
            headers=PICNIC_HEADERS,
        )
        self.assertEqual(cart.type, "ORDER")

    def test_add_multiple_products(self):
        self.session_mock().post.return_value = self.MockResponse(
            {"type": "ORDER"}, 200
        )
        self.client.add_product("gs4puhf3a", count=5)
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/add_product",
            json={"product_id": "gs4puhf3a", "count": 5},
            headers=PICNIC_HEADERS,
        )

    def test_remove_product(self):
        self.session_mock().post.return_value = self.MockResponse(
            {"type": "ORDER"}, 200
        )
        self.client.remove_product("gs4puhf3a", count=5)
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/remove_product",
            json={"product_id": "gs4puhf3a", "count": 5},
            headers=PICNIC_HEADERS,
        )

    def test_clear_cart(self):
        self.session_mock().post.return_value = self.MockResponse(
            {"type": "ORDER"}, 200
        )
        cart = self.client.clear_cart()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/cart/clear",
            json=None,
            headers=PICNIC_HEADERS,
        )
        self.assertEqual(cart.type, "ORDER")

    def test_get_delivery_slots(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"delivery_slots": [{"slot_id": "abc"}], "selected_slot": None}, 200
        )
        slots = self.client.get_delivery_slots()
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/cart/delivery_slots", headers=None
        )
        self.assertEqual(slots.delivery_slots[0].slot_id, "abc")

    def test_get_delivery(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"type": "DELIVERY", "delivery_id": "3fpawshusz3", "status": "CURRENT"},
            200,
        )
        delivery = self.client.get_delivery("3fpawshusz3")
        self.session_mock().get.assert_called_with(
            self.expected_base_url + "/deliveries/3fpawshusz3", headers=None
        )
        self.assertEqual(delivery.delivery_id, "3fpawshusz3")
        self.assertEqual(delivery.status, "CURRENT")

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
        self.session_mock().post.return_value = self.MockResponse([], 200)
        result = self.client.get_deliveries()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/deliveries/summary", json=[]
        )
        self.assertEqual(result, [])

    def test_get_deliveries(self):
        with pytest.raises(NotImplementedError):
            self.client.get_deliveries(summary=False)

    def test_get_current_deliveries(self):
        self.session_mock().post.return_value = self.MockResponse(
            [{"delivery_id": "d1", "status": "CURRENT"}], 200
        )
        result = self.client.get_current_deliveries()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/deliveries/summary", json=["CURRENT"]
        )
        self.assertEqual(result[0].delivery_id, "d1")
        self.assertEqual(result[0].status, "CURRENT")

    def test_get_categories(self):
        with pytest.raises(NotImplementedError):
            self.client.get_categories()

    def test_get_category_by_ids(self):
        self.session_mock().get.return_value = self.MockResponse(
            {"children": [
                {
                    "id": "vertical-article-tiles-sub-header-22193",
                    "pml": {
                        "component": {
                            "accessibilityLabel": "Halvarine"
                        }
                    }
                }
            ]},
            200
        )

        category = self.client.get_category_by_ids(1000, 22193)
        self.session_mock().get.assert_called_with(
            f"{self.expected_base_url}/pages/L2-category-page-root" +
            "?category_id=1000&l3_category_id=22193", headers=PICNIC_HEADERS
        )

        self.assertEqual(category.name, "Halvarine")
        self.assertEqual(category.l2_id, 1000)
        self.assertEqual(category.l3_id, 22193)

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

    def test_login_requires_2fa(self):
        response = {
            "user_id": "123-456-7890",
            "second_factor_authentication_required": True,
            "show_second_factor_authentication_intro": False,
            "error": {},
        }
        self.session_mock().post.return_value = self.MockResponse(response, 200)

        client = PicnicAPI()
        with self.assertRaises(Picnic2FARequired) as ctx:
            client.login("test-user", "test-password")
        self.assertEqual(
            str(ctx.exception), "Two-factor authentication required"
        )
        self.assertEqual(ctx.exception.response, response)

    def test_generate_2fa_code(self):
        self.session_mock().post.return_value = self.MockResponse(
            None, 204, content=b""
        )

        result = self.client.generate_2fa_code()
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/user/2fa/generate",
            json={"channel": "SMS"},
            headers=PICNIC_HEADERS,
        )
        self.assertIsNone(result)

    def test_generate_2fa_code_email(self):
        self.session_mock().post.return_value = self.MockResponse(
            None, 204, content=b""
        )

        self.client.generate_2fa_code(channel="EMAIL")
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/user/2fa/generate",
            json={"channel": "EMAIL"},
            headers=PICNIC_HEADERS,
        )

    def test_verify_2fa_code_success(self):
        self.session_mock().post.return_value = self.MockResponse(
            None, 204, content=b""
        )

        result = self.client.verify_2fa_code("123456")
        self.session_mock().post.assert_called_with(
            self.expected_base_url + "/user/2fa/verify",
            json={"otp": "123456"},
            headers=PICNIC_HEADERS,
        )
        self.assertIsNone(result)

    def test_verify_2fa_code_invalid(self):
        response = {
            "error": {
                "code": "OTP_NOT_VALID",
                "message": "Otp is not valid",
                "details": {},
            }
        }
        self.session_mock().post.return_value = self.MockResponse(response, 200)

        with self.assertRaises(Picnic2FAError) as ctx:
            self.client.verify_2fa_code("000000")
        self.assertEqual(str(ctx.exception), "Otp is not valid")
        self.assertEqual(ctx.exception.code, "OTP_NOT_VALID")

    def test_2fa_auth_error(self):
        response = {
            "error": {
                "code": "AUTH_ERROR",
                "message": "Authentication failed.",
            }
        }
        self.session_mock().post.return_value = self.MockResponse(response, 400)

        with self.assertRaises(PicnicAuthError):
            self.client.verify_2fa_code("123456")
