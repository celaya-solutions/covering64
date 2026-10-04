#!/usr/bin/env python3
# Document:    Lazy Master Continuation Exact Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check all hundred master assignments, exact residual rows, and signed cuts."""

import hashlib
import itertools as it
import json
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE
RAW = ROOT / "experiments/scratch/lazy-heavy-master-continuation-20261004"
HIGH = 2**63 - 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    receipts = {}

    def capture(path):
        data = path.read_bytes()
        receipts[str(path.relative_to(ROOT))] = sha(data)
        return data

    gate = json.loads(capture(HERE / "initial-gate.json"))
    assert gate["passed"]
    assert sha(capture(SOURCE / "run.py")) == gate["source_sha256"]
    manifest = json.loads(capture(SOURCE / "manifest.json"))
    report = json.loads(capture(SOURCE / "results.json"))
    assert report["manifest_sha256"] == gate["manifest_sha256"]
    assert sha(capture(SOURCE / "manifest.json")) == gate["manifest_sha256"]
    initial = capture(RAW / "master.pbtxt")
    assert sha(initial) == gate["master_sha256"]
    expected = text_format.Parse(initial.decode(), cp_model_pb2.CpModelProto())
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    blocks = list(it.combinations(range(1, 17), 5))
    ordinary = [b for b in blocks if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [b for b in blocks if sum(a <= set(b) for a in anchors) == 1
             and all(len(set(b) & a) != 2 for a in anchors)]
    supports = [((), 64, 64)]
    supports += [(t, 1, HIGH if frozenset(t) in anchors else 2)
                 for t in it.combinations(range(1, 17), 3)]
    supports += [((p,), 20, 20) for p in range(1, 17)]
    for pair in it.combinations(range(1, 17), 2):
        targets = {7 if q in a else 6 if q == max(a) + 1 else 5
                   for a in anchors for p, q in (pair, pair[::-1]) if p in a}
        assert len(targets) <= 1
        supports.append((pair, min(targets) if targets else 5, max(targets) if targets else 7))
    rows = [([i for i, b in enumerate(ordinary) if set(s) <= set(b)],
             [i for i, b in enumerate(heavy) if set(s) <= set(b)], lo, hi)
            for s, lo, hi in supports]
    assert len(rows) == 697 and len(report["steps"]) == report["new_cuts"] == 100
    checked = []
    for step, record in enumerate(report["steps"]):
        directory = RAW / f"step-{step:02}"
        captured = capture(directory / "master.pbtxt")
        assert sha(captured) == record["master_sha256"]
        actual = text_format.Parse(captured.decode(), cp_model_pb2.CpModelProto())
        assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
            deterministic=True)
        assert len(actual.constraints) == 629 + step
        params = text_format.Parse(capture(directory / "parameters.pbtxt").decode(),
                                   sat_parameters_pb2.SatParameters())
        ep = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=5, num_search_workers=1, random_seed=2026104061 + step,
            randomize_search=True, log_search_progress=True, log_to_stdout=False)
        assert params.SerializeToString(deterministic=True) == ep.SerializeToString(
            deterministic=True)
        response = text_format.Parse(capture(directory / "response.pbtxt").decode(),
                                     cp_model_pb2.CpSolverResponse())
        selected = set(record["heavy_indices"])
        assert len(selected) == 28 and record["cut_count"] == 24 + step
        assert list(response.solution) == [int(i in selected) for i in range(276)]
        chosen = [tuple(map(int, line.split())) for line in
                  capture(directory / "heavy.txt").decode().splitlines()]
        assert chosen == [heavy[i] for i in sorted(selected)]
        for row in actual.constraints:
            value = sum(c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
                        if i in selected)
            assert row.linear.domain[0] <= value <= row.linear.domain[1]
        shifted = []
        for oi, hi, lower, upper in rows:
            shift = len(selected & set(hi))
            shifted.append([oi, [1] * len(oi), lower - shift,
                            upper if upper == HIGH else upper - shift])
        assert json.loads(capture(directory / "completion-rows.json")) == shifted
        cut = json.loads(capture(directory / "learned-cut.json"))
        dual = cut["dual"]
        indices = [i for i, _ in dual["weights"]]
        assert indices == sorted(set(indices)) and dual["denominator"] in (1000, 10000, 1000000)
        oc, hc, constant = [0] * 1200, [0] * 276, 0
        for row_id, weight in dual["weights"]:
            assert type(row_id) is int and 0 <= row_id < 697
            assert type(weight) is int and weight != 0
            oi, hi, lower, upper = rows[row_id]
            bound = lower if weight > 0 else upper
            assert abs(bound) < 2**60
            constant += weight * bound
            for i in oi:
                oc[i] += weight
            for i in hi:
                hc[i] += weight
        box, lhs = sum(max(0, c) for c in oc), sum(hc[i] for i in selected)
        rhs = constant - box
        assert (cut["coefficients"], cut["ordinary_coefficients"]) == (hc, oc)
        assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
            constant, box, lhs, rhs)
        assert (dual["rhs_numerator"], dual["box_max_numerator"]) == (constant - lhs, box)
        gap = Fraction(rhs - lhs, dual["denominator"])
        assert gap > 0 and dual["proves_infeasible"] is True
        assert dual["gap"] == record["gap"] == [gap.numerator, gap.denominator]
        assert cut["denominator"] == dual["denominator"]
        capture(directory / "numerical-dual.json")
        capture(directory / "solver.log")
        row = expected.constraints.add().linear
        for i, c in enumerate(hc):
            if c:
                row.vars.append(i)
                row.coeffs.append(c)
        row.domain.extend([rhs, HIGH])
        checked.append({"step": step, "master_rows": len(actual.constraints),
                        "gap": dual["gap"], "signed_rows": len(indices),
                        "heavy_tuple": sorted(selected)})
    result = {"passed": True, "incremental_masters": 100, "separated_heavy_tuples": 100,
              "checked_new_cuts": 100, "total_checked_cuts": 124,
              "completion_rows_each": 697, "results": checked,
              "source_manifest_sha256": report["manifest_sha256"],
              "source_revision": manifest["source_revision"],
              "checker_sha256": sha(Path(__file__).read_bytes()), "receipts": receipts,
              "optimization_runs": 0,
              "scope": "Exact rational separation of 100 fixed heavy tuples in the regular "
                       "four-sevenfold family. No ordinary integrality, no global nonexistence."}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("passed", "incremental_masters", "checked_new_cuts")}))


if __name__ == "__main__":
    main()
