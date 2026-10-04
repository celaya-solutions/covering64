#!/usr/bin/env python3
# Document:    Complete Link Switch Sweep Independent Readback
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount the saved 136 LP results without launching a solver."""

import hashlib
import json
import math
from pathlib import Path

from basis import INF, digest, rebuild, shifted

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "lp-guided-full-sweep"
RAW = ROOT / "experiments/scratch/lp-guided-full-sweep-20261004"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    gate_bytes = (HERE / "audit.json").read_bytes()
    gate = json.loads(gate_bytes)
    proposal_bytes, result_bytes = (SOURCE / "proposal.json").read_bytes(), (
        SOURCE / "result.json").read_bytes()
    proposal, result = json.loads(proposal_bytes), json.loads(result_bytes)
    assert gate["passed"] and sha(proposal_bytes) == gate["proposal_sha256"]
    assert result["gate_sha256"] == sha(gate_bytes)
    assert result["source_sha256"] == gate["source_sha256"] == sha(
        (SOURCE / "sweep.py").read_bytes())
    assert result["proposal_sha256"] == gate["proposal_sha256"]
    assert result["budgets"] == proposal["budgets"]
    for relative, expected in result["raw_sha256"].items():
        assert sha((RAW / relative).read_bytes()) == expected
    assert json.loads((RAW / "evaluations.json").read_bytes()) == result["records"]
    blocks, _, ordinary, heavy, rows = rebuild()
    assert len(ordinary) == 1200 and len(result["records"]) == 136
    records, cached, fresh = [], 0, 0
    for rank, record in enumerate(result["records"]):
        neighbor = proposal["neighbors"][rank]
        assert record["rank"] == neighbor["rank"] == rank
        for field in ("heavy_sha256", "heavy_global_ids", "shifted_rows_sha256"):
            assert record[field] == neighbor[field]
        chosen = tuple(blocks[i] for i in record["heavy_global_ids"])
        concrete = shifted(rows, heavy, chosen)
        assert digest(chosen) == record["heavy_sha256"]
        assert digest(concrete) == record["shifted_rows_sha256"]
        assert record["status"] == "OPTIMAL" and record["time_limit_seconds"] == 1
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
        num, den = neighbor["maximum_cut_lower_bound"]
        assert residual + 1e-5 >= num / den
        assert residual > proposal["baseline_elastic_objective"] + 1e-5
        row = {"rank": rank, "heavy_sha256": record["heavy_sha256"],
               "rows_sha256": digest(concrete), "vector_sha256": sha(vector_bytes),
               "residual": residual, "cached": record["cached"]}
        if record["cached"]:
            old = proposal["cached"][record["heavy_sha256"]]["record"]
            for field in ("objective", "seconds", "vector_path", "vector_sha256", "status"):
                assert old[field] == record[field]
            cached += 1
        else:
            dual_bytes = (ROOT / record["dual_path"]).read_bytes()
            assert sha(dual_bytes) == record["dual_sha256"]
            dual = json.loads(dual_bytes)
            assert len(dual) == 697 and all(math.isfinite(w) for w in dual)
            assert max(abs(w) for w in dual) <= 1 + 1e-6
            row["dual_sha256"] = sha(dual_bytes)
            fresh += 1
        records.append(row)
    assert (cached, fresh) == (
        result["cached_evaluations"], result["fresh_evaluations"]) == (23, 113)
    assert result["complete_neighborhood"] and result["stop_reason"] == "complete_neighborhood"
    assert result["best_objective"] == proposal["baseline_elastic_objective"]
    assert result["best_heavy_global_ids"] == proposal["baseline_heavy_global_ids"]
    assert not result["exact_fractional_feasibility"] and not result["covering_witness"]
    assert not result["global_lower_bound_claim"]
    assert result["solver_seconds"] <= 40 and result["wall_seconds"] <= 60
    seconds = sum(r["seconds"] for r in result["records"] if not r["cached"])
    assert abs(seconds - result["solver_seconds"]) < 1e-9
    best = min(records, key=lambda r: r["residual"])
    report = {"passed": True, "states": 136, "cached": 23, "fresh": 113,
              "all_reported_optimal": True, "fresh_dual_vectors_checked": 113,
              "unchanged_objective": result["best_objective"], "best_neighbor": best,
              "solver_seconds": seconds, "wall_seconds": result["wall_seconds"],
              "gate_sha256": sha(gate_bytes), "result_sha256": sha(result_bytes),
              "source_sha256": gate["source_sha256"],
              "basis_sha256": sha((HERE / "basis.py").read_bytes()),
              "checker_sha256": sha(Path(__file__).read_bytes()), "records": records,
              "optimization_runs": 0,
              "scope": "Complete numerical LP sweep in one fixed heavy-switch neighborhood. "
                       "No exact local optimality theorem, integer cover or global exclusion."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in
                      ("passed", "states", "fresh_dual_vectors_checked", "best_neighbor")}))


if __name__ == "__main__":
    main()
