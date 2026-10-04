#!/usr/bin/env python3
# Document:    Independent Maximum Margin Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay every saved model, exact margin, LP vector and learned support plane."""

import importlib.util
import json
import math
from collections import Counter
from fractions import Fraction

from check import HERE, HIGH, PLANES, RAW, SCALE, SOURCE, build_expected, encoded, sha
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    gate = json.loads((HERE / "audit.json").read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    result = json.loads((SOURCE / "result.json").read_text())
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "audit.json")
    assert result["source_sha256"] == gate["source_sha256"] == sha(SOURCE / "run.py")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert sha(PLANES) == gate["checked_planes_sha256"]
    for relative, expected_hash in result["raw_sha256"].items():
        assert sha(RAW / relative) == expected_hash
    basis_path = HERE.parent / "lp-guided-complete-sweep-independent/basis.py"
    spec = importlib.util.spec_from_file_location("independent_completion_basis", basis_path)
    basis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(basis)
    blocks, _, ordinary, heavy, rows = basis.rebuild()
    cuts = json.loads(PLANES.read_text())
    records, checked, seen = result["records"], [], set()
    assert len(records) <= 20 and result["initial_cuts"] == 333
    assert result["combined_solver_seconds"] <= 80 and result["wall_seconds"] <= 100
    assert result["budget"] == manifest["budget"]
    total_solver, best = 0.0, result["initial_objective"]
    best_ids = manifest["baseline_heavy_global_ids"]
    for step, record in enumerate(records):
        directory = RAW / f"step-{step:03d}"
        expected, global_ids, planes, upper = build_expected(cuts)
        assert global_ids == [blocks.index(block) for block in heavy]
        actual = text_format.Parse((directory / "master.pbtxt").read_text(),
                                   cp_model_pb2.CpModelProto())
        assert record["step"] == step and sha(directory / "master.pbtxt") == record["master_sha256"]
        assert encoded(actual) == encoded(expected)
        assert record["cut_count"] == len(cuts) == 333 + len(checked)
        assert record["safe_margin_upper_units"] == upper
        assert len(actual.constraints) == 938 + len(checked)
        parameters = text_format.Parse((directory / "parameters.pbtxt").read_text(),
                                       sat_parameters_pb2.SatParameters())
        expected_parameters = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=3, num_search_workers=1, random_seed=2026104064 + step,
            randomize_search=True, log_search_progress=True, log_to_stdout=False)
        assert encoded(parameters) == encoded(expected_parameters)
        response = text_format.Parse((directory / "response.pbtxt").read_text(),
                                     cp_model_pb2.CpSolverResponse())
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == record["master_status"]
        total_solver += record["master_seconds"]
        assert record["seed"] == 2026104064 + step
        assert response.wall_time == record["master_reported_seconds"]
        if record["master_status"] not in ("OPTIMAL", "FEASIBLE"):
            assert step == len(records) - 1 and result["stop_reason"] == "master_without_candidate"
            continue
        ids = record["heavy_global_ids"]
        selected = {global_ids.index(index) for index in ids}
        assert len(selected) == 28 and tuple(ids) not in seen
        seen.add(tuple(ids))
        values = list(response.solution)
        assert values[:276] == [int(i in selected) for i in range(276)] and len(values) == 277
        for row in actual.constraints:
            activity = sum(coefficient * values[index] for index, coefficient
                           in zip(row.linear.vars, row.linear.coeffs, strict=True))
            assert row.linear.domain[0] <= activity <= row.linear.domain[1]
        margin = min(sum(coefficients[i] for i in selected) - rhs for coefficients, rhs in planes)
        achieved = values[276]
        assert 0 <= achieved <= margin <= upper
        assert achieved == record["margin_units"] == response.objective_value
        assert margin == record["actual_minimum_margin_units"]
        assert response.best_objective_bound == record["margin_bound_units"] >= achieved
        if record["master_status"] == "OPTIMAL":
            assert achieved == margin and response.best_objective_bound == achieved
        shifted = basis.shifted(rows, heavy, [heavy[i] for i in sorted(selected)])
        assert shifted == json.loads((directory / "completion-rows.json").read_text())
        assert basis.digest([heavy[i] for i in sorted(selected)]) == record["heavy_sha256"]
        numerical = record["lp"]
        total_solver += numerical["seconds"]
        primal = json.loads((directory / "numerical-primal.json").read_text())
        dual_values = json.loads((directory / "numerical-dual.json").read_text())
        assert len(primal) == len(ordinary) == 1200
        assert all(math.isfinite(v) and -1e-7 <= v <= 1 + 1e-7 for v in primal)
        assert len(dual_values) == 697 and all(math.isfinite(v) for v in dual_values)
        residual = 0.0
        for indices, coefficients, lower, upper_bound in shifted:
            activity = math.fsum(coefficient * primal[index] for index, coefficient
                                 in zip(indices, coefficients, strict=True))
            residual += max(0.0, lower - activity)
            if upper_bound != HIGH:
                residual += max(0.0, activity - upper_bound)
        assert abs(residual - numerical["recomputed_l1_residual"]) <= 1e-6
        assert residual <= numerical["objective"] + 1e-6
        if numerical["status"] == "OPTIMAL":
            assert abs(residual - numerical["objective"]) <= 1e-6
            if numerical["objective"] < best - 1e-7:
                best, best_ids = numerical["objective"], ids
        cut = json.loads((directory / "learned-cut.json").read_text())
        assert record["learned_cut_sha256"] == sha(directory / "learned-cut.json")
        dual = cut["dual"]
        weights, used = [0] * 697, set()
        assert dual["denominator"] == cut["denominator"] == SCALE
        for row_id, weight in dual["weights"]:
            assert type(row_id) is int and 0 <= row_id < 697 and row_id not in used
            assert type(weight) is int and 0 < abs(weight) <= SCALE
            assert weight >= 0 or rows[row_id][3] != HIGH
            used.add(row_id)
            weights[row_id] = weight
        ordinary_coefficients = [sum(weights[r] for r, row in enumerate(rows) if i in row[0])
                                 for i in range(1200)]
        heavy_coefficients = [sum(weights[r] for r, row in enumerate(rows) if i in row[1])
                              for i in range(276)]
        constant = sum(w * (rows[r][2] if w > 0 else rows[r][3])
                       for r, w in enumerate(weights) if w)
        box = sum(max(0, value) for value in ordinary_coefficients)
        lhs = sum(heavy_coefficients[i] for i in selected)
        assert cut["ordinary_coefficients"] == ordinary_coefficients
        assert cut["coefficients"] == heavy_coefficients
        assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
            constant, box, lhs, constant - box)
        assert (dual["rhs_numerator"], dual["box_max_numerator"]) == (constant - lhs, box)
        gap = Fraction(constant - box - lhs, SCALE)
        assert gap > 0 and dual["proves_infeasible"]
        assert dual["gap"] == record["gap"] == [gap.numerator, gap.denominator]
        cuts.append(cut)
        checked.append({"step": step, "margin_units": achieved,
                        "actual_minimum_margin_units": margin, "residual": residual,
                        "master_status": record["master_status"], "gap": dual["gap"],
                        "distance_from_baseline": 28 - len(set(ids) & set(
                            manifest["baseline_heavy_global_ids"])),
                        "learned_cut_sha256": sha(directory / "learned-cut.json")})
    assert len(checked) == result["new_cuts"]
    assert abs(total_solver - result["combined_solver_seconds"]) < 1e-6
    assert best == result["best_objective"] and best_ids == result["best_heavy_global_ids"]
    report = {"passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
              "gate_sha256": sha(HERE / "audit.json"), "result_sha256": sha(SOURCE / "result.json"),
              "basis_sha256": sha(basis_path), "incremental_models_checked": len(records),
              "new_planes_checked": len(checked), "total_checked_planes": len(cuts),
              "actual_best_objective": best, "combined_solver_seconds": total_solver,
              "wall_seconds": result["wall_seconds"],
              "master_status_counts": dict(Counter(r["master_status"] for r in records)),
              "results": checked, "scope": "Exact bounded pilot replay in fixed-anchor family."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
