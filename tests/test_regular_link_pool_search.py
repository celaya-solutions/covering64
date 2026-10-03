# Document:    Pooled Link Construction Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
from itertools import combinations
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "pool", Path(__file__).resolve().parents[1] / "scripts/regular_link_pool_search.py")
pool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pool)


def test_repeated_family_has_distinct_anchors_and_closes_anchor_triples():
    plane = pool.links.projective_plane()
    fixed = pool.assemble([plane], [3], [])
    assert len(fixed) == len(set(fixed)) == 46
    covered = {t for b in fixed for t in combinations(b, 3)}
    assert all(t in covered for t in combinations(range(1, 17), 3)
               if set(t) & {1, 2, 3})


def test_assembly_rejects_wrong_family_count():
    plane = pool.links.projective_plane()
    with pytest.raises(ValueError, match="exactly three"):
        pool.assemble([plane], [2], [])


def test_spoke_pool_rejects_plane_as_wrong_missing_graph():
    with pytest.raises(ValueError, match="missing-pair graph"):
        pool.spoke_pool(pool.links.projective_plane())
