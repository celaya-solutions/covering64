# Document:    Large Neighborhood Search Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import importlib.util
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import pytest

from covering64.core import Universe, verify_cover

SPEC = importlib.util.spec_from_file_location(
    "lns_search", Path(__file__).parents[1] / "scripts" / "lns_search.py")
lns = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lns)


def test_repair_matches_exhaustive_optimum():
    universe = Universe.build(5, 2, 1)
    incumbent = [(1, 2), (1, 3)]
    ids = [universe.blocks.index(block) for block in incumbent]
    result = lns.repair_neighborhood(universe, incumbent, ids, 2, 3, seed=64)
    optimum = min(len(verify_cover(blocks, 5, 2, 1)["uncovered"])
                  for count in range(3) for blocks in combinations(universe.blocks, count))
    assert result["status"] == "OPTIMAL"
    assert result["uncovered"] == optimum == 1
    assert len(result["witness"]) <= 2


def test_repairs_around_retained_block_and_can_change_neutrally():
    universe = Universe.build(4, 2, 1)
    incumbent = [(1, 2), (1, 3)]
    removed = [universe.blocks.index((1, 3))]
    result = lns.repair_neighborhood(universe, incumbent, removed, 2, 3, change=True)
    assert result["verification"]["valid"]
    assert (1, 2) in result["witness"]
    assert (1, 3) not in result["witness"]


@pytest.mark.parametrize("removed", [[0, 0], [9], [True]])
def test_rejects_invalid_removed_ids(removed):
    with pytest.raises(ValueError):
        lns.repair_neighborhood(Universe.build(4, 2, 1), [(1, 2)], removed, 2, 1)


def test_rejects_damaged_or_duplicate_incumbent():
    universe = Universe.build(4, 2, 1)
    for blocks in [[(1, 2), (1, 2)], [(1, 1)], [(0, 2)]]:
        with pytest.raises(ValueError):
            lns.repair_neighborhood(universe, blocks, [], 2, 1)


@pytest.mark.parametrize("target, feasible", [(2, False), (3, True)])
def test_exact_repairs_and_safe_link_bounds_match_small_exhaustion(target, feasible):
    universe = Universe.build(4, 3, 2)
    incumbent = list(universe.blocks)
    brute = any(verify_cover(blocks, 4, 3, 2)["valid"]
                for count in range(target + 1)
                for blocks in combinations(universe.blocks, count))
    result = lns.repair_neighborhood(universe, incumbent, range(4), target, 3, exact=True)
    assert brute is feasible
    assert (result["witness"] is not None) is feasible
    if feasible:
        assert result["verification"]["valid"]
    else:
        assert result["status"] == "INFEASIBLE"


def test_lp_screen_returns_independently_valid_dual_and_does_not_reject_equality():
    universe = Universe.build(4, 2, 1)
    blocks = [(1, 2), (3, 4)]
    removed = [universe.blocks.index(block) for block in blocks]
    result = lns.repair_neighborhood(
        universe, blocks, removed, 1, 2, exact=True, lp_screen=True)
    assert result["status"] == "LP_CERTIFIED_INFEASIBLE"
    certificate = result["lp_certificate"]
    weights = {triple: Fraction(numerator, denominator)
               for triple, numerator, denominator in certificate["weights"]}
    assert all(weight >= 0 for weight in weights.values())
    assert all(sum((weights.get(triple, Fraction(0)) for triple in coverage), Fraction(0)) <= 1
               for coverage in universe.coverage)
    assert sum(weights.values(), Fraction(0)) == Fraction(*certificate["lower_bound"]) == 2
    feasible = lns.repair_neighborhood(
        universe, blocks, removed, 2, 2, exact=True, lp_screen=True)
    assert feasible["verification"]["valid"]
