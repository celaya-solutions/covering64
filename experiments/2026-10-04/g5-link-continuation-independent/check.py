# Document:    Independent Fixed-g5 Continuation Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild fixed rows, finite neighbors and cache identity without optimization."""

import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g5-link-continuation"
spec = importlib.util.spec_from_file_location(
    "independent_g5_continuation", DAY / "g5-link-descent-independent/independent.py"
)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def read(path):
    return json.loads(Path(path).read_text())


def main():
    assert not (HERE / "audit.json").exists()
    manifest = read(SOURCE / "manifest.json")
    preflight = read(SOURCE / "preflight.json")
    assert manifest["source_sha256"] == preflight["source_sha256"] == ind.sha(SOURCE / "run.py")
    assert manifest["registry_source_sha256"] == ind.sha(SOURCE / "registry.py")
    assert manifest["preflight_sha256"] == ind.sha(SOURCE / "preflight.json")
    for path, expected in manifest["input_files"].items():
        assert ind.sha(ROOT / path) == expected
    blocks, _, ordinary, heavy, rows = ind.basis()
    ids = [blocks.index(block) for block in ordinary]
    family_sha = ind.digest({"rows": rows, "ordinary_global_ids": ids, "graph_index": 5})
    assert family_sha == manifest["family_sha256"] == preflight["family_sha256"]
    assert ids == manifest["ordinary_global_ids"]
    assert manifest["graph_index"] == 5 and tuple(manifest["hub_excesses"]) == ind.GRAPH
    assert manifest["hub_pair_targets"] == [7, 5, 5, 5, 5, 7]
    assert manifest["six_row_changes"] == preflight["six_row_changes"]
    assert [(r["row"], r["before"], r["after"]) for r in manifest["six_row_changes"]] == [
        (622, [5, 7], [7, 7]), (626, [5, 7], [5, 5]), (630, [5, 7], [5, 5]),
        (664, [5, 7], [5, 5]), (668, [5, 7], [5, 5]), (690, [5, 7], [7, 7])
    ]
    previous_path = DAY / "g5-link-descent/result.json"
    previous = read(previous_path)
    post_path = DAY / "g5-link-descent-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == ind.sha(previous_path)
    cache_path = ROOT / "experiments/scratch/g5-link-descent-20261004/final-cache.json"
    assert ind.sha(cache_path) == previous["raw_sha256"]["final-cache.json"]
    old_cache = read(cache_path)
    assert manifest["initial_cache"] == [record for _, record in sorted(old_cache.items())]
    assert len(old_cache) == len(manifest["initial_cache"]) == 255
    baseline = manifest["baseline"]
    assert baseline == old_cache[previous["trajectory"][-1]["cache_key"]]
    assert baseline["heavy_global_ids"] == previous["best_heavy_global_ids"]
    assert baseline["objective"] == manifest["baseline_elastic_objective"] == 11.500690015970484
    chosen = tuple(blocks[i] for i in baseline["heavy_global_ids"])
    assert not ind.validate_receipt(chosen, preflight["baseline_registry"])
    baseline_residual = ind.check_vector(baseline)
    for key, record in old_cache.items():
        candidate = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert len(candidate) == len(set(candidate)) == 28
        assert record["status"] == "OPTIMAL" and record["family_sha256"] == family_sha
        assert record["heavy_sha256"] == ind.digest(candidate)
        assert record["shifted_rows_sha256"] == ind.digest(ind.shifted(rows, heavy, candidate))
        assert key == record["cache_key"] == ind.digest({
            "family_sha256": family_sha, "heavy_sha256": record["heavy_sha256"],
            "shifted_rows_sha256": record["shifted_rows_sha256"]
        })
        assert all(not excluded for _, excluded in ind.classify(candidate))
        for label in ("vector", "dual"):
            assert ind.sha(ROOT / record[f"{label}_path"]) == record[f"{label}_sha256"]
        ind.check_vector(record)
    bundle = read(ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json")
    assert bundle["heavy_global_ids"] == [blocks.index(block) for block in heavy]
    accepted, rejected = ind.validate_ranking(
        chosen, preflight["neighbors"], family_sha, bundle["cuts"]
    )
    assert (accepted, rejected) == (88, 40)
    assert preflight["generated"] == manifest["initial_generated"] == 128
    assert accepted == preflight["accepted"] == manifest["initial_accepted"]
    assert rejected == preflight["rejected"] == manifest["initial_rejected"]
    assert manifest["budgets"] == {
        "rounds": 10, "fresh_lps": 1000, "solver_seconds": 150, "wall_seconds": 200,
        "each_lp_seconds": 1, "workers": 1, "seed": 2026104
    }
    damaged = copy.deepcopy(preflight["neighbors"])
    damaged[-1] = damaged[0]
    try:
        ind.validate_ranking(chosen, damaged, family_sha, bundle["cuts"])
    except AssertionError:
        pass
    else:
        raise AssertionError("Duplicate state accepted")
    damaged = copy.deepcopy(preflight["baseline_registry"])
    damaged["links"][0]["both_transports"][0]["physical_to_representative"][0] = 0
    try:
        ind.validate_receipt(chosen, damaged)
    except AssertionError:
        pass
    else:
        raise AssertionError("Damaged mapping accepted")
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": ind.sha(__file__),
        "independent_basis_sha256": ind.sha(DAY / "g5-link-descent-independent/independent.py"),
        "source_sha256": ind.sha(SOURCE / "run.py"),
        "manifest_sha256": ind.sha(SOURCE / "manifest.json"),
        "preflight_sha256": ind.sha(SOURCE / "preflight.json"),
        "previous_postcheck_sha256": ind.sha(post_path),
        "family_sha256": family_sha, "graph_index": 5,
        "neighbors": 128, "accepted": 88, "rejected": 40,
        "initial_cache_entries_checked": 255, "damaged_controls_rejected": 2,
        "baseline_residual_recounted": baseline_residual,
        "source_review": [
            "Only the prior hash-bound 255 fixed-g5 records initialize the cache",
            "Each cached primal is recounted and every registry link is independently classified",
            "Original14 broad cuts rank only; no pruning of registry-accepted neighbors",
            "One second and one worker per LP; caps10rounds/1000fresh/150solver/200wall",
            "Guards148.9solver/193before-neighborhood/196inner-wall",
            "Ordinary descent requires all accepted neighbors evaluated OPTIMAL",
            "Exact primal records are saved and selected independently of numerical OPTIMAL",
            "UNKNOWN, timeouts and incomplete neighborhoods remain inconclusive",
        ],
        "scope": "Preparation gate only; no solver execution or lower-bound claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
