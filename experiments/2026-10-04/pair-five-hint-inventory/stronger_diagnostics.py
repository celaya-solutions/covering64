# Document:    Existing Hint Stronger Pair-Two-Triple Diagnostics
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      87913e99f82f9ca90339f48f97f208bd7162adbc015f351cffb45b929f5c0c87
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exact finite inventory recount; no optimizer and no hint or model changes."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "stronger-diagnostics.json"
    assert not output.exists()
    inventory_path = HERE / "pair-link-diagnostics.json"
    assert sha(inventory_path) == "faebd03a3a1e1dfb3509b37486f8625bc3ee8814d73abf7c1eabe4df06c236a5"
    inventory = json.loads(inventory_path.read_text())
    records = []
    for item in inventory["records"]:
        path = ROOT / item["path"]
        assert sha(path) == item["sha256"]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        pair_counts = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
        triple_counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
        violations = []
        checked = 0
        for pair in itertools.combinations(range(1, 17), 2):
            outside = [point for point in range(1, 17) if point not in pair]
            for a, b in itertools.combinations(outside, 2):
                first, second = tuple(sorted((*pair, a))), tuple(sorted((*pair, b)))
                lhs = 3 * pair_counts[pair] - triple_counts[first] - triple_counts[second]
                checked += 1
                if lhs < 12:
                    violations.append(
                        {
                            "pair": pair,
                            "outside": [a, b],
                            "pair_count": pair_counts[pair],
                            "triple_counts": [triple_counts[first], triple_counts[second]],
                            "lhs": lhs,
                            "deficit": 12 - lhs,
                        }
                    )
        assert checked == 10920
        records.append(
            {
                "path": item["path"],
                "sha256": item["sha256"],
                "holes": item["holes"],
                "single_triple_violations": len(item["pair_triple_violations"]),
                "two_triple_violations": len(violations),
                "two_triple_total_deficit": sum(row["deficit"] for row in violations),
                "two_triple_deficit_histogram": dict(
                    sorted(Counter(row["deficit"] for row in violations).items())
                ),
                "violations": violations,
            }
        )
    assert len(records) == 17
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "source_sha256": sha(Path(__file__)),
        "input_sha256": sha(inventory_path),
        "distinct_states": 17,
        "rows_checked": 17 * 10920,
        "records": records,
        "qualifying_states": sum(
            row["single_triple_violations"] == 0 and row["two_triple_violations"] == 0
            for row in records
        ),
        "scope": "Finite read-only diagnostics of the declared17states; no model, "
        "hint, or parameter changes. No optimizer.",
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "sha256": sha(output),
                "qualifying_states": result["qualifying_states"],
                "summary": [
                    {
                        key: row[key]
                        for key in [
                            "holes",
                            "sha256",
                            "single_triple_violations",
                            "two_triple_violations",
                            "two_triple_total_deficit",
                        ]
                    }
                    for row in records
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
