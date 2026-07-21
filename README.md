# Python-Picnic-API

**This library is undergoing rapid changes as is the Picnic API itself. It is mainly intended for use within Home Assistant, but there are integration tests running regularly checking for failures in features not used by the Home Assistant integration.**

**If you want to know why interacting with Picnic is getting harder than ever, check out their blogpost about architectural changes: [https://blog.picnic.nl/adding-write-functionality-to-pages-with-self-service-apis-d09aa7dbc9c0](https://jobs.picnic.app/en/blogs/adding-write-functionality-to-pages-with-self-service-apis)**

Fork of the Unofficial Python wrapper for the [Picnic](https://picnic.app) API. While not all API methods have been implemented yet, you'll find most of what you need to build a working application is available.

This library is not affiliated with Picnic and retrieves data from the endpoints of the mobile application. **Use at your own risk.**

## Credits

A big thanks to @MikeBrink for building the first versions of this library.

@maartenpaul and @thijmen-j continously provided fixes that were then merged into this fork.

## Getting started

The easiest way to install is directly from pip:

```bash
$ pip install python-picnic-api2
```

Then create a new instance of `PicnicAPI` and login using your credentials:

```python
from python_picnic_api2 import PicnicAPI

picnic = PicnicAPI(username='username', password='password', country_code="NL")
```

The country_code parameter defaults to `NL`, but you have to change it if you live in a different country than the Netherlands (ISO 3166-1 Alpha-2). This obviously only works for countries that picnic services.

### Two-factor authentication (2FA)

For new logins, Picnic may require two-factor authentication. When 2FA is required, logging in raises a `Picnic2FARequired` exception. You then need to request a code and verify it:

```python
from python_picnic_api2 import PicnicAPI, Picnic2FARequired, Picnic2FAError

picnic = PicnicAPI(country_code="NL")

try:
    picnic.login(username='username', password='password')
except Picnic2FARequired:
    # Request a code via SMS or EMAIL
    picnic.generate_2fa_code(channel="SMS")

    code = input("Enter the code you received: ")
    picnic.verify_2fa_code(code)
```

After successful verification, the session is authenticated and you can use the API normally. If the code is invalid, `Picnic2FAError` is raised.

## Typed models (2.x)

As of 2.x the API returns typed [pydantic](https://docs.pydantic.dev) models
instead of raw dicts. This covers both the "page" endpoints Picnic serves as a
layout tree of widgets (`search`, `get_article`, `get_category_by_ids`) and the
domain-JSON endpoints (`get_user`, `get_cart`, `get_delivery_slots`,
`get_delivery`, `get_deliveries` / `get_current_deliveries`, and the cart-mutation
methods). Every model exposes `.raw` with the original, untouched payload as an
escape hatch for data that isn't modelled yet, and `.model_dump()` for a
plain-dict view.

A couple of endpoints still return raw dicts: `get_delivery_scenario` and
`get_delivery_position` (only populated while a delivery is en route, so there is
no stable shape to model), and `get_article_category` (appears to have been
removed by Picnic — use `get_article(id, add_category=True)` instead).

If you are upgrading from 1.x, see the [migration notes](#migrating-from-1x-to-20).

## Usage

### Searching for an article

```python
result = picnic.search('coffee')          # -> SearchResult
result.items[0].name                        # 'Lavazza Caffè Crema e Aroma Bohnen'
result.items[0].display_price               # 1799  (price shown on the tile, in cents)
result.items[0].raw                         # original tile payload
```

Search tiles only carry `display_price` (the price shown, in integer cents) — the
raw payload has no separate `price` key — so read `display_price`.

### Get article by ID

```python
article = picnic.get_article("s1019822")   # -> Article | None
article.id                                  # 's1019822'
article.name                                # 'Lavazza Caffè Crema e Aroma Bohnen'
article.product_name                        # 'Caffè Crema e Aroma Bohnen'
article.producer                            # 'Lavazza'  (None for unbranded produce)
article.unit_quantity                       # '1kg'
article.price_per_unit                      # '€17.99/kg'  (comparative price, may be None)
article.price                               # 1799  (current price, integer cents)
article.original_price                      # 2249 when on sale, else None
article.image_id                            # hero product image id
article.description                         # product description (markdown)
article.highlights                          # ['Lange **haltbar**', ...] feature bullets
article.is_bundle                           # True for multipacks with other pack sizes
article.bundle_variant_ids                  # ['s1018999', ...] other pack-size article ids

# Optionally resolve the article's category (an extra request):
article = picnic.get_article("s1019822", add_category=True)
article.category.name                       # 'Koffiebonen'
```

### Get article by GTIN (EAN)

```python
article = picnic.get_article_by_gtin("8000070025400")  # -> Article | None
article.name                                # 'Lavazza Caffè Crema e Aroma Bohnen'
```

### Get the user

```python
user = picnic.get_user()          # -> User
user.contact_email                  # 'you@example.com'
user.address.city                   # 'Amsterdam'
user.total_deliveries               # 25
```

### Check cart

```python
cart = picnic.get_cart()          # -> Cart
cart.total_count                    # 3
cart.total_price                    # 1234  (integer cents)
cart.items[0].items[0].name         # 'Lavazza Caffè Crema e Aroma Bohnen'
cart.raw                            # original cart payload
```

### Manipulating your cart

All of these methods return the updated `Cart`.

```python
# Add product with ID "s1019822" 2x
picnic.add_product("s1019822", 2)

# Remove product with ID "s1019822" 1x
picnic.remove_product("s1019822")

# Clear your cart
picnic.clear_cart()
```

### See upcoming deliveries

```python
deliveries = picnic.get_current_deliveries()   # -> list[DeliverySummary]
deliveries[0].delivery_id
deliveries[0].status                             # 'CURRENT'
deliveries[0].slot.window_start                  # '2025-04-29T17:15:00.000+02:00'

# Full detail (order lines, articles, payment info) for one delivery:
delivery = picnic.get_delivery(deliveries[0].delivery_id)   # -> Delivery
delivery.orders[0].items[0].items[0].name
```

### See available delivery slots

```python
slots = picnic.get_delivery_slots()   # -> DeliverySlots
slots.delivery_slots[0].window_start    # '2025-04-29T17:15:00.000+02:00'
slots.selected_slot.slot_id
```

## Migrating from 1.x to 2.0

- `search()` now returns a `SearchResult` (`.items` is a list of `SearchResultItem`)
  instead of `[{"items": [...]}]`.
- `get_article()` / `get_article_by_gtin()` now return an `Article` (or `None`)
  instead of a `dict`; use `.id` / `.name` / `.category` instead of key access.
- `get_category_by_ids()` now returns a `Category` instead of a `dict`.
- Missing/unexpected PML nodes now raise `PicnicParseError` (from
  `python_picnic_api2`) instead of a bare `KeyError`.
- The domain-JSON methods now return typed models instead of raw dicts:
  `get_user()` → `User`, `get_cart()` / `add_product()` / `remove_product()` /
  `clear_cart()` → `Cart`, `get_delivery_slots()` → `DeliverySlots`,
  `get_delivery()` → `Delivery`, and `get_deliveries()` /
  `get_current_deliveries()` → `list[DeliverySummary]`. Use attribute access
  (`cart.items`, `user.contact_email`) instead of `["items"]` / `["contact_email"]`.
- `get_delivery_scenario()`, `get_delivery_position()` and `get_article_category()`
  still return raw dicts (see [Typed models](#typed-models-2x)).
- Any field you need that isn't modelled yet is available on `model.raw`.
