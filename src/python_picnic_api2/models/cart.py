"""Cart model, parsed from the ``/cart`` domain-JSON endpoint.

The cart is itself an ``ORDER``: its :attr:`items` are order lines. It also
carries the currently offered delivery slots and the selected slot.
"""

from .base import PicnicModel
from .common import OrderLine, SelectedSlot, Slot


class Cart(PicnicModel):
    """The shopping cart returned by ``get_cart`` and the cart-mutation methods."""

    type: str | None = None
    id: str | None = None
    items: list[OrderLine] = []
    delivery_slots: list[Slot] = []
    selected_slot: SelectedSlot | None = None
    total_count: int | None = None
    total_price: int | None = None
    checkout_total_price: int | None = None
    mts: int | None = None
    deposit_breakdown: list = []
    state_token: str | None = None
    membership_savings: int | None = None


__all__ = ["Cart"]
