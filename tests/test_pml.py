from python_picnic_api2.models import pml


def test_walk_recurses_into_dicts_nested_in_lists():
    # Regression: the old find_nodes_by_content failed to recurse into dicts
    # that live inside lists. walk() must visit every dict.
    tree = {
        "children": [
            {"id": "a"},
            {"children": [{"id": "b"}, {"id": "c"}]},
        ]
    }
    ids = {node["id"] for node in pml.walk(tree) if "id" in node}
    assert ids == {"a", "b", "c"}


def test_find_returns_first_match_by_id():
    tree = {"children": [{"id": "x"}, {"id": "target", "value": 1}]}
    node = pml.find(tree, id="target")
    assert node == {"id": "target", "value": 1}


def test_find_by_id_prefix():
    tree = {"children": [
        {"id": "vertical-article-tiles-sub-header-22193", "value": 1},
        {"id": "something-else"},
    ]}
    node = pml.find(tree, id_prefix="vertical-article-tiles-sub-header-")
    assert node["value"] == 1


def test_find_all_enforces_limit():
    # Regression: the old helper never enforced its max_nodes limit.
    tree = {"items": [{"type": "T"} for _ in range(50)]}
    assert len(pml.find_all(tree, type="T")) == 50
    assert len(pml.find_all(tree, type="T", limit=3)) == 3


def test_find_all_match_predicate_requires_key_presence():
    tree = {"items": [
        {"type": "TILE", "sellingUnit": {"id": "1"}},
        {"type": "TILE"},  # missing sellingUnit -> should not match
    ]}
    matches = pml.find_all(tree, match={"type": "TILE", "sellingUnit": {}})
    assert len(matches) == 1
    assert matches[0]["sellingUnit"]["id"] == "1"


def test_strip_colors():
    assert pml.strip_colors("#(#333333)Milk#(#333333)") == "Milk"
    assert pml.strip_colors("#(#AbCdEf)Milk") == "Milk"
    assert pml.strip_colors("plain") == "plain"
    assert pml.strip_colors(None) is None


def test_text_of_strips_colors():
    assert pml.text_of({"markdown": "#(#333333)Halvarine"}) == "Halvarine"
    assert pml.text_of({"text": "Brand"}) == "Brand"
    assert pml.text_of({}) is None


def test_accessibility_label_and_on_press_target():
    node = {"pml": {"component": {
        "accessibilityLabel": "Halvarine",
        "onPress": {"target": "app.picnic://categories/1/l2/2/l3/3"},
    }}}
    assert pml.accessibility_label(node) == "Halvarine"
    assert pml.on_press_target(node) == "app.picnic://categories/1/l2/2/l3/3"
    assert pml.accessibility_label({}) is None
    assert pml.on_press_target({}) is None
