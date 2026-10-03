# Document:    Link Isomorphism Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "classify", Path(__file__).resolve().parents[1] / "scripts" / "classify_link_designs.py")
classify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classify)

LINK = [(2, 3, 4, 5), (2, 3, 6, 7), (2, 4, 6, 8), (2, 5, 9, 10),
        (2, 11, 13, 15), (2, 12, 14, 16), (3, 8, 11, 12), (3, 9, 14, 15),
        (3, 10, 13, 16), (4, 7, 15, 16), (4, 9, 12, 13), (4, 10, 11, 14),
        (5, 6, 13, 14), (5, 7, 11, 12), (5, 8, 15, 16), (6, 9, 11, 16),
        (6, 10, 12, 15), (7, 8, 9, 10), (7, 8, 13, 14)]
OTHER = [(2, 3, 4, 5), (2, 3, 6, 7), (2, 4, 6, 8), (2, 5, 9, 11),
         (2, 10, 13, 15), (2, 12, 14, 16), (3, 8, 15, 16), (3, 9, 10, 14),
         (3, 11, 12, 13), (4, 7, 13, 14), (4, 9, 12, 15), (4, 10, 11, 16),
         (5, 6, 10, 12), (5, 7, 15, 16), (5, 8, 13, 14), (6, 9, 13, 16),
         (6, 11, 14, 15), (7, 8, 9, 10), (7, 8, 11, 12)]


def test_relabeling_is_found_and_explicit_map_reproduces_control():
    relabeling = {p: 2 + ((p - 2) * 7 + 3) % 15 for p in range(2, 17)}
    target = classify.map_blocks(LINK, relabeling)
    mapping = classify.isomorphism(LINK, target)
    assert mapping is not None
    assert classify.map_blocks(LINK, mapping) == target


def test_distinct_hub_controls_are_not_isomorphic():
    classify.structure(OTHER)
    assert classify.isomorphism(LINK, OTHER) is None


def test_duplicate_and_damaged_links_are_rejected():
    with pytest.raises(ValueError, match="malformed"):
        classify.structure(LINK[:-1] + [LINK[0]])
    with pytest.raises(ValueError):
        classify.structure(LINK[:-1] + [(7, 8, 13, 15)])
    with pytest.raises(ValueError, match="labels"):
        classify.structure([[0 if p == 2 else p for p in b] for b in LINK])
    with pytest.raises(ValueError, match="labels"):
        classify.structure([[True if p == 2 else p for p in b] for b in LINK])


def test_same_hub_blocks_with_different_excess_graph_are_rejected(tmp_path):
    relabeling = {p: p for p in range(2, 17)}
    relabeling[11], relabeling[13] = 13, 11
    other = classify.map_blocks(LINK, relabeling)
    assert {b for b in LINK if 2 in b} == {b for b in other if 2 in b}
    folder = tmp_path / "input"
    (folder / "enumeration").mkdir(parents=True)
    rows = [{"number": 1, "link": LINK}, {"number": 2, "link": other}]
    (folder / "enumeration" / "1.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(ValueError, match="pair-excess"):
        classify.main([str(folder), "--output", str(tmp_path / "output")])
