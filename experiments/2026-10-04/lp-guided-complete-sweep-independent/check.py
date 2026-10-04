#!/usr/bin/env python3
# Document:    Independent Complete Link Switch Sweep Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind full finite enumeration, exact row hashes, and the prior optimal cache."""

import hashlib
import json
import math
from pathlib import Path

from basis import INF, digest, neighbors, rebuild, shifted

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lp-guided-full-sweep"
PILOT = HERE.parent / "lp-guided-link-switch"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    captured = (SOURCE / "proposal.json").read_bytes()
    proposal = json.loads(captured)
    source_bytes = (SOURCE / "sweep.py").read_bytes()
    assert sha(source_bytes) == proposal["source_sha256"]
    for relative, expected in proposal["input_files"].items():
        assert sha((ROOT / relative).read_bytes()) == expected
    previous_bytes = (PILOT / "result.json").read_bytes()
    previous = json.loads(previous_bytes)
    previous_check = json.loads((PILOT / "readback.json").read_bytes())
    assert previous_check["passed"] and previous_check["result_sha256"] == sha(previous_bytes)
    assert proposal["baseline_heavy_global_ids"] == previous["best_heavy_global_ids"]
    assert proposal["baseline_elastic_objective"] == previous["final_objective"]
    assert proposal["budgets"] == {"one_neighborhood": True, "each_lp_seconds": 1,
                                    "solver_seconds": 40, "wall_seconds": 60,
                                    "workers": 1, "seed": 2026104}
    blocks, anchors, ordinary, heavy, rows = rebuild()
    gids = {b: i for i, b in enumerate(blocks)}
    hids = {b: i for i, b in enumerate(heavy)}
    fixed = tuple(blocks[i] for i in proposal["baseline_heavy_global_ids"])
    expected = neighbors(fixed, anchors, heavy)
    assert len(expected) == proposal["neighborhood_count"] == 136
    assert proposal["ordinary_global_ids"] == [gids[b] for b in ordinary]
    bundle_path = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
    bundle = json.loads(bundle_path.read_bytes())
    assert bundle["heavy_blocks"] == [list(b) for b in heavy]
    assert len(bundle["cuts"]) == 14
    by_key, order = {}, []
    for rank, record in enumerate(proposal["neighbors"]):
        chosen = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert record["rank"] == rank and chosen in expected
        assert list(chosen) == sorted(chosen)
        assert record["heavy_local_ids"] == [hids[b] for b in chosen]
        assert all(record[k] == value for k, value in expected[chosen].items())
        assert record["heavy_sha256"] == digest(chosen)
        concrete = shifted(rows, heavy, chosen)
        assert record["shifted_rows_sha256"] == digest(concrete)
        violations = [max(0, c["rhs"] - sum(c["coefficients"][hids[b]] for b in chosen))
                      for c in bundle["cuts"]]
        assert record["cut_violation_numerators"] == violations
        assert record["maximum_cut_lower_bound"] == [max(violations), 1000]
        assert record["heavy_sha256"] not in by_key
        by_key[record["heavy_sha256"]] = (record, concrete)
        order.append((max(violations), tuple(record["heavy_global_ids"])))
    assert order == sorted(order) and len(by_key) == len(expected)
    prior_records = {r["heavy_sha256"]: r for q in previous["rounds"] for r in q["results"]}
    usable = {key for key, r in prior_records.items()
              if key in by_key and r["status"] == "OPTIMAL" and "vector_path" in r}
    assert usable == set(proposal["cached"]) and len(usable) == 23
    cached_receipts = []
    for key, binding in proposal["cached"].items():
        record = binding["record"]
        assert record == prior_records[key] and record["status"] == "OPTIMAL"
        ranking_bytes = (ROOT / binding["ranking_path"]).read_bytes()
        assert sha(ranking_bytes) == binding["ranking_sha256"]
        ranking = json.loads(ranking_bytes)
        assert ranking["round"] == binding["source_round"]
        prior_neighbor = ranking["neighbors"][record["rank"]]
        assert prior_neighbor == binding["neighbor"]
        current_neighbor, concrete = by_key[key]
        for field in ("heavy_sha256", "heavy_global_ids", "shifted_rows_sha256"):
            assert prior_neighbor[field] == current_neighbor[field]
        vector_bytes = (ROOT / record["vector_path"]).read_bytes()
        assert sha(vector_bytes) == record["vector_sha256"]
        values = json.loads(vector_bytes)
        assert len(values) == 1200
        assert all(math.isfinite(x) and -1e-7 <= x <= 1 + 1e-7 for x in values)
        residual = 0.0
        for ids, coefs, lower, upper in concrete:
            value = sum(c * values[i] for i, c in zip(ids, coefs, strict=True))
            residual += max(0.0, lower - value)
            if upper != INF:
                residual += max(0.0, value - upper)
        assert abs(residual - record["objective"]) <= 1e-5
        assert abs(residual - record["recomputed_l1_residual"]) <= 1e-5
        assert residual > 1e-7
        cached_receipts.append({"heavy_sha256": key, "source_round": binding["source_round"],
                                "rows_sha256": digest(concrete),
                                "vector_sha256": sha(vector_bytes), "residual": residual})
    assert proposal["fresh_calls_expected"] == 113 and proposal["optimizer_calls"] == 0
    result = {"passed": True, "proposal_sha256": sha(captured),
              "source_sha256": sha(source_bytes), "complete_neighbors": 136,
              "exact_shifted_rows_checked": 136 * 697, "cached_optimal_results": 23,
              "expected_fresh_solves": 113, "cached": cached_receipts,
              "basis_sha256": sha((HERE / "basis.py").read_bytes()),
              "checker_sha256": sha(Path(__file__).read_bytes()),
              "source_review": {
                  "LP": "Same fixed elastic LP; adds only capture of 697 row duals.",
                  "caps": "One fixed neighborhood; 1s each, 40s solver, 60s wall, 1.1s margin.",
                  "workers": "One GLOP worker, fixed random seed 2026104.",
                  "cache": "Only prior OPTIMAL records with matching tuple, rows and vector hash.",
                  "stop": "Stop early on exact rational fractional feasibility; no cover claim.",
                  "status": "Complete neighborhood means attempted, not exact local optimality.",
              }, "optimization_runs": 0}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("passed", "complete_neighbors", "cached_optimal_results")}))


if __name__ == "__main__":
    main()
