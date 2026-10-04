# Document:    H9 H10 Union Disjoint-Support Certificate Producer
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      22dbeb9924e71048bad21fe5d452ea4c48a02d8c288f2b67cbab47c3ae567400
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Produce a finite disjoint-support counting certificate; no covering solver."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}
SOURCES = [
    (
        "experiments/2026-10-04/weak-pair-h9-d23-neutral-queue-runtime-independent/"
        "family-a0a737c4010f68fc.txt",
        "a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc",
    ),
    (
        "experiments/2026-10-04/native-five-core-record-pilot/seed-2026105602/"
        "search-final-weak64.txt",
        "85f6e38a537691442cf6097a68b1364a755ac1ba8312d61adfc88c26abb6a90e",
    ),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    assert not (HERE / "certificate.json").exists(), "preserve frozen certificate"
    sources = []
    for relative, expected in SOURCES:
        path = ROOT / relative
        assert sha(path) == expected
        rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert rows == sorted(set(rows)) and len(rows) == 64
        assert all(row in RANK for row in rows)
        sources.append({"path": relative, "sha256": expected, "ids": [RANK[b] for b in rows]})
    union = sorted({i for source in sources for i in source["ids"]})
    assert len(union) == 128
    supports = []
    for triple in itertools.combinations(range(1, 17), 3):
        carriers = [i for i in union if set(triple) <= set(BLOCKS[i])]
        assert carriers
        supports.append({"triple": list(triple), "carrier_ids": carriers})
    singleton_for = {}
    for row in supports:
        if len(row["carrier_ids"]) == 1:
            singleton_for.setdefault(row["carrier_ids"][0], row)
    forced = sorted(singleton_for)
    pair_for = {}
    for row in supports:
        pair = tuple(row["carrier_ids"])
        if len(pair) == 2 and not set(pair).intersection(forced):
            pair_for.setdefault(pair, row)
    edges = sorted(pair_for)
    available = set(union) - set(forced)
    matched = []
    while True:
        eligible = [edge for edge in edges if set(edge) <= available]
        if not eligible:
            break
        degree = Counter(index for edge in eligible for index in edge)
        chosen = min(
            eligible, key=lambda e: (min(degree[i] for i in e), sum(degree[i] for i in e), e)
        )
        matched.append(pair_for[chosen])
        available.difference_update(chosen)
    assert len(forced) == 15 and len(matched) == 56
    (HERE / "union-128.txt").write_text(
        "".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in union)
    )
    dump(HERE / "incidence.json", {"candidate_ids": union, "triple_supports": supports})
    certificate = {
        "scope": (
            "Every complete cover drawn only from this exact 128-block union "
            "needs at least 71 blocks."
        ),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip(),
        "producer_sha256": sha(Path(__file__)),
        "sources": sources,
        "union_path": str((HERE / "union-128.txt").relative_to(ROOT)),
        "union_sha256": sha(HERE / "union-128.txt"),
        "union_ids": union,
        "incidence_path": str((HERE / "incidence.json").relative_to(ROOT)),
        "incidence_sha256": sha(HERE / "incidence.json"),
        "triple_count": 560,
        "support_histogram": dict(sorted(Counter(len(r["carrier_ids"]) for r in supports).items())),
        "forced_rows": [singleton_for[i] for i in forced],
        "forced_ids": forced,
        "matched_pair_rows": matched,
        "remaining_pair_rows": sum(
            len(r["carrier_ids"]) == 2 and not set(forced).intersection(r["carrier_ids"])
            for r in supports
        ),
        "distinct_remaining_pair_supports": len(edges),
        "uncovered_after_forced": sum(
            not set(forced).intersection(r["carrier_ids"]) for r in supports
        ),
        "matched_pair_count": len(matched),
        "selected_lower_bound": len(forced) + len(matched),
        "proof": (
            "Each listed singleton triple forces its unique union carrier. Each listed pair "
            "triple requires at least one of its two union carriers. The 15 singleton supports "
            "and 56 pair supports are pairwise disjoint, so their coverage inequalities sum "
            "to at least 71 selected union blocks. No statement applies outside this union."
        ),
        "matching_algorithm": (
            "Repeatedly choose edge minimizing (min endpoint degree, sum degrees, IDs)."
        ),
        "optimizer_launches": 0,
        "covering_model_prepared": False,
        "solver_preparation_avoided": True,
    }
    dump(HERE / "certificate.json", certificate)
    print(
        json.dumps(
            {
                "certificate_sha256": sha(HERE / "certificate.json"),
                "forced": len(forced),
                "matching": len(matched),
                "lower_bound": 71,
            }
        )
    )


if __name__ == "__main__":
    main()
