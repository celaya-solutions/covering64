# Document:    Restricted Residual Dual Controls
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
from pathlib import Path

import pytest

from covering64.core import Universe

spec = importlib.util.spec_from_file_location(
    "screen", Path(__file__).resolve().parents[1] / "scripts" / "screen_double_hubs.py")
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def test_fractional_dual_is_checked_against_every_column():
    universe = Universe.build(3, 2, 1)
    result = screen.restricted_dual(universe, [], [0, 1, 2])
    assert Fraction(*result["lower_bound"]) == Fraction(3, 2)
    weights = {t: Fraction(n, d) for t, n, d in result["weights"]}
    assert all(sum(weights.get(t, 0) for t in covered) <= 1 for covered in universe.coverage)
    assert result["all_block_capacity_valid"]


def test_retained_coverage_is_not_weighted():
    universe = Universe.build(4, 2, 1)
    result = screen.restricted_dual(universe, [0], [5])
    assert Fraction(*result["lower_bound"]) == 1
    assert {t for t, _, _ in result["weights"]}.isdisjoint(universe.coverage[0])


def test_malformed_candidate_family_is_rejected():
    universe = Universe.build(3, 2, 1)
    with pytest.raises(ValueError, match="duplicate"):
        screen.restricted_dual(universe, [], [0, 0, 1])
    with pytest.raises(ValueError, match="overlap"):
        screen.restricted_dual(universe, [0], [0, 1])
