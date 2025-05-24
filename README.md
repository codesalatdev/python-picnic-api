# Python-Picnic-API

**This library is undergoing rapid changes as is the Picnic API itself. It is mainly intended for use within Home Assistant, but there are integration tests running regularly checking for failures in features not used bu the Home Assistant integration**

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

## Searching for an article

```python
picnic.search('coffee')
```

```python
[{'items': [{'id': 's1019822', 'name': 'Lavazza Caffè Crema e Aroma Bohnen', 'decorators': [], 'display_price': 1799, 'image_id': 'aecbf7d3b018025ec78daf5a1099b6842a860a2e3faeceec777c13d708ce442c', 'max_count': 99, 'unit_quantity': '1kg', 'sole_article_id': None}, ... ]}]
```

## Get article by ID

```python
picnic.get_article("s1019822")
```
```python
{'name': 'Lavazza Caffè Crema e Aroma Bohnen', 'id': 's1019822'}
```

## Get article by GTIN (EAN)
```python
picnic.get_article_by_gtin("8000070025400")
```
```python
{'name': 'Lavazza Caffè Crema e Aroma Bohnen', 'id': 's1019822'}
```

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
