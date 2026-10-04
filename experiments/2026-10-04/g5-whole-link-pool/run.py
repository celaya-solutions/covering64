# Document:    Fixed-g5 Whole-Link Survivor Pool LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      87b2dab17d4f42734e7847c15e75ae061ea9cd8afa6c595906340d50bae529ce
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze and screen exactly the 3496 independently checked whole-link survivors."""

import argparse
import gzip
import importlib.util
import json
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = ROOT / "experiments/2026-10-04"
PLAN = DAY / "g5-larger-screen"
CUTS = ROOT / "experiments/scratch/g5-larger-screen-20261004"
PREP = ROOT / "experiments/scratch/g5-whole-link-pool-preparation-20261004"
RAW = ROOT / "experiments/scratch/g5-whole-link-pool-20261004"
SCREEN = DAY / "g5-larger-independent/audit.json"
DESCENT = DAY / "g5-link-continuation"


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


def dump_compressed(path, value):
    Path(path).write_bytes(gzip.compress(json.dumps(value).encode(), mtime=0))


def prepare():
    assert not PREP.exists() and not (HERE / "manifest.json").exists()
    screen = json.loads(SCREEN.read_text())
    assert screen["passed"] and screen["graph_index"] == 5
    assert screen["neighborhoods"]["whole-link"]["combined_unexcluded"] == 3496
    assert screen["neighborhoods"]["whole-link"]["combined_unexcluded_uncached"] == 3496
    assert screen["g5_bundle_sha256"] == sha(CUTS / "g5-cuts.json.gz")
    assert screen["envelope_results_sha256"] == sha(PLAN / "envelope-results.json")
    result = json.loads((DESCENT / "result.json").read_text())
    post_path = DAY / "g5-link-continuation-independent/postcheck.json"
    post = json.loads(post_path.read_text())
    assert post["passed"] and post["result_sha256"] == sha(DESCENT / "result.json")
    assert result["graph_index"] == 5 and result["best_objective"] == 8.152937802508724
    baseline = result["trajectory"][-1]
    family = json.loads((DESCENT / "manifest.json").read_text())["family_sha256"]
    blocks, ordinary, heavy, _, rows, changes = branch.basis()
    pool_path = PLAN / "whole-link-unexcluded.json.gz"
    pool = json.loads(gzip.decompress(pool_path.read_bytes()))
    assert len(pool) == len({tuple(ids) for ids in pool}) == 3496
    fixed = set(result["best_heavy_global_ids"])
    pool.sort(key=lambda ids: (len(fixed - set(ids)), ids))
    old_cache = json.loads(
        (ROOT / "experiments/scratch/g5-link-continuation-20261004/final-cache.json").read_text()
    )
    assert len(old_cache) == 720
    assert result["raw_sha256"]["final-cache.json"] == sha(
        ROOT / "experiments/scratch/g5-link-continuation-20261004/final-cache.json"
    )
    assert not {tuple(ids) for ids in pool} & {
        tuple(record["heavy_global_ids"]) for record in old_cache.values()
    }
    registry = branch.registry_module.Registry()
    conditional = json.loads((CUTS / "g5-cuts.json").read_text())
    broad = json.loads(gzip.decompress((CUTS / "broad-cuts-reference.json.gz").read_bytes()))
    assert conditional["count"] == 720 and broad["count"] == 353
    assert conditional["family_sha256"] == family and conditional["graph_index"] == 5
    assert conditional == json.loads(gzip.decompress((CUTS / "g5-cuts.json.gz").read_bytes()))
    assert conditional["six_row_changes"] == json.loads(json.dumps(changes))
    assert family == data_hash({
        "rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary], "graph_index": 5
    })
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
    dump_compressed(inventory_path, inventory)
    ordered_pool_path = PREP / "pool.json.gz"
    dump_compressed(
        ordered_pool_path,
        {
            "heavy_global_ids": pool,
            "ordering": (
                "Replacement distance from g5 local minimum, then lexicographic global IDs."
            ),
        },
    )
    rows_path = PREP / "unconditional-rows.json.gz"
    dump_compressed(rows_path, rows)
    lp_spec = {
        "ordinary_variables": 1200, "ordinary_bounds": [0, 1], "continuous": True,
        "row_count": 697, "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "slack_rule": "One nonnegative lower slack with coefficient+1 per finite lower bound; "
        "one nonnegative upper slack with coefficient-1 per finite upper bound.",
        "objective": "Minimize sum of all slack variables with coefficient1.",
        "infinite_bound_sentinel": branch.generator.INF,
        "slack_variables": sum(low != branch.generator.INF for _, _, low, _ in rows)
        + sum(high != branch.generator.INF for _, _, _, high in rows),
        "solver": "GLOP", "workers": 1, "time_limit_seconds": 1, "seed": 2026104,
        "solve_source_path": str(Path(branch.sweep.__file__).relative_to(ROOT)),
        "solve_source_sha256": sha(branch.sweep.__file__),
    }
    assert len(ordinary) == lp_spec["ordinary_variables"] == 1200
    assert len(rows) == lp_spec["row_count"] == 697
    assert lp_spec["slack_variables"] == 1390
    dump(PREP / "lp-spec.json", lp_spec)
    inputs = json.loads((PLAN / "inputs.json").read_text())
    inputs.update(json.loads((DESCENT / "manifest.json").read_text())["input_files"])
    paths = [
        Path(__file__),
        SCREEN,
        CUTS / "g5-cuts.json",
        CUTS / "g5-cuts.json.gz",
        CUTS / "broad-cuts-reference.json.gz",
        PLAN / "envelope-results.json",
        PLAN / "whole-link-unexcluded.json.gz",
        DESCENT / "run.py",
        DESCENT / "result.json",
        DESCENT / "manifest.json",
        DESCENT / "registry.py",
        DAY / "g5-link-continuation-independent/postcheck.json",
        ROOT / baseline["vector_path"],
        ROOT / baseline["dual_path"],
        ROOT / "experiments/scratch/g5-link-continuation-20261004/final-cache.json",
        Path(branch.sweep.__file__),
        Path(branch.generator.__file__),
        branch.generator.LP_CORE,
    ]
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest
    source_snapshot = []
    for relative, digest in sorted(inputs.items()):
        if Path(relative).suffix != ".py":
            continue
        destination = PREP / "frozen-sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
        assert sha(destination) == digest
        source_snapshot.append({"original_path": relative,
                                "path": str(destination.relative_to(ROOT)), "sha256": digest})
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision_at_freeze": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": inputs,
        "screen_audit_sha256": sha(SCREEN),
        "graph_index": 5,
        "hub_excesses": [2, 0, 0, 0, 0, 2],
        "hub_pair_targets": [7, 5, 5, 5, 5, 7],
        "family_sha256": family,
        "six_row_changes": changes,
        "pool_count": 3496,
        "pool_path": str(ordered_pool_path.relative_to(ROOT)),
        "pool_sha256": sha(ordered_pool_path),
        "inventory_path": str(inventory_path.relative_to(ROOT)),
        "inventory_sha256": sha(inventory_path),
        "unconditional_rows_path": str(rows_path.relative_to(ROOT)),
        "unconditional_rows_sha256": sha(rows_path),
        "lp_spec_path": str((PREP / "lp-spec.json").relative_to(ROOT)),
        "lp_spec_sha256": sha(PREP / "lp-spec.json"),
        "source_snapshot": source_snapshot,
        "distance_histogram": dict(sorted(Counter(
            candidate["distance_replacements"] for candidate in inventory
        ).items())),
        "baseline": baseline,
        "baseline_elastic_objective": result["best_objective"],
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "cached_count": 0,
        "budgets": {
            "pool_count": 3496,
            "each_lp_seconds": 1,
            "solver_seconds": 540,
            "wall_seconds": 630,
            "workers": 1,
            "seed": 2026104,
        },
        "optimization_calls": 0,
        "stop_policy": (
            "Stop immediately on numerical residual <=1e-7, attempt exact rational primal "
            "checks, then stop even if exact reconstruction fails."
        ),
        "scope": (
            "Only this frozen 3496-state pool under g5; "
            "no other candidates and no broad-model cache reuse."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "pool": 3496,
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
    pool_path = ROOT / manifest["pool_path"]
    assert sha(pool_path) == manifest["pool_sha256"]
    for path_key, sha_key in (("unconditional_rows_path", "unconditional_rows_sha256"),
                              ("lp_spec_path", "lp_spec_sha256")):
        assert sha(ROOT / manifest[path_key]) == manifest[sha_key]
    for saved in manifest["source_snapshot"]:
        assert sha(ROOT / saved["path"]) == saved["sha256"]
    inventory_path = ROOT / manifest["inventory_path"]
    assert sha(inventory_path) == manifest["inventory_sha256"]
    inventory = json.loads(gzip.decompress(inventory_path.read_bytes()))
    assert len(inventory) == 3496
    assert [item["heavy_global_ids"] for item in inventory] == json.loads(
        gzip.decompress(pool_path.read_bytes())
    )["heavy_global_ids"]
    assert not RAW.exists() and not (HERE / "result.json").exists()
    RAW.mkdir()
    for path in [Path(__file__), HERE / "manifest.json", pool_path, gate_path,
                 ROOT / manifest["lp_spec_path"], ROOT / manifest["unconditional_rows_path"]]:
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
        "graph_index": 5,
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
        if solver_seconds >= 538.9 or time.monotonic() - started >= 625:
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
        model_path = RAW / f"rank-{rank:04d}-rows.json.gz"
        dump_compressed(model_path, shifted)
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
            model_path=str(model_path.relative_to(ROOT)),
            model_sha256=sha(model_path),
        )
        if values is not None:
            vector_path = RAW / f"rank-{rank:04d}-values.json"
            dual_path = RAW / f"rank-{rank:04d}-dual.json"
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
                            graph_index=5,
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
        with (RAW / "evaluations.jsonl").open("a") as log:
            log.write(json.dumps(record) + "\n")
        if (rank + 1) % 100 == 0 or numerical_zero:
            dump(RAW / "evaluations.json", records)
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
    dump(RAW / "evaluations.json", records)
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "pool_count": 3496,
        "evaluated_count": len(records),
        "fresh_evaluations": len(records),
        "cached_evaluations": 0,
        "complete_pool": len(records) == 3496,
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
    assert len(records) <= 3496 and solver_seconds <= 540 and wall_seconds <= 630
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
