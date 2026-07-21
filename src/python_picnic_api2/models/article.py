"""Article model, parsed from the ``product-details-page-root`` PML page."""

from .base import PicnicModel
from .category import Category
from .pml import find, find_all, on_press_target, strip_colors, text_of, walk

# The container holding the article's title/producer/quantity text nodes.
_MAIN_CONTAINER_ID = "product-details-page-root-main-container"
_CATEGORY_BUTTON_ID = "category-button"
# Containers common to every product-details page (present across countries and
# product types); each holds one section of the page.
_DESCRIPTION_ID = "product-page-description"
_HIGHLIGHTS_ID = "product-page-highlights"
# Bundle/multipack pages carry one "product-page-bundle-item-<id>" container per
# pack size; ordinary product pages carry none.
_BUNDLE_ITEM_PREFIX = "product-page-bundle-item-"
# Leading characters that mark a price-per-unit line (e.g. "€1.15/L").
_CURRENCY = "€$£"


def _bundle_variant_ids(data, article_id: str) -> list[str]:
    """Return the *other* pack-size article ids on a bundle page, in order.

    Bundle/multipack pages list several pack sizes, each in a
    ``product-page-bundle-item-<id>`` container. Returns the sibling ids (all but
    the requested article); an empty list means this is not a bundle page.
    """
    ids: list[str] = []
    for node in find_all(data, id_prefix=_BUNDLE_ITEM_PREFIX):
        variant_id = node["id"][len(_BUNDLE_ITEM_PREFIX):]
        if variant_id and variant_id != article_id and variant_id not in ids:
            ids.append(variant_id)
    return ids


def _all_texts(container) -> list[str]:
    """Return every non-empty (color-stripped) text in ``container``, in order."""
    texts: list[str] = []
    for node in walk(container):
        text = text_of(node)
        if text and text.strip():
            texts.append(text.strip())
    return texts


def _raw_text(node) -> str | None:
    """Return a node's raw (un-stripped) markdown/text, if it has any."""
    for key in ("markdown", "text"):
        value = node.get(key)
        if isinstance(value, str):
            return value
    return None


def _price_cents(value) -> int | None:
    """Return an integer-cents price from a node's ``price`` value, or ``None``.

    DE returns prices as ``int`` (``95``) but NL returns ``float`` (``1035.0``);
    both must parse. ``bool`` is rejected (it is an ``int`` subclass).
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return round(value)


def _scan_prices(scope) -> tuple[int | None, int | None]:
    """Return ``(price, original_price)`` from the ``PRICE`` nodes in ``scope``.

    ``price`` is the first non-crossed price; ``original_price`` is a
    struck-through (``isCrossed``) price, trusted only while still within the
    product's own price block (before a second, non-crossed price appears — later
    prices belong to recommendation tiles).
    """
    price: int | None = None
    original_price: int | None = None
    non_crossed_seen = 0
    for node in walk(scope):
        if node.get("type") != "PRICE":
            continue
        value = _price_cents(node.get("price"))
        if value is None:
            continue
        if node.get("isCrossed"):
            if original_price is None and non_crossed_seen <= 1:
                original_price = value
        else:
            non_crossed_seen += 1
            if price is None:
                price = value
    return price, original_price


def _find_prices(data, article_id: str) -> tuple[int | None, int | None]:
    """Return ``(price, original_price)`` in integer cents for ``article_id``.

    Bundle / multipack pages list several pack sizes, each in its own
    ``product-page-bundle-item-<id>`` container with its own price, and the main
    container carries no price at all. The price for *this* article must come from
    its matching bundle-item container — taking the first ``PRICE`` on the page
    would return a different pack size's price. For ordinary pages there is no such
    container and the product's price nodes are simply the first on the page.
    Falls back to any node carrying a numeric ``price`` so a layout variant never
    leaves the price unset.
    """
    bundle_item = find(data, id=f"product-page-bundle-item-{article_id}")
    if bundle_item is not None:
        price, original_price = _scan_prices(bundle_item)
        if price is not None:
            return price, original_price

    price, original_price = _scan_prices(data)
    if price is None:
        for node in walk(data):
            value = _price_cents(node.get("price"))
            if value is not None and not node.get("isCrossed"):
                price = value
                break
    return price, original_price


def _parse_main_texts(
    container,
) -> tuple[str | None, str | None, str | None, str | None]:
    """Classify the main container's texts into (product_name, producer,
    unit_quantity, price_per_unit) by *role*, not position.

    The title is the ``HEADER1`` node; the unit quantity is a colour-coded line
    starting with a digit (``"1L"``, ``"5 Stück"``); the price-per-unit starts
    with a currency symbol (``"€1.15/L"``); the producer/brand is a plain text
    line. A positional read broke on brand-less products (produce) and trailing
    badges like ``"Tiefkühl"``.
    """
    title = producer = unit_quantity = price_per_unit = None
    fallback_title = None
    for node in walk(container):
        raw = _raw_text(node)
        if raw is None:
            continue
        text = strip_colors(raw).strip()
        if not text:
            continue
        if fallback_title is None:
            fallback_title = text
        if node.get("textType") == "HEADER1" and title is None:
            title = text
            continue
        colour_coded = "#(" in raw
        first = text[0]
        if first in _CURRENCY:
            if price_per_unit is None:
                price_per_unit = text
        elif colour_coded and first.isdigit():
            if unit_quantity is None:
                unit_quantity = text
        elif not colour_coded and producer is None:
            producer = text
    return (title or fallback_title), producer, unit_quantity, price_per_unit


class Article(PicnicModel):
    """A Picnic article (product)."""

    id: str
    #: The composed display name, ``"<producer> <product_name>"``.
    name: str | None = None
    #: The product title on its own, e.g. ``"H-Milch 3,5%"``.
    product_name: str | None = None
    #: The brand / producer, e.g. ``"Gut&Günstig"``. ``None`` for unbranded
    #: products such as fresh produce.
    producer: str | None = None
    #: The pack size, e.g. ``"1L"`` / ``"5 Stück"``.
    unit_quantity: str | None = None
    #: The comparative price, e.g. ``"€1.15/L"``.
    price_per_unit: str | None = None
    #: The current price in integer cents, e.g. ``95``. NB: for bundles/multipacks
    #: (:attr:`is_bundle`) Picnic exposes only a *per-unit* price here — the full
    #: amount charged for the pack is not in the page payload and only appears once
    #: the item is added to the cart.
    price: int | None = None
    #: The pre-sale price in integer cents when on sale, else ``None``.
    original_price: int | None = None
    #: Other pack-size article ids when this is a bundle/multipack, else ``[]``.
    bundle_variant_ids: list[str] = []

    @property
    def is_bundle(self) -> bool:
        """Whether this product is a bundle/multipack with other pack sizes."""
        return bool(self.bundle_variant_ids)
    #: The hero product image id (usable with Picnic's image CDN).
    image_id: str | None = None
    #: The product description (markdown, may include ``**bold**`` and newlines).
    description: str | None = None
    #: Short feature bullets shown on the page, e.g. ``["Lange **haltbar**", ...]``.
    highlights: list[str] = []
    category: Category | None = None

    @classmethod
    def from_page(cls, data: dict, article_id: str) -> "Article | None":
        """Build an :class:`Article` from a ``product-details-page-root`` payload.

        The page is a layout tree. The article's title, brand, unit quantity and
        price-per-unit are read from the main container by *role* (see
        :func:`_parse_main_texts`), the ``price`` from the first price node (see
        :func:`_find_price`) and the hero ``image_id`` from the page's first
        image-gallery node. Returns ``None`` when the page has no recognizable
        article container (e.g. an unsupported / experimental layout variant).
        """
        container = find(data, id=_MAIN_CONTAINER_ID)
        if container is None:
            return None

        product_name, producer, unit_quantity, price_per_unit = \
            _parse_main_texts(container)
        if not product_name:
            return None

        price, original_price = _find_prices(data, article_id)
        bundle_variant_ids = _bundle_variant_ids(data, article_id)

        # The first image-gallery node on the page is the hero product image.
        gallery = find(data, type="image_gallery")
        image_id = gallery.get("image_id") if gallery else None

        # Description is a single markdown block; highlights are short bullets.
        description_container = find(data, id=_DESCRIPTION_ID)
        description_texts = _all_texts(description_container) \
            if description_container else []
        description = description_texts[0] if description_texts else None

        highlights_container = find(data, id=_HIGHLIGHTS_ID)
        highlights = _all_texts(highlights_container) if highlights_container else []

        # Historical behaviour composes "<producer> <product_name>" as the name.
        display_name = " ".join(part for part in (producer, product_name) if part)

        return cls(
            id=article_id,
            name=display_name or None,
            product_name=product_name,
            producer=producer,
            unit_quantity=unit_quantity,
            price_per_unit=price_per_unit,
            price=price,
            original_price=original_price,
            bundle_variant_ids=bundle_variant_ids,
            image_id=image_id,
            description=description,
            highlights=highlights,
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
