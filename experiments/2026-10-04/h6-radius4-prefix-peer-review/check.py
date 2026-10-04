# Document:    H6 Radius-Four Prefix Peer Review
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      81ee9abe5dd9d17d287bce3b51e0beb8e615124a6b2b54620263f351dfc5bba1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount saved tiny fixture families independently, without invoking any native binary."""

import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = HERE.parent / "h6-strict-hole-radius4-prefix-pilot"
MANIFEST_SHA = "05d72d833e4005aad2b06af0bc4064bd03fac53a2c3030009f2665efd9c77111"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(PILOT / "manifest.json") == MANIFEST_SHA
    manifest = json.loads((PILOT / "manifest.json").read_text())
    for path, digest in manifest["pins"].items():
        assert sha(ROOT / path) == digest, path
    controls = json.loads((PILOT / "controls.json").read_text())
    assert controls["passed"] and not controls["production_search_launched"]
    assert (
        controls["production_prefixes_explored"] == controls["production_replacement_tuples"] == 0
    )
    blocks = list(itertools.combinations(range(1, 8), 5))
    rank = {block: i for i, block in enumerate(blocks)}
    all_triples = set(itertools.combinations(range(1, 8), 3))
    covers = [set(itertools.combinations(block, 3)) for block in blocks]
    receipts = []
    for fixture in controls["fixtures"]:
        command = fixture["command"]
        initial_path, directory = Path(command[1]), Path(command[4])
        assert sha(initial_path) == fixture["input_sha256"]
        assert sha(directory / "candidates.tsv") == fixture["ledger_sha256"]
        initial = [
            rank[tuple(map(int, line.split()))] for line in initial_path.read_text().splitlines()
        ]
        assert initial == fixture["ids"]
        assert len(initial) == len(set(initial))
        original = set(initial)
        holes = len(all_triples - set().union(*(covers[i] for i in initial)))
        assert holes == fixture["holes"]
        expected = {}
        families_visited, exact_distance_families = 0, 0
        # Entire-family enumeration, not deletion/addition enumeration:
        # choose any same-size family from the full21-block universe first.
        for family in itertools.combinations(range(21), len(original)):
            families_visited += 1
            if len(original - set(family)) != 4:
                continue
            exact_distance_families += 1
            uncovered = all_triples - set().union(*(covers[i] for i in family))
            if len(uncovered) <= holes - 1:
                expected[family] = len(uncovered)
        actual = {}
        with (directory / "candidates.tsv").open() as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        assert [int(row["candidate"]) for row in rows] == list(range(1, len(rows) + 1))
        for row in rows:
            path = directory / f"candidate-{row['candidate']}.txt"
            family = tuple(
                rank[tuple(map(int, line.split()))] for line in path.read_text().splitlines()
            )
            assert len(family) == len(set(family)) == len(original)
            assert family == tuple(sorted(family)) and family not in actual
            assert int(row["distance"]) == 4
            assert sorted(original - set(family)) == list(map(int, row["drop_ids"].split(",")))
            assert sorted(set(family) - original) == list(map(int, row["add_ids"].split(",")))
            actual[family] = int(row["holes"])
        assert actual == expected
        assert (
            len(actual) == fixture["oracle_candidates"] == len(list(directory.glob("candidate-*")))
        )
        assert exact_distance_families == fixture["oracle_tuples"]
        summary = fixture["native_summary"]
        assert summary["status"] == "complete" and summary["candidates"] == len(actual)
        assert len(summary["shells"]) == 1 and summary["shells"][0]["complete"]
        assert summary["shells"][0]["distance"] == 4
        receipts.append(
            {
                "initial_ids": initial,
                "initial_holes": holes,
                "entire_families_visited": families_visited,
                "exact_distance_families": exact_distance_families,
                "candidates": len(actual),
                "candidate_set_equality": True,
            }
        )
    result = {
        "passed": True,
        "launch_permission": "Root decides separately.",
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": sha(PILOT / "search.cpp"),
        "runner_sha256": sha(PILOT / "run.py"),
        "rehash_pin_count": len(manifest["pins"]),
        "fixtures": receipts,
        "source_review": {
            "ordered_suffix_maintained": True,
            "top_remaining_residual_gain_bound_safe": True,
            "necessary_residual_gain_floor_safe": True,
            "nonpositive_demand_keeps_all_completions": True,
            "equal_masks_remain_distinct_full_blocks": True,
            "residual_mask_width_at_most46": True,
            "no_pair_weak_or_core_search_filters": True,
            "complete_exact_distance4_not_combined_radius_claim": True,
            "candidate_dual_verification_and_postclassification": True,
        },
        "native_binary_invocations": 0,
        "actual_h6_prefixes_explored": 0,
        "scope": "Read-only source review and independent complete-family recount of "
        "saved v7 controls. No real-H6 prefix, replacement tuple, or production search. "
        "No claim that the timed real-H6 shell will finish.",
    }
    (HERE / "review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "rehash_pin_count": result["rehash_pin_count"],
                "fixture_candidates": [row["candidates"] for row in receipts],
            }
        )
    )


if __name__ == "__main__":
    main()
