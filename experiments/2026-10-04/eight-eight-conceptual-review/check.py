# Document:    Independent Eight Plus Eight Construction Arithmetic
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9f11271f9dfad368483ca76209831b5a0f028930f22f036789371d054ebe6410
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite recount only: no producer imports, model helpers or solver calls."""

import hashlib
import itertools
import json
from collections import Counter
from functools import reduce
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TYPES = {"A": {1, 2, 3}, "B": {1, 2, 4}}


def affine_planes():
    return {
        (normal, parity): tuple(
            point for point in range(8) if ((point & normal).bit_count() % 2) == parity
        )
        for normal in range(1, 8)
        for parity in range(2)
    }


def recipe(kind, offset):
    quads = [
        tuple(p + offset for p in quad)
        for (normal, _), quad in affine_planes().items()
        if normal not in TYPES[kind]
    ]
    triples = set(itertools.combinations(range(offset, offset + 8), 3))
    covered = Counter(t for q in quads for t in itertools.combinations(q, 3))
    assert len(covered) == 32 and set(covered.values()) == {1}
    remaining = sorted(triples - set(covered))
    assert len(remaining) == 24
    assert set(Counter(p for q in quads for p in q).values()) == {4}
    return sorted(quads), remaining


def pool(left, right):
    result = set()
    for kind, offset, opposite in [(left, 1, range(9, 17)), (right, 9, range(1, 9))]:
        quads, triples = recipe(kind, offset)
        for quad in quads:
            result.update(tuple(sorted((*quad, p))) for p in opposite)
        for triple in triples:
            result.update(
                tuple(sorted((*triple, *pair))) for pair in itertools.combinations(opposite, 2)
            )
    assert len(result) == 1472
    return result


def main():
    planes = affine_planes()
    plane_values = list(planes.values())
    all_triples = Counter(t for q in plane_values for t in itertools.combinations(q, 3))
    assert len(all_triples) == 56 and set(all_triples.values()) == {1}
    regular = []
    for selected in itertools.combinations(planes, 8):
        counts = Counter(p for key in selected for p in planes[key])
        if set(counts.values()) != {4}:
            continue
        normal_counts = Counter(n for n, _ in selected)
        assert set(normal_counts.values()) == {2}
        omitted = set(range(1, 8)) - set(normal_counts)
        dependent = 0
        for normal in omitted:
            dependent ^= normal
        regular.append("A" if dependent == 0 else "B")
    assert len(regular) == 35 and Counter(regular) == {"A": 7, "B": 28}

    prior = set()
    seed_receipts = []
    for name in ("affine-independent.txt", "traded-independent.txt"):
        path = ROOT / "experiments/2026-10-03/sqs-extension-independent" / name
        quads = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        counts = Counter(t for q in quads for t in itertools.combinations(q, 3))
        assert len(quads) == 140 and len(counts) == 560 and set(counts.values()) == {1}
        prior.update(tuple(sorted((*q, p))) for q in quads for p in range(1, 17) if p not in q)
        seed_receipts.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    assert len(prior) == 1744

    profiles = {}
    for kind in TYPES:
        quads, triples = recipe(kind, 1)
        pair_q = Counter(pair for q in quads for pair in itertools.combinations(q, 2))
        histogram = Counter(pair_q[pair] for pair in itertools.combinations(range(1, 9), 2))
        profiles[kind] = {
            "selected_quads": quads,
            "uncovered_internal_triples": triples,
            "pair_q_histogram": dict(sorted(histogram.items())),
            "required_extension_pair_occurrences": sum(
                max(q - 1, 0) * count for q, count in histogram.items()
            ),
        }
    recipes = {}
    affine_pool = {
        block
        for block in itertools.combinations(range(1, 17), 5)
        if any(
            reduce(int.__xor__, (p - 1 for p in q)) == 0 for q in itertools.combinations(block, 4)
        )
    }
    assert len(affine_pool) == 1680
    for left, right in [("A", "A"), ("A", "B"), ("B", "B")]:
        candidates = pool(left, right)
        rows = sorted(candidates)
        canonical = "".join(" ".join(map(str, row)) + "\n" for row in rows)
        recipes[left + right] = {
            "candidate_blocks": len(rows),
            "candidate_pool_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "intersection_with_prior_affine_pool": len(candidates & affine_pool),
            "intersection_with_prior_two_sqs_union": len(candidates & prior),
            "outside_prior_two_sqs_union": len(candidates - prior),
        }
    result = {
        "passed": True,
        "scope": (
            "Arithmetic and conditional template classification; "
            "no claim every 64-cover has this partition/template."
        ),
        "all_eight_quad_subsets_checked": 3003,
        "degree_four_subsets": len(regular),
        "degree_four_types": dict(Counter(regular)),
        "profiles": profiles,
        "recipes": recipes,
        "prior_seed_sources": seed_receipts,
        "selected_blocks": 64,
        "internal_triples_exactly_once": 112,
        "mixed_triples_required": 448,
        "mixed_triple_incidences": 528,
        "mixed_excess_if_cover": 80,
        "model_audit": "Performed separately; this checker imports no model producer helpers.",
        "solver_calls": 0,
    }
    (HERE / "arithmetic.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"passed": True, "regular_subsets": len(regular), "recipes": recipes}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
