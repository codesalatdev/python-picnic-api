from requests import Response, Session


class PicnicAuthError(Exception):
    """Indicates an error when authenticating to the Picnic API."""


class Picnic2FARequired(Exception):
    """Indicates that two-factor authentication is required."""

    def __init__(
        self,
        message: str = "Two-factor authentication required",
        response: dict = None,
    ):
        super().__init__(message)
        self.response = response or {}


class Picnic2FAError(Exception):
    """Indicates an error during two-factor authentication (e.g. invalid OTP)."""

    def __init__(
        self,
        message: str = "Two-factor authentication failed",
        code: str = None,
    ):
        super().__init__(message)
        self.code = code


class PicnicAPISession(Session):
    AUTH_HEADER = "x-picnic-auth"

    def __init__(self, auth_token: str = None):
        super().__init__()
        self._auth_token = auth_token

        self.headers.update(
            {
                "User-Agent": "okhttp/4.9.0",
                "Content-Type": "application/json; charset=UTF-8",
                self.AUTH_HEADER: self._auth_token,
            }
        )

    @property
    def authenticated(self):
        """Returns whether the user is authenticated by checking if the
        authentication token is set."""
        return bool(self._auth_token)

    @property
    def auth_token(self):
        """Returns the auth token."""
        return self._auth_token

    def _update_auth_token(self, auth_token):
        """Update the auth token if not None and changed."""
        if auth_token and auth_token != self._auth_token:
            self._auth_token = auth_token
            self.headers.update({self.AUTH_HEADER: self._auth_token})

    def get(self, url, **kwargs) -> Response:
        """Do a GET request and update the auth token if set."""
        response = super().get(url, **kwargs)
        self._update_auth_token(response.headers.get(self.AUTH_HEADER))

        return response

    def post(self, url, data=None, json=None, **kwargs) -> Response:
        """Do a POST request and update the auth token if set."""
        response = super().post(url, data, json, **kwargs)
        self._update_auth_token(response.headers.get(self.AUTH_HEADER))

        return response


__all__ = ["PicnicAuthError", "Picnic2FARequired", "Picnic2FAError", "PicnicAPISession"]
