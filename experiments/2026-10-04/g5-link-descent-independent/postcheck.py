#!/usr/bin/env python3
# Document:    Independent Registry Filtered Graph Five Descent Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay complete branch neighborhoods, registry filters, LP vectors and cache."""

import json

from independent import (
    HERE,
    RAW,
    ROOT,
    SOURCE,
    basis,
    check_vector,
    digest,
    sha,
    validate_ranking,
)


def main():
    output = HERE / "postcheck.json"
    assert not output.exists()
    gate = json.loads((HERE / "audit.json").read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    result = json.loads((SOURCE / "result.json").read_text())
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "audit.json")
    assert gate["independent_basis_sha256"] == sha(HERE / "independent.py")
    assert result["source_sha256"] == gate["source_sha256"] == sha(SOURCE / "run.py")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert result["budgets"] == manifest["budgets"]
    assert result["graph_index"] == 5 and result["family_sha256"] == manifest["family_sha256"]
    for relative, expected_hash in result["raw_sha256"].items():
        assert sha(RAW / relative) == expected_hash
    assert result["rounds"] == json.loads((RAW / "rounds.json").read_text())
    blocks, _, _, _, _ = basis()
    cuts = json.loads(
        (ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json").read_text()
    )["cuts"]
    baseline = manifest["baseline"]
    cache = {record["cache_key"]: record for record in manifest["initial_cache"]}
    trajectory = [baseline]
    chosen = tuple(blocks[i] for i in baseline["heavy_global_ids"])
    best = baseline["objective"]
    fresh, cached, solver_seconds, all_records, checked_rounds = 0, 0, 0.0, [], []
    assert result["initial_objective"] == best == 15.06922063054413
    assert len(result["rounds"]) <= 3
    for round_number, summary in enumerate(result["rounds"], start=1):
        folder = RAW / f"round-{round_number}"
        ranking = json.loads((folder / "ranking.json").read_text())
        ranked = ranking["neighbors"]
        assert summary["round"] == ranking["round"] == round_number
        assert ranking["incumbent_heavy_global_ids"] == [blocks.index(block) for block in chosen]
        assert ranking["incumbent_objective"] == summary["incumbent_objective"] == best
        assert summary["ranking_sha256"] == sha(folder / "ranking.json")
        accepted_count, rejected_count = validate_ranking(
            chosen, ranked, manifest["family_sha256"], cuts
        )
        assert accepted_count == summary["accepted"] == ranking["accepted"]
        assert rejected_count == summary["rejected"] == ranking["rejected"]
        assert len(ranked) == summary["generated"] == accepted_count + rejected_count
        accepted = [record for record in ranked if record["accepted"]]
        evaluated = (
            json.loads((folder / "evaluations.json").read_text())
            if (folder / "evaluations.json").exists()
            else []
        )
        if evaluated:
            assert sha(folder / "evaluations.json") == summary["evaluations_sha256"]
        else:
            assert summary["evaluations_sha256"] is None
        assert summary["evaluated"] == len(evaluated) <= len(accepted)
        residuals = []
        for neighbor, record in zip(accepted, evaluated):
            assert record["round"] == round_number and record["rank"] == neighbor["rank"]
            for field in ("heavy_sha256", "heavy_global_ids", "shifted_rows_sha256", "cache_key"):
                assert record[field] == neighbor[field]
            assert record["family_sha256"] == manifest["family_sha256"]
            assert record["registry_accepted"] and neighbor["registry"]["accepted"]
            assert record["registry_receipt_sha256"] == digest(neighbor["registry"])
            assert record["ranking_sha256"] == summary["ranking_sha256"]
            key = record["cache_key"]
            if record["cached"]:
                cached += 1
                assert key in cache and cache[key]["status"] == record["status"] == "OPTIMAL"
                assert record["cached_origin_record_sha256"] == digest(cache[key])
                for field in (
                    "objective",
                    "vector_path",
                    "vector_sha256",
                    "dual_path",
                    "dual_sha256",
                    "source_round",
                    "heavy_global_ids",
                    "family_sha256",
                    "shifted_rows_sha256",
                ):
                    assert record[field] == cache[key][field]
            else:
                fresh += 1
                assert key not in cache and record["source_round"] == round_number
                assert record["time_limit_seconds"] == 1
                solver_seconds += record["seconds"]
                assert solver_seconds <= 60
            if "vector_path" in record:
                residual = check_vector(record)
                residuals.append(residual)
            else:
                assert record["status"] not in ("OPTIMAL", "FEASIBLE")
            if record["status"] == "OPTIMAL":
                numerator, denominator = neighbor["maximum_cut_lower_bound"]
                assert record["objective"] + 1e-5 >= numerator / denominator
                cache[key] = record.copy()
            all_records.append(record)
        complete = len(evaluated) == len(accepted)
        all_optimal = complete and all(record["status"] == "OPTIMAL" for record in evaluated)
        assert summary["complete"] == complete and summary["all_optimal"] == all_optimal
        eligible = [
            record
            for record in evaluated
            if record["status"] == "OPTIMAL" and record["objective"] < best - 1e-7
        ]
        selected = (
            min(eligible, key=lambda record: (record["objective"], record["heavy_global_ids"]))
            if eligible and all_optimal
            else None
        )
        assert selected == summary["selected"]
        assert summary["minimum_evaluated_objective"] == min(
            (record["objective"] for record in evaluated if "objective" in record), default=None
        )
        checked_rounds.append(
            {
                "round": round_number,
                "generated": len(ranked),
                "accepted": accepted_count,
                "rejected": rejected_count,
                "evaluated": len(evaluated),
                "complete": complete,
                "all_optimal": all_optimal,
                "incumbent_objective": best,
                "minimum_residual_recounted": min(residuals, default=None),
            }
        )
        if selected is not None:
            best = selected["objective"]
            chosen = tuple(blocks[i] for i in selected["heavy_global_ids"])
            trajectory.append(selected)
        else:
            assert round_number == len(result["rounds"])
            if complete and all_optimal:
                assert result["stop_reason"] == "complete_accepted_neighborhood_no_improvement"
    assert all_records == result["records"]
    assert trajectory == result["trajectory"]
    assert cache == json.loads((RAW / "final-cache.json").read_text())
    assert (fresh, cached) == (result["fresh_evaluations"], result["cached_evaluations"])
    assert fresh <= 350 and abs(solver_seconds - result["solver_seconds"]) <= 1e-6
    assert result["wall_seconds"] <= 90
    assert result["best_objective"] == best
    assert result["best_heavy_global_ids"] == [blocks.index(block) for block in chosen]
    assert not result["covering_witness"] and not result["global_lower_bound_claim"]
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "independent_basis_sha256": sha(HERE / "independent.py"),
        "gate_sha256": sha(HERE / "audit.json"),
        "result_sha256": sha(SOURCE / "result.json"),
        "rounds": checked_rounds,
        "fresh": fresh,
        "cached": cached,
        "solver_seconds": solver_seconds,
        "wall_seconds": result["wall_seconds"],
        "initial_objective": baseline["objective"],
        "best_objective": best,
        "stop_reason": result["stop_reason"],
        "scope": "Fixed graph5, registry-admissible two-edge neighborhoods. Numerical "
        "LP objectives and local comparisons do not prove a global bound.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
