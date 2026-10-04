# Document:    Independent Six-Hole Release Result Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9fc65881a7d6d5fb8ceac952aa5a7ec799849edfe77318dfd2639cdc4ab95bfb
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit every saved state and final response without optimizer calls."""

import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("release_gate", HERE / "check.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ROOT, SOURCE, basis = gate.ROOT, gate.SOURCE, gate.basis
RAW = ROOT / "experiments/scratch/six-hole-pool-release-20261004"
read, digest, dump = gate.read, gate.digest, gate.dump


def check_response(response, model, outcome, manifest):
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == outcome["status"]
    assert response.best_objective_bound == outcome["objective_bound"]
    assert response.wall_time == outcome["reported_seconds"]
    assert abs(response.wall_time - outcome["seconds"]) < 1
    assert 0 <= response.wall_time <= 122 and 0 <= outcome["seconds"] <= 123
    if response.status == cp_model_pb2.UNKNOWN:
        assert not response.solution and not outcome["improvements"] and outcome["final"] is None
        return None
    assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
    values = list(response.solution)
    ids = [i for i in range(4368) if values[i]]
    assert values == gate.assignment(ids, manifest["partitions"])
    objective = gate.check_values(model, values)
    assert objective == response.objective_value == outcome["best_composite_objective"]
    assert 0 <= response.best_objective_bound <= objective
    assert outcome["final"]["ids"] == ids
    assert outcome["final"]["composite_objective"] == objective
    return ids


def check_state(saved, model, manifest, pool):
    path = ROOT / saved["path"]
    assert digest(path) == saved["sha256"]
    ids = basis.parse_seed(path)
    profile = basis.profile(ids)
    assert ids == saved["ids"] and profile == saved["profile"]
    assert set(ids) <= set(pool)
    overlap = len(set(ids) & set(manifest["core_rows"][0]))
    assert overlap == saved["original_core_overlap"]
    assert saved["holes"] == len(profile["holes"])
    values = gate.assignment(ids, manifest["partitions"])
    assert gate.check_values(model, values) == saved["composite_objective"]
    assert saved["composite_objective"] == 65 * len(profile["holes"]) + overlap
    return {
        "path": saved["path"],
        "sha256": digest(path),
        "ids": ids,
        "profile": profile,
        "holes": len(profile["holes"]),
        "composite_objective": saved["composite_objective"],
        "known_core_overlaps": [len(set(ids) & set(core)) for core in manifest["core_rows"]],
        "common_hint_blocks": len(set(ids) & set(manifest["hint"])),
        "all_five_heavy_scan": gate.scan(ids),
        "verifiers": gate.verify(path, ids),
    }


def witness_controls(ids):
    lines = [" ".join(map(str, basis.BLOCKS[i])) for i in ids]
    controls = []
    damaged = {
        "malformed": ["1 2 3 4 17"] + lines[1:],
        "duplicate": [lines[1]] + lines[1:],
        "damaged_cardinality": lines[:-1],
    }
    with tempfile.TemporaryDirectory(prefix="six-hole-independent-") as directory:
        for label, content in damaged.items():
            path = Path(directory) / f"{label}.txt"
            path.write_text("\n".join(content) + "\n")
            assert basis.reject(lambda: basis.parse_seed(path))
            receipts = []
            for command in (
                ["uv", "run", "covering64", "verify"],
                ["uv", "run", "python", "scripts/check_cover.py"],
            ):
                result = subprocess.run(
                    command + [str(path), "--expected-blocks", "64"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode != 0
                if result.stdout:
                    assert not json.loads(result.stdout)["valid"]
                receipts.append(
                    {
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
            controls.append({"label": label, "verifiers": receipts})
    return controls


def main():
    assert not (HERE / "postcheck.json").exists()
    manifest = read(SOURCE / "manifest.json")
    result = read(SOURCE / "result.json")
    start = read(RAW / "start.json")
    frozen_gate = read(HERE / "gate.json")
    assert frozen_gate["passed"]
    assert result["manifest_sha256"] == start["manifest_sha256"] == gate.MANIFEST_SHA
    assert digest(SOURCE / "manifest.json") == gate.MANIFEST_SHA
    assert digest(SOURCE / "run.py") == result["source_sha256"] == gate.SOURCE_SHA
    assert result["gate_sha256"] == start["gate_sha256"] == digest(HERE / "gate.json")
    assert not result["global_lower_bound_claim"]
    assert len(result["cases"]) == result["optimizer_calls"] <= 2
    assert len(result["cases"]) == 2 or result["cases"][0]["final"]["holes"] == 0
    for relative, checksum in frozen_gate["independent_sources"].items():
        assert digest(ROOT / relative) == checksum
    for mapping in (manifest["input_files"], manifest["proof_files"]):
        for relative, checksum in mapping.items():
            assert digest(ROOT / relative) == checksum
    for name, source in (
        ("run.py", SOURCE / "run.py"),
        ("manifest.json", SOURCE / "manifest.json"),
        ("gate.json", HERE / "gate.json"),
    ):
        assert (RAW / name).read_bytes() == source.read_bytes()
    reports, models, responses, all_states = [], [], [], []
    for case, outcome in zip(manifest["cases"], result["cases"]):
        assert case["name"] == outcome["name"]
        assert digest(ROOT / case["model_path"]) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format((ROOT / case["model_path"]).read_text())
        gate.check_model(
            model, case["pool"], manifest["hint"], manifest["core_rows"], manifest["partitions"]
        )
        for item in outcome["raw_files"].values():
            assert digest(ROOT / item["path"]) == item["sha256"]
        params = sat_parameters_pb2.SatParameters()
        parameter_path = ROOT / outcome["raw_files"]["parameters"]["path"]
        text_format.Parse(parameter_path.read_text(), params)
        assert digest(parameter_path) == case["parameters_sha256"]
        assert params == sat_parameters_pb2.SatParameters(
            max_time_in_seconds=120,
            num_search_workers=4,
            random_seed=2026104101,
            log_search_progress=True,
            log_to_stdout=False,
        )
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((ROOT / outcome["raw_files"]["response"]["path"]).read_text(), response)
        ids = check_response(response, model, outcome, manifest)
        saved_reports, best = [], 65 * 561 + 60
        for saved in outcome["improvements"]:
            assert saved["composite_objective"] < best
            best = saved["composite_objective"]
            checked = check_state(saved, model, manifest, case["pool"])
            saved_reports.append(checked)
            all_states.append(checked)
        final, tie = None, None
        if ids is not None:
            assert best == response.objective_value and best <= 449
            final = check_state(outcome["final"], model, manifest, case["pool"])
            assert final["ids"] == ids
            # Keep our own witness extracted directly from the native response.
            path = HERE / f"{case['name']}-final-response.txt"
            path.write_text("".join(" ".join(map(str, basis.BLOCKS[i])) + "\n" for i in ids))
            assert digest(path) == final["sha256"]
            final["independent_extraction"] = str(path.relative_to(ROOT))
            all_states.append(final)
            tie = {
                "same_objective": final["composite_objective"]
                == saved_reports[-1]["composite_objective"],
                "same_blocks": ids == saved_reports[-1]["ids"],
                "common_blocks": len(set(ids) & set(saved_reports[-1]["ids"])),
            }
        log = (ROOT / outcome["raw_files"]["log"]["path"]).read_text()
        assert log.count("Starting CP-SAT solver") == log.count("CpSolverResponse summary:") == 1
        assert f"status: {outcome['status']}" in log
        assert "random_seed: 2026104101" in log and "max_time_in_seconds: 120" in log
        assert "num_search_workers: 4" in log
        reports.append(
            {
                "name": case["name"],
                "pool_size": case["pool_size"],
                "status": outcome["status"],
                "objective_bound": response.best_objective_bound,
                "seconds": outcome["seconds"],
                "reported_seconds": response.wall_time,
                "saved": saved_reports,
                "final": final,
                "final_tie": tie,
            }
        )
        models.append(model)
        responses.append(response)
    controls = []
    if responses[0].solution:
        for label, mutate in (
            (
                "selected_block",
                lambda r: r.solution.__setitem__(next(i for i in range(4368) if r.solution[i]), 0),
            ),
            ("hole_bit", lambda r: r.solution.__setitem__(4368, 1 - r.solution[4368])),
            ("threshold_bit", lambda r: r.solution.__setitem__(4928, 1 - r.solution[4928])),
            ("objective", lambda r: setattr(r, "objective_value", r.objective_value + 1)),
            ("bound", lambda r: setattr(r, "best_objective_bound", r.best_objective_bound + 1)),
            ("status", lambda r: setattr(r, "status", cp_model_pb2.UNKNOWN)),
            ("wall_time", lambda r: setattr(r, "wall_time", r.wall_time + 1)),
        ):
            damaged = cp_model_pb2.CpSolverResponse()
            damaged.CopyFrom(responses[0])
            mutate(damaged)
            assert basis.reject(
                lambda: check_response(damaged, models[0], result["cases"][0], manifest)
            )
            controls.append(label)
    malformed_controls = witness_controls(all_states[0]["ids"]) if all_states else []
    audit = {
        "passed": True,
        "optimizer_calls": 0,
        "producer_optimizer_calls": result["optimizer_calls"],
        "checker_sha256": digest(Path(__file__)),
        "gate_checker_sha256": digest(HERE / "check.py"),
        "gate_sha256": digest(HERE / "gate.json"),
        "manifest_sha256": gate.MANIFEST_SHA,
        "result_sha256": digest(SOURCE / "result.json"),
        "cases": reports,
        "saved_and_final_states": len(all_states),
        "distinct_states": len({r["sha256"] for r in all_states}),
        "damaged_response_controls_rejected": controls,
        "malformed_witness_controls": malformed_controls,
        "all_five_heavy_obstructions": [
            {"path": r["path"], "obstructions": r["all_five_heavy_scan"]["five_heavy_obstructions"]}
            for r in all_states
            if r["all_five_heavy_scan"]["five_heavy_obstructions"]
        ],
        "raw_files": {
            str(p.relative_to(ROOT)): digest(p) for p in sorted(RAW.iterdir()) if p.is_file()
        },
        "scope": (
            "Two bounded construction pilots; UNKNOWN inconclusive. "
            "No cover or global theorem unless independently verified."
        ),
    }
    dump(HERE / "postcheck.json", audit)
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": digest(HERE / "postcheck.json"),
                "states": len(all_states),
                "obstructions": len(audit["all_five_heavy_obstructions"]),
            }
        )
    )


if __name__ == "__main__":
    main()
