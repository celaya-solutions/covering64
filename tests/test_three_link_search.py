# Document:    Three Link Construction Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
import random
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "three", Path(__file__).resolve().parents[1] / "scripts/three_link_search.py")
three = importlib.util.module_from_spec(spec)
spec.loader.exec_module(three)
SPOKE = ((0, 2, 6, 7), (0, 3, 7, 10), (0, 4, 5, 12), (0, 8, 9, 11),
         (1, 2, 10, 12), (1, 3, 6, 9), (1, 4, 7, 11), (1, 5, 8, 10),
         (2, 3, 5, 11), (2, 4, 8, 9), (3, 6, 8, 12), (4, 6, 10, 11), (5, 7, 9, 12))


def test_plane_pairs_and_regular_degrees():
    plane = three.projective_plane()
    assert not three.check_template(plane)
    assert Counter(pair for b in plane for pair in combinations(b, 2)) == {
        p: 1 for p in combinations(range(13), 2)}


def test_permuted_spoke_links_close_all_anchor_triples():
    rng = random.Random(42)
    kinds = ("pg", "spoke", "spoke")
    templates = (three.projective_plane(), SPOKE, SPOKE)
    permutations = [three.random_map(kind, 1 + i % 2, rng) for i, kind in enumerate(kinds)]
    for _ in range(40):
        permutations = [three.mutate(p, kind, rng) for p, kind in zip(permutations, kinds)]
        blocks = three.fixed_blocks(templates, permutations)
        covered = {t for b in blocks for t in combinations(b, 3)}
        assert all(t in covered for t in combinations(range(1, 17), 3)
                   if set(t) & {1, 2, 3})
        degrees = Counter(p for b in blocks for p in b)
        assert [degrees[p] for p in (1, 2, 3, 4, 5)] == [20, 20, 20, 14, 13]


def test_invalid_link_controls():
    with pytest.raises(ValueError, match="permutation"):
        three.mapped(SPOKE, [0] * 13)
    with pytest.raises(ValueError, match="malformed"):
        three.check_template(SPOKE[:-1] + (SPOKE[0],))
    permutation = list(range(13))
    permutation[1], permutation[3] = permutation[3], permutation[1]
    with pytest.raises(ValueError, match="outside"):
        three.check_template(three.mapped(SPOKE, permutation))
