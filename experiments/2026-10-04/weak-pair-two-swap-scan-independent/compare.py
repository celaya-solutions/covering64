# Document:    Independent Two-Swap Native Control Comparison
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compare native support, completion, count, metric, and rollback control records."""

import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-independent-20261004"
ORACLE = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"


def compare(suffix):
    spec = importlib.util.spec_from_file_location("two_swap_count_oracle", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    require = oracle.require
    direct = json.loads((RAW / "control-expectations.json").read_text())
    extra = json.loads((RAW / "empty-support.json").read_text())
    fixtures = direct["fixtures"] + extra["fixtures"]
    expected_cases = {(tuple(row["outgoing"]), row["first_incoming"]): row for row in fixtures}
    events = [
        json.loads(line) for line in (RAW / f"{suffix}.stdout.jsonl").read_text().splitlines()
    ]
    require(not (RAW / f"{suffix}.stderr.txt").read_text(), "native/sanitizer stderr")
    require(events[0]["event"] == "universe", "missing universe record")
    expected_supersets = {}
    for index, points in enumerate(oracle.SUBSETS[5]):
        for size in range(6):
            for subset in itertools.combinations(points, size):
                mask = sum(1 << (p - 1) for p in subset)
                expected_supersets.setdefault(mask, []).append(index)
    native_supersets = {mask: ids for mask, ids in events[0]["supersets"]}
    require(len(native_supersets) == len(events[0]["supersets"]), "duplicate mask table")
    require(native_supersets == expected_supersets, "complete superset table mismatch")
    require(events[0]["pair_masks"] == list(oracle.MASKS[2]), "pair mask rank mismatch")
    seen_partials, full_states, conveniences = [], {}, []
    counters = 0

    def check_state(native, expected):
        nonlocal counters
        require(native["ids"] == expected["ids"], "state IDs")
        counts = {str(size): values for size, values in expected["counts"].items()}
        require(native["counts"] == counts, "direct subset counters")
        require(native["pair_metrics"] == expected["pair_metrics"], "per-pair metric mismatch")
        metrics = expected["metrics"] | {
            "cardinality": len(expected["ids"]),
            "legal": expected["legal"],
        }
        require(native["metrics"] == metrics, "full metrics mismatch")
        counters += 2500
        return metrics

    require(events[1]["event"] == "initial", "missing initial state")
    check_state(events[1]["state"], {"ids": direct["base_ids"], **direct["baseline"]})
    chosen = set(direct["base_ids"])
    for event in events[2:-1]:
        kind = event["event"]
        if kind == "partial":
            key = (tuple(event["outgoing"]), event["first_incoming"])
            require(key in expected_cases and key not in seen_partials, "unexpected partial")
            seen_partials.append(key)
            case = expected_cases[key]
            check_state(event["state"], case["partial"])
            support = {
                "mask": case["support_mask"],
                "size": case["support_mask"].bit_count(),
                "deficit_gt_one": case["worst_deficit"] > 1,
                "impossible": case["worst_deficit"] > 1 or case["support_mask"].bit_count() > 5,
            }
            require(event["support"] == support, "support reduction mismatch")
            require(event["completions"] == case["expected_completions"], "completion omission")
        elif kind == "final_control":
            outgoing, incoming = event["outgoing"], event["incoming"]
            key = tuple(outgoing + incoming)
            require(
                key not in full_states
                and outgoing == sorted(set(outgoing))
                and incoming == sorted(set(incoming)),
                "duplicate/unsorted final swap",
            )
            require(
                len(outgoing) == len(incoming) == 2
                and set(outgoing) <= chosen
                and not (set(incoming) & chosen),
                "final swap roles",
            )
            ids = sorted((chosen - set(outgoing)) | set(incoming))
            direct_state = {"ids": ids, **oracle.analyze(ids, direct["core_rows"])}
            metrics = check_state(event["state"], direct_state)
            require(event["evaluation"] == metrics, "incremental four-block metrics")
            full_states[key] = {"outgoing": outgoing, "incoming": incoming, **direct_state}
        elif kind == "convenience":
            key = tuple(event["outgoing"] + event["incoming"])
            require(key in full_states and key not in conveniences, "unexpected convenience")
            conveniences.append(key)
            direct_state = full_states[key]
            require(
                event["metrics"]
                == direct_state["metrics"] | {"cardinality": 64, "legal": direct_state["legal"]},
                "convenience metric",
            )
        else:
            raise ValueError("unknown control event")
    final = events[-1]
    require(
        final
        == {
            "event": "finished",
            "partials": 31,
            "final_controls": 60,
            "invalid_operations_rejected": 29,
            "rollback_passed": True,
            "optimizer_launches": 0,
        },
        "terminal control counts",
    )
    require(
        len(seen_partials) == len(expected_cases) == 31
        and len(full_states) == 60
        and len(conveniences) == 60,
        "missing fixed control record",
    )
    return {
        "passed": True,
        "superset_masks": len(expected_supersets),
        "superset_entries": sum(map(len, expected_supersets.values())),
        "partials": 31,
        "full_controls": 60,
        "subset_counters_compared": counters,
        "all_completion_checks": direct["completion_checks"] + extra["completion_checks"],
        "invalid_operations_rejected": 29,
        "full_states": list(full_states.values()),
    }
