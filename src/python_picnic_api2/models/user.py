"""User model, parsed from the ``/user`` domain-JSON endpoint."""

from .base import PicnicModel


class Address(PicnicModel):
    """A delivery address."""

    id: str | None = None
    house_number: int | None = None
    house_number_ext: str | None = None
    postcode: str | None = None
    street: str | None = None
    city: str | None = None


class Subscription(PicnicModel):
    """A mailing-list / push subscription toggle."""

    list_id: str | None = None
    subscribed: bool | None = None
    name: str | None = None


class HouseholdDetails(PicnicModel):
    """Self-reported household composition."""

    adults: int | None = None
    children: int | None = None
    cats: int | None = None
    dogs: int | None = None
    author: str | None = None
    last_edit_ts: int | None = None


class User(PicnicModel):
    """The authenticated user account, returned by ``get_user``."""

    user_id: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    address: Address | None = None
    phone: str | None = None
    contact_email: str | None = None
    customer_type: str | None = None
    subscriptions: list[Subscription] = []
    push_subscriptions: list[Subscription] = []
    household_details: HouseholdDetails | None = None
    # Flat map of consent-key -> bool; not worth its own model.
    consent_decisions: dict | None = None
    check_general_consent: bool | None = None
    placed_order: bool | None = None
    received_delivery: bool | None = None
    total_deliveries: int | None = None
    completed_deliveries: int | None = None


__all__ = ["Address", "Subscription", "HouseholdDetails", "User"]
