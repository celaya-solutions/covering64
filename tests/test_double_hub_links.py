# Document:    Double Hub Enumeration Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
from pathlib import Path

import pytest
from test_classify_link_designs import LINK, OTHER

spec = importlib.util.spec_from_file_location(
    "double_hub", Path(__file__).resolve().parents[1] / "scripts" / "double_hub_links.py")
double = importlib.util.module_from_spec(spec)
spec.loader.exec_module(double)


def test_singleton_permutations_can_change_the_second_matching():
    target = [b for b in LINK if 2 in b]
    mappings = list(double.unrestricted_hub_maps(LINK, target))
    # Four automorphisms of the uncolored hub incidence pattern, times
    #2!*3!*3! free singleton permutations in its three nonsingleton rows.
    assert len(mappings) == 288
    wanted = {p: p for p in range(2, 17)}
    wanted[11], wanted[13] = 13, 11
    assert wanted in mappings
    mapped = double.classification.map_blocks(LINK, wanted)
    assert double.classification.structure(mapped)[3] != double.classification.structure(LINK)[3]


def test_both_compatible_link_types_are_enumerated():
    links, counts = double.enumerate_second_links({"1": LINK, "4": OTHER}, LINK)
    assert counts == {"1": 288, "4": 288}
    assert len(links) == 216
    assert {origin["source_class"] for origin in links.values()} == {"1", "4"}
    matchings = set()
    for second in links:
        _, hub, _, matching = double.classification.structure(second)
        assert hub == 1
        matchings.add(tuple(matching))
    assert len(matchings) > 1


def test_duplicate_hub_blocks_are_rejected():
    target = [b for b in LINK if 2 in b]
    target[-1] = target[0]
    with pytest.raises(ValueError, match="invalid"):
        list(double.unrestricted_hub_maps(LINK, target))
