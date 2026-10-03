"""Check necessary link bounds against an independently verified control."""

import importlib.util
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("link_search", ROOT / "scripts/link_search.py")
link_search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(link_search)


def normalized_baseline():
    blocks = read_blocks(ROOT / "data/baselines/belic-1997.txt")
    counts = Counter(p for b in blocks for p in b)
    order = sorted(range(1, 17), key=lambda p: (counts[p], p))
    relabel = {p: i + 1 for i, p in enumerate(order)}
    return {tuple(sorted(relabel[p] for p in b)) for b in blocks}


def check_fixed_blocks(blocks, target):
    universe = Universe.build()
    model, selected = link_search.build_link_model(universe, target)
    for block, variable in zip(universe.blocks, selected):
        model.add(variable == int(block in blocks))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.num_search_workers = 1
    return solver.solve(model)


def test_known_cover_survives_bounds_and_degree_normalization():
    assert check_fixed_blocks(normalized_baseline(), 65) == cp_model.OPTIMAL


def test_deleted_block_control_rejected_by_exact_model():
    blocks = normalized_baseline()
    blocks.remove(min(blocks))
    assert check_fixed_blocks(blocks, 64) == cp_model.INFEASIBLE
