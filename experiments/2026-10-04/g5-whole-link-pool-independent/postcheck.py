#!/usr/bin/env python3
# Document:    Independent Graph Five Whole Link Pool Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebind all saved pool evaluations and independently recount numerical residuals."""

import gzip
import json
from collections import Counter

from check import HERE, RAW, ROOT, SOURCE, ind


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    gate = json.loads((HERE / "audit.json").read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    result = json.loads((SOURCE / "result.json").read_text())
    assert gate["passed"] and result["gate_sha256"] == ind.sha(HERE / "audit.json")
    assert result["source_sha256"] == gate["source_sha256"] == ind.sha(SOURCE / "run.py")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == ind.sha(SOURCE / "manifest.json")
    for relative, expected_hash in result["raw_sha256"].items():
        assert ind.sha(RAW / relative) == expected_hash
    assert result["budgets"] == manifest["budgets"] and result["pool_count"] == 3496
    assert result["graph_index"] == 5 and result["family_sha256"] == manifest["family_sha256"]
    assert result["records"] == json.loads((RAW / "evaluations.json").read_text())
    inventory = json.loads(gzip.decompress((ROOT / manifest["inventory_path"]).read_bytes()))
    assert ind.sha(ROOT / manifest["inventory_path"]) == gate["inventory_sha256"]
    records = result["records"]
    assert len(records) == result["evaluated_count"] == result["fresh_evaluations"] <= 3496
    assert result["cached_evaluations"] == 0 and result["complete_pool"] == (len(records) == 3496)
    assert result["solver_seconds"] <= 540 and result["wall_seconds"] <= 630
    best, best_ids = (
        manifest["baseline_elastic_objective"],
        manifest["baseline"]["heavy_global_ids"],
    )
    total_solver, zero, improvements, checked = 0.0, False, [], []
    for rank, (record, entry) in enumerate(zip(records, inventory)):
        assert record["rank"] == entry["rank"] == rank
        for field in (
            "heavy_global_ids",
            "heavy_sha256",
            "shifted_rows_sha256",
            "family_sha256",
            "profile_key",
            "distance_replacements",
        ):
            assert record[field] == entry[field]
        assert record["registry_receipt_sha256"] == ind.digest(entry["registry"])
        assert entry["registry"]["accepted"]
        assert record["time_limit_seconds"] == 1
        total_solver += record["seconds"]
        model_path = ROOT / record["model_path"]
        assert ind.sha(model_path) == record["model_sha256"]
        concrete = json.loads(gzip.decompress(model_path.read_bytes()))
        blocks, _, _, heavy, rows = ind.basis()
        selected = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert concrete == json.loads(json.dumps(ind.shifted(rows, heavy, selected)))
        assert ind.digest(concrete) == record["shifted_rows_sha256"]
        assert not ind.validate_receipt(selected, entry["registry"])
        residual = None
        if "vector_path" in record:
            residual = ind.check_vector(record)
            if record["status"] == "OPTIMAL" and record["objective"] < best - 1e-7:
                best, best_ids = record["objective"], record["heavy_global_ids"]
                improvements.append((rank, best_ids, best))
            if record["recomputed_l1_residual"] <= 1e-7:
                zero = True
                assert rank == len(records) - 1
                assert result["stop_reason"] in (
                    "unresolved_numerical_feasibility",
                    "checked_exact_fractional_feasibility",
                )
        else:
            assert record["status"] not in ("OPTIMAL", "FEASIBLE")
        checked.append(
            {
                "rank": rank,
                "status": record["status"],
                "residual_recounted": residual,
                "heavy_sha256": record["heavy_sha256"],
                "vector_sha256": record.get("vector_sha256"),
                "dual_sha256": record.get("dual_sha256"),
            }
        )
    assert abs(total_solver - result["solver_seconds"]) <= 1e-6
    assert result["best_objective"] == best and result["best_heavy_global_ids"] == best_ids
    assert [
        (record["rank"], record["heavy_global_ids"], record["objective"])
        for record in result["improvements"]
    ] == improvements
    assert result["numerical_zero"] == zero
    assert not result["covering_witness"] and not result["global_lower_bound_claim"]
    if not zero:
        assert not result["exact_fractional_feasibility"]
        assert result["stop_reason"] == (
            "complete_pool" if len(records) == 3496 else "solver_or_wall_budget"
        )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "gate_sha256": ind.sha(HERE / "audit.json"),
        "result_sha256": ind.sha(SOURCE / "result.json"),
        "evaluated": len(records),
        "complete_pool": result["complete_pool"],
        "statuses": dict(Counter(record["status"] for record in records)),
        "solver_seconds": total_solver,
        "wall_seconds": result["wall_seconds"],
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best,
        "improvements": len(improvements),
        "numerical_zero": zero,
        "exact_primal_requires_separate_replay": result["exact_fractional_feasibility"],
        "records": checked,
        "scope": "Numerical readback of the frozen fixed-graph-five "
        "3496-state pool. No exact positivity or global lower-bound claim.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
