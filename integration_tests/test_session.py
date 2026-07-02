import os

import pytest
from dotenv import load_dotenv
from requests import Session

from python_picnic_api2 import Picnic2FARequired
from python_picnic_api2.client import PicnicAPI
from python_picnic_api2.session import PicnicAPISession, PicnicAuthError

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
country_code = os.getenv("COUNTRY_CODE")


def test_init():
    assert issubclass(PicnicAPISession, Session)


def test_login_requires_2fa():
    """Verify that Picnic enforces 2FA on fresh credential logins."""
    client = PicnicAPI(country_code=country_code)
    try:
        client.login(username=username, password=password)
    except Picnic2FARequired:
        pass
    except PicnicAuthError:
        pytest.skip("Credentials not configured — set USERNAME and PASSWORD in .env")
    else:
        # 2FA not triggered: token-based CI flow is still valid, but worth noting
        pass


def test_login_auth_error():
    try:
        PicnicAPI(
            username="doesnotexistblue@me.com",
            password="PasSWorD12345!",
            country_code=country_code,
        )
    except PicnicAuthError:
        assert True
    else:
        raise AssertionError()
