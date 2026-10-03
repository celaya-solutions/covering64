import importlib.util
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "four_seven_search", Path(__file__).parents[1] / "scripts/four_seven_search.py"
)
search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(search)


@pytest.mark.parametrize("case,histogram", [("cycle", {5: 92, 6: 16, 7: 12}),
                                           ("matching", {5: 94, 6: 12, 7: 14})])
def test_branch_pair_counts(case, histogram):
    targets = search.pair_targets(case)
    assert Counter(targets.values()) == histogram
    assert sum(targets.values()) == 640
    assert all(sum(n for pair, n in targets.items() if p in pair) == 80 for p in range(1, 17))


def test_allowed_block_partition():
    blocks = list(combinations(range(1, 17), 5))
    allowed = [b for b in blocks if search.allowed_block(b)]
    assert len(allowed) == 1476
    heavy = [b for b in allowed if any(set(a) <= set(b) for a in search.ANCHORS)]
    assert len(heavy) == 276
    assert Counter(len(set(b) & set(search.HUBS)) for b in allowed if b not in heavy) == {
        1: 324, 2: 648, 3: 216, 4: 12,
    }


@pytest.mark.parametrize("case", ["cycle", "matching"])
def test_full_model_retains_lex_order_and_no_extra_block_fixing(case):
    universe, model, xs, holes = search.build_model(case)
    assert not model.validate()
    assert not holes
    assert len(xs) == 4368
    assert len(model.proto.variables) == 4368
    assert len(model.proto.constraints) == 3593
    assert universe.blocks == tuple(combinations(range(1, 17), 5))
    fixed = list(model.proto.constraints)[:2892]
    assert {row.linear.vars[0] for row in fixed} == {
        i for i, b in enumerate(universe.blocks) if not search.allowed_block(b)
    }
    assert all(list(row.linear.domain) == [0, 0] for row in fixed)


def test_bad_parameters_and_damaged_candidate():
    for value in (-1, 561, True, 1.0):
        with pytest.raises(ValueError):
            search.build_model("cycle", value)
    with pytest.raises(ValueError):
        search.pair_targets("unknown")
    with pytest.raises(ValueError):
        search.check_candidate([(1, 2, 3, 4, 5)] * 64, "cycle")
    with pytest.raises(ValueError):
        search.check_candidate(list(combinations(range(1, 17), 5))[:64], "cycle")


def test_partial_model_tracks_all_holes_without_claiming_completeness():
    _, model, _, holes = search.build_model("cycle", 30)
    assert not model.validate()
    assert len(holes) == 560
    assert len(model.proto.variables) == 4928
    assert len(model.proto.constraints) == 4154


@pytest.mark.parametrize("case", ["cycle", "matching"])
def test_optional_group_action_preserves_branch_and_has_free_block_orbits(case):
    universe, model, xs, _ = search.build_model(case)
    targets = search.pair_targets(case)
    for g in search.group_generators(case):
        assert sorted(g) == list(range(1, 17))
        assert {tuple(sorted(g[p - 1] for p in t)) for t in search.ANCHORS} == set(search.ANCHORS)
        assert {tuple(sorted(g[p - 1] for p in pair)): n for pair, n in targets.items()} == targets
    info = search.add_group_symmetry(model, xs, universe, case)
    assert info["orbit_sizes"] == {4: 1092}
    assert info["allowed_orbits"] == 369
    assert len(model.proto.variables) == 4368
    assert len(model.proto.constraints) == 3593 + 3276
    assert not model.validate()
