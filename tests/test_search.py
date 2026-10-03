"""Tiny exact instances exercise repairs, exhaustive audits, and input checks."""

import pytest

from covering64.core import Universe, verify_cover
from covering64.search import audit_small_exchanges, run_exchange_search


def test_three_to_two_exchange_improves_cover_and_verifies_witness():
    universe = Universe.build(v=4, k=3, t=2)
    result = run_exchange_search(
        universe, universe.blocks, attempts=1, remove=3, seconds_per_attempt=1, seed=7
    )

    assert result["status"] == "improved"
    assert result["initial_block_count"] == 4
    assert result["final_block_count"] == 3
    assert len(result["witness"]) == 3
    assert verify_cover(result["witness"], v=4, k=3, t=2)["valid"]
    assert result["verification"]["valid"]
    attempt = result["attempts"][0]
    assert attempt["accepted"]
    assert attempt["seed"] == 7
    assert len(attempt["removed_ids"]) == 3
    assert len(attempt["replacement_ids"]) == 2
    assert attempt["solver_status"] in {"OPTIMAL", "FEASIBLE"}


def test_irreducible_exchange_reports_local_infeasibility():
    universe = Universe.build(v=4, k=2, t=2)
    result = run_exchange_search(
        universe, universe.blocks, attempts=3, remove=3, seconds_per_attempt=1, seed=11
    )

    assert result["status"] == "no_improvement"
    assert result["final_block_count"] == 6
    assert result["witness"] is None
    assert result["verification"]["valid"]
    assert [attempt["seed"] for attempt in result["attempts"]] == [11, 12, 13]
    for attempt in result["attempts"]:
        assert attempt["solver_status"] == "INFEASIBLE"
        assert not attempt["accepted"]
        assert len(attempt["uncovered_triples"]) == 3
        assert attempt["candidate_count"] == 3
        assert attempt["replacement_limit"] == 2


def test_pair_audit_finds_every_compression_in_star_cover():
    universe = Universe.build(v=4, k=2, t=1)
    incumbent = ((1, 2), (1, 3), (1, 4))
    result = audit_small_exchanges(universe, incumbent)

    assert result["status"] == "improved"
    assert result["deletion_checks"] == 3
    assert result["deletable_block_ids"] == []
    assert result["pair_checks"] == 3
    assert len(result["compressible_pairs"]) == 3
    assert len(result["witness"]) == 2
    assert verify_cover(result["witness"], v=4, k=2, t=1)["valid"]
    incumbent_ids = {universe.blocks.index(block) for block in incumbent}
    for pair in result["compressible_pairs"]:
        assert pair["replacement_count"] == 1
        retained_ids = incumbent_ids.difference(pair["removed_ids"])
        candidate = [universe.blocks[index] for index in retained_ids] + [pair["replacement"]]
        assert verify_cover(candidate, v=4, k=2, t=1)["valid"]


def test_pair_audit_exhausts_irreducible_cover():
    universe = Universe.build(v=4, k=2, t=2)
    result = audit_small_exchanges(universe, universe.blocks)

    assert result["status"] == "no_small_exchange"
    assert result["deletion_checks"] == 6
    assert result["deletable_block_ids"] == []
    assert result["pair_checks"] == 15
    assert result["compressible_pairs"] == []
    assert result["min_pair_deficit"] == 2
    assert len(result["min_pair_deficit_pairs"]) == 15
    assert result["witness"] is None
    assert result["verification"]["valid"]


def test_deletion_audit_finds_all_redundant_blocks():
    universe = Universe.build(v=4, k=3, t=2)
    result = audit_small_exchanges(universe, universe.blocks)

    assert result["deletion_checks"] == 4
    assert result["deletable_block_ids"] == list(range(4))
    assert result["pair_checks"] == 6
    assert len(result["witness"]) == 3
    assert verify_cover(result["witness"], v=4, k=3, t=2)["valid"]


def test_exchange_rejects_incomplete_incumbent():
    universe = Universe.build(v=4, k=2, t=2)
    with pytest.raises(ValueError, match="incumbent"):
        run_exchange_search(universe, universe.blocks[:-1], attempts=1, remove=3)


def test_audit_rejects_incomplete_incumbent():
    universe = Universe.build(v=4, k=2, t=2)
    with pytest.raises(ValueError, match="incumbent"):
        audit_small_exchanges(universe, universe.blocks[:-1])


def test_zero_attempts_preserves_checked_incumbent():
    universe = Universe.build(v=4, k=2, t=2)
    result = run_exchange_search(universe, universe.blocks, attempts=0, remove=3)

    assert result["status"] == "no_improvement"
    assert result["initial_block_count"] == result["final_block_count"] == 6
    assert result["completed_attempts"] == 0
    assert result["attempts"] == []
    assert result["witness"] is None
    assert result["verification"]["valid"]


@pytest.mark.parametrize(
    "parameters",
    [
        {"attempts": -1},
        {"remove": 2},
        {"remove": 7},
        {"seconds_per_attempt": 0},
    ],
)
def test_exchange_rejects_invalid_parameters(parameters):
    universe = Universe.build(v=4, k=3, t=2)
    with pytest.raises(ValueError):
        run_exchange_search(universe, universe.blocks, **parameters)
