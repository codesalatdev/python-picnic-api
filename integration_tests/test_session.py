import os

from dotenv import load_dotenv
from requests import Session

from python_picnic_api2.client import PicnicAPI
from python_picnic_api2.session import PicnicAPISession, PicnicAuthError

load_dotenv()

country_code = os.getenv("COUNTRY_CODE")


def test_init():
    assert issubclass(PicnicAPISession, Session)


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
