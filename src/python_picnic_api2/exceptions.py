"""Exceptions raised by the Picnic API client.

Authentication-related exceptions live in :mod:`python_picnic_api2.session` for
historical reasons and are re-exported here so that all public exceptions can be
imported from a single place.
"""

from .session import Picnic2FAError, Picnic2FARequired, PicnicAuthError


class PicnicParseError(Exception):
    """Raised when a Picnic PML ("layout") response cannot be parsed into a model.

    The Picnic ``/pages/*`` endpoints return a UI layout tree of widgets that
    varies by country and A/B test. When an expected node or field is missing
    this is raised instead of a bare ``KeyError`` so callers get a clear,
    actionable message about what was being looked for.
    """

    def __init__(self, message: str, *, endpoint: str | None = None):
        if endpoint:
            message = f"{message} (endpoint: {endpoint})"
        super().__init__(message)
        self.endpoint = endpoint


__all__ = [
    "PicnicParseError",
    "PicnicAuthError",
    "Picnic2FARequired",
    "Picnic2FAError",
]
