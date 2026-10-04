# Document:    Independent Core-Avoiding Pool Result Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9fb19631bfea8293043ddc28e83082a90f922feeb68cf3c8a045ea5d77d7a01c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount all saved incumbents and final responses, without optimization."""

import importlib.util
import json
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("independent_core_pool", HERE / "check.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
basis = gate.basis
ROOT, TARGET = gate.ROOT, gate.TARGET
RAW = ROOT / "experiments/scratch/heterogeneous-core-pool-20261004"


def verify(path, prefix):
    ids = basis.parse_seed(path)
    profile = basis.profile(ids)
    receipts = {}
    for label, command in [
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
    ]:
        proc = subprocess.run(
            command + [str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        report = json.loads(proc.stdout)
        assert proc.returncode == int(bool(profile["holes"])) and not proc.stderr
        assert report["blocks"] == 64 and report["valid"] == (not profile["holes"])
        assert report["canonical_sha256"] == basis.digest(path)
        assert report["uncovered"] == [list(basis.TRIPLES[i]) for i in profile["holes"]]
        output = HERE / f"{prefix}-{label}.json"
        output.write_text(proc.stdout)
        receipts[label] = {"path": str(output.relative_to(ROOT)), "sha256": basis.digest(output)}
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": basis.digest(path),
        "ids": ids,
        "profile": profile,
        "verifiers": receipts,
    }


def check_response(response, model, result):
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
    values = list(response.solution)
    assert len(values) == 4928 and set(values) <= {0, 1}
    ids = [i for i in range(4368) if values[i]]
    assert len(ids) == 64
    profile = basis.profile(ids)
    assert [i for i in range(560) if values[4368 + i]] == profile["holes"]
    assert len(profile["holes"]) == response.objective_value == result["best_holes"]
    assert response.best_objective_bound == result["objective_bound"]
    assert abs(response.wall_time - result["seconds"]) < 0.2
    for row in model.proto.constraints:
        if all(values[v] if v >= 0 else not values[-v - 1] for v in row.enforcement_literal):
            total = sum(
                values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= total <= row.linear.domain[1]
    return ids


def main():
    manifest_path = TARGET / "manifest.json"
    result_path = TARGET / "result.json"
    manifest = json.loads(manifest_path.read_text())
    result = json.loads(result_path.read_text())
    start = json.loads((RAW / "start.json").read_text())
    gate_path = HERE / "gate.json"
    assert basis.digest(manifest_path) == result["manifest_sha256"] == gate.MANIFEST_SHA
    assert basis.digest(TARGET / "run.py") == manifest["source_sha256"]
    assert basis.digest(gate_path) == result["gate_sha256"] == start["gate_sha256"]
    assert start["manifest_sha256"] == gate.MANIFEST_SHA
    assert len(result["cases"]) == 2
    assert not (RAW / "stderr.log").read_text()
    reports = []
    models, responses = [], []
    for offset, (case, outcome) in enumerate(zip(manifest["cases"], result["cases"], strict=True)):
        name = case["name"]
        assert name == outcome["name"]
        model_path = ROOT / case["model_path"]
        assert basis.digest(model_path) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format(model_path.read_text())
        gate.check_model(model, case["pool"], manifest["hint"], manifest["core_rows"])
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse((RAW / f"{name}-parameters.pbtxt").read_text(), params)
        assert params == sat_parameters_pb2.SatParameters(
            max_time_in_seconds=30,
            num_search_workers=4,
            random_seed=2026104091 + offset,
            log_search_progress=True,
            log_to_stdout=False,
        )
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((RAW / f"{name}-response.pbtxt").read_text(), response)
        ids = check_response(response, model, outcome)
        path = HERE / f"{name}-final-response.txt"
        path.write_text("".join(" ".join(map(str, basis.BLOCKS[i])) + "\n" for i in ids))
        final = verify(path, f"{name}-final-response")
        final["known_core_overlaps"] = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
        final["saved_seed_common_blocks"] = {
            Path(s["path"]).stem: len(set(ids) & set(s["ids"])) for s in manifest["sources"]
        }
        best = 561
        saved_reports = []
        for index, saved in enumerate(outcome["improvements"]):
            assert saved["objective"] < best
            best = saved["objective"]
            witness = ROOT / saved["path"]
            assert basis.digest(witness) == saved["sha256"]
            checked = verify(witness, f"{name}-saved-{index}")
            assert checked["ids"] == saved["ids"]
            assert checked["profile"] == saved["profile"]
            assert len(checked["profile"]["holes"]) == saved["objective"]
            assert set(saved["ids"]) <= set(case["pool"])
            checked["known_core_overlaps"] = [
                len(set(saved["ids"]) & set(core)) for core in manifest["core_rows"]
            ]
            assert max(checked["known_core_overlaps"]) <= 59
            saved_reports.append(checked)
        assert best == outcome["best_holes"]
        log = (RAW / f"{name}-solver.log").read_text()
        assert log.count("Starting CP-SAT solver") == log.count("CpSolverResponse summary:") == 1
        assert f"status: {outcome['status']}" in log
        reports.append(
            {
                "name": name,
                "status": outcome["status"],
                "best_holes": best,
                "objective_bound": outcome["objective_bound"],
                "observed_seconds": outcome["seconds"],
                "response_wall_time": response.wall_time,
                "saved": saved_reports,
                "final": final,
            }
        )
        models.append(model)
        responses.append(response)
    controls = []
    for name, mutate in [
        (
            "selected_block",
            lambda r: r.solution.__setitem__(next(i for i in range(4368) if r.solution[i]), 0),
        ),
        ("hole_bit", lambda r: r.solution.__setitem__(4368, 1 - r.solution[4368])),
        ("objective", lambda r: setattr(r, "objective_value", r.objective_value + 1)),
        ("status", lambda r: setattr(r, "status", cp_model_pb2.UNKNOWN)),
    ]:
        damaged = cp_model_pb2.CpSolverResponse()
        damaged.CopyFrom(responses[0])
        mutate(damaged)
        assert basis.reject(lambda: check_response(damaged, models[0], result["cases"][0]))
        controls.append(name)
    audit = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": basis.digest(Path(__file__)),
        "gate_checker_sha256": basis.digest(HERE / "check.py"),
        "gate_sha256": basis.digest(gate_path),
        "manifest_sha256": gate.MANIFEST_SHA,
        "result_sha256": basis.digest(result_path),
        "cases": reports,
        "damaged_controls_rejected": controls,
        "raw_sha256": {p.name: basis.digest(p) for p in sorted(RAW.iterdir()) if p.is_file()},
        "scope": "Restricted pools with two declared core-avoidance rows; no unrestricted claim.",
    }
    basis.dump(HERE / "postcheck.json", audit)
    print(json.dumps({"passed": True, "sha256": basis.digest(HERE / "postcheck.json")}))


if __name__ == "__main__":
    main()
