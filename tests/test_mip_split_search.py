# Document:    Independent MIP solver controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Exercise positive and impossible controls through SCIP itself."""

import importlib.util
from pathlib import Path

from ortools.linear_solver import pywraplp

from covering64.core import read_blocks, verify_cover

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mip_split", ROOT / "scripts/mip_split_search.py")
MIP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIP)


def test_known_cover_is_accepted_by_scip():
    universe, solver, variables = MIP.build_model("unrestricted", target=65)
    known = set(read_blocks(ROOT / "data/baselines/belic-1997.txt"))
    for block, variable in zip(universe.blocks, variables):
        solver.Add(variable == int(block in known))
    solver.SetNumThreads(1)
    solver.SetTimeLimit(3000)
    assert solver.Solve() == pywraplp.Solver.OPTIMAL
    blocks = [b for b, x in zip(universe.blocks, variables) if x.solution_value() > 0.5]
    assert set(blocks) == known
    assert verify_cover(blocks)["valid"]


def test_twenty_occurrences_per_point_need_64_blocks():
    _, solver, _ = MIP.build_model("regular20", target=63)
    solver.SetNumThreads(1)
    solver.SetTimeLimit(3000)
    assert solver.Solve() == pywraplp.Solver.INFEASIBLE
