import hashlib

import pytest
from pysat.formula import CNF
from pysat.solvers import Solver

from covering64.core import Universe, verify_cover
from covering64.exact import solve_exact, write_cnf


@pytest.fixture
def small_universe():
    # All six pairs on four points require at least three distinct triples.
    return Universe.build(v=4, k=3, t=2)


def test_cp_sat_accepts_cover_and_rejects_impossible_size(small_universe):
    feasible = solve_exact(small_universe, 3, seconds=5)
    impossible = solve_exact(small_universe, 2, seconds=5)
    assert feasible["status"] in {"FEASIBLE", "OPTIMAL"}
    assert f"status: {feasible['status']}" in feasible["response_stats"]
    assert len(feasible["witness"]) == 3
    assert verify_cover(feasible["witness"], v=4, k=3, t=2)["valid"]
    assert impossible["status"] == "INFEASIBLE"
    assert "status: INFEASIBLE" in impossible["response_stats"]
    assert impossible["witness"] is None
    assert impossible["proof_generated"] is False


def test_cp_sat_hints_do_not_restrict_the_search(small_universe):
    result = solve_exact(small_universe, 3, hint=[(4, 3, 2)], seconds=5)
    assert result["verification"]["valid"]
    assert result["settings"]["hint_blocks"] == 1
    with pytest.raises(ValueError, match="duplicate"):
        solve_exact(small_universe, 3, hint=[(1, 2, 3), (3, 2, 1)])
    with pytest.raises(ValueError, match="invalid block"):
        solve_exact(small_universe, 3, hint=[(1, 2, 5)])


@pytest.mark.parametrize("target", [0, 1, 2, 3, 4])
def test_cnf_matches_cover_feasibility(tmp_path, small_universe, target):
    output = tmp_path / f"size-{target}.cnf"
    report = write_cnf(small_universe, target, output)
    formula = CNF(from_file=str(output))
    assert report["sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    assert report["variables"] == formula.nv
    assert report["clauses"] == len(formula.clauses)
    assert report["coverage_clauses"] == 6
    with Solver(name="g3", bootstrap_with=formula) as solver:
        assert solver.solve() is (target >= 3)
        if target >= 3:
            positive = {literal for literal in solver.get_model() if literal > 0}
            witness = [block for i, block in enumerate(small_universe.blocks, 1) if i in positive]
            assert len(witness) <= target
            assert verify_cover(witness, v=4, k=3, t=2)["valid"]
            # A model can be padded to exactly target distinct blocks.
            unused = [block for block in small_universe.blocks if block not in witness]
            padded = witness + unused[: target - len(witness)]
            assert len(padded) == target
            assert verify_cover(padded, v=4, k=3, t=2)["valid"]


@pytest.mark.parametrize("target", [0, 1, 2, 3, 4])
def test_cnf_projects_to_precisely_the_allowed_covering_families(
    tmp_path, small_universe, target
):
    output = tmp_path / f"projection-{target}.cnf"
    write_cnf(small_universe, target, output)
    formula = CNF(from_file=str(output))
    with Solver(name="g3", bootstrap_with=formula) as solver:
        for mask in range(1 << len(small_universe.blocks)):
            family = [
                block for i, block in enumerate(small_universe.blocks) if mask & (1 << i)
            ]
            assumptions = [
                i + 1 if mask & (1 << i) else -(i + 1)
                for i in range(len(small_universe.blocks))
            ]
            expected = len(family) <= target and verify_cover(family, v=4, k=3, t=2)["valid"]
            assert solver.solve(assumptions=assumptions) is expected


def test_first_block_normalization_preserves_feasibility(tmp_path, small_universe):
    result = solve_exact(small_universe, 3, seconds=5, fix_first_block=True)
    assert list(small_universe.blocks[0]) in result["witness"]
    output = tmp_path / "normalized.cnf"
    report = write_cnf(small_universe, 3, output, fix_first_block=True)
    assert report["symmetry_clauses"] == 1
    with Solver(name="g3", bootstrap_with=CNF(from_file=str(output))) as solver:
        assert solver.solve()
        assert 1 in solver.get_model()


@pytest.mark.parametrize("target", [-1, 5, 1.5, True])
def test_invalid_target_is_rejected(tmp_path, small_universe, target):
    with pytest.raises(ValueError, match="target"):
        write_cnf(small_universe, target, tmp_path / "invalid.cnf")
    with pytest.raises(ValueError, match="target"):
        solve_exact(small_universe, target)


@pytest.mark.parametrize(
    "settings", [{"seconds": 0}, {"seconds": float("nan")}, {"workers": 0}, {"seed": -1}]
)
def test_invalid_solver_settings_are_rejected(small_universe, settings):
    with pytest.raises(ValueError):
        solve_exact(small_universe, 3, **settings)
