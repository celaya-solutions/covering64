import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model


@pytest.mark.parametrize("cut_family", ["feature", "facet"])
def test_mismatched_proof_rejected_before_output(tmp_path, cut_family):
    script = Path(__file__).parents[1] / "scripts" / "four_seven_link_lp.py"
    proof = tmp_path / "damaged-proof.json"
    proof.write_text("{}\n")
    output = tmp_path / "screen"
    result = subprocess.run(
        [sys.executable, str(script), "--representatives", str(tmp_path / "absent.json"),
         "--output", str(output), f"--{cut_family}-cuts", f"--{cut_family}-proof", str(proof)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert f"{cut_family} proof hash does not match" in result.stderr
    assert not output.exists()


@pytest.mark.parametrize("counts", [["--four-hub-blocks", "0"],
                                   ["--double-hub-triples", "1"],
                                   ["--four-hub-blocks", "2", "--double-hub-triples", "4"]])
def test_partial_or_impossible_hub_case_rejected_before_output(tmp_path, counts):
    script = Path(__file__).parents[1] / "scripts" / "four_seven_link_lp.py"
    output = tmp_path / "screen"
    result = subprocess.run(
        [sys.executable, str(script), "--representatives", str(tmp_path / "absent.json"),
         "--output", str(output), *counts],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert "must be supplied together" in result.stderr or "six exhaustive" in result.stderr
    assert not output.exists()


@pytest.fixture(scope="module")
def screen():
    scripts = Path(__file__).parents[1] / "scripts"
    spec = importlib.util.spec_from_file_location(
        "four_seven_link_lp", scripts / "four_seven_link_lp.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(scripts))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(scripts))
    return module


def test_phase_one_duals_certify_conflicting_rows(screen):
    rows = [((0,), (1,), 1, 1), ((0,), (1,), 0, 0)]
    assert screen.solve_lp(rows, 1, 5)["status"] == pywraplp.Solver.INFEASIBLE
    phase = screen.solve_lp(rows, 1, 5, phase_one=True)
    assert phase["status"] == pywraplp.Solver.OPTIMAL
    assert phase["objective"] == pytest.approx(1)
    cert = screen.exact_certificate(rows, 1, phase["weights"])
    assert cert["proves_infeasible"]
    assert cert["gap"] == [1, 1]
    assert not screen.exact_certificate(rows, 1, [0, 0])["proves_infeasible"]
    restricted = screen.solve_lp(rows, 1, 5, phase_one=True, soft_rows=[0])
    assert restricted["objective"] == pytest.approx(1)
    assert screen.exact_certificate(rows, 1, restricted["weights"])["gap"] == [1, 1]


def test_box_bound_and_damaged_rhs_control(screen):
    rows = [((0,), (1,), 2, None)]
    phase = screen.solve_lp(rows, 1, 5, phase_one=True)
    cert = screen.exact_certificate(rows, 1, phase["weights"])
    assert cert["proves_infeasible"]
    assert cert["gap"] == [1, 1]
    changed = [((0,), (1,), 1, None)]
    assert not screen.exact_certificate(changed, 1, phase["weights"])["proves_infeasible"]


def test_feasible_phase_one_and_invalid_weights(screen):
    rows = [((0,), (1,), 1, None)]
    phase = screen.solve_lp(rows, 1, 5, phase_one=True)
    assert phase["objective"] == pytest.approx(0)
    assert not screen.exact_certificate(rows, 1, phase["weights"])["proves_infeasible"]
    for weights in ([], [float("nan")], [float("inf")], [-1]):
        with pytest.raises(ValueError):
            screen.exact_certificate(rows, 1, weights)


def test_only_boolean_unconditional_linear_models_accepted(screen):
    model = cp_model.CpModel()
    x = model.new_bool_var("x")
    model.add(x == 1)
    rows, width = screen.linear_rows(model)
    assert width == 1
    assert rows == [((0,), (1,), 1, 1)]
    model.add(x == 0).only_enforce_if(x)
    with pytest.raises(ValueError):
        screen.linear_rows(model)
    other = cp_model.CpModel()
    y = other.new_int_var(0, 2, "y")
    other.add(y <= 1)
    with pytest.raises(ValueError):
        screen.linear_rows(other)
    nonlinear = cp_model.CpModel()
    z = nonlinear.new_bool_var("z")
    nonlinear.add_bool_or([z])
    before = str(nonlinear.proto)
    with pytest.raises(ValueError):
        screen.linear_rows(nonlinear)
    assert str(nonlinear.proto) == before


def test_damaged_denominator_and_row_controls(screen):
    rows = [((0,), (1,), 0, 1)]
    for denominator in (-1, 0, True, 1.0):
        with pytest.raises(ValueError):
            screen.exact_certificate(rows, 1, [1.0], denominator)
    damaged = [
        ((0, 1), (1,), 0, 1),
        ((0, 0), (1, 1), 0, 1),
        ((-1,), (1,), 0, 1),
        ((1,), (1,), 0, 1),
        ((True,), (1,), 0, 1),
        ((0,), (1.0,), 0, 1),
        ((0,), (1,), 2, 1),
        ((0,), (1,), 0, float("inf")),
    ]
    for row in damaged:
        with pytest.raises(ValueError):
            screen.exact_certificate([row], 1, [1.0])
        with pytest.raises(ValueError):
            screen.solve_lp([row], 1, 1)
    for bad in ([-1], [1], [True], [0, 0]):
        with pytest.raises(ValueError):
            screen.solve_lp(rows, 1, 1, phase_one=True, soft_rows=bad)
    with pytest.raises(ValueError):
        screen.solve_lp(rows, 1, 1, soft_rows=[0])
