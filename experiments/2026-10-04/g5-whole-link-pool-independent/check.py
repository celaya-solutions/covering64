#!/usr/bin/env python3
# Document:    Independent Graph Five Whole Link Pool Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind exactly 3496 screened states to graph-five rows and four-link receipts."""

import gzip
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "g5-whole-link-pool"
RAW = ROOT / "experiments/scratch/g5-whole-link-pool-20261004"
SCREEN = HERE.parent / "g5-larger-independent/audit.json"
helper_path = HERE.parent / "g5-link-descent-independent/independent.py"
spec = importlib.util.spec_from_file_location("independent_g5_pool", helper_path)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    assert manifest["source_sha256"] == ind.sha(SOURCE / "run.py")
    for path, expected_hash in manifest["input_files"].items():
        assert ind.sha(ROOT / path) == expected_hash
    screen = json.loads(SCREEN.read_text())
    assert screen["passed"] and screen["neighborhoods"]["whole-link"]["combined_unexcluded"] == 3496
    assert manifest["screen_audit_sha256"] == ind.sha(SCREEN)
    pool_path = HERE.parent / "g5-larger-screen/whole-link-unexcluded.json.gz"
    unexcluded = json.loads(gzip.decompress(pool_path.read_bytes()))
    baseline = manifest["baseline"]
    best_ids = set(baseline["heavy_global_ids"])
    expected_order = sorted(unexcluded, key=lambda ids: (28 - len(best_ids & set(ids)), ids))
    ordered_path = ROOT / manifest["pool_path"]
    pool = json.loads(gzip.decompress(ordered_path.read_bytes()))["heavy_global_ids"]
    assert pool == expected_order and len(pool) == len({tuple(ids) for ids in pool}) == 3496
    assert manifest["pool_sha256"] == ind.sha(ordered_path)
    inventory_path = ROOT / manifest["inventory_path"]
    assert ind.sha(inventory_path) == manifest["inventory_sha256"]
    inventory = json.loads(gzip.decompress(inventory_path.read_bytes()))
    assert len(inventory) == 3496
    blocks, _, ordinary, heavy, rows = ind.basis()
    family = ind.digest(
        {"rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary], "graph_index": 5}
    )
    assert family == manifest["family_sha256"]
    assert manifest["graph_index"] == 5 and manifest["hub_excesses"] == [2, 0, 0, 0, 0, 2]
    assert manifest["hub_pair_targets"] == [7, 5, 5, 5, 5, 7]
    assert manifest["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    branch_manifest = json.loads((HERE.parent / "g5-link-continuation/manifest.json").read_text())
    branch_result = json.loads((HERE.parent / "g5-link-continuation/result.json").read_text())
    assert manifest["six_row_changes"] == branch_manifest["six_row_changes"]
    assert baseline == branch_result["trajectory"][-1]
    assert manifest["baseline_elastic_objective"] == baseline["objective"] == 8.152937802508724
    baseline_residual = ind.check_vector(baseline)
    cache = json.loads(
        (ROOT / "experiments/scratch/g5-link-continuation-20261004/final-cache.json").read_text()
    )
    cached_ids = {tuple(record["heavy_global_ids"]) for record in cache.values()}
    distances = Counter()
    for rank, (ids, entry) in enumerate(zip(pool, inventory, strict=True)):
        assert entry["rank"] == rank and entry["heavy_global_ids"] == ids
        assert tuple(ids) not in cached_ids
        chosen = tuple(blocks[i] for i in ids)
        assert len(chosen) == len(set(chosen)) == 28 and set(chosen) <= set(heavy)
        assert entry["heavy_sha256"] == ind.digest(chosen)
        assert entry["shifted_rows_sha256"] == ind.digest(ind.shifted(rows, heavy, chosen))
        assert entry["family_sha256"] == family
        assert entry["profile_key"] == ind.digest(
            {
                "family_sha256": family,
                "heavy_sha256": entry["heavy_sha256"],
                "shifted_rows_sha256": entry["shifted_rows_sha256"],
            }
        )
        assert not ind.validate_receipt(chosen, entry["registry"])
        distance = 28 - len(best_ids & set(ids))
        assert entry["distance_replacements"] == distance
        distances[distance] += 1
    assert distances == {5: 60, 6: 924, 7: 2512}
    assert manifest["cached_count"] == 0 and manifest["optimization_calls"] == 0
    assert manifest["budgets"] == {
        "pool_count": 3496,
        "each_lp_seconds": 1,
        "solver_seconds": 540,
        "wall_seconds": 630,
        "workers": 1,
        "seed": 2026104,
    }
    assert manifest["distance_histogram"] == {str(k): v for k, v in distances.items()}
    for item in manifest["source_snapshot"]:
        assert ind.sha(ROOT / item["path"]) == item["sha256"]
        assert ind.sha(ROOT / item["original_path"]) == item["sha256"]
    rows_path = ROOT / manifest["unconditional_rows_path"]
    assert ind.sha(rows_path) == manifest["unconditional_rows_sha256"]
    assert json.loads(gzip.decompress(rows_path.read_bytes())) == json.loads(json.dumps(rows))
    spec_path = ROOT / manifest["lp_spec_path"]
    assert ind.sha(spec_path) == manifest["lp_spec_sha256"]
    spec = json.loads(spec_path.read_text())
    assert spec["ordinary_variables"] == 1200 and spec["ordinary_bounds"] == [0, 1]
    assert spec["continuous"] and spec["slack_variables"] == 1390 and spec["row_count"] == 697
    assert spec["solver"] == "GLOP" and spec["workers"] == spec["time_limit_seconds"] == 1
    assert spec["seed"] == 2026104 and spec["infinite_bound_sentinel"] == ind.INF
    assert spec["ordinary_global_ids"] == manifest["ordinary_global_ids"]
    assert ind.sha(ROOT / spec["solve_source_path"]) == spec["solve_source_sha256"]
    # The producer stores every shifted model before using the unchanged audited LP helper.
    source = (SOURCE / "run.py").read_text()
    assert "solver_seconds >= 538.9" in source and "time.monotonic() - started >= 625" in source
    assert "solver_seconds <= 540 and wall_seconds <= 630" in source
    assert "branch.sweep.solve(shifted)" in source and "time_limit_seconds" in source
    assert "recomputed_l1_residual" in source and "if numerical_zero:" in source
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "helper_sha256": ind.sha(helper_path),
        "source_sha256": ind.sha(SOURCE / "run.py"),
        "manifest_sha256": ind.sha(SOURCE / "manifest.json"),
        "screen_audit_sha256": ind.sha(SCREEN),
        "pool_sha256": ind.sha(ordered_path),
        "inventory_sha256": ind.sha(inventory_path),
        "pool_count": 3496,
        "shifted_rows_checked": 3496 * 697,
        "registry_links_checked": 3496 * 4,
        "cached_candidates": 0,
        "distances": dict(distances),
        "baseline_residual_recounted": baseline_residual,
        "source_review": [
            "Only frozen inventory entries are solved; no candidate expansion or cache reuse",
            "Same one-worker one-second GLOP helper and fixed graph-five completion model",
            "Stop before538.9 solver seconds or625 wall seconds; assert540/630 totals",
            "Immediately stop at numerical zero after bounded exact-primal attempts",
            "UNKNOWN/timeouts remain inconclusive; no integer-cover or global-bound claim",
        ],
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
