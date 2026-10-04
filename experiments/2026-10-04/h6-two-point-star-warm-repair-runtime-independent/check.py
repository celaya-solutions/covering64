# Document:    Independent Warm Star Runtime Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6a99a582834140d3d837d8a03c385ba2f6333c29ce74a9a5b591f5b676f67a45
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay persisted results and classify real families without any optimization."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-two-point-star-warm-repair"
INDEPENDENT = HERE.parent / "h6-two-point-star-warm-repair-independent"
MANIFEST_SHA = "b2ddc08cc5cd816046b2e49621bcc475c9d60b99c61ed7d7b266b28553d584d1"
GATE_SHA = "a03d8a46c9ea8c91ace7d6e4f5e438701c167fe1c226ac8a8a2386fd5730b4de"
STATIC_CHECK_SHA = "80f632cee76cc5b3dafa13e16331c5a2d00dd262e9dc7a4e182c0b1fc89ee63d"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
PAIRS = list(itertools.combinations(range(1, 17), 2))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def classify(ids, inventory):
    assert ids == sorted(set(ids)) and len(ids) == 64
    blocks = [BLOCKS[i] for i in ids]
    pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    quads = Counter(q for b in blocks for q in itertools.combinations(b, 4))
    d2max = d2sum = d3 = d4 = 0
    for pair in PAIRS:
        points = [p for p in range(1, 17) if p not in pair]
        row = [triples[tuple(sorted((*pair, p)))] for p in points]
        terms = [
            max(0, 12 - 3 * pairs[pair] + row[a] + row[b])
            for a, b in itertools.combinations(range(14), 2)
        ]
        d2max += max(terms)
        d2sum += sum(terms)
        d3 += sum(max(0, 13 - 3 * pairs[pair] + value) for value in row)
        d4 += sum(
            max(0, 12 - 3 * pairs[pair] + 2 * quads[tuple(sorted((*pair, a, b)))])
            for a, b in itertools.combinations(points, 2)
        )
    cores = [*inventory["core_rows"], inventory["sixth_cap"]["ids"]]
    overlaps = [len(set(ids).intersection(core)) for core in cores]
    thresholds = [55, 55, 55, 55, 56, inventory["sixth_cap"]["threshold"]]
    holes = [list(t) for t in TRIPLES if not triples[t]]
    min_pair = min(pairs[p] for p in PAIRS)
    weak = min_pair >= 5 and d3 == d4 == 0
    caps = all(a <= b for a, b in zip(overlaps, thresholds))
    return {
        "cardinality": 64,
        "holes": len(holes),
        "uncovered": holes,
        "minimum_pair_count": min_pair,
        "D2max": d2max,
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "six_named_overlaps": overlaps,
        "six_named_caps_apply": True,
        "six_named_caps_pass": caps,
        "weak_qualified": weak,
        "weak_six_cap_qualified": weak and caps,
        "pair_histogram": dict(sorted(Counter(pairs[p] for p in PAIRS).items())),
        "triple_histogram": dict(sorted(Counter(triples[t] for t in TRIPLES).items())),
    }


def dual(path, ids):
    package = verify_cover([BLOCKS[i] for i in ids])
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    standalone = json.loads(process.stdout)
    assert not process.stderr and process.returncode == int(not package["valid"])
    assert package["valid"] == standalone["valid"]
    assert len(package["uncovered"]) == standalone["uncovered_count"]
    assert standalone["blocks"] == 64 and standalone["cardinality_matches"]
    return {"package": package, "standalone": standalone}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-sha256", required=True)
    args = parser.parse_args()
    result_path = PRODUCER / "result.json"
    assert sha(result_path) == args.result_sha256
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(INDEPENDENT / "gate.json") == GATE_SHA
    assert sha(INDEPENDENT / "check.py") == STATIC_CHECK_SHA
    assert not (HERE / "postcheck.json").exists()
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for group in ("dependencies", "prepared_files"):
        for name, digest in manifest[group].items():
            assert sha(ROOT / name) == digest, name
    assert sha(PRODUCER / "run.py") == manifest["source_sha256"]
    result = json.loads(result_path.read_text())
    assert result["manifest_sha256"] == MANIFEST_SHA and result["gate_sha256"] == GATE_SHA
    assert result["calls"] == 1 and result["relaunch"] is False
    for name, digest in result["raw_files"].items():
        assert sha(ROOT / name) == digest, name
    raw = ROOT / "experiments/scratch/h6-two-point-star-warm-repair-20261004"
    run = raw / "run-1"
    command = result["command"]
    assert Path(command[1]) == PRODUCER / "run.py" and command[2] == "--child"
    assert Path(command[3]) == INDEPENDENT / "gate.json"
    launch = json.loads((run / "launch.json").read_text())
    assert launch["gate_sha256"] == GATE_SHA and launch["manifest_sha256"] == MANIFEST_SHA
    assert json.loads((run / "child-started.json").read_text())["one_call"] is True
    assert (run / "parameters.pbtxt").read_bytes() == (ROOT / manifest["parameters"]).read_bytes()
    params = sat_parameters_pb2.SatParameters()
    text_format.Parse((run / "parameters.pbtxt").read_text(), params)
    assert params == sat_parameters_pb2.SatParameters(
        max_time_in_seconds=120,
        num_search_workers=4,
        random_seed=2026106002,
        log_search_progress=True,
    )
    spec = importlib.util.spec_from_file_location(
        "warm_runtime_static_checker", INDEPENDENT / "check.py"
    )
    static = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(static)
    model = static.proto(ROOT / manifest["model"])
    inventory_path = HERE.parent / "native-h9-h10-reuse-pilot/manifest.json"
    assert sha(inventory_path) == "13b26e00b3743ad33cbd94553079d1bb60b6fdf43b5f2bc79dd8ceab1c3f9241"
    inventory = json.loads(inventory_path.read_text())
    initial_values = json.loads((raw / "initial-vector.json").read_text())["values"]
    static.check_vector(model, initial_values)
    initial_ids = [i for i, value in enumerate(initial_values[:4368]) if value]
    initial_path = HERE.parent / "h6-anchored-pair-repair/candidate-02.txt"
    initial = {
        "sha256": sha(initial_path),
        "feasible_in_model": True,
        "classification": classify(initial_ids, inventory),
        "verifiers": dual(initial_path, initial_ids),
        "role": "Known H9 partial input; not a cover or a new solver result.",
    }
    assert initial["classification"]["holes"] == 9
    assert initial["classification"]["D3"] == 1 and not initial["classification"]["weak_qualified"]
    vector_paths = sorted(run.glob("callback-*.json"))
    callback_count = len(vector_paths)
    if (run / "final-vector.json").exists():
        vector_paths.append(run / "final-vector.json")
    assert [str(p.relative_to(ROOT)) for p in vector_paths] == [
        r["vector"] for r in result["saved"]
    ]
    saved = []
    for path, producer in zip(vector_paths, result["saved"]):
        values = json.loads(path.read_text())["values"]
        static.check_vector(model, values)
        ids = [i for i, value in enumerate(values[:4368]) if value]
        witness = ROOT / producer["witness"]
        expected = "".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in ids)
        assert witness.read_text() == expected and sha(witness) == producer["sha256"]
        profile = classify(ids, inventory)
        checks = dual(witness, ids)
        assert profile["holes"] == sum(values[4368:]) == producer["holes"]
        assert len(checks["package"]["uncovered"]) == profile["holes"]
        assert (
            checks["standalone"]["canonical_sha256"] == producer["verifiers"][1]["canonical_sha256"]
        )
        saved.append(
            {
                "vector": str(path.relative_to(ROOT)),
                "vector_sha256": sha(path),
                "witness": str(witness.relative_to(ROOT)),
                "sha256": sha(witness),
                "feasible_in_model": True,
                "classification": profile,
                "verifiers": checks,
            }
        )
    outcome = result["outcome"]
    response = None
    if outcome is not None:
        assert json.loads((run / "outcome.json").read_text()) == outcome
        assert outcome["callbacks"] == callback_count
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((run / "response.pbtxt").read_text(), response)
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == outcome["status"]
        if outcome["status"] in ("FEASIBLE", "OPTIMAL"):
            final = json.loads((run / "final-vector.json").read_text())["values"]
            assert list(response.solution) == final
            static.check_vector(model, final)
            assert outcome["objective"] == sum(final[4368:])
        else:
            assert not response.solution and not (run / "final-vector.json").exists()
    covers = [row for row in saved if row["classification"]["holes"] == 0]
    assert result["cover_found"] == bool(covers)
    for row in covers:
        assert row["verifiers"]["package"]["valid"] and row["verifiers"]["standalone"]["valid"]
    damage_controls = {}
    for name, value in (("boolean", True), ("float", 1.0), ("outside_domain", 2)):
        damaged = list(initial_values)
        damaged[0] = value
        damage_controls[name] = static.reject(lambda: static.check_vector(model, damaged))
    damaged = list(initial_values)
    damaged[4368] = 1 - damaged[4368]
    damage_controls["false_hole"] = static.reject(lambda: static.check_vector(model, damaged))
    previous = json.loads((HERE.parent / "h6-two-point-star-repair/result.json").read_text())
    assert previous["outcome"]["status"] == "UNKNOWN" and previous["saved"] == []
    report = {
        "passed": True,
        "result_sha256": args.result_sha256,
        "manifest_sha256": MANIFEST_SHA,
        "gate_sha256": GATE_SHA,
        "checker_sha256": sha(__file__),
        "raw_hashes_checked": len(result["raw_files"]),
        "returncode": result["returncode"],
        "watchdog_fired": result["watchdog_fired"],
        "outcome": outcome,
        "callbacks": callback_count,
        "saved_vectors": len(saved),
        "initial": initial,
        "saved": saved,
        "cover_found": bool(covers),
        "unique_saved_families": len({row["sha256"] for row in saved}),
        "new_saved_families": len({row["sha256"] for row in saved} - {sha(initial_path)}),
        "best_saved_holes": min((r["classification"]["holes"] for r in saved), default=None),
        "best_known_model_feasible_holes": min([9, *(r["classification"]["holes"] for r in saved)]),
        "prior_unknown_reported_objective": previous["outcome"]["objective"],
        "prior_unknown_objective_is_incumbent": False,
        "damage_controls": damage_controls,
        "real_optimizer_calls": 0,
        "scope": "Independent replay of one fixed-star continuation. H9 input is model "
        "feasible but partial. Prior UNKNOWN objective6 is not an incumbent. All caps and "
        "weak metrics are postclassification. No unrestricted or nonexistence conclusion.",
    }
    dump(HERE / "postcheck.json", report)
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "saved_vectors": len(saved),
                "best_saved_holes": report["best_saved_holes"],
                "cover_found": report["cover_found"],
            }
        )
    )


if __name__ == "__main__":
    main()
