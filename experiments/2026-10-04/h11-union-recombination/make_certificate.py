# Document:    H11 Union Disjoint-Support Certificate Producer
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      639e02cd8ef646a7982eb521c24e40b9d23b0c9c30154228f5fa48fe3633faf4
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
        "experiments/2026-10-04/weak-pair-neutral-queue-runtime-independent/"
        "family-f621e945358cc9e5.txt",
        "f621e945358cc9e51c53995ee9a4a6161a0124778984fa410a87227984a28a7a",
    ),
    (
        "experiments/2026-10-04/native-variable-partial-start/seed-2026104802/"
        "search-record-5-admissible64.txt",
        "439d5153ba2f2063c8dedb20ce71f9381dfecdca087e4fa9f9f0dd3808f4d22f",
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
    assert len(forced) == 19 and len(matched) == 54
    (HERE / "union-128.txt").write_text(
        "".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in union)
    )
    dump(HERE / "incidence.json", {"candidate_ids": union, "triple_supports": supports})
    certificate = {
        "scope": (
            "Every complete cover drawn only from this exact 128-block union "
            "needs at least 73 blocks."
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
            "triple requires at least one of its two union carriers. The 19 singleton supports "
            "and 54 pair supports are pairwise disjoint, so their coverage inequalities sum "
            "to at least 73 selected union blocks. No statement applies outside this union."
        ),
        "matching_algorithm": (
            "Repeatedly choose edge minimizing (min endpoint degree, sum degrees, IDs)."
        ),
        "optimizer_launches": 0,
        "covering_model_prepared": False,
        "planned_cp_run_canceled": True,
    }
    dump(HERE / "certificate.json", certificate)
    print(
        json.dumps(
            {
                "certificate_sha256": sha(HERE / "certificate.json"),
                "forced": len(forced),
                "matching": len(matched),
                "lower_bound": 73,
            }
        )
    )


if __name__ == "__main__":
    main()
