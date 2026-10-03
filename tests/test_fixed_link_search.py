# Document:    Fixed Link Model Checks
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
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover

SPEC = importlib.util.spec_from_file_location(
    "fixed_link_search", Path(__file__).parents[1] / "scripts" / "fixed_link_search.py")
fixed_link = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixed_link)


@pytest.mark.parametrize("target", [2, 3])
def test_fixed_link_model_matches_complete_restricted_enumeration(target):
    universe = Universe.build(6, 4, 2)
    link = [(1, 2, 3), (3, 4, 5)]
    fixed = [(1, 2, 3, 6), (3, 4, 5, 6)]
    candidates = [block for block in universe.blocks if 6 not in block]
    brute = any(verify_cover(fixed + list(extra), 6, 4, 2)["valid"]
                for count in range(target - len(fixed) + 1)
                for extra in combinations(candidates, count))
    model, variables, fixed_ids, _ = fixed_link.build_fixed_link_model(universe, link, target)
    assert list(variables) == sorted(variables)
    assert [universe.blocks[i] for i in variables] == candidates
    assert [universe.blocks[i] for i in fixed_ids] == fixed
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    status = solver.Solve(model)
    assert (status in (cp_model.FEASIBLE, cp_model.OPTIMAL)) is brute
    if brute:
        blocks = fixed + [universe.blocks[i] for i in variables if solver.Value(variables[i])]
        assert verify_cover(blocks, 6, 4, 2)["valid"]


@pytest.mark.parametrize("link", [[(1, 2)], [(1, 2), (1, 2)], [(1, 2), (1, 4)]])
def test_invalid_incomplete_or_duplicate_links_are_rejected(link):
    with pytest.raises(ValueError):
        fixed_link.build_fixed_link_model(Universe.build(4, 3, 2), link, 3)
