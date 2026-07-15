"""Building blocks shared by the cart and delivery domain-JSON models.

These endpoints (unlike the PML ``/pages/*`` ones) return clean, nested domain
JSON, so the models are plain pydantic with no tree traversal. Prices are integer
cents, timestamps are kept as the raw ISO-8601 strings (e.g.
``"2026-07-15T14:15:00.000+02:00"``) to stay byte-faithful to the payload.
"""

from .base import PicnicModel


class Decorator(PicnicModel):
    """A UI/pricing decorator attached to an order article (e.g. ``QUANTITY``).

    ``type`` is the only key present on every variant; the extras below cover the
    common kinds (``QUANTITY`` -> ``quantity``, ``UNIT_QUANTITY`` ->
    ``unit_quantity_text``, ``PRODUCT_SIZE`` -> ``text``). Anything else is kept
    via ``extra="ignore"`` + the parent model's :attr:`raw`.
    """

    type: str | None = None
    quantity: int | None = None
    unit_quantity_text: str | None = None
    text: str | None = None


class Slot(PicnicModel):
    """A delivery slot, as embedded in the cart, delivery-slot list and deliveries."""

    slot_id: str | None = None
    hub_id: str | None = None
    fc_id: str | None = None
    window_start: str | None = None
    window_end: str | None = None
    cut_off_time: str | None = None
    is_available: bool | None = None
    selected: bool | None = None
    reserved: bool | None = None
    minimum_order_value: int | None = None
    unavailability_reason: str | None = None
    slot_characteristics: list = []


class SelectedSlot(PicnicModel):
    """The currently selected slot reference (``slot_id`` + ``state``)."""

    slot_id: str | None = None
    state: str | None = None


class Eta(PicnicModel):
    """An estimated-arrival window (``start``/``end`` ISO timestamps)."""

    start: str | None = None
    end: str | None = None


class TransactionInfo(PicnicModel):
    """Payment info attached to an order."""

    bank_id: str | None = None
    payment_type: str | None = None
    redacted_iban: str | None = None
    refund_account: bool | None = None


class OrderArticle(PicnicModel):
    """A single article (product) inside an order line."""

    type: str | None = None
    id: str | None = None
    name: str | None = None
    image_ids: list[str] = []
    unit_quantity: str | None = None
    price: int | None = None
    max_count: int | None = None
    perishable: bool | None = None
    decorators: list[Decorator] = []


class OrderLine(PicnicModel):
    """An order line: one or more identical articles with a line price."""

    type: str | None = None
    id: str | None = None
    items: list[OrderArticle] = []
    display_price: int | None = None
    price: int | None = None


class Order(PicnicModel):
    """An order.

    A single model covers both the rich delivery-detail order (with line items and
    payment info) and the lean order summary returned by ``/deliveries/summary``
    (just totals + status); every field is optional so the missing ones simply
    stay ``None``.
    """

    type: str | None = None
    id: str | None = None
    items: list[OrderLine] = []
    total_price: int | None = None
    checkout_total_price: int | None = None
    total_savings: int | None = None
    total_deposit: int | None = None
    cancellable: bool | None = None
    cancellation_time: str | None = None
    transaction_info: TransactionInfo | None = None
    creation_time: str | None = None
    status: str | None = None
    deposit_breakdown: list = []
    membership_savings: int | None = None


__all__ = [
    "Decorator",
    "Slot",
    "SelectedSlot",
    "Eta",
    "TransactionInfo",
    "OrderArticle",
    "OrderLine",
    "Order",
]
