# Document:    Two-Partition Five-Heavy Saved-State Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      536f8844b9f964308c04260001b1904e959d8bc1d4e45ef0bc5419ba54523bb6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Apply the stated five-heavy obstruction to two fixed labeled partitions."""

import json
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path, expected):
    rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(rows) == len(set(rows)) == expected
    assert all(
        len(row) == len(set(row)) == 5
        and row == tuple(sorted(row))
        and min(row) >= 1
        and max(row) <= 16
        for row in rows
    )
    return rows


def main():
    inventory_path = DAY / "heterogeneous-seed-inventory/inventory.json"
    postcheck_path = DAY / "heterogeneous-core-pool-independent/postcheck.json"
    inventory = json.loads(inventory_path.read_text())
    postcheck = json.loads(postcheck_path.read_text())
    assert postcheck["passed"]
    core_path = ROOT / inventory["core_path"]
    assert digest(core_path) == inventory["core_sha256"]
    core = read(core_path, 60)
    counts = Counter(t for b in core for t in combinations(b, 3))
    original = sorted(t for t, n in counts.items() if n >= 6)
    assert len(original) == 5 and len(set().union(*map(set, original))) == 15
    mapping = inventory["entries"][1]["known_checked_core_map_images"]
    assert sorted(mapping) == list(range(1, 17))
    mapped = [tuple(sorted(mapping[p - 1] for p in t)) for t in original]
    partitions = [original, mapped]
    assert len(set().union(*map(set, mapped))) == 15
    cases = [
        {
            "name": row["name"],
            "path": row["path"],
            "sha256": row["sha256"],
            "source": "inventory",
            "holes": row["holes"],
        }
        for row in inventory["entries"]
    ]
    cases += [
        {
            "name": row["name"] + "-core-pool-final",
            "path": row["final"]["path"],
            "sha256": row["final"]["sha256"],
            "source": "core_pool_final",
            "holes": len(row["final"]["profile"]["holes"]),
        }
        for row in postcheck["cases"]
    ]
    records = []
    for case in cases:
        path = ROOT / case["path"]
        assert digest(path) == case["sha256"]
        blocks = read(path, 64)
        counts = Counter(t for b in blocks for t in combinations(b, 3))
        assert 560 - len(counts) == case["holes"]
        multiplicities = [[counts[t] for t in partition] for partition in partitions]
        obstructed = [
            all(n >= 6 for n in values) and sum(n >= 7 for n in values) >= 2
            for values in multiplicities
        ]
        records.append(
            {
                **case,
                "partition_multiplicities": multiplicities,
                "partition_obstructed": obstructed,
                "avoids_both_fixed_partition_obstructions": not any(obstructed),
            }
        )
    passing = [
        r
        for r in records
        if r["source"] == "inventory" and r["avoids_both_fixed_partition_obstructions"]
    ]
    passing.sort(key=lambda r: (r["holes"], r["name"]))
    assert [r["name"] for r in passing] == ["g5-raw-17", "g5-score-19", "sqs-23"]
    assert all(records[i]["partition_obstructed"] == [False, True] for i in (10, 11))
    audit = {
        "optimizer_calls": 0,
        "checker_sha256": digest(Path(__file__)),
        "inputs": {
            str(p.relative_to(ROOT)): digest(p) for p in [inventory_path, postcheck_path, core_path]
        },
        "partitions": partitions,
        "mapped_point_images": mapping,
        "records": records,
        "passing_inventory_states_by_holes": [r["name"] for r in passing],
        "lowest_hole_passing_inventory_state": passing[0],
        "criterion": (
            "Five vertex-disjoint triples all have multiplicity at least six, "
            "with at least two at least seven."
        ),
        "scope": (
            "Exact recount on two named partitions only; "
            "no new theorem or complete partition search."
        ),
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "lowest_holes": passing[0]["holes"],
                "lowest_state": passing[0]["name"],
                "audit_sha256": digest(HERE / "audit.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
