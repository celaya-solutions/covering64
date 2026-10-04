# Document:    Fixed-g1 Whole-Link Survivor Pool LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c0c924d8f9d8253977f66adc9fd4bcbb0b18e02680511d4aeeff55ab0c060bfd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze and screen exactly the 757 independently checked whole-link survivors."""

import argparse
import gzip
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = ROOT / "experiments/2026-10-04"
PLAN = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
PREP = ROOT / "experiments/scratch/g1-whole-link-pool-preparation-20261004"
RAW = ROOT / "experiments/scratch/g1-whole-link-pool-20261004"
SCREEN = DAY / "g1-larger-independent/audit.json"
DESCENT = DAY / "g1-link-descent"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


branch = load(DESCENT / "run.py", "whole_pool_branch")
sha = branch.sha
data_hash = branch.data_hash


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    assert not PREP.exists() and not (HERE / "manifest.json").exists()
    screen = json.loads(SCREEN.read_text())
    assert screen["passed"] and screen["whole_link_survivors"] == 757
    assert screen["conditional_bundle_sha256"] == sha(PLAN / "g1-cuts.json")
    assert screen["envelope_results_sha256"] == sha(PLAN / "envelope-results.json")
    result = json.loads((DESCENT / "result.json").read_text())
    baseline = result["trajectory"][-1]
    family = json.loads((DESCENT / "manifest.json").read_text())["family_sha256"]
    blocks, ordinary, heavy, _, rows, changes = branch.basis()
    pool_path = PLAN / "whole-link-unexcluded.json.gz"
    pool = json.loads(gzip.decompress(pool_path.read_bytes()))
    assert len(pool) == len({tuple(ids) for ids in pool}) == 757
    fixed = set(result["best_heavy_global_ids"])
    pool.sort(key=lambda ids: (len(fixed - set(ids)), ids))
    old_cache = json.loads(
        (ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json").read_text()
    )
    assert not {tuple(ids) for ids in pool} & {
        tuple(record["heavy_global_ids"]) for record in old_cache.values()
    }
    registry = branch.registry_module.Registry()
    conditional = json.loads((PLAN / "g1-cuts.json").read_text())
    broad = json.loads((PLAN / "broad-cuts-reference.json").read_text())
    assert conditional["count"] == 243 and broad["count"] == 353
    assert conditional["family_sha256"] == family and conditional["graph_index"] == 1
    lookup = {blocks.index(b): i for i, b in enumerate(heavy)}
    inventory = []
    for rank, ids in enumerate(pool):
        assert len(ids) == len(set(ids)) == 28 and ids == sorted(ids)
        selected = [blocks[i] for i in ids]
        receipt = registry.classify(selected)
        assert receipt["accepted"] and len(receipt["links"]) == 4
        positions = [lookup[i] for i in ids]
        assert all(
            sum(cut["coefficients"][i] for i in positions) >= cut["rhs"]
            for cut in conditional["cuts"] + broad["cuts"]
        )
        shifted = branch.generator.shifted_rows(rows, heavy, selected)
        heavy_sha = data_hash(selected)
        rows_sha = data_hash(shifted)
        inventory.append(
            {
                "rank": rank,
                "heavy_global_ids": ids,
                "heavy_sha256": heavy_sha,
                "shifted_rows_sha256": rows_sha,
                "family_sha256": family,
                "profile_key": branch.profile_key(heavy_sha, rows_sha, family),
                "distance_replacements": len(fixed - set(ids)),
                "registry": receipt,
            }
        )
    PREP.mkdir()
    inventory_path = PREP / "inventory.json.gz"
    inventory_path.write_bytes(gzip.compress(json.dumps(inventory).encode(), mtime=0))
    dump(
        HERE / "pool.json",
        {
            "heavy_global_ids": pool,
            "ordering": (
                "Replacement distance from g1 local minimum, then lexicographic global IDs."
            ),
        },
    )
    inputs = json.loads((PLAN / "inputs.json").read_text())
    inputs.update(json.loads((DESCENT / "manifest.json").read_text())["input_files"])
    paths = [
        Path(__file__),
        SCREEN,
        PLAN / "g1-cuts.json",
        PLAN / "broad-cuts-reference.json",
        PLAN / "envelope-results.json",
        PLAN / "whole-link-unexcluded.json.gz",
        DESCENT / "run.py",
        DESCENT / "result.json",
        DESCENT / "manifest.json",
        DESCENT / "registry.py",
        DAY / "g1-link-descent-independent/postcheck.json",
        ROOT / baseline["vector_path"],
        ROOT / baseline["dual_path"],
        ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json",
    ]
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision_at_freeze": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "screen_audit_sha256": sha(SCREEN),
        "graph_index": 1,
        "hub_excesses": [0, 1, 1, 1, 1, 0],
        "hub_pair_targets": [5, 6, 6, 6, 6, 5],
        "family_sha256": family,
        "six_row_changes": changes,
        "pool_count": 757,
        "pool_sha256": sha(HERE / "pool.json"),
        "inventory_path": str(inventory_path.relative_to(ROOT)),
        "inventory_sha256": sha(inventory_path),
        "baseline": baseline,
        "baseline_elastic_objective": result["best_objective"],
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "cached_count": 0,
        "budgets": {
            "pool_count": 757,
            "each_lp_seconds": 1,
            "solver_seconds": 160,
            "wall_seconds": 200,
            "workers": 1,
            "seed": 2026104,
        },
        "optimization_calls": 0,
        "stop_policy": (
            "Stop immediately on numerical residual <=1e-7, attempt exact rational primal "
            "checks, then stop even if exact reconstruction fails."
        ),
        "scope": (
            "Only this frozen 757-state pool under g1; "
            "no other candidates and no broad-model cache reuse."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "pool": 757,
                "inventory_sha256": sha(inventory_path),
                "baseline": result["best_objective"],
            }
        )
    )


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == sha(__file__) == manifest["source_sha256"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert sha(HERE / "pool.json") == manifest["pool_sha256"]
    inventory_path = ROOT / manifest["inventory_path"]
    assert sha(inventory_path) == manifest["inventory_sha256"]
    inventory = json.loads(gzip.decompress(inventory_path.read_bytes()))
    assert len(inventory) == 757
    assert [item["heavy_global_ids"] for item in inventory] == json.loads(
        (HERE / "pool.json").read_text()
    )["heavy_global_ids"]
    assert not RAW.exists() and not (HERE / "result.json").exists()
    RAW.mkdir()
    for path in [Path(__file__), HERE / "manifest.json", HERE / "pool.json", gate_path]:
        (RAW / path.name).write_bytes(path.read_bytes())
    started = time.monotonic()
    blocks, ordinary, heavy, _, rows, _ = branch.basis()
    registry = branch.registry_module.Registry()
    exact = load(branch.generator.LP_CORE, "whole_pool_exact")
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "budgets": manifest["budgets"],
        "graph_index": 1,
        "family_sha256": manifest["family_sha256"],
    }
    dump(RAW / "start.json", start)
    solver_seconds = 0.0
    best_objective = manifest["baseline_elastic_objective"]
    best_ids = manifest["baseline"]["heavy_global_ids"]
    records = []
    improvements = []
    stop_reason = "complete_pool"
    exact_feasible = False
    numerical_zero = False
    for candidate in inventory:
        if solver_seconds >= 158.9 or time.monotonic() - started >= 195:
            stop_reason = "solver_or_wall_budget"
            break
        rank = candidate["rank"]
        selected = [blocks[i] for i in candidate["heavy_global_ids"]]
        live_receipt = registry.classify(selected)
        assert live_receipt["accepted"] and data_hash(live_receipt) == data_hash(
            candidate["registry"]
        )
        shifted = branch.generator.shifted_rows(rows, heavy, selected)
        assert data_hash(shifted) == candidate["shifted_rows_sha256"]
        record, values, dual = branch.sweep.solve(shifted)
        solver_seconds += record["seconds"]
        record.update(
            rank=rank,
            heavy_global_ids=candidate["heavy_global_ids"],
            heavy_sha256=candidate["heavy_sha256"],
            shifted_rows_sha256=candidate["shifted_rows_sha256"],
            profile_key=candidate["profile_key"],
            family_sha256=manifest["family_sha256"],
            registry_receipt_sha256=data_hash(live_receipt),
            distance_replacements=candidate["distance_replacements"],
        )
        if values is not None:
            vector_path = RAW / f"rank-{rank:03d}-values.json"
            dual_path = RAW / f"rank-{rank:03d}-dual.json"
            dump(vector_path, values)
            dump(dual_path, dual)
            record.update(
                vector_path=str(vector_path.relative_to(ROOT)),
                vector_sha256=sha(vector_path),
                dual_path=str(dual_path.relative_to(ROOT)),
                dual_sha256=sha(dual_path),
            )
            if record["status"] == "OPTIMAL" and record["objective"] < best_objective - 1e-7:
                best_objective = record["objective"]
                best_ids = record["heavy_global_ids"]
                improvements.append(record.copy())
            if record["recomputed_l1_residual"] <= 1e-7:
                numerical_zero = True
                stop_reason = "unresolved_numerical_feasibility"
                attempts = []
                for limit in (100, 10000, 1000000, 1000000000):
                    primal = exact.exact_primal(shifted, values, limit)
                    attempts.append({"denominator_limit": limit, "passed": primal is not None})
                    if primal is not None:
                        primal.update(
                            graph_index=1,
                            family_sha256=manifest["family_sha256"],
                            heavy_global_ids=record["heavy_global_ids"],
                            ordinary_global_ids=manifest["ordinary_global_ids"],
                            shifted_rows_sha256=record["shifted_rows_sha256"],
                        )
                        dump(HERE / "exact-primal.json", primal)
                        record["exact_primal_sha256"] = sha(HERE / "exact-primal.json")
                        exact_feasible = True
                        stop_reason = "checked_exact_fractional_feasibility"
                        break
                dump(RAW / "exact-primal-attempts.json", attempts)
        records.append(record)
        dump(RAW / "evaluations.json", records)
        if (rank + 1) % 100 == 0 or numerical_zero:
            print(
                json.dumps(
                    {
                        "evaluated": len(records),
                        "solver_seconds": solver_seconds,
                        "wall_seconds": time.monotonic() - started,
                        "best_objective": best_objective,
                        "numerical_zero": numerical_zero,
                    }
                ),
                flush=True,
            )
        if numerical_zero:
            break
    wall_seconds = time.monotonic() - started
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "pool_count": 757,
        "evaluated_count": len(records),
        "fresh_evaluations": len(records),
        "cached_evaluations": 0,
        "complete_pool": len(records) == 757,
        "solver_seconds": solver_seconds,
        "wall_seconds": wall_seconds,
        "stop_reason": stop_reason,
        "numerical_zero": numerical_zero,
        "exact_fractional_feasibility": exact_feasible,
        "covering_witness": False,
        "global_lower_bound_claim": False,
        "records": records,
        "improvements": improvements,
    }
    assert len(records) <= 757 and solver_seconds <= 160 and wall_seconds <= 200
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.iterdir()) if path.is_file()
    }
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("records", "improvements", "raw_sha256")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        assert args.gate is not None
        run(args.gate)
