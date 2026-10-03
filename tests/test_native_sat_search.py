# Document:    Native Cardinality SAT Model Checks
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

from covering64.core import Universe, verify_cover

SPEC = importlib.util.spec_from_file_location(
    "native_sat_search", Path(__file__).parents[1] / "scripts" / "native_sat_search.py")
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


@pytest.mark.parametrize("target", [0, 1, 2, 3, 4])
def test_native_solver_matches_full_small_enumeration(target):
    universe = Universe.build(4, 3, 2)
    brute = any(verify_cover(blocks, 4, 3, 2)["valid"]
                for count in range(target + 1)
                for blocks in combinations(universe.blocks, count))
    model = native.native_model(universe, target)
    assert model["variables"] == len(universe.blocks)
    with native.make_solver(model) as solver:
        status = solver.solve()
        assert status is brute
        if status:
            assignment = set(solver.get_model())
            blocks = [block for i, block in enumerate(universe.blocks) if i + 1 in assignment]
            assert verify_cover(blocks, 4, 3, 2)["valid"]
            assert len(blocks) <= target


def test_hint_relabeling_only_changes_phases_and_rejects_duplicate_blocks():
    universe = Universe.build(5, 3, 2)
    phases, permutation = native.hint_phases(universe, [(1, 2, 3), (2, 3, 4)], 13)
    assert sorted(abs(x) for x in phases) == list(range(1, len(universe.blocks) + 1))
    assert sum(x > 0 for x in phases) == 2
    assert set(permutation.values()) == set(range(1, 6))
    with pytest.raises(ValueError):
        native.hint_phases(universe, [(1, 2, 3), (1, 2, 3)], 13)
