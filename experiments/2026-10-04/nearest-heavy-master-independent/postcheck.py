# Document:    Independent Replay of the Nearest-Heavy Campaign
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1c0b43a68cc91f059342be9f26d54c8d0e1cedfc2ad5bfb0e1bb06fbd474e2ba
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay incremental masters, shifted rows, vectors, and exact separating cuts."""

import hashlib
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "nearest-heavy-master"
RAW = ROOT / "experiments/scratch/nearest-heavy-master-20261004"
HIGH = 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(model):
    return model.SerializeToString(deterministic=True)


def main():
    assert not (HERE / "postcheck.json").exists()
    gate = json.loads((HERE / "audit.json").read_text())
    report = json.loads((SOURCE / "result.json").read_text())
    assert gate["passed"] and report["gate_sha256"] == sha(HERE / "audit.json")
    assert report["source_sha256"] == gate["source_sha256"] == sha(SOURCE / "run.py")
    assert report["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    for relative, expected_hash in report["raw_sha256"].items():
        assert sha(RAW / relative) == expected_hash
    assert sha(RAW / "master.pbtxt") == gate["master_sha256"]
    expected = text_format.Parse((RAW / "master.pbtxt").read_text(), cp_model_pb2.CpModelProto())
    basis_path = HERE.parent / "lp-guided-complete-sweep-independent/basis.py"
    spec = importlib.util.spec_from_file_location("independent_completion_basis", basis_path)
    basis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(basis)
    blocks, _, ordinary, heavy, rows = basis.rebuild()
    gids = [blocks.index(block) for block in heavy]
    records = report["records"]
    assert len(records) <= 100 and report["initial_cuts"] == 238
    assert report["combined_solver_seconds"] <= 180 and report["wall_seconds"] <= 240
    checked, cumulative_solver, best = [], 0.0, report["initial_objective"]
    for step, record in enumerate(records):
        directory = RAW / f"step-{step:03d}"
        assert record["step"] == step and sha(directory / "master.pbtxt") == record["master_sha256"]
        actual = text_format.Parse((directory / "master.pbtxt").read_text(),
                                  cp_model_pb2.CpModelProto())
        assert encoded(actual) == encoded(expected)
        assert len(actual.constraints) == 843 + len(checked)
        params = text_format.Parse((directory / "parameters.pbtxt").read_text(),
                                  sat_parameters_pb2.SatParameters())
        ep = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=2, num_search_workers=1, random_seed=2026104063 + step,
            randomize_search=True, log_search_progress=True, log_to_stdout=False)
        assert encoded(params) == encoded(ep)
        response = text_format.Parse((directory / "response.pbtxt").read_text(),
                                     cp_model_pb2.CpSolverResponse())
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == record["master_status"]
        cumulative_solver += record["master_seconds"]
        if record["master_status"] not in ("OPTIMAL", "FEASIBLE"):
            assert step == len(records) - 1 and report["stop_reason"] == "master_without_candidate"
            continue
        selected = {gids.index(index) for index in record["heavy_global_ids"]}
        assert len(selected) == 28 and record["cut_count"] == 238 + len(checked)
        assert list(response.solution) == [int(i in selected) for i in range(276)]
        for row in actual.constraints:
            value = sum(c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
                        if i in selected)
            assert row.linear.domain[0] <= value <= row.linear.domain[1]
        distance = 28 - len(set(record["heavy_global_ids"]) &
                            set(json.loads((SOURCE / "manifest.json").read_text())[
                                "baseline_heavy_global_ids"]))
        assert distance == response.objective_value == record["distance_replacements"]
        shifted = basis.shifted(rows, heavy, [heavy[i] for i in selected])
        assert shifted == json.loads((directory / "completion-rows.json").read_text())
        numerical = record["lp"]
        cumulative_solver += numerical["seconds"]
        values = json.loads((directory / "numerical-primal.json").read_text())
        assert len(values) == len(ordinary) == 1200
        assert all(math.isfinite(value) and -1e-7 <= value <= 1 + 1e-7 for value in values)
        residual = 0.0
        for ids, coefficients, lower, upper in shifted:
            value = math.fsum(c * values[i] for i, c in zip(ids, coefficients, strict=True))
            residual += max(0.0, lower - value)
            if upper != HIGH:
                residual += max(0.0, value - upper)
        assert abs(residual - numerical["recomputed_l1_residual"]) <= 1e-6
        assert residual <= numerical["objective"] + 1e-6
        if numerical["status"] == "OPTIMAL":
            assert abs(residual - numerical["objective"]) <= 1e-6
            best = min(best, numerical["objective"])
        cut = json.loads((directory / "learned-cut.json").read_text())
        assert record["learned_cut_sha256"] == sha(directory / "learned-cut.json")
        dual = cut["dual"]
        indices = [index for index, _ in dual["weights"]]
        assert indices == sorted(set(indices)) and dual["denominator"] == 1_000_000
        oc, hc, constant = [0] * 1200, [0] * 276, 0
        for row_id, weight in dual["weights"]:
            assert type(row_id) is int and 0 <= row_id < 697
            assert type(weight) is int and weight
            oi, hi, lower, upper = rows[row_id]
            bound = lower if weight > 0 else upper
            assert abs(bound) < 2**60
            constant += weight * bound
            for index in oi:
                oc[index] += weight
            for index in hi:
                hc[index] += weight
        box, lhs = sum(max(0, c) for c in oc), sum(hc[i] for i in selected)
        rhs = constant - box
        assert (cut["coefficients"], cut["ordinary_coefficients"]) == (hc, oc)
        assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
            constant, box, lhs, rhs)
        assert (dual["rhs_numerator"], dual["box_max_numerator"]) == (constant - lhs, box)
        gap = Fraction(rhs - lhs, dual["denominator"])
        assert gap > 0 and dual["proves_infeasible"]
        assert dual["gap"] == record["gap"] == [gap.numerator, gap.denominator]
        row = expected.constraints.add().linear
        for index, coefficient in enumerate(hc):
            if coefficient:
                row.vars.append(index)
                row.coeffs.append(coefficient)
        row.domain.extend([rhs, HIGH])
        checked.append({"step": step, "gap": dual["gap"], "residual": residual,
                        "master_rows": len(actual.constraints), "distance": distance})
    assert len(checked) == report["new_cuts"]
    assert abs(cumulative_solver - report["combined_solver_seconds"]) < 1e-6
    assert best == report["best_objective"]
    audit = {
        "passed": True, "checker_sha256": sha(__file__), "source_sha256": sha(SOURCE / "run.py"),
        "result_sha256": sha(SOURCE / "result.json"), "basis_sha256": sha(basis_path),
        "incremental_masters": len(records), "checked_new_cuts": len(checked),
        "completion_rows_each": 697, "total_checked_input_and_new_cuts": 238 + len(checked),
        "numerical_vectors_recounted": len(checked), "results": checked,
        "optimization_calls": 0, "scope": "Exact fixed-heavy separation and bounded-run replay.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({key: value for key, value in audit.items() if key != "results"}))


if __name__ == "__main__":
    main()
