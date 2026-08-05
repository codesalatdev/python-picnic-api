from hashlib import md5
from urllib.parse import quote

import typing_extensions

from .exceptions import PicnicParseError
from .helper import _url_generator
from .models import (
    Article,
    Cart,
    Category,
    Delivery,
    DeliverySlots,
    DeliverySummary,
    SearchResult,
    User,
    pml,
)
from .session import (
    Picnic2FAError,
    Picnic2FARequired,
    PicnicAPISession,
    PicnicAuthError,
)

DEFAULT_URL = "https://storefront-prod.{}.picnicinternational.com/api/{}"
DEFAULT_COUNTRY_CODE = "NL"
DEFAULT_API_VERSION = "15"
_HEADERS = {
    "x-picnic-agent": "30100;1.206.1-#15408",
    "x-picnic-did": "598F770380CA54B6",
}


class PicnicAPI:
    def __init__(
        self,
        username: str = None,
        password: str = None,
        country_code: str = DEFAULT_COUNTRY_CODE,
        auth_token: str = None,
    ):
        self._country_code = country_code
        self._base_url = _url_generator(
            DEFAULT_URL, self._country_code, DEFAULT_API_VERSION
        )

        self.session = PicnicAPISession(auth_token=auth_token)

        # Login if not authenticated
        if not self.session.authenticated and username and password:
            self.login(username, password)

    def _get(self, path: str, add_picnic_headers=False):
        url = self._base_url + path

        # Make the request, add special picnic headers if needed
        headers = _HEADERS if add_picnic_headers else None
        response = self.session.get(url, headers=headers).json()

        if self._contains_auth_error(response):
            raise PicnicAuthError("Picnic authentication error")

        return response

    def _post(
        self, path: str, data=None, base_url_override=None, add_picnic_headers=False
    ):
        url = (base_url_override if base_url_override else self._base_url) + path
        kwargs = {"json": data}
        if add_picnic_headers:
            kwargs["headers"] = _HEADERS
        response = self.session.post(url, **kwargs).json()

        if self._contains_auth_error(response):
            raise PicnicAuthError(
                f"Picnic authentication error: {response['error'].get('message')}"
            )

        return response

    @staticmethod
    def _contains_auth_error(response):
        if not isinstance(response, dict):
            return False

        error_code = response.get("error", {}).get("code")
        return error_code == "AUTH_ERROR" or error_code == "AUTH_INVALID_CRED"

    @staticmethod
    def _requires_2fa(response):
        if not isinstance(response, dict):
            return False

        return "second_factor_authentication_required" in response \
        and response["second_factor_authentication_required"] is True

    def login(self, username: str, password: str):
        path = "/user/login"
        secret = md5(password.encode("utf-8")).hexdigest()
        data = {"key": username, "secret": secret, "client_id": 30100}

        response = self._post(path, data, add_picnic_headers=True)

        if self._requires_2fa(response):
            raise Picnic2FARequired(
                message=response.get("error", {}).get(
                    "message", "Two-factor authentication required"
                ),
                response=response,
            )

        return response

    def _post_2fa(self, path: str, data=None):
        """POST for 2FA endpoints that may return empty (204) or JSON error bodies."""
        url = self._base_url + path
        response = self.session.post(url, json=data, headers=_HEADERS)

        if response.status_code == 204 or not response.content:
            return None

        json_body = response.json()

        # This should not happen because password auth is already done
        # at this point, but just in case.
        if self._contains_auth_error(json_body):
            raise PicnicAuthError(
                f"Picnic authentication error: {json_body['error'].get('message')}"
            )

        error = json_body.get("error", {})
        if error.get("code"):
            raise Picnic2FAError(
                message=error.get("message", "Two-factor authentication failed"),
                code=error["code"],
            )

        return json_body

    def generate_2fa_code(self, channel: str = "SMS"):
        """Request a 2FA code to be sent via the specified channel.

        Args:
            channel: The delivery channel ("SMS" or "EMAIL").

        Raises:
            Picnic2FAError: If the server returns an error (e.g. invalid channel).
        """
        path = "/user/2fa/generate"
        data = {"channel": channel}
        self._post_2fa(path, data)

    def verify_2fa_code(self, code: str):
        """Verify the 2FA code to complete authentication.

        Args:
            code: The OTP code received via SMS or email.

        Raises:
            Picnic2FAError: If the OTP code is invalid.
        """
        path = "/user/2fa/verify"
        data = {"otp": code}
        self._post_2fa(path, data)

    def logged_in(self):
        return self.session.authenticated

    def get_user(self) -> User:
        return User.from_api(self._get("/user"))

    def search(self, term: str) -> SearchResult:
        path = f"/pages/search-page-results?search_term={quote(term)}"
        raw_results = self._get(path, add_picnic_headers=True)
        return SearchResult.from_page(raw_results)

    def get_cart(self) -> Cart:
        return Cart.from_api(self._get("/cart", add_picnic_headers=True))

    def get_article(self, article_id: str, add_category=False) -> Article | None:
        path = f"/pages/product-details-page-root?id={article_id}" + \
            "&show_category_action=true"
        data = self._get(path, add_picnic_headers=True)

        article = Article.from_page(data, article_id)
        if article is None:
            return None

        if add_category:
            cat_ids = Article.category_ids_from_page(data)
            if cat_ids is None:
                raise PicnicParseError(
                    f"Could not extract category from article with id {article_id}",
                    endpoint="product-details-page-root",
                )
            _, l2_id, l3_id = cat_ids
            article.category = self.get_category_by_ids(l2_id, l3_id)

        return article

    def get_article_category(self, article_id: str):
        """Return the raw category payload for an article.

        Not modelled: this endpoint appears to have been removed by Picnic (it
        returns an error object, like ``get_categories``). Kept for backwards
        compatibility; returns the raw dict. Use ``get_article(id,
        add_category=True)`` to resolve an article's category instead.
        """
        path = "/articles/" + article_id + "/category"
        return self._get(path)

    def add_product(self, product_id: str, count: int = 1) -> Cart:
        data = {"product_id": product_id, "count": count}
        return Cart.from_api(self._post("/cart/add_product", data,
                                        add_picnic_headers=True))

    def remove_product(self, product_id: str, count: int = 1) -> Cart:
        data = {"product_id": product_id, "count": count}
        return Cart.from_api(self._post("/cart/remove_product", data,
                                        add_picnic_headers=True))

    def clear_cart(self) -> Cart:
        return Cart.from_api(self._post("/cart/clear", add_picnic_headers=True))

    def get_delivery_slots(self) -> DeliverySlots:
        return DeliverySlots.from_api(self._get("/cart/delivery_slots"))

    def get_delivery(self, delivery_id: str) -> Delivery:
        path = "/deliveries/" + delivery_id
        return Delivery.from_api(self._get(path))

    def get_delivery_scenario(self, delivery_id: str):
        """Return the raw driving-scenario payload for a delivery.

        Not modelled: it is only populated while a delivery is en route, so
        there is no stable sample to build a model against. Returns the raw dict.
        """
        path = "/deliveries/" + delivery_id + "/scenario"
        return self._get(path, add_picnic_headers=True)

    def get_delivery_position(self, delivery_id: str):
        """Return the raw driver-position payload for a delivery.

        Not modelled: only populated while a delivery is en route (otherwise
        empty). Returns the raw dict.
        """
        path = "/deliveries/" + delivery_id + "/position"
        return self._get(path, add_picnic_headers=True)

    @typing_extensions.deprecated(
        """The option to show unsummarized deliveries was removed by picnic.
        The optional parameter 'summary' will be removed in the future and default
        to True.
        You can ignore this warning if you do not pass the 'summary' argument to
        this function."""
    )
    def get_deliveries(
        self, summary: bool = True, data: list = None
    ) -> list[DeliverySummary]:
        data = [] if data is None else data
        if not summary:
            raise NotImplementedError()
        raw = self._post("/deliveries/summary", data=data)
        return [DeliverySummary.from_api(item) for item in raw]

    def get_current_deliveries(self) -> list[DeliverySummary]:
        return self.get_deliveries(data=["CURRENT"])

    def get_categories(self, depth: int = 0):
        raise NotImplementedError("This endpoint has been removed by picnic\
        and is no longer functional.")

    def get_category_by_ids(self, l2_id: int, l3_id: int) -> Category:
        path = "/pages/L2-category-page-root" + \
            f"?category_id={l2_id}&l3_category_id={l3_id}"
        data = self._get(path, add_picnic_headers=True)
        node = pml.find(
            data, id=f"vertical-article-tiles-sub-header-{l3_id}")
        if node is None:
            raise PicnicParseError(
                "Could not find category with specified IDs",
                endpoint="L2-category-page-root",
            )
        return Category(
            l2_id=l2_id, l3_id=l3_id,
            name=pml.accessibility_label(node), raw=data)

    def get_article_by_gtin(self, etan: str, maxRedirects: int = 5):
        # Finds the article ID for a gtin/ean (barcode).

        url = "https://picnic.app/" + self._country_code.lower() + "/qr/gtin/" + etan
        while maxRedirects > 0:
            if url == "http://picnic.app/nl/link/store/storefront":
                # gtin unknown
                return None
            r = self.session.get(url, headers=_HEADERS, allow_redirects=False)
            maxRedirects -= 1
            if ";id=" in r.url:
                # found the article id
                return self.get_article(r.url.split(";id=", 1)[1])
            if "Location" not in r.headers:
                # article id not found but also no futher redirect
                return None
            url = r.headers["Location"]
        return None


__all__ = ["PicnicAPI"]
