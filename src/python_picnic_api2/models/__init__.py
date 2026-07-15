"""Typed data models for Picnic API responses."""

from .article import Article
from .base import PicnicModel
from .cart import Cart
from .category import Category
from .common import (
    Decorator,
    Eta,
    Order,
    OrderArticle,
    OrderLine,
    SelectedSlot,
    Slot,
    TransactionInfo,
)
from .delivery import Delivery, DeliverySlots, DeliverySummary
from .search import SearchResult, SearchResultItem
from .user import Address, HouseholdDetails, Subscription, User

__all__ = [
    "PicnicModel",
    "Article",
    "Category",
    "SearchResult",
    "SearchResultItem",
    # Domain-JSON models
    "User",
    "Address",
    "Subscription",
    "HouseholdDetails",
    "Cart",
    "DeliverySlots",
    "Delivery",
    "DeliverySummary",
    # Shared building blocks
    "Slot",
    "SelectedSlot",
    "Eta",
    "TransactionInfo",
    "Order",
    "OrderLine",
    "OrderArticle",
    "Decorator",
]
