# Document:    Existing Hint Pair-Link and Heavy-Hub Diagnostics
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a40b420642af159096b87e7bac3853c51e18020b11ff802f847dd67ecf9975e2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount two proposed pair-link cut families on saved eligible states only."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PAIRS = list(itertools.combinations(range(1, 17), 2))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
QUADS = list(itertools.combinations(range(1, 17), 4))
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordering(row):
    return row["holes"], row["core_overlaps"][0], row["path"]


def main():
    output = HERE / "pair-link-diagnostics.json"
    assert not output.exists()
    inventory_path = HERE / "result.json"
    assert sha(inventory_path) == "6bd68172725a8df464f7c27a56ba70c1cceeb4dc4d67f2e699c0a2d171ed1e62"
    inventory = json.loads(inventory_path.read_text())
    selected = {}
    for row in sorted(inventory["records"], key=ordering):
        if row["eligible"]:
            selected.setdefault(tuple(row["ids"]), row)
    assert len(selected) == 17
    records = []
    for source in selected.values():
        path = ROOT / source["path"]
        assert sha(path) == source["sha256"]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 64
        assert sorted(RANK[block] for block in blocks) == source["ids"]
        counts = {
            size: Counter(
                subset for block in blocks for subset in itertools.combinations(block, size)
            )
            for size in (1, 2, 3, 4)
        }
        assert min(counts[2][pair] for pair in PAIRS) == source["minimum_pair_count"]
        assert sum(counts[3][triple] == 0 for triple in TRIPLES) == source["holes"]
        heavy = []
        for triple in TRIPLES:
            if counts[3][triple] < 6:
                continue
            endpoints = Counter(
                point
                for block in blocks
                if set(triple).issubset(block)
                for point in block
                if point not in triple
            )
            heavy.append(
                {
                    "triple": triple,
                    "multiplicity": counts[3][triple],
                    "outside_degrees": [
                        {"point": point, "degree": endpoints[point]}
                        for point in range(1, 17)
                        if point not in triple
                    ],
                    "repeated_hubs": [
                        point for point, degree in sorted(endpoints.items()) if degree > 1
                    ],
                }
            )
        hub_uses = Counter(point for item in heavy for point in item["repeated_hubs"])
        hub_inside = [
            {
                "source_triple": source_item["triple"],
                "hub": point,
                "containing_heavy_triple": destination["triple"],
            }
            for source_item in heavy
            for point in source_item["repeated_hubs"]
            for destination in heavy
            if point in destination["triple"]
        ]
        triple_violations, quad_violations = [], []
        minimum_slacks = {3: 1000, 4: 1000}
        rows_checked = {3: 0, 4: 0}
        for size, subsets, coefficient, lower, violations in [
            (3, TRIPLES, 1, 13, triple_violations),
            (4, QUADS, 2, 12, quad_violations),
        ]:
            for subset in subsets:
                for pair in itertools.combinations(subset, 2):
                    lhs = 3 * counts[2][pair] - coefficient * counts[size][subset]
                    minimum_slacks[size] = min(minimum_slacks[size], lhs - lower)
                    rows_checked[size] += 1
                    if lhs < lower:
                        violations.append(
                            {
                                "pair": pair,
                                "subset": subset,
                                "pair_count": counts[2][pair],
                                "subset_count": counts[size][subset],
                                "left_hand_side": lhs,
                                "lower_bound": lower,
                                "deficit": lower - lhs,
                            }
                        )
        assert rows_checked == {3: 1680, 4: 10920}
        record = {
            "path": source["path"],
            "sha256": source["sha256"],
            "holes": source["holes"],
            "core_overlaps": source["core_overlaps"],
            "minimum_pair_count": source["minimum_pair_count"],
            "global_partition_maximum": source["maximum_partition_weight"],
            "point_degrees": [counts[1][(point,)] for point in range(1, 17)],
            "degree_histogram": dict(sorted(Counter(counts[1].values()).items())),
            "triple_histogram": dict(sorted(Counter(counts[3][t] for t in TRIPLES).items())),
            "heavy_triples": heavy,
            "hub_use_counts": dict(sorted(hub_uses.items())),
            "reused_hubs": [point for point, uses in sorted(hub_uses.items()) if uses > 1],
            "hub_inside_other_heavy": hub_inside,
            "pair_triple_rows_checked": rows_checked[3],
            "pair_quad_rows_checked": rows_checked[4],
            "pair_triple_minimum_slack": minimum_slacks[3],
            "pair_quad_minimum_slack": minimum_slacks[4],
            "pair_triple_violations": triple_violations,
            "pair_quad_violations": quad_violations,
            "passes_both_pair_link_families": not (triple_violations or quad_violations),
        }
        records.append(record)
    qualifying = sorted(
        (record for record in records if record["passes_both_pair_link_families"]), key=ordering
    )
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "source_sha256": sha(Path(__file__)),
        "inventory_sha256": sha(inventory_path),
        "distinct_states": len(records),
        "pair_triple_rows_checked": 1680 * len(records),
        "pair_quad_rows_checked": 10920 * len(records),
        "qualifying_states": len(qualifying),
        "best_qualifying": qualifying[0] if qualifying else None,
        "selected_prepared_hint": next(
            record for record in records if record["sha256"] == inventory["best"]["sha256"]
        ),
        "records": records,
        "scope": "Exact diagnostics of the 17 previously eligible distinct states. "
        "No mutation of the prepared pair-floor model or seed. Cut validity is being "
        "audited separately; these arithmetic counts do not prove a new lower bound.",
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "distinct_states": len(records),
                "qualifying_states": len(qualifying),
                "best_qualifying": (
                    {key: qualifying[0][key] for key in ["path", "sha256", "holes"]}
                    if qualifying
                    else None
                ),
                "selected_hint_triple_violations": len(
                    result["selected_prepared_hint"]["pair_triple_violations"]
                ),
                "selected_hint_quad_violations": len(
                    result["selected_prepared_hint"]["pair_quad_violations"]
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
