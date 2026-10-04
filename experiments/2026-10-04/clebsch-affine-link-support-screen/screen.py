# Document:    Finite Support Screen of Pinned Clebsch Affine Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1470ef16cef50fb6fc4e1668b0f3bc6d2754b2f2c795f4a3e7974ccf754235cc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exact integer support counting and forced-block propagation, without a solver."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CONSTRUCTION = ROOT / "experiments/2026-10-04/clebsch-point-link-construction"
PROFILE = ROOT / (
    "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
)
BLOCKS = tuple(combinations(range(1, 17), 5))
IDS = {block: index for index, block in enumerate(BLOCKS)}
TRIPLES = {index: tuple(combinations(block, 3)) for index, block in enumerate(BLOCKS)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def canonical_bytes(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode("ascii")


def pool_hash(active):
    return sha256((" ".join(map(str, sorted(active))) + "\n").encode("ascii")).hexdigest()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def count_support(active, residual):
    support = {triple: [] for triple in residual}
    for index in sorted(active):
        for triple in TRIPLES[index]:
            support[triple].append(index)
    deficient = [triple for triple, demand in residual.items() if len(support[triple]) < demand]
    tight = [
        triple
        for triple, demand in residual.items()
        if demand > 0 and len(support[triple]) == demand
    ]
    forced = {}
    for triple in tight:
        for index in support[triple]:
            forced.setdefault(index, triple)
    forced_counts = Counter(triple for index in forced for triple in TRIPLES[index])
    conflicts = [triple for triple, count in forced_counts.items() if count > residual[triple]]
    return support, deficient, forced, forced_counts, conflicts


def screen(link, classes, profiles):
    point = link["point"]
    others = tuple(x for x in range(1, 17) if x != point)
    profile = {tuple(triple) for triple in profiles[str(link["profile_seed"])]}
    local = [
        tuple(sorted(link["canonical_to_actual"][x - 1] for x in block))
        for block in classes[link["class"]]["canonical_blocks"]
    ]
    partial = sorted(tuple(sorted((point, *block))) for block in local)
    require(
        sha256(canonical_bytes(partial)).hexdigest() == link["partial_canonical_sha256"],
        "pinned partial hash",
    )
    counts = Counter(triple for block in local for triple in combinations(block, 3))
    residual = {
        triple: 1 + (triple in profile) - counts[triple] for triple in combinations(others, 3)
    }
    require(min(residual.values()) >= 0 and sum(residual.values()) == 440, "initial rows")
    initial_domain = [IDS[block] for block in combinations(others, 5)]
    require(len(initial_domain) == 3003, "entire point-avoiding domain")
    active = {
        index for index in initial_domain if all(residual[triple] > 0 for triple in TRIPLES[index])
    }
    initial = count_support(active, residual)
    result = {
        "profile_seed": link["profile_seed"],
        "point": point,
        "class": link["class"],
        "partial_canonical_sha256": link["partial_canonical_sha256"],
        "initial_candidates": len(active),
        "initial_candidate_ids_sha256": pool_hash(active),
        "initial_deficient_rows": len(initial[1]),
        "initial_forced_blocks": len(initial[2]),
        "initial_forced_conflict_rows": len(initial[4]),
        "rounds": [],
    }
    fixed = set()
    while True:
        require(sum(residual.values()) == 10 * (44 - len(fixed)), "remaining incidence sum")
        support, deficient, forced, forced_counts, conflicts = count_support(active, residual)
        trace = {
            "active_candidates": len(active),
            "active_candidate_ids_sha256": pool_hash(active),
            "remaining_blocks": 44 - len(fixed),
            "remaining_demand_sum": sum(residual.values()),
        }
        result["rounds"].append(trace)
        if deficient:
            triple = min(deficient)
            trace.update(
                {
                    "outcome": "insufficient_support",
                    "triple": triple,
                    "demand": residual[triple],
                    "support_block_ids": support[triple],
                }
            )
            break
        if conflicts:
            triple = min(conflicts)
            relevant = sorted(index for index in forced if triple in TRIPLES[index])
            trace.update(
                {
                    "outcome": "forced_conflict",
                    "triple": triple,
                    "demand": residual[triple],
                    "forced_block_ids": relevant,
                    "forcing_rows": [
                        {
                            "block_id": index,
                            "triple": forced[index],
                            "demand": residual[forced[index]],
                            "support_block_ids": support[forced[index]],
                        }
                        for index in relevant
                    ],
                }
            )
            break
        if not forced:
            trace.update(
                {
                    "outcome": "survives_finite_screen",
                    "positive_rows": sum(demand > 0 for demand in residual.values()),
                    "minimum_support_slack": min(
                        len(support[t]) - demand for t, demand in residual.items() if demand > 0
                    ),
                }
            )
            break
        trace.update(
            {
                "outcome": "propagate_forced_blocks",
                "forced_block_ids": sorted(forced),
                "forcing_rows": [
                    {
                        "block_id": index,
                        "triple": forced[index],
                        "demand": residual[forced[index]],
                        "support_block_ids": support[forced[index]],
                    }
                    for index in sorted(forced)
                ],
            }
        )
        require(not fixed.intersection(forced), "distinct forced blocks")
        fixed.update(forced)
        residual = {triple: demand - forced_counts[triple] for triple, demand in residual.items()}
        require(min(residual.values()) >= 0, "nonnegative propagated rows")
        active = {
            index
            for index in active - set(forced)
            if all(residual[triple] > 0 for triple in TRIPLES[index])
        }
    result["outcome"] = result["rounds"][-1]["outcome"]
    result["propagated_blocks"] = sorted(fixed)
    return result


def main():
    classes = json.loads((CONSTRUCTION / "classes.json").read_text())
    links = json.loads((CONSTRUCTION / "recipe-point-maps.json").read_text())
    profiles = json.loads(PROFILE.read_text())
    require(len(links) == 256, "all recipe point maps")
    results = [screen(link, classes, profiles) for link in links]
    save("cases.json", results)
    outcomes = Counter(row["outcome"] for row in results)
    initial_rejected = sum(
        bool(row["initial_deficient_rows"] or row["initial_forced_conflict_rows"])
        for row in results
    )
    survivors = [
        {key: row[key] for key in ("profile_seed", "point", "class")}
        for row in results
        if row["outcome"] == "survives_finite_screen"
    ]
    summary = {
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": sys.version,
        "source_sha256": digest(Path(__file__)),
        "construction_classes_sha256": digest(CONSTRUCTION / "classes.json"),
        "construction_maps_sha256": digest(CONSTRUCTION / "recipe-point-maps.json"),
        "profile_file_sha256": digest(PROFILE),
        "cases_sha256": digest(OUT / "cases.json"),
        "cases": len(results),
        "outcomes": dict(outcomes),
        "initial_insufficient_support_cases": sum(
            row["initial_deficient_rows"] > 0 for row in results
        ),
        "initial_forced_conflict_cases": sum(
            row["initial_forced_conflict_rows"] > 0 for row in results
        ),
        "initial_rejected_union": initial_rejected,
        "initial_candidates_range": [
            min(row["initial_candidates"] for row in results),
            max(row["initial_candidates"] for row in results),
        ],
        "maximum_rounds": max(len(row["rounds"]) for row in results),
        "survivors": survivors,
        "point_one_outcomes": {
            str(row["profile_seed"]): row["outcome"] for row in results if row["point"] == 1
        },
        "block_id_convention": "zero-based lexicographic C(16,5) variables",
        "candidate_pool_hash_convention": "sorted IDs separated by ASCII spaces with final LF",
        "solver_calls": 0,
        "scope": (
            "Only each explicitly pinned affine20-block partial with its fixed excess profile. "
            "Does not enumerate other isomorphic affine embeddings or other local decompositions."
        ),
        "survival_meaning": "No contradiction from finite support propagation; not feasibility.",
        "global_conclusion": "None.",
    }
    save("summary.json", summary)
    print(
        json.dumps(
            {key: summary[key] for key in ("cases", "outcomes", "maximum_rounds", "survivors")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
