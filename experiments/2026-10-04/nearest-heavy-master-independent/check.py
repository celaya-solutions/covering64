# Document:    Independent Preparation Gate for the Nearest-Heavy Master
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b231eeadf1f3e01db5878cff4a412492d6c4e07646707cf024bb607561ff5e9a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild all master rows and its soft objective without importing its builder."""

import argparse
import hashlib
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "nearest-heavy-master"
RAW = ROOT / "experiments/scratch/nearest-heavy-master-20261004"
LOW, HIGH = -(2**63), 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(cut_gate_path):
    assert not (HERE / "audit.json").exists()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    assert manifest["source_sha256"] == sha(SOURCE / "run.py")
    assert sha(RAW / "run-frozen.py") == manifest["source_sha256"]
    assert sha(RAW / "master.pbtxt") == manifest["master_sha256"]
    for path, expected in manifest["input_files"].items():
        assert sha(ROOT / path) == expected
    bundle_path = HERE.parent / "lp-guided-sweep-cuts/bundle.json"
    gate = json.loads(cut_gate_path.read_text())
    assert gate["passed"] and gate["bundle_sha256"] == sha(bundle_path)
    bundle = json.loads(bundle_path.read_text())
    base = json.loads((ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/"
                       "cut-bundle.json").read_text())
    cuts = list(base["cuts"])
    for substring, count in (("/lazy-heavy-master/learned-cut-", 10),
                             ("/lazy-heavy-master-continuation-20261004/", 100)):
        paths = sorted(path for path in manifest["input_files"]
                       if substring in path and "learned-cut" in path)
        assert len(paths) == count
        cuts.extend(json.loads((ROOT / path).read_text()) for path in paths)
    assert len(cuts) == 124
    cuts.extend(bundle["cuts"])
    cuts.append(json.loads((HERE.parent / "lp-guided-best-lp/cut.json").read_text()))
    blocks = list(it.combinations(range(1, 17), 5))
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    heavy = [block for block in blocks if sum(a <= set(block) for a in anchors) == 1
             and all(len(set(block) & a) != 2 for a in anchors)]
    global_ids = [blocks.index(block) for block in heavy]
    assert len(heavy) == 276
    assert global_ids == base["heavy_global_ids"] == bundle["heavy_global_ids"]
    expected = cp_model_pb2.CpModelProto()
    for index in global_ids:
        expected.variables.add(name=f"block_{index}", domain=[0, 1])

    def add_row(coefficients, lower, upper):
        row = expected.constraints.add().linear
        for index, coefficient in enumerate(coefficients):
            if coefficient:
                row.vars.append(index)
                row.coeffs.append(coefficient)
        row.domain.extend([lower, upper])

    add_row([1] * 276, 28, 28)
    for anchor in anchors:
        for point in range(1, 17):
            if point not in anchor:
                target = 2 if point == max(anchor) + 1 else 1
                add_row([int(anchor | {point} <= set(block)) for block in heavy],
                        target, target)
    for triple in it.combinations(range(1, 17), 3):
        if frozenset(triple) not in anchors:
            coefficients = [int(set(triple) <= set(block)) for block in heavy]
            if any(coefficients):
                add_row(coefficients, LOW, 2)
    assert len(expected.constraints) == 605
    for cut in cuts:
        assert len(cut["coefficients"]) == 276
        add_row(cut["coefficients"], cut["rhs"], HIGH)
    baseline = manifest["baseline_heavy_global_ids"]
    assert len(baseline) == len(set(baseline)) == 28
    for index, global_id in enumerate(global_ids):
        if global_id in baseline:
            expected.objective.vars.append(index)
            expected.objective.coeffs.append(-1)
    expected.objective.offset = 28
    expected.objective.scaling_factor = 1
    actual = text_format.Parse((RAW / "master.pbtxt").read_text(), cp_model_pb2.CpModelProto())
    def serialize(model):
        return model.SerializeToString(deterministic=True)

    assert serialize(actual) == serialize(expected)
    assert manifest["cut_count"] == len(cuts) == 238
    assert manifest["unique_normalized_cuts"] == 238
    assert manifest["master_rows"] == len(actual.constraints) == 843
    assert manifest["budget"] == {
        "candidates": 100, "master_seconds_each": 2, "lp_seconds_each": 1,
        "combined_solver_seconds": 180, "wall_seconds": 240, "workers": 1,
        "seed": 2026104063,
    }
    damaged = cp_model_pb2.CpModelProto()
    damaged.CopyFrom(actual)
    damaged.objective.coeffs[0] = 1
    assert serialize(damaged) != serialize(expected)
    damaged.CopyFrom(actual)
    damaged.constraints[-1].linear.domain[0] += 1
    assert serialize(damaged) != serialize(expected)
    audit = {
        "passed": True, "source_sha256": sha(SOURCE / "run.py"),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "checker_sha256": sha(__file__), "master_sha256": sha(RAW / "master.pbtxt"),
        "cut_gate_path": str(cut_gate_path.relative_to(ROOT)),
        "cut_gate_sha256": sha(cut_gate_path), "bundle_sha256": sha(bundle_path),
        "master_variables": 276, "master_rows": 843, "cuts": 238,
        "objective": "28 minus baseline overlap; no radius constraint",
        "damaged_controls_rejected": 2, "solver_calls": 0,
        "source_review": [
            "Same frozen 697-row completion LP and one-worker GLOP method",
            "One-worker CP-SAT 2s, LP 1s, at most 100 candidates",
            "Stops before combined budget 176.8s or wall budget 234s",
            "Final combined solver <=180s and wall <=240s assertions",
            "Exact signed-bound cut lift, fixed baseline objective, no nearest proof on FEASIBLE",
            "Stop on exact primal, unresolved LP/dual, or master without candidate",
        ],
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cut_gate", type=Path)
    main(parser.parse_args().cut_gate.resolve())
