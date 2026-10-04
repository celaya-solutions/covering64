# Document:    Independent Weak-Pair Native Control Comparison
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fff66ae334c4c1894806363fb7d5a61e8f48c1ab1634e794db01ee90dffb52c2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compare finite native snapshots with full independent inclusion recounts."""

import itertools
import json
from pathlib import Path

import oracle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-swap-scan-independent-20261004"


def compare_state(native, direct):
    oracle.require(native["ids"] == direct["ids"], "state IDs differ")
    oracle.require(native["counts"] == direct["counts"], "direct counters differ")
    oracle.require(native["pair_metrics"] == direct["pair_metrics"], "per-pair metrics differ")
    expected = direct["metrics"] | {"cardinality": 64, "legal": direct["legal"]}
    oracle.require(native["metrics"] == expected, "state metrics differ")
    return expected


def compare_universe(native):
    oracle.require(len(native["columns"]) == 4368, "block-column count")
    for index, (points, pairs, triples, quads) in enumerate(native["columns"]):
        oracle.require(tuple(points) == oracle.SUBSETS[5][index], "block lex order")
        for size, actual in ((2, pairs), (3, triples), (4, quads)):
            expected = sorted(
                oracle.INDEX[size][subset] for subset in itertools.combinations(points, size)
            )
            oracle.require(sorted(actual) == expected, "column membership mismatch")
    oracle.require(len(native["pair_rows"]) == 120, "pair-row count")
    for index, (triples, quads) in enumerate(native["pair_rows"]):
        pair = oracle.MASKS[2][index]
        for size, actual in ((3, triples), (4, quads)):
            expected = [i for i, mask in enumerate(oracle.MASKS[size]) if mask & pair == pair]
            oracle.require(sorted(actual) == expected, "pair-row membership mismatch")


def compare(suffix):
    direct = json.loads((RAW / "oracle-snapshots.json").read_text())
    totals = {
        "trials": 0,
        "invalid_operations_rejected": 0,
        "predicate_rejections": 0,
        "rank_controls": 0,
        "subset_counters_compared": 0,
    }
    for base in ("old_h12", "cp_final"):
        events = [
            json.loads(line)
            for line in (RAW / f"{base}-{suffix}.stdout.jsonl").read_text().splitlines()
        ]
        oracle.require(not (RAW / f"{base}-{suffix}.stderr.txt").read_text(), "sanitizer stderr")
        oracle.require(events[0]["event"] == "universe", "missing universe control")
        compare_universe(events[0])
        oracle.require(events[1]["event"] == "initial", "missing initial state")
        compare_state(events[1]["state"], direct["bases"][base])
        selected = [row for row in direct["snapshots"] if row["case"]["base"] == base]
        oracle.require(len(events) == len(selected) + 3, "event count")
        for event, expected in zip(events[2:-1], selected, strict=True):
            oracle.require(event["event"] == "trial", "not trial event")
            oracle.require(
                (event["out"], event["in"]) == (expected["case"]["out"], expected["case"]["in"]),
                "wrong control swap",
            )
            metrics = compare_state(event["state"], expected)
            oracle.require(event["evaluation"] == metrics, "affected-pair evaluation mismatch")
            flags = [int(i in expected["affected_pairs"]) for i in range(120)]
            oracle.require(event["affected"] == flags, "affected pair union mismatch")
            overlap = expected["case"]["intersection"]
            oracle.require(sum(flags) == 20 - overlap * (overlap - 1) // 2, "union size")
            totals["subset_counters_compared"] += 2500
        final = events[-1]
        oracle.require(final["event"] == "finished" and final["rollback_passed"], "rollback")
        oracle.require(
            final["trials"] == len(selected) and final["optimizer_launches"] == 0, "control scope"
        )
        oracle.require(
            final["invalid_operations_rejected"] == 12
            and final["predicate_rejections"] == 5
            and final["rank_controls"] == 2,
            "control counts",
        )
        for key in (
            "trials",
            "invalid_operations_rejected",
            "predicate_rejections",
            "rank_controls",
        ):
            totals[key] += final[key]
    return {"passed": True, "universe_columns": 4368, "pair_row_groups": 120, **totals}
