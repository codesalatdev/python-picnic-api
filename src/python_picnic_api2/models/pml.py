"""Tolerant traversal helpers for Picnic's PML ("layout") responses.

The ``/pages/*`` endpoints return a UI tree of widgets rather than clean domain
JSON. The shape differs by country and A/B test, so parsing must never rely on
fixed paths. These helpers walk the whole tree and match nodes by ``id``, ``id``
prefix, ``type`` or a nested-inclusion predicate.

This module replaces the older ``helper.find_nodes_by_content`` which had two
bugs: it never enforced its ``max_nodes`` limit, and it failed to recurse into
dicts nested inside lists.
"""

import re
from collections.abc import Iterator

# Inline color codes embedded in markdown text. Picnic uses two forms: a hex code
# ``#(#333333)Some text#(#333333)`` and a named palette code ``#(GREEN1)...#(GREEN1)``.
_COLOR_CODE = re.compile(r"#\((?:#[0-9A-Fa-f]{6}|[A-Z][A-Z0-9_]*)\)")


def walk(node) -> Iterator[dict]:
    """Yield every dict contained in ``node``, depth-first (including ``node``).

    Recurses into every value of every dict and every item of every list, so
    dicts nested inside lists are visited too.
    """
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def _is_included(node_dict: dict, filter_dict: dict) -> bool:
    """Return whether ``filter_dict`` is a (recursive) subset of ``node_dict``.

    An empty dict value means "this key must be present" regardless of its value;
    a ``None`` filter value means "this key must be present with any value".
    """
    for key, value in filter_dict.items():
        if key not in node_dict:
            return False
        if isinstance(value, dict) and isinstance(node_dict[key], dict):
            if not _is_included(node_dict[key], value):
                return False
        elif value is not None and node_dict[key] != value:
            return False
    return True


def _matches(
    node: dict,
    *,
    id: str | None,
    id_prefix: str | None,
    type: str | None,
    match: dict | None,
) -> bool:
    if id is not None and node.get("id") != id:
        return False
    if id_prefix is not None:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.startswith(id_prefix):
            return False
    if type is not None and node.get("type") != type:
        return False
    return match is None or _is_included(node, match)


def find_all(
    node,
    *,
    id: str | None = None,
    id_prefix: str | None = None,
    type: str | None = None,
    match: dict | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Return all dict nodes in ``node`` matching the given criteria.

    ``limit`` is actually enforced (stops walking once reached).
    """
    results: list[dict] = []
    for candidate in walk(node):
        if _matches(candidate, id=id, id_prefix=id_prefix, type=type, match=match):
            results.append(candidate)
            if limit is not None and len(results) >= limit:
                break
    return results


def find(
    node,
    *,
    id: str | None = None,
    id_prefix: str | None = None,
    type: str | None = None,
    match: dict | None = None,
) -> dict | None:
    """Return the first matching dict node, or ``None``."""
    results = find_all(
        node, id=id, id_prefix=id_prefix, type=type, match=match, limit=1
    )
    return results[0] if results else None


def strip_colors(text):
    """Remove Picnic inline color codes (``#(#RRGGBB)``) from markdown text.

    Non-string input is returned unchanged.
    """
    if not isinstance(text, str):
        return text
    return _COLOR_CODE.sub("", text)


def _component(node) -> dict | None:
    """Return a node's PML component dict, tolerating a couple of nestings."""
    if not isinstance(node, dict):
        return None
    pml = node.get("pml")
    if isinstance(pml, dict) and isinstance(pml.get("component"), dict):
        return pml["component"]
    if isinstance(node.get("component"), dict):
        return node["component"]
    return node


def text_of(node) -> str | None:
    """Return a node's text/markdown content with color codes stripped."""
    if not isinstance(node, dict):
        return None
    for key in ("markdown", "text"):
        value = node.get(key)
        if isinstance(value, str):
            return strip_colors(value)
    return None


def accessibility_label(node) -> str | None:
    """Return the ``accessibilityLabel`` of a node's component, if any."""
    component = _component(node)
    if component:
        label = component.get("accessibilityLabel")
        if isinstance(label, str):
            return label
    return None


def on_press_target(node) -> str | None:
    """Return the ``onPress.target`` deep-link of a node's component, if any."""
    component = _component(node)
    if not component:
        return None
    on_press = component.get("onPress")
    if isinstance(on_press, dict):
        target = on_press.get("target")
        if isinstance(target, str):
            return target
    return None


def find_nodes_by_content(node, filter: dict, limit: int | None = None) -> list[dict]:
    """Predicate-dict search, kept for parity with the old helper.

    Equivalent to ``find_all(node, match=filter, limit=limit)`` but with the
    ``limit`` actually enforced and correct recursion into lists.
    """
    return find_all(node, match=filter, limit=limit)


__all__ = [
    "walk",
    "find",
    "find_all",
    "find_nodes_by_content",
    "strip_colors",
    "text_of",
    "accessibility_label",
    "on_press_target",
]
