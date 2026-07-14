"""Article model, parsed from the ``product-details-page-root`` PML page."""

from .base import PicnicModel
from .category import Category
from .pml import find, on_press_target, text_of, walk

# The container holding the article's title/producer/quantity text nodes.
_MAIN_CONTAINER_ID = "product-details-page-root-main-container"
_CATEGORY_BUTTON_ID = "category-button"


class Article(PicnicModel):
    """A Picnic article (product)."""

    id: str
    #: The composed display name, ``"<producer> <product_name>"``.
    name: str | None = None
    #: The product title on its own, e.g. ``"H-Milch 3,5%"``.
    product_name: str | None = None
    #: The brand / producer, e.g. ``"Gut&Günstig"``.
    producer: str | None = None
    unit_quantity: str | None = None
    category: Category | None = None

    @classmethod
    def from_page(cls, data: dict, article_id: str) -> "Article | None":
        """Build an :class:`Article` from a ``product-details-page-root`` payload.

        The page is a layout tree; the article's title, brand and unit quantity
        are the first three text nodes (in document order) inside the main
        container. Returns ``None`` when the page has no recognizable article
        container (e.g. an unsupported / experimental layout variant).
        """
        container = find(data, id=_MAIN_CONTAINER_ID)
        if container is None:
            return None

        texts: list[str] = []
        for node in walk(container):
            text = text_of(node)
            if text and text.strip():
                texts.append(text.strip())
        if not texts:
            return None

        product_name = texts[0]
        producer = texts[1] if len(texts) > 1 else None
        unit_quantity = texts[2] if len(texts) > 2 else None

        # Historical behaviour composes "<producer> <product_name>" as the name.
        display_name = " ".join(part for part in (producer, product_name) if part)

        return cls(
            id=article_id,
            name=display_name or None,
            product_name=product_name,
            producer=producer,
            unit_quantity=unit_quantity,
            raw=data,
        )

    @staticmethod
    def category_ids_from_page(data: dict) -> tuple[int, int, int] | None:
        """Extract ``(l1_id, l2_id, l3_id)`` from the page's category button."""
        button = find(data, id=_CATEGORY_BUTTON_ID)
        if button is None:
            return None
        target = on_press_target(button)
        return Category.parse_deeplink(target) if target else None


__all__ = ["Article"]
