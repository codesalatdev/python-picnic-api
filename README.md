# Python-Picnic-API

**This library is undergoing rapid changes as is the Picnic API itself. It is mainly intended for use within Home Assistant, but there are integration tests running regularly checking for failures in features not used by the Home Assistant integration.**

**If you want to know why interacting with Picnic is getting harder than ever, check out their blogpost about architectural changes: [https://blog.picnic.nl/adding-write-functionality-to-pages-with-self-service-apis-d09aa7dbc9c0](https://jobs.picnic.app/en/blogs/adding-write-functionality-to-pages-with-self-service-apis)**

Fork of the Unofficial Python wrapper for the [Picnic](https://picnic.app) API. While not all API methods have been implemented yet, you'll find most of what you need to build a working application are available. 

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

## Typed models (2.0)

As of 2.0 the "page" endpoints that Picnic now serves as a layout tree of widgets
(`search`, `get_article`, `get_category_by_ids`) return typed [pydantic](https://docs.pydantic.dev)
models instead of raw dicts. Every model exposes `.raw` with the original,
untouched payload as an escape hatch for data that isn't modelled yet, and
`.model_dump()` for a plain-dict view. See the [migration notes](#migrating-from-1x-to-20).

## Searching for an article

```python
result = picnic.search('coffee')          # -> SearchResult
result.items[0].name                        # 'Lavazza Caffè Crema e Aroma Bohnen'
result.items[0].display_price               # 1799
result.items[0].raw                         # original tile payload
```

## Get article by ID

```python
article = picnic.get_article("s1019822")   # -> Article | None
article.id                                  # 's1019822'
article.name                                # 'Lavazza Caffè Crema e Aroma Bohnen'

# Optionally resolve the article's category (an extra request):
article = picnic.get_article("s1019822", add_category=True)
article.category.name                       # 'Koffiebonen'
```

## Get article by GTIN (EAN)
```python
article = picnic.get_article_by_gtin("8000070025400")  # -> Article | None
article.name                                # 'Lavazza Caffè Crema e Aroma Bohnen'
```

## Migrating from 1.x to 2.0

- `search()` now returns a `SearchResult` (`.items` is a list of `SearchResultItem`)
  instead of `[{"items": [...]}]`.
- `get_article()` / `get_article_by_gtin()` now return an `Article` (or `None`)
  instead of a `dict`; use `.id` / `.name` / `.category` instead of key access.
- `get_category_by_ids()` now returns a `Category` instead of a `dict`.
- Missing/unexpected PML nodes now raise `PicnicParseError` (from
  `python_picnic_api2`) instead of a bare `KeyError`.
- All other methods (`get_cart`, `get_deliveries`, `get_user`, …) still return
  raw dicts for now; models for those will land in a follow-up release.
- Any field you need that isn't modelled yet is available on `model.raw`.

## Check cart

```python
picnic.get_cart()
```

```python
{'type': 'ORDER', 'id': 'shopping_cart', 'items': [{'type': 'ORDER_LINE', 'id': '1470', 'items': [{'type': 'ORDER_ARTICLE', 'id': 's1019822', 'name': 'Lavazza Caffè Crema e Aroma Bohnen',...
```

## Manipulating your cart
All of these methods will return the shopping cart.

```python
# Add product with ID "s1019822" 2x
picnic.add_product("s1019822", 2)

# Remove product with ID "s1019822" 1x
picnic.remove_product("s1019822")

# Clear your cart
picnic.clear_cart()
```

## See upcoming deliveries

```python
picnic.get_current_deliveries()
```

```python
[{'delivery_id': 'XXYYZZ', 'creation_time': '2025-04-28T08:08:41.666+02:00', 'slot': {'slot_id': 'XXYYZZ', 'hub_id': '...
```

## See available delivery slots

```python
picnic.get_delivery_slots()
```

```python
{'delivery_slots': [{'slot_id': 'XXYYZZ', 'hub_id': 'YYY', 'fc_id': 'FCX', 'window_start': '2025-04-29T17:15:00.000+02:00', 'window_end': '2025-04-29T19:15:00.000+02:00'...
```
