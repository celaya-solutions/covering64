# Document:    Residual Kernel Solver Checks
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

from covering64.core import Universe

SPEC = importlib.util.spec_from_file_location(
    "dual_kernel_search", Path(__file__).parents[1] / "scripts" / "dual_kernel_search.py")
kernel = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kernel)


def test_exact_kernel_repairs_and_certifies_too_small_budget():
    universe = Universe.build(4, 2, 1)
    certificate = {"weights": [[i, 1, 2] for i in range(4)], "lower_bound": [2, 1]}
    feasible = kernel.solve_kernel(universe, [], certificate, 2, 2)
    assert feasible["verification"]["valid"]
    assert len(feasible["witness"]) == 2
    excluded = kernel.solve_kernel(universe, [], certificate, 1, 2)
    assert excluded["status"] == "LP_CERTIFIED_INFEASIBLE"


def test_weight_on_retained_coverage_cannot_prune_candidates():
    universe = Universe.build(4, 2, 1)
    certificate = {"weights": [[0, 1, 1]], "lower_bound": [1, 1]}
    with pytest.raises(ValueError, match="already covered"):
        kernel.solve_kernel(universe, [0], certificate, 2, 2)
