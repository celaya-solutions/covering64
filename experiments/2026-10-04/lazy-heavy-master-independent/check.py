#!/usr/bin/env python3
# Document:    Independent Lazy Heavy Master Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently reconstruct the complete master and its 697-row LP basis."""

import hashlib
import importlib.util
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lazy-heavy-master"
OLD = ROOT / "experiments/2026-10-03"
RAW = ROOT / "experiments/scratch/lazy-heavy-master-20261004"
LOW, HIGH = -(2**63), 2**63 - 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    manifest_bytes = (SOURCE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    source_bytes = (SOURCE / "run.py").read_bytes()
    bundle_bytes = (OLD / "cut-survivor-lp-screen/cut-bundle.json").read_bytes()
    bundle = json.loads(bundle_bytes)
    proto_bytes = (RAW / "master.pbtxt").read_bytes()
    gate_bytes = (HERE.parent / "cut-bundle-independent/audit.json").read_bytes()
    gate = json.loads(gate_bytes)
    oracle_path = OLD / "lookahead-cut-independent/check.py"
    lp_path = OLD / "cut-survivor-lp-screen/lp_core.py"
    assert manifest["source_sha256"] == sha(source_bytes)
    assert (RAW / "run-frozen.py").read_bytes() == source_bytes
    assert manifest["master_sha256"] == sha(proto_bytes)
    assert manifest["bundle_sha256"] == sha(bundle_bytes) == gate["bundle_sha256"]
    assert gate["passed"] and gate["cuts"] == 14
    assert manifest["cut_gate_sha256"] == sha(gate_bytes)
    assert manifest["oracle_sha256"] == sha(oracle_path.read_bytes())
    assert manifest["lp_sha256"] == sha(lp_path.read_bytes())
    assert (manifest["seed"], manifest["iterations"], manifest["master_seconds_each"],
            manifest["lp_seconds_each_phase"], manifest["workers"]) == (
                2026104041, 10, 10, 10, 1)

    blocks = list(it.combinations(range(1, 17), 5))
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    ordinary = [b for b in blocks if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [b for b in blocks if sum(a <= set(b) for a in anchors) == 1
             and all(len(set(b) & a) != 2 for a in anchors)]
    assert (len(ordinary), len(heavy)) == (1200, 276)
    global_ids = [blocks.index(b) for b in heavy]
    assert bundle["heavy_blocks"] == [list(b) for b in heavy]
    assert bundle["heavy_global_ids"] == global_ids
    assert bundle["ordinary_global_ids"] == [blocks.index(b) for b in ordinary]
    expected = cp_model_pb2.CpModelProto()
    for gid in global_ids:
        expected.variables.add(name=f"block_{gid}", domain=[0, 1])

    def add_row(coefficients, lower, upper):
        row = expected.constraints.add().linear
        for i, coefficient in enumerate(coefficients):
            if coefficient:
                row.vars.append(i)
                row.coeffs.append(coefficient)
        row.domain.extend([lower, upper])

    add_row([1] * 276, 28, 28)
    for anchor in anchors:
        for point in range(1, 17):
            if point not in anchor:
                count = 2 if point == max(anchor) + 1 else 1
                add_row([int(anchor | {point} <= set(b)) for b in heavy], count, count)
    upper_rows = 0
    for triple in it.combinations(range(1, 17), 3):
        if frozenset(triple) not in anchors:
            coefficients = [int(set(triple) <= set(b)) for b in heavy]
            if any(coefficients):
                add_row(coefficients, LOW, 2)
                upper_rows += 1
    assert upper_rows == 552 and len(bundle["cuts"]) == 14
    for cut in bundle["cuts"]:
        add_row(cut["coefficients"], cut["rhs"], HIGH)
    actual = text_format.Parse(proto_bytes.decode(), cp_model_pb2.CpModelProto())
    assert len(expected.variables) == 276 and len(expected.constraints) == 619
    assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
        deterministic=True), "Full master protobuf differs"

    # Reconstruct the whole completion basis without using the production oracle.
    supports = [((), 64, 64)]
    supports += [(t, 1, HIGH if frozenset(t) in anchors else 2)
                 for t in it.combinations(range(1, 17), 3)]
    supports += [((p,), 20, 20) for p in range(1, 17)]
    for pair in it.combinations(range(1, 17), 2):
        target = None
        for anchor in anchors:
            for point, other in (pair, pair[::-1]):
                if point in anchor:
                    value = 7 if other in anchor else 6 if other == max(anchor) + 1 else 5
                    assert target is None or target == value
                    target = value
        supports.append((pair, 5 if target is None else target,
                         7 if target is None else target))
    rows = [([i for i, b in enumerate(ordinary) if set(s) <= set(b)],
             [i for i, b in enumerate(heavy) if set(s) <= set(b)], lo, hi)
            for s, lo, hi in supports]
    assert len(rows) == 697
    spec = importlib.util.spec_from_file_location("pinned_existing_oracle", oracle_path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    ob, oo, oh, _, production_rows = oracle.rebuild()
    assert (ob, oo, oh, production_rows) == (blocks, ordinary, heavy, rows)

    # Replay all signed row sums on this freshly reconstructed unconditional basis.
    for cut in bundle["cuts"]:
        dual_bytes = (ROOT / cut["dual_path"]).read_bytes()
        assert sha(dual_bytes) == cut["dual_sha256"]
        dual = json.loads(dual_bytes)
        oc, hc, constant = [0] * 1200, [0] * 276, 0
        for row_id, weight in dual["weights"]:
            oi, hi, lower, upper = rows[row_id]
            bound = lower if weight > 0 else upper
            assert type(weight) is int and weight != 0 and abs(bound) < 2**60
            constant += weight * bound
            for i in oi:
                oc[i] += weight
            for i in hi:
                hc[i] += weight
        box = sum(max(0, c) for c in oc)
        assert hc == cut["coefficients"] and constant - box == cut["rhs"]
        assert constant == cut["constant_numerator"]
        assert box == cut["ordinary_box_max_numerator"]

    result = {
        "passed": True, "master_variables": 276, "master_rows": 619,
        "row_counts": {"cardinality": 1, "outside_degrees": 52,
                       "nonanchor_upper": 552, "replayed_cuts": 14},
        "exact_full_proto_match": True, "completion_rows": 697,
        "ordinary_columns": 1200, "heavy_columns": 276,
        "source_review": {
            "shift": "Subtract selected-heavy count from both finite bounds; keep upper INF.",
            "lp": "1200 continuous variables in [0,1]; each phase has 10 second limit.",
            "dual": "Positive signed rows use lower bounds, negative rows finite upper bounds.",
            "cut": "heavy_sum >= constant - sum(max(0, ordinary_coefficient)).",
            "separation": "Integer arithmetic checks shifted RHS, box, and source violation.",
            "primal": "Exact rational rows/box; fractional completion is not an integer cover.",
            "budget": "At most 10 iterations, 10 seconds CP and two 10 second LP phases each.",
            "scope": "Regular four-sevenfold family, all six hub graphs; no CP exclusion theorem.",
        },
        "source_sha256": sha(source_bytes), "manifest_sha256": sha(manifest_bytes),
        "master_sha256": sha(proto_bytes), "bundle_sha256": sha(bundle_bytes),
        "cut_gate_sha256": sha(gate_bytes), "oracle_sha256": sha(oracle_path.read_bytes()),
        "lp_sha256": sha(lp_path.read_bytes()), "checker_sha256": sha(Path(__file__).read_bytes()),
        "optimization_runs": 0,
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("passed", "master_variables", "master_rows", "completion_rows")}))


if __name__ == "__main__":
    main()
