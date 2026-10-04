# Document:    H6 Two Point Star Independent Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      76c76d60f8d63004524bf500e74f755aa6cc687cb1435d5d07d761e0d9547bb7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Verify saved runtime evidence without solver or subprocess calls."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model, cp_model_helper

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-two-point-star-repair"
RAW = ROOT / "experiments/scratch/h6-two-point-star-repair-20261004"
GATE = HERE.parent / "h6-two-point-star-repair-independent/gate.json"
GATE_SHA = "7e52c187e94ee9a5761e65fbe5912230cbf00f7cd2048df49b0f5adb7a7000aa"
MANIFEST_SHA = "29014890a28ed880861ced497d635d8d0ec75b6b5e815cac2e068ac0c2dc60dc"
RUNNER_SHA = "b177c7986a8c35b03013f3bd8da18102151794a52d564c938033cf2a1e2943fd"
MODEL_SHA = "32f04e29da51daa7983f2f64b75b966fe5779eae0e830df1ef5af5d4434d0814"
PARAMS_SHA = "871be3961403e8ebdede9b54e4c3bc69038cdbd499799907f02661a4a0615db0"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
PAIRS = tuple(itertools.combinations(range(1, 17), 2))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def normalized(value):
    return json.loads(json.dumps(value))


def errors(proto, values):
    assert len(values) == len(proto.variables)
    assert all(type(v) is int for v in values)
    found = []
    for i, (variable, value) in enumerate(zip(proto.variables, values)):
        bounds = list(variable.domain)
        if not any(a <= value <= b for a, b in zip(bounds[::2], bounds[1::2])):
            found.append(["domain", i])
    for i, row in enumerate(proto.constraints):
        assert row.has_linear()
        if all(values[e] if e >= 0 else not values[-e - 1] for e in row.enforcement_literal):
            amount = sum(values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs))
            bounds = list(row.linear.domain)
            if not any(a <= amount <= b for a, b in zip(bounds[::2], bounds[1::2])):
                found.append(["row", i])
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-sha256", required=True)
    args = parser.parse_args()
    assert sha(GATE) == GATE_SHA and read(GATE)["passed"] and read(GATE)["decision"] == "GO"
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "run.py") == RUNNER_SHA
    assert sha(PRODUCER / "result.json") == args.result_sha256
    manifest = read(PRODUCER / "manifest.json")
    result = read(PRODUCER / "result.json")
    for group in ("dependencies", "prepared_files"):
        for path, digest in manifest[group].items():
            assert sha(ROOT / path) == digest
    assert sha(RAW / "model.pbtxt") == MODEL_SHA
    assert sha(RAW / "parameters.pbtxt") == PARAMS_SHA
    assert sha(GATE.parent / "checks.json") == (
        "26b7a58dc545e662faec521a6493905b93938db898cbb51f473fc9225a377470"
    )
    assert result["manifest_sha256"] == MANIFEST_SHA and result["gate_sha256"] == GATE_SHA
    assert result["calls"] == 1 and result["relaunch"] is False
    assert result["command"] == [sys.executable, str(PRODUCER / "run.py"), "--child", str(GATE)]
    assert result["scope"] == manifest["scope"]
    output = RAW / "run-1"
    assert sorted(p.name for p in RAW.glob("run-*")) == ["run-1"]
    assert read(output / "launch.json") == {
        "gate_sha256": GATE_SHA,
        "manifest_sha256": MANIFEST_SHA,
    }
    assert read(output / "child-started.json") == {"one_call": True, "gate_sha256": GATE_SHA}
    assert sha(output / "parameters.pbtxt") == PARAMS_SHA
    actual_raw = {str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*")) if p.is_file()}
    assert result["raw_files"] == actual_raw
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((RAW / "model.pbtxt").read_text()) and not model.validate()
    initial = read(RAW / "initial-vector.json")["values"]
    assert errors(model.proto, initial) == [["row", 1164], ["row", 1175], ["row", 1221]]
    relaxed = cp_model.CpModel()
    relaxed.proto.copy_from(model.proto)
    for row in (1164, 1175, 1221):
        relaxed.proto.constraints[row].linear.domain[0] = 4
    assert not errors(relaxed.proto, initial)
    damage_controls = []
    for name, index, value in [
        ("bool", 0, True),
        ("float", 0, 0.0),
        ("outside_domain", 0, 2),
        ("hole_flag_flipped", 4368 + initial[4368:].index(1), 0),
        ("covered_flag_flipped", 4368 + initial[4368:].index(0), 1),
    ]:
        damaged = list(initial)
        damaged[index] = value
        try:
            assert not errors(relaxed.proto, damaged)
        except AssertionError:
            damage_controls.append(name)
        else:
            raise AssertionError(f"accepted damage: {name}")
    for name, damaged in [("short", initial[:4927]), ("long", [*initial, 0])]:
        try:
            errors(relaxed.proto, damaged)
        except AssertionError:
            damage_controls.append(name)
        else:
            raise AssertionError(f"accepted damage: {name}")

    standalone_path = ROOT / "scripts/check_cover.py"
    spec = importlib.util.spec_from_file_location("standalone_h6_star_runtime", standalone_path)
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    callback_paths = sorted(output.glob("callback-*.json"))
    assert [p.name for p in callback_paths] == [
        f"callback-{i:03}.json" for i in range(1, len(callback_paths) + 1)
    ]
    paths = list(callback_paths)
    final_path = output / "final-vector.json"
    if final_path.exists():
        paths.append(final_path)
    assert [row["vector"] for row in result["saved"]] == [str(p.relative_to(ROOT)) for p in paths]
    checked = []
    for path, saved in zip(paths, result["saved"]):
        values = read(path)["values"]
        assert not errors(model.proto, values)
        ids = [i for i in range(4368) if values[i]]
        blocks = [BLOCKS[i] for i in ids]
        assert len(blocks) == 64
        triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
        pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
        holes = [t for t in TRIPLES if triples[t] == 0]
        assert values[4368:] == [int(triples[t] == 0) for t in TRIPLES]
        assert len(holes) <= 6 and min(pairs[p] for p in PAIRS) >= 5
        assert all(
            values[i] == initial[i] for i, b in enumerate(BLOCKS) if not {6, 10}.intersection(b)
        )
        witness = output / (path.stem + ".txt")
        canonical = "".join(" ".join(map(str, b)) + "\n" for b in blocks).encode()
        assert witness.read_bytes() == canonical
        assert saved["witness"] == str(witness.relative_to(ROOT))
        assert saved["sha256"] == sha(witness) and saved["holes"] == len(holes)
        package = normalized(verify_cover(blocks))
        external = normalized(standalone.verify_cover(blocks, expected_blocks=64))
        assert package["valid"] == external["valid"] == (not holes)
        assert package["canonical_sha256"] == external["canonical_sha256"] == sha(witness)
        assert package["uncovered"] == external["uncovered"] == [list(t) for t in holes]
        for actual, recorded in zip((package, external), saved["verifiers"]):
            assert all(recorded[key] == value for key, value in actual.items())
        assert len(saved["verifiers"]) == 2
        assert saved["verifiers"][0]["expected_block_count_matches"] is True
        assert saved["verifiers"][1]["cardinality_matches"] is True
        checked.append(
            {
                "vector": saved["vector"],
                "sha256": sha(witness),
                "holes": len(holes),
                "minimum_pair_count": min(pairs.values()),
                "package": package,
                "standalone": external,
            }
        )

    response_path = output / "response.pbtxt"
    outcome_path = output / "outcome.json"
    outcome = read(outcome_path) if outcome_path.exists() else None
    assert result["outcome"] == outcome
    response_status = None
    if response_path.exists():
        response = cp_model_helper.CpSolverResponse()
        assert response.parse_text_format(response_path.read_text())
        response_status = {
            0: "UNKNOWN",
            1: "MODEL_INVALID",
            2: "FEASIBLE",
            3: "INFEASIBLE",
            4: "OPTIMAL",
        }[int(response.status)]
        assert outcome is not None and outcome["status"] == response_status
        assert abs(outcome["wall_seconds"] - response.wall_time) < 1e-7
        assert outcome["objective"] == response.objective_value
        assert outcome["bound"] == response.best_objective_bound
        assert outcome["callbacks"] == len(callback_paths)
        if response_status in ("FEASIBLE", "OPTIMAL"):
            assert final_path.exists() and read(final_path)["values"] == list(response.solution)
            assert response.objective_value == sum(response.solution[4368:])
        else:
            assert not final_path.exists() and not response.solution
    if result["watchdog_fired"]:
        assert result["elapsed_seconds"] >= 140 and result["returncode"] in (-15, -9, 0)
    else:
        assert result["returncode"] == 0 and outcome is not None and response_path.exists()
        assert 0 <= outcome["wall_seconds"] <= result["elapsed_seconds"]
    assert result["cover_found"] is any(row["holes"] == 0 for row in checked)
    if result["cover_found"]:
        assert sha(PRODUCER / "cover.txt") in {
            row["sha256"] for row in checked if row["holes"] == 0
        }
    else:
        assert not (PRODUCER / "cover.txt").exists()
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "result_sha256": args.result_sha256,
        "gate_sha256": GATE_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "model_sha256": MODEL_SHA,
        "parameters_sha256": PARAMS_SHA,
        "calls": 1,
        "relaunch": False,
        "watchdog_fired": result["watchdog_fired"],
        "elapsed_seconds": result["elapsed_seconds"],
        "returncode": result["returncode"],
        "status": response_status,
        "outcome": outcome,
        "initial_hint_feasible": False,
        "initial_hint_pair_row_violations": [1164, 1175, 1221],
        "callbacks_checked": len(callback_paths),
        "saved_vectors_checked": len(paths),
        "families": checked,
        "vector_damage_controls_rejected": damage_controls,
        "raw_files": actual_raw,
        "cover_found": result["cover_found"],
        "optimizer_launches": 0,
        "native_process_launches": 0,
        "scope": (
            "This fixed {6,10} star neighborhood only. UNKNOWN or watchdog termination is "
            "inconclusive. INFEASIBLE is an uncertified local solver result. "
            "No claim of unrestricted infeasibility or feasible initial hint."
        ),
    }
    target = HERE / "postcheck.json"
    assert not target.exists(), "preserve runtime audit receipt"
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    assert target.stat().st_size < 1_000_000
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(target),
                "status": response_status,
                "saved_vectors": len(paths),
                "cover_found": result["cover_found"],
            }
        )
    )


if __name__ == "__main__":
    main()
