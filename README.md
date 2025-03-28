# Python-Picnic-API

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
from python_picnic_api import PicnicAPI

picnic = PicnicAPI(username='username', password='password', country_code="NL")
```

The country_code parameter defaults to `NL`, but you have to change it if you live in a different country than the Netherlands (ISO 3166-1 Alpha-2). This obviously only works for countries that picnic services.

## Searching for a product

```python
picnic.search('coffee')
```

```python
[{'items': [{'id': 's1019822', 'name': 'Lavazza Caffè Crema e Aroma Bohnen', 'decorators': [], 'display_price': 1799, 'image_id': 'aecbf7d3b018025ec78daf5a1099b6842a860a2e3faeceec777c13d708ce442c', 'max_count': 99, 'unit_quantity': '1kg', 'sole_article_id': None}, ... ]}]
```