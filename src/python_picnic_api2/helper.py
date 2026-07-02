import json
import logging
import re

LOGGER = logging.getLogger(__name__)

IMAGE_SIZES = ["small", "medium", "regular", "large", "extra-large"]
IMAGE_BASE_URL = "https://storefront-prod.nl.picnicinternational.com/static/images"

SOLE_ARTICLE_ID_PATTERN = re.compile(r'"sole_article_id":"(\w+)"')


def _url_generator(url: str, country_code: str, api_version: str):
    return url.format(country_code.lower(), api_version)


def get_recipe_image(id: str, size="regular"):
    sizes = IMAGE_SIZES + ["1250x1250"]
    assert size in sizes, "size must be one of: " + ", ".join(sizes)
    return f"{IMAGE_BASE_URL}/recipes/{id}/{size}.png"


def get_image(id: str, size="regular", suffix="webp"):
    assert "tile" in size if suffix == "webp" else True, (
        "webp format only supports tile sizes"
    )
    assert suffix in ["webp", "png"], "suffix must be webp or png"
    sizes = IMAGE_SIZES + [f"tile-{size}" for size in IMAGE_SIZES]

    assert size in sizes, "size must be one of: " + ", ".join(sizes)
    return f"{IMAGE_BASE_URL}/{id}/{size}.{suffix}"


def find_nodes_by_content(node, filter, max_nodes: int = 10):
    nodes = []

    if len(nodes) >= max_nodes:
        return nodes

    def is_dict_included(node_dict, filter_dict):
        for k, v in filter_dict.items():
            if k not in node_dict:
                return False
            if isinstance(v, dict) and isinstance(node_dict[k], dict):
                if not is_dict_included(node_dict[k], v):
                    return False
            elif node_dict[k] != v and v is not None:
                return False
        return True

    if is_dict_included(node, filter):
        nodes.append(node)

    if isinstance(node, dict):
        for _, v in node.items():
            if isinstance(v, dict):
                nodes.extend(find_nodes_by_content(v, filter, max_nodes))
                continue
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict | list):
                        nodes.extend(find_nodes_by_content(
                            item, filter, max_nodes))
                        continue

    return nodes


def _extract_search_results(raw_results, max_items: int = 10):
    """Extract search results from the nested dictionary structure returned by
    Picnic search. Number of max items can be defined to reduce excessive nested
    search"""

    LOGGER.debug(f"Extracting search results from {raw_results}")

    body = raw_results.get("body", {})
    nodes = find_nodes_by_content(body.get("child", {}), {
        "type": "SELLING_UNIT_TILE", "sellingUnit": {}})

    search_results = []
    for node in nodes:
        selling_unit = node["sellingUnit"]
        sole_article_ids = SOLE_ARTICLE_ID_PATTERN.findall(
            json.dumps(node))
        sole_article_id = sole_article_ids[0] if sole_article_ids else None
        result_entry = {
            **selling_unit,
            "sole_article_id": sole_article_id,
        }
        LOGGER.debug(f"Found article {result_entry}")
        search_results.append(result_entry)

    LOGGER.debug(
        f"Found {len(search_results)}/{max_items} products after extraction")

    return [{"items": search_results}]
