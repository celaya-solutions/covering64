# Document:    Complete Degree Split Model Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import importlib.util
from collections import Counter
from itertools import combinations
from pathlib import Path

from ortools.sat.python import cp_model

from covering64.core import verify_cover

SPEC = importlib.util.spec_from_file_location(
    "degree_split_search", Path(__file__).parents[1] / "scripts" / "degree_split_search.py")
split = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(split)
NATIVE_SPEC = importlib.util.spec_from_file_location(
    "native_degree_control", Path(__file__).parents[1] / "scripts" / "native_sat_search.py")
native = importlib.util.module_from_spec(NATIVE_SPEC)
NATIVE_SPEC.loader.exec_module(native)

# A separately verified19-block C(15,4,2) link. Adding every5-block away from
# point16 gives a large positive control with a complete degree19 point link.
LINK = [
    (1, 2, 8, 15), (1, 3, 9, 10), (1, 4, 5, 14), (1, 6, 7, 12), (1, 11, 12, 13),
    (2, 3, 4, 12), (2, 5, 6, 11), (2, 6, 10, 13), (2, 7, 9, 14), (3, 5, 9, 13),
    (3, 6, 14, 15), (3, 7, 8, 11), (4, 6, 8, 9), (4, 7, 13, 15), (4, 10, 11, 14),
    (5, 7, 10, 15), (5, 8, 10, 12), (8, 12, 13, 14), (9, 11, 12, 15),
]


def test_complete_degree19_link_can_be_canonicalized_and_model_accepts_control():
    assert verify_cover(LINK, 15, 4, 2)["valid"]
    full = [block + (16,) for block in LINK] + list(combinations(range(1, 16), 5))
    canonical, mapping = split.normalize_split_hint(full, "degree19")
    assert set(mapping) == set(mapping.values()) == set(range(1, 17))
    assert mapping[16] == 1
    assert verify_cover(canonical)["valid"]
    assert set(canonical).intersection(split.representative_blocks())
    counts = Counter(triple for block in canonical for triple in combinations(block, 3))
    for a, b in combinations(range(2, 17), 2):
        assert counts[(1, a, b)] == (2 if (a, b) in split.excess_pairs() else 1)
    universe, model, variables = split.build_split_model(
        "degree19", target=len(canonical), normalize=True)
    selected = set(canonical)
    for block, variable in zip(universe.blocks, variables):
        model.Add(variable == int(block in selected))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    assert solver.Solve(model) == cp_model.OPTIMAL
    native_model = native.native_model(universe, len(canonical), branch="degree19", normalize=True)
    with native.make_solver(native_model) as native_solver:
        for i, block in enumerate(universe.blocks):
            native_solver.add_clause([i + 1 if block in selected else -i - 1])
        assert native_solver.solve()
    # Swap the uniquely distinguished center with a leaf. This remains a full
    # cover with point1 degree19 but violates the chosen canonical labeling.
    swap = {x: (3 if x == 2 else 2 if x == 3 else x) for x in range(1, 17)}
    noncanonical = {tuple(sorted(swap[x] for x in block)) for block in canonical}
    assert verify_cover(noncanonical)["valid"]
    with native.make_solver(native_model) as native_solver:
        for i, block in enumerate(universe.blocks):
            native_solver.add_clause([i + 1 if block in noncanonical else -i - 1])
        assert not native_solver.solve()


def test_regular20_branch_cannot_accept_fewer_than64_blocks():
    _, model, _ = split.build_split_model("regular20", target=63)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 3
    assert solver.Solve(model) == cp_model.INFEASIBLE


def test_regular_hint_normalization_selects_first_block_and_preserves_degree_multiset():
    blocks = [tuple(sorted(x + 1 for x in block)) for block in [(1, 3, 6, 9, 12), (0, 2, 4, 6, 8)]]
    transformed, mapping = split.normalize_split_hint(blocks, "regular20")
    assert (1, 2, 3, 4, 5) in transformed
    assert set(mapping) == set(mapping.values()) == set(range(1, 17))
    assert sorted(Counter(x for block in blocks for x in block).values()) == sorted(
        Counter(x for block in transformed for x in block).values())
