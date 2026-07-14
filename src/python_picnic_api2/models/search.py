"""Search-result models, parsed from the ``search-page-results`` PML page."""

import json
import re

from .base import PicnicModel
from .pml import find_all

# ``sole_article_id`` is buried as a serialized string somewhere inside a tile.
_SOLE_ARTICLE_ID_PATTERN = re.compile(r'"sole_article_id":"(\w+)"')


class SearchResultItem(PicnicModel):
    """A single product tile in a search result."""

    id: str
    name: str | None = None
    display_price: int | None = None
    price: int | None = None
    image_id: str | None = None
    unit_quantity: str | None = None
    unit_quantity_sub: str | None = None
    max_count: int | None = None
    price_ranges: list | None = None
    sole_article_id: str | None = None
    decorators: list = []


class SearchResult(PicnicModel):
    """A search response: a collection of product tiles."""

    items: list[SearchResultItem] = []

    @classmethod
    def from_page(cls, data: dict) -> "SearchResult":
        """Build a :class:`SearchResult` from a ``search-page-results`` payload.

        Finds ``SELLING_UNIT_TILE`` nodes anywhere in the tree, merges each
        node's ``sellingUnit`` payload with its ``sole_article_id``.
        """
        body = data.get("body", {}) if isinstance(data, dict) else {}
        nodes = find_all(
            body.get("child", {}),
            match={"type": "SELLING_UNIT_TILE", "sellingUnit": {}},
        )

        items: list[SearchResultItem] = []
        for node in nodes:
            fields = dict(node.get("sellingUnit", {}))
            sole_ids = _SOLE_ARTICLE_ID_PATTERN.findall(json.dumps(node))
            if sole_ids:
                fields["sole_article_id"] = sole_ids[0]
            item = SearchResultItem.model_validate(fields)
            item.raw = node
            items.append(item)

        return cls(items=items, raw=data)


__all__ = ["SearchResult", "SearchResultItem"]
