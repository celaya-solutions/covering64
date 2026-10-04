#!/usr/bin/env python3
# Document:    Independent Graph One Whole Link Pool Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind exactly 757 screened states to graph-one rows and four-link receipts."""

import gzip
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "g1-whole-link-pool"
RAW = ROOT / "experiments/scratch/g1-whole-link-pool-20261004"
SCREEN = HERE.parent / "g1-larger-independent/audit.json"
helper_path = HERE.parent / "g1-link-descent-independent/independent.py"
spec = importlib.util.spec_from_file_location("independent_g1_pool", helper_path)
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
    assert screen["passed"] and screen["whole_link_survivors"] == 757
    assert manifest["screen_audit_sha256"] == ind.sha(SCREEN)
    pool_path = ROOT / screen["whole_link_pool_path"]
    assert ind.sha(pool_path) == screen["whole_link_pool_sha256"]
    unexcluded = json.loads(gzip.decompress(pool_path.read_bytes()))
    baseline = manifest["baseline"]
    best_ids = set(baseline["heavy_global_ids"])
    expected_order = sorted(unexcluded, key=lambda ids: (28 - len(best_ids & set(ids)), ids))
    pool = json.loads((SOURCE / "pool.json").read_text())["heavy_global_ids"]
    assert pool == expected_order and len(pool) == len({tuple(ids) for ids in pool}) == 757
    assert manifest["pool_sha256"] == ind.sha(SOURCE / "pool.json")
    inventory_path = ROOT / manifest["inventory_path"]
    assert ind.sha(inventory_path) == manifest["inventory_sha256"]
    inventory = json.loads(gzip.decompress(inventory_path.read_bytes()))
    assert len(inventory) == 757
    blocks, _, ordinary, heavy, rows = ind.basis()
    family = ind.digest(
        {"rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary], "graph_index": 1}
    )
    assert family == manifest["family_sha256"]
    assert manifest["graph_index"] == 1 and manifest["hub_excesses"] == [0, 1, 1, 1, 1, 0]
    assert manifest["hub_pair_targets"] == [5, 6, 6, 6, 6, 5]
    assert manifest["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    branch_manifest = json.loads((HERE.parent / "g1-link-descent/manifest.json").read_text())
    branch_result = json.loads((HERE.parent / "g1-link-descent/result.json").read_text())
    assert manifest["six_row_changes"] == branch_manifest["six_row_changes"]
    assert baseline == branch_result["trajectory"][-1]
    assert manifest["baseline_elastic_objective"] == baseline["objective"] == 7.52051548546158
    baseline_residual = ind.check_vector(baseline)
    cache = json.loads(
        (ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json").read_text()
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
    assert distances == {6: 72, 7: 685}
    assert manifest["cached_count"] == 0 and manifest["optimization_calls"] == 0
    assert manifest["budgets"] == {
        "pool_count": 757,
        "each_lp_seconds": 1,
        "solver_seconds": 160,
        "wall_seconds": 200,
        "workers": 1,
        "seed": 2026104,
    }
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "helper_sha256": ind.sha(helper_path),
        "source_sha256": ind.sha(SOURCE / "run.py"),
        "manifest_sha256": ind.sha(SOURCE / "manifest.json"),
        "screen_audit_sha256": ind.sha(SCREEN),
        "pool_sha256": ind.sha(SOURCE / "pool.json"),
        "inventory_sha256": ind.sha(inventory_path),
        "pool_count": 757,
        "shifted_rows_checked": 757 * 697,
        "registry_links_checked": 757 * 4,
        "cached_candidates": 0,
        "distances": dict(distances),
        "baseline_residual_recounted": baseline_residual,
        "source_review": [
            "Only frozen inventory entries are solved; no candidate expansion or cache reuse",
            "Same one-worker one-second GLOP helper and fixed graph-one completion model",
            "Stop before158.9 solver seconds or195 wall seconds; assert160/200 totals",
            "Immediately stop at numerical zero after bounded exact-primal attempts",
            "UNKNOWN/timeouts remain inconclusive; no integer-cover or global-bound claim",
        ],
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
