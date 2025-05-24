import re
from hashlib import md5
from urllib.parse import quote

import typing_extensions

from .helper import (
    _extract_search_results,
    _tree_generator,
    _url_generator,
)
from .session import PicnicAPISession, PicnicAuthError

DEFAULT_URL = "https://storefront-prod.{}.picnicinternational.com/api/{}"
GLOBAL_GATEWAY_URL = "https://gateway-prod.global.picnicinternational.com"
DEFAULT_COUNTRY_CODE = "NL"
DEFAULT_API_VERSION = "15"
_HEADERS = {
    "x-picnic-agent": "30100;1.15.272-15295;",
    "x-picnic-did": "3C417201548B2E3B",
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

        self.high_level_categories = None

    def initialize_high_level_categories(self):
        """Initialize high-level categories once to avoid multiple requests."""
        if not self.high_level_categories:
            self.high_level_categories = self.get_categories(depth=1)

    def _get(self, path: str, add_picnic_headers=False):
        url = self._base_url + path

        # Make the request, add special picnic headers if needed
        headers = _HEADERS if add_picnic_headers else None
        response = self.session.get(url, headers=headers).json()

        if self._contains_auth_error(response):
            raise PicnicAuthError("Picnic authentication error")

        return response

    def _post(self, path: str, data=None, base_url_override=None):
        url = (base_url_override if base_url_override else self._base_url) + path
        response = self.session.post(url, json=data).json()

        if self._contains_auth_error(response):
            raise PicnicAuthError(
                f"Picnic authentication error: \
                    {response['error'].get('message')}"
            )

        return response

    @staticmethod
    def _contains_auth_error(response):
        if not isinstance(response, dict):
            return False

        error_code = response.setdefault("error", {}).get("code")
        return error_code == "AUTH_ERROR" or error_code == "AUTH_INVALID_CRED"

    def login(self, username: str, password: str):
        path = "/user/login"
        secret = md5(password.encode("utf-8")).hexdigest()
        data = {"key": username, "secret": secret, "client_id": 30100}

        return self._post(path, data)

    def logged_in(self):
        return self.session.authenticated

    def get_user(self):
        return self._get("/user")

    def search(self, term: str):
        path = f"/pages/search-page-results?search_term={quote(term)}"
        raw_results = self._get(path, add_picnic_headers=True)
        return _extract_search_results(raw_results)

    def get_cart(self):
        return self._get("/cart")

    def get_article(self, article_id: str, add_category_name=False):
        if add_category_name:
            raise NotImplementedError()
        path = f"/pages/product-details-page-root?id={article_id}"
        data = self._get(path, add_picnic_headers=True)
        article_details = []
        for block in data["body"]["child"]["child"]["children"]:
            if block["id"] == "product-details-page-root-main-container":
                article_details = block["pml"]["component"]["children"]

        if len(article_details) == 0:
            return None

        color_regex = re.compile(r"#\(#\d{6}\)")
        producer = re.sub(color_regex, "", str(article_details[1].get("markdown", "")))
        article_name = re.sub(color_regex, "", str(article_details[0]["markdown"]))

        article = {"name": f"{producer} {article_name}", "id": article_id}

        return article

    def get_article_category(self, article_id: str):
        path = "/articles/" + article_id + "/category"
        return self._get(path)

    def add_product(self, product_id: str, count: int = 1):
        data = {"product_id": product_id, "count": count}
        return self._post("/cart/add_product", data)

    def remove_product(self, product_id: str, count: int = 1):
        data = {"product_id": product_id, "count": count}
        return self._post("/cart/remove_product", data)

    def clear_cart(self):
        return self._post("/cart/clear")

    def get_delivery_slots(self):
        return self._get("/cart/delivery_slots")

    def get_delivery(self, delivery_id: str):
        path = "/deliveries/" + delivery_id
        return self._get(path)

    def get_delivery_scenario(self, delivery_id: str):
        path = "/deliveries/" + delivery_id + "/scenario"
        return self._get(path, add_picnic_headers=True)

    def get_delivery_position(self, delivery_id: str):
        path = "/deliveries/" + delivery_id + "/position"
        return self._get(path, add_picnic_headers=True)

    @typing_extensions.deprecated(
        """The option to show unsummarized deliveries was removed by picnic.
        The optional parameter 'summary' will be removed in the future and default
        to True.
        You can ignore this warning if you do not pass the 'summary' argument to
        this function."""
    )
    def get_deliveries(self, summary: bool = True, data: list = None):
        data = [] if data is None else data
        if not summary:
            raise NotImplementedError()
        return self._post("/deliveries/summary", data=data)

    def get_current_deliveries(self):
        return self.get_deliveries(data=["CURRENT"])

    def get_categories(self, depth: int = 0):
        return self._get(f"/my_store?depth={depth}")["catalog"]

    def print_categories(self, depth: int = 0):
        tree = "\n".join(_tree_generator(self.get_categories(depth=depth)))
        print(tree)

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
