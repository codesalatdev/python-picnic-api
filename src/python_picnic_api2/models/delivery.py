"""Delivery models, parsed from the ``/deliveries/*`` and ``/cart/delivery_slots``
domain-JSON endpoints.
"""

from .base import PicnicModel
from .common import Eta, Order, SelectedSlot, Slot


class DeliverySlots(PicnicModel):
    """The available delivery slots, returned by ``get_delivery_slots``."""

    delivery_slots: list[Slot] = []
    selected_slot: SelectedSlot | None = None


class Delivery(PicnicModel):
    """A single delivery in full detail, returned by ``get_delivery``.

    Contains the full order tree (orders -> lines -> articles), the slot and,
    once en route, an ETA.
    """

    type: str | None = None
    delivery_id: str | None = None
    creation_time: str | None = None
    slot: Slot | None = None
    eta2: Eta | None = None
    status: str | None = None
    orders: list[Order] = []
    returned_containers: list = []
    parcels: list = []
    id: str | None = None


class DeliverySummary(PicnicModel):
    """A lightweight delivery from ``/deliveries/summary``.

    Same shape as :class:`Delivery` but the orders are summaries (totals + status,
    no line items). Returned by ``get_deliveries`` / ``get_current_deliveries``.
    """

    delivery_id: str | None = None
    creation_time: str | None = None
    slot: Slot | None = None
    eta2: Eta | None = None
    status: str | None = None
    orders: list[Order] = []


__all__ = ["DeliverySlots", "Delivery", "DeliverySummary"]
