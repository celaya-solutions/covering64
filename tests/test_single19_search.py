# Document:    Sole Degree-Nineteen Input Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2baea2f3325864fff028d204adce9fff6dc2f39094ffc6cbc639c34dd8bc360e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import sys
from itertools import combinations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import single19_search as search  # noqa: E402


@pytest.fixture
def link():
    return search.read_blocks(
        ROOT / "experiments/2026-10-03/link-classification/shape-1-class-0.txt")


def test_malformed_and_damaged_links_are_rejected(link):
    malformed = [link[:-1], [link[0], *link[:-1]]]
    for replacement in ((1, 2, 2, 3, 4), (0, 2, 3, 4, 5), (1, 2, 3, 4, 17),
                        (True, *link[0][1:]), tuple(reversed(link[0]))):
        malformed.append([replacement, *link[1:]])
    for candidate in combinations(range(2, 17), 4):
        replacement = (1, *candidate)
        damaged = [replacement, *link[1:]]
        if len(set(damaged)) != 19:
            continue
        covered = {pair for block in damaged for pair in combinations(block[1:], 2)}
        if len(covered) < 105:
            malformed.append(damaged)
            break
    else:
        raise AssertionError("missing damaged genuine-subset control")
    for bad in malformed:
        with pytest.raises(ValueError):
            search.build_model(bad, 2)


@pytest.mark.parametrize("bad", (1, 0, 17, True, 2.0, "2"))
def test_wrong_high_point_is_rejected(link, bad):
    with pytest.raises(ValueError, match="degree21 point"):
        search.build_model(link, bad)


def test_global_block_order_and_conditional_degree_profile(link):
    universe, model, xs = search.build_model(link, 7)
    assert tuple(universe.blocks) == tuple(combinations(range(1, 17), 5))
    assert len(xs) == len(model.proto.variables) == 4368
    assert all(x.index == i and x.name == f"block_{i}" for i, x in enumerate(xs))
    rows, width = search.linear_rows(model)
    assert width == 4368
    fixed = {indices[0]: low for indices, coefs, low, high in rows
             if len(indices) == 1 and coefs == (1,) and low == high}
    assert len(fixed) == 1365
    assert sum(fixed.values()) == 19
    assert {universe.blocks[i] for i, value in fixed.items() if value} == set(link)
    profiles = []
    for point in range(1, 17):
        containing = tuple(i for i, block in enumerate(universe.blocks) if point in block)
        exact = [low for indices, coefs, low, high in rows
                 if indices == containing and all(c == 1 for c in coefs) and low == high]
        assert len(exact) == 1
        profiles.append(exact[0])
    assert profiles == [19, 20, 20, 20, 20, 20, 21, 20, 20, 20, 20, 20, 20, 20, 20, 20]
    assert sum(profiles) == 5 * 64
