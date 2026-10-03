# Document:    Four Missing Pair Construction Controls
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
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "r4", Path(__file__).resolve().parents[1] / "scripts/r4_link_search.py")
r4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r4)
TEMPLATE = ((0, 1, 2, 12), (0, 3, 8, 11), (0, 4, 6, 7), (0, 5, 9, 10),
            (1, 3, 6, 10), (1, 4, 8, 9), (1, 5, 7, 11), (2, 3, 7, 9),
            (2, 4, 8, 10), (2, 5, 6, 11), (3, 4, 5, 12), (6, 7, 8, 12),
            (9, 10, 11, 12))


def test_r4_missing_pairs_and_hole_compatible_maps():
    assert r4.missing_matching(TEMPLATE) == [(4, 11), (5, 8), (6, 9), (7, 10)]
    rng = random.Random(42)
    for leaf in (1, 2):
        permutation = r4.compatible_map(TEMPLATE, leaf, rng)
        for _ in range(50):
            permutation = r4.mutate(TEMPLATE, permutation, leaf, rng)
            holes = r4.links.check_template(r4.links.mapped(TEMPLATE, permutation))
            assert len(holes) == 4
            assert (0, leaf) in holes
            assert (0, 3 - leaf) not in holes


def test_damaged_r4_template_is_rejected():
    with pytest.raises(ValueError, match="distinct"):
        r4.missing_matching(TEMPLATE[:-1] + (TEMPLATE[0],))
    with pytest.raises(ValueError, match="distinct"):
        r4.missing_matching(((0, 0, 1, 2), *TEMPLATE[1:]))
