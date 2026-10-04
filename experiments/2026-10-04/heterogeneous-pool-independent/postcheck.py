# Document:    Independent Heterogeneous Pool Result Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      16a228eb22ec9a3e793fd909212cc7c5a8799b73eeb98158684b4723d0f3302d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay the two saved CP responses and witness receipts without solving."""

import importlib.util
import json
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pool_independent_gate", HERE / "check.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ROOT = gate.ROOT
TARGET = gate.TARGET
RAW = ROOT / "experiments/scratch/heterogeneous-pool-20261004"


def check_response(response, model, record, pool):
    assert response.status == cp_model_pb2.FEASIBLE and record["status"] == "FEASIBLE"
    values = list(response.solution)
    assert len(values) == 4928 and set(values) <= {0, 1}
    ids = [i for i in range(4368) if values[i]]
    assert len(ids) == 64 and set(ids) <= set(pool)
    profile = gate.profile(ids)
    assert [i for i in range(560) if values[4368 + i]] == profile["holes"]
    assert response.objective_value == len(profile["holes"]) == record["best_holes"] == 3
    assert response.best_objective_bound == record["objective_bound"] == 0
    assert abs(response.wall_time - record["seconds"]) < 0.1
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
    gate_path = HERE / "gate.json"
    manifest = json.loads(manifest_path.read_text())
    result = json.loads(result_path.read_text())
    start = json.loads((RAW / "start.json").read_text())
    receipts_path = TARGET / "verifiers.json"
    receipts = json.loads(receipts_path.read_text())
    inventory = json.loads(
        (ROOT / "experiments/2026-10-04/heterogeneous-seed-inventory/inventory.json").read_text()
    )
    core = [
        tuple(map(int, row.split()))
        for row in (ROOT / inventory["core_path"]).read_text().splitlines()
    ]
    known_cores = {
        entry["name"]: {
            gate.RANK[tuple(sorted(entry["known_checked_core_map_images"][p - 1] for p in block))]
            for block in core
        }
        for entry in inventory["entries"]
        if entry["known_checked_core_map_images"] is not None
    }
    assert gate.digest(manifest_path) == gate.MANIFEST_SHA == result["manifest_sha256"]
    assert gate.digest(gate_path) == result["gate_sha256"] == start["gate_sha256"]
    assert start["manifest_sha256"] == gate.MANIFEST_SHA
    assert gate.digest(TARGET / "run.py") == manifest["source_sha256"]
    assert len(result["cases"]) == len(receipts) == 2
    assert not (RAW / "stderr.log").read_text()
    reports = []
    models = []
    responses = []
    for offset, (case, record, receipt) in enumerate(
        zip(manifest["cases"], result["cases"], receipts, strict=True)
    ):
        name = case["name"]
        assert name == record["name"] == receipt["case"]
        model_path = ROOT / case["model_path"]
        assert gate.digest(model_path) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format(model_path.read_text())
        gate.check_model(model, case["pool"], manifest["hint"])
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse((RAW / f"{name}-parameters.pbtxt").read_text(), params)
        assert params.max_time_in_seconds == 30 and params.num_search_workers == 4
        assert params.random_seed == 2026104091 + offset
        assert params.log_search_progress and not params.log_to_stdout
        expected_params = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=30,
            num_search_workers=4,
            random_seed=2026104091 + offset,
            log_search_progress=True,
            log_to_stdout=False,
        )
        assert params == expected_params
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((RAW / f"{name}-response.pbtxt").read_text(), response)
        ids = check_response(response, model, record, case["pool"])
        final_path = HERE / f"{name}-final-response.txt"
        final_path.write_text("".join(" ".join(map(str, gate.BLOCKS[i])) + "\n" for i in ids))
        final_receipts = {}
        for label, command in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
        ]:
            proc = subprocess.run(
                command + [str(final_path), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(proc.stdout)
            assert proc.returncode == 1 and not proc.stderr and not report["valid"]
            assert report["blocks"] == 64 and report["canonical_sha256"] == gate.digest(final_path)
            assert report["uncovered"] == [
                list(gate.TRIPLES[i]) for i in gate.profile(ids)["holes"]
            ]
            output = HERE / f"{name}-final-response-{label}.json"
            output.write_text(proc.stdout)
            final_receipts[label] = {
                "path": str(output.relative_to(ROOT)),
                "sha256": gate.digest(output),
            }
        assert len(record["improvements"]) == 1
        saved = record["improvements"][0]
        path = ROOT / saved["path"]
        assert gate.parse_seed(path) == manifest["hint"] == saved["ids"]
        assert gate.digest(path) == saved["sha256"] == receipt["sha256"]
        assert saved["profile"] == gate.profile(saved["ids"])
        assert saved["objective"] == receipt["expected_holes"] == 3
        assert receipt["path"] == saved["path"]
        for checker in receipt["checks"].values():
            report_path = ROOT / checker["output"]
            assert gate.digest(report_path) == checker["sha256"]
            report = json.loads(report_path.read_text())
            assert checker["exit_code"] == 1 and not report["valid"]
            assert report["blocks"] == 64 and report["canonical_sha256"] == saved["sha256"]
            assert report["uncovered"] == [list(gate.TRIPLES[i]) for i in saved["profile"]["holes"]]
        log = (RAW / f"{name}-solver.log").read_text()
        assert log.count("Starting CP-SAT solver") == 1
        assert log.count("CpSolverResponse summary:") == 1
        assert "status: FEASIBLE" in log
        models.append(model)
        responses.append(response)
        reports.append(
            {
                "name": name,
                "status": record["status"],
                "holes": 3,
                "saved_best_same_as_initial_hint": True,
                "final_response_same_as_initial_hint": ids == manifest["hint"],
                "final_response_path": str(final_path.relative_to(ROOT)),
                "final_response_sha256": gate.digest(final_path),
                "final_response_profile": gate.profile(ids),
                "known_core_overlaps": {
                    name: len(set(ids) & values) for name, values in known_cores.items()
                },
                "saved_seed_common_blocks": {
                    Path(s["path"]).stem: len(set(ids) & set(s["ids"])) for s in manifest["sources"]
                },
                "matching_histogram_sources": [
                    Path(s["path"]).stem
                    for s in manifest["sources"]
                    if all(
                        s[key] == gate.profile(ids)[key]
                        for key in ("degree_histogram", "pair_histogram", "triple_histogram")
                    )
                ],
                "final_response_verifiers": final_receipts,
                "configured_seconds": 30,
                "observed_seconds": record["seconds"],
                "response_wall_time": response.wall_time,
                "workers": 4,
                "objective_bound": 0,
                "sha256": saved["sha256"],
            }
        )
    controls = []
    for name, mutate in [
        (
            "selected_block",
            lambda r: r.solution.__setitem__(next(i for i in range(4368) if r.solution[i]), 0),
        ),
        ("hole_bit", lambda r: r.solution.__setitem__(4368, 1)),
        ("objective", lambda r: setattr(r, "objective_value", 2)),
        ("bound", lambda r: setattr(r, "best_objective_bound", 1)),
        ("status", lambda r: setattr(r, "status", cp_model_pb2.UNKNOWN)),
    ]:
        damaged = cp_model_pb2.CpSolverResponse()
        damaged.CopyFrom(responses[0])
        mutate(damaged)
        assert gate.reject(
            lambda: check_response(
                damaged, models[0], result["cases"][0], manifest["cases"][0]["pool"]
            )
        )
        controls.append(name)
    audit = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": gate.digest(Path(__file__)),
        "independent_gate_checker_sha256": gate.digest(HERE / "check.py"),
        "manifest_sha256": gate.MANIFEST_SHA,
        "result_sha256": gate.digest(result_path),
        "gate_sha256": gate.digest(gate_path),
        "verifiers_sha256": gate.digest(receipts_path),
        "cases": reports,
        "damaged_controls_rejected": controls,
        "raw_sha256": {p.name: gate.digest(p) for p in sorted(RAW.iterdir()) if p.is_file()},
        "scope": "No improvement. FEASIBLE with bound zero leaves both pools inconclusive.",
    }
    gate.dump(HERE / "postcheck.json", audit)
    print(json.dumps({"passed": True, "sha256": gate.digest(HERE / "postcheck.json")}))


if __name__ == "__main__":
    main()
