"""Category model, parsed from the L2 category page and article deep-links."""

import re

from .base import PicnicModel

# Deep-link on a product's category button, e.g.
# ``app.picnic://categories/1000/l2/2000/l3/3000``.
_CATEGORY_DEEPLINK = re.compile(
    r"app\.picnic://categories/(\d+)/l2/(\d+)/l3/(\d+)"
)


class Category(PicnicModel):
    """A Picnic category identified by its L2/L3 ids."""

    l2_id: int | None = None
    l3_id: int | None = None
    name: str | None = None

    @classmethod
    def parse_deeplink(cls, target: str) -> tuple[int, int, int] | None:
        """Extract ``(l1_id, l2_id, l3_id)`` from a category deep-link target."""
        match = _CATEGORY_DEEPLINK.match(target or "")
        if not match:
            return None
        return tuple(int(group) for group in match.groups())  # type: ignore[return-value]


__all__ = ["Category"]
