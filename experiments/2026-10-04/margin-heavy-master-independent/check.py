#!/usr/bin/env python3
# Document:    Independent Maximum Margin Heavy Master Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct the integer model and signed margin objective without a solve."""

import hashlib
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "margin-heavy-master"
RAW = ROOT / "experiments/scratch/margin-heavy-master-20261004"
PLANES = ROOT / "experiments/scratch/lp-guided-larger-intersection-20261004/checked-planes.json"
INTERSECTION = HERE.parent / "lp-guided-complete-sweep-independent/cut-intersection.json"
LOW, HIGH, SCALE = -(2**63), 2**63 - 1, 1000000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(model):
    return model.SerializeToString(deterministic=True)


def build_expected(cuts):
    blocks = list(it.combinations(range(1, 17), 5))
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    heavy = [block for block in blocks if sum(a <= set(block) for a in anchors) == 1
             and all(len(set(block) & a) != 2 for a in anchors)]
    global_ids = [blocks.index(block) for block in heavy]
    planes = [([v * (SCALE // c["denominator"]) for v in c["coefficients"]],
               c["rhs"] * (SCALE // c["denominator"])) for c in cuts]
    assert all(SCALE % c["denominator"] == 0 for c in cuts)
    upper = min(sum(sorted(c, reverse=True)[:28]) - rhs for c, rhs in planes)
    assert 0 <= upper < 2**60
    assert all(abs(rhs) + sum(map(abs, c)) + upper < 2**60 for c, rhs in planes)
    expected = cp_model_pb2.CpModelProto()
    for index in global_ids:
        expected.variables.add(name=f"block_{index}", domain=[0, 1])
    expected.variables.add(name="minimum_cut_margin_units", domain=[0, upper])

    def add_row(coefficients, lower, upper_bound):
        row = expected.constraints.add().linear
        for index, coefficient in enumerate(coefficients):
            if coefficient:
                row.vars.append(index)
                row.coeffs.append(coefficient)
        row.domain.extend([lower, upper_bound])

    add_row([1] * 276, 28, 28)
    for anchor in anchors:
        for point in range(1, 17):
            if point not in anchor:
                target = 2 if point == max(anchor) + 1 else 1
                add_row([int(anchor | {point} <= set(block)) for block in heavy], target, target)
    for triple in it.combinations(range(1, 17), 3):
        if frozenset(triple) not in anchors:
            coefficients = [int(set(triple) <= set(block)) for block in heavy]
            if any(coefficients):
                add_row(coefficients, LOW, 2)
    assert len(expected.constraints) == 605
    for coefficients, rhs in planes:
        add_row(coefficients + [-1], rhs, HIGH)
    expected.objective.vars.append(276)
    expected.objective.coeffs.append(-1)
    expected.objective.scaling_factor = -1
    return expected, global_ids, planes, upper


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    assert sha(SOURCE / "run.py") == manifest["source_sha256"] == sha(RAW / "run-frozen.py")
    for path, expected_hash in manifest["input_files"].items():
        assert sha(ROOT / path) == expected_hash
    prior = json.loads(INTERSECTION.read_text())
    assert prior["passed"] and prior["all_plane_signed_sums_and_norm_bounds_rechecked"]
    assert prior["initial_cuts"] + prior["new_cuts"] == 333
    assert sha(PLANES) == prior["checked_planes_sha256"]
    cuts = json.loads(PLANES.read_text())
    expected, _, _, upper = build_expected(cuts)
    assert len(cuts) == manifest["cut_count"] == 333
    actual = text_format.Parse((RAW / "master.pbtxt").read_text(), cp_model_pb2.CpModelProto())
    assert sha(RAW / "master.pbtxt") == manifest["master_sha256"]
    assert encoded(actual) == encoded(expected)
    assert len(actual.variables) == manifest["master_variables"] == 277
    assert len(actual.constraints) == manifest["master_rows"] == 938
    assert upper == manifest["safe_margin_upper_units"] == 141507155
    assert manifest["common_denominator"] == SCALE
    assert manifest["budget"] == {
        "candidates": 20, "master_seconds_each": 3, "lp_seconds_each": 1,
        "combined_solver_seconds": 80, "wall_seconds": 100, "workers": 1, "seed": 2026104064,
    }
    damaged = cp_model_pb2.CpModelProto()
    damaged.CopyFrom(actual)
    damaged.objective.scaling_factor = 1
    assert encoded(damaged) != encoded(expected)
    damaged.CopyFrom(actual)
    damaged.constraints[-1].linear.coeffs[-1] = 1
    assert encoded(damaged) != encoded(expected)
    damaged.CopyFrom(actual)
    damaged.variables[-1].domain[0] = -1
    assert encoded(damaged) != encoded(expected)
    report = {"passed": True, "solver_calls": 0, "checker_sha256": sha(__file__),
              "source_sha256": sha(SOURCE / "run.py"),
              "manifest_sha256": sha(SOURCE / "manifest.json"),
              "master_sha256": sha(RAW / "master.pbtxt"),
              "plane_audit_sha256": sha(INTERSECTION), "checked_planes_sha256": sha(PLANES),
              "cuts": 333, "master_rows": 938, "master_variables": 277,
              "safe_margin_upper_units": upper, "damaged_controls_rejected": 3,
              "source_review": [
                  "Same frozen structural master, 697 completion rows and one-second GLOP helper",
                  "At most20 candidates; CP-SAT3s one worker; seed2026104064+step",
                  "Stop before75.8 combined solver seconds or94 wall seconds; assert80/100",
                  "Record integer achieved margin, minimum plane margin, bound and status",
                  "New cuts have exact positive source gap and asserted weight norm <=1000000",
                  "No Hamming objective; no feasibility claim from margin alone",
              ]}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
