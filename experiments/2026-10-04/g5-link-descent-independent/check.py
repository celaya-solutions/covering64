#!/usr/bin/env python3
# Document:    Independent Registry Filtered Graph Five Descent Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Validate fixed graph rows, all initial neighbors, registry receipts and cache."""

import copy
import json

from independent import (
    GRAPH,
    HERE,
    ROOT,
    SOURCE,
    basis,
    check_vector,
    digest,
    sha,
    shifted,
    validate_ranking,
    validate_receipt,
)


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    preflight = json.loads((SOURCE / "preflight.json").read_text())
    assert manifest["source_sha256"] == preflight["source_sha256"] == sha(SOURCE / "run.py")
    assert sha(SOURCE / "registry.py") == manifest["registry_source_sha256"]
    assert sha(SOURCE / "preflight.json") == manifest["preflight_sha256"]
    for path, expected_hash in manifest["input_files"].items():
        assert sha(ROOT / path) == expected_hash
    blocks, _, ordinary, heavy, rows = basis()
    ids = [blocks.index(block) for block in ordinary]
    family_sha = digest({"rows": rows, "ordinary_global_ids": ids, "graph_index": 5})
    assert family_sha == manifest["family_sha256"] == preflight["family_sha256"]
    assert ids == manifest["ordinary_global_ids"]
    assert manifest["graph_index"] == 5 and tuple(manifest["hub_excesses"]) == GRAPH
    assert manifest["hub_pair_targets"] == [7, 5, 5, 5, 5, 7]
    assert manifest["six_row_changes"] == preflight["six_row_changes"]
    assert [(r["row"], r["before"], r["after"]) for r in manifest["six_row_changes"]] == [
        (622, [5, 7], [7, 7]),
        (626, [5, 7], [5, 5]),
        (630, [5, 7], [5, 5]),
        (664, [5, 7], [5, 5]),
        (668, [5, 7], [5, 5]),
        (690, [5, 7], [7, 7]),
    ]
    baseline = manifest["baseline"]
    chosen = tuple(blocks[i] for i in baseline["heavy_global_ids"])
    assert len(chosen) == len(set(chosen)) == 28 and digest(chosen) == baseline["heavy_sha256"]
    assert baseline["family_sha256"] == family_sha and baseline["status"] == "OPTIMAL"
    assert baseline["shifted_rows_sha256"] == digest(shifted(rows, heavy, chosen))
    assert baseline["cache_key"] == digest(
        {
            "family_sha256": family_sha,
            "heavy_sha256": baseline["heavy_sha256"],
            "shifted_rows_sha256": baseline["shifted_rows_sha256"],
        }
    )
    assert not validate_receipt(chosen, baseline["registry"])
    assert baseline["registry"] == preflight["baseline_registry"]
    result = json.loads((ROOT / baseline["result_path"]).read_text())
    assert sha(ROOT / baseline["result_path"]) == baseline["result_sha256"]
    assert (
        result["branch_elastic_objective"]
        == baseline["objective"]
        == (manifest["baseline_elastic_objective"])
        == 15.06922063054413
    )
    residual = check_vector(baseline)
    initial = manifest["initial_cache"]
    assert len(initial) == len({record["cache_key"] for record in initial}) == 2
    assert initial[0] == baseline
    assert {record["objective"] for record in initial} == {15.06922063054413, 15.317006713016973}
    for record in initial:
        candidate = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert record["status"] == "OPTIMAL" and record["source_round"] == 0
        assert record["family_sha256"] == family_sha
        assert record["heavy_sha256"] == digest(candidate)
        assert record["shifted_rows_sha256"] == digest(shifted(rows, heavy, candidate))
        assert record["cache_key"] == digest(
            {
                "family_sha256": family_sha,
                "heavy_sha256": record["heavy_sha256"],
                "shifted_rows_sha256": record["shifted_rows_sha256"],
            }
        )
        assert not validate_receipt(candidate, record["registry"])
        assert sha(ROOT / record["result_path"]) == record["result_sha256"]
        saved = json.loads((ROOT / record["result_path"]).read_text())
        assert saved["status"] == "OPTIMAL"
        assert saved["branch_elastic_objective"] == record["objective"]
        check_vector(record)
    bundle = json.loads(
        (ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json").read_text()
    )
    assert bundle["heavy_global_ids"] == [blocks.index(block) for block in heavy]
    accepted, rejected = validate_ranking(
        chosen, preflight["neighbors"], family_sha, bundle["cuts"]
    )
    assert (accepted, rejected) == (86, 41)
    assert preflight["generated"] == manifest["initial_generated"] == 127
    assert accepted == preflight["accepted"] == manifest["initial_accepted"]
    assert rejected == preflight["rejected"] == manifest["initial_rejected"]
    assert manifest["budgets"] == {
        "rounds": 3,
        "fresh_lps": 350,
        "solver_seconds": 60,
        "wall_seconds": 90,
        "each_lp_seconds": 1,
        "workers": 1,
        "seed": 2026104,
    }
    damaged = copy.deepcopy(preflight["neighbors"])
    damaged[-1] = damaged[0]
    try:
        validate_ranking(chosen, damaged, family_sha, bundle["cuts"])
        raise RuntimeError("Duplicate control was accepted")
    except AssertionError:
        pass
    damaged_receipt = copy.deepcopy(baseline["registry"])
    damaged_receipt["links"][0]["both_transports"][0]["physical_to_representative"][0] = 0
    try:
        validate_receipt(chosen, damaged_receipt)
        raise RuntimeError("Damaged mapping control was accepted")
    except AssertionError:
        pass
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "independent_basis_sha256": sha(HERE / "independent.py"),
        "source_sha256": sha(SOURCE / "run.py"),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "preflight_sha256": sha(SOURCE / "preflight.json"),
        "family_sha256": family_sha,
        "graph_index": 5,
        "six_hub_rows_checked": True,
        "neighbors": 127,
        "accepted": accepted,
        "rejected": rejected,
        "link_receipts_checked": 516,
        "damaged_controls_rejected": 2,
        "baseline_residual_recounted": residual,
        "initial_cache_entries_checked": 2,
        "source_review": [
            "Only registry-accepted neighbors reach LP calls; rejection receipts saved",
            "Only OPTIMAL exact same-family/tuple/row profiles enter cache",
            "Frozen single-worker one-second GLOP method; at most3 rounds/350 fresh calls",
            "Stop margins58.9solver/86wall before solve and83wall before neighborhood",
            "Assertions60solver/90wall; descend only after every accepted result OPTIMAL",
            "Fixed graph5 branch baseline separate from broad all-graph objective",
        ],
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
