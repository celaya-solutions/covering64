# Document:    Relabeled Core Necessary-Condition Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      cc3c713422cd18962f8cfa5d76a536531af13d5a8b1464482d23f07f330f3107
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Solver-free complete necessary-condition screen plus explicit core transports."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {b: i for i, b in enumerate(BLOCKS)}
TRIPLES = list(itertools.combinations(range(1, 17), 3))
CORE_PATH = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
CORE_SHA = "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
assert hashlib.sha256(CORE_PATH.read_bytes()).hexdigest() == CORE_SHA
CORE = [tuple(map(int, line.split())) for line in CORE_PATH.read_text().splitlines()]
CORE_COUNTS = Counter(t for b in CORE for t in itertools.combinations(b, 3))
CORE_HEAVY = [t for t in TRIPLES if CORE_COUNTS[t] >= 6]
assert len(CORE_HEAVY) == 5 and all(CORE_COUNTS[t] == 6 for t in CORE_HEAVY)
assert len(set(itertools.chain.from_iterable(CORE_HEAVY))) == 15
assert all(sum(set(t) <= set(b) for t in CORE_HEAVY) <= 1 for b in BLOCKS)
MAPS = [list(range(1, 17)), [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13]]


def partitions(counts):
    """Enumerate every disjoint five-triple set with total deficit at most four."""
    eligible = sorted(
        (max(0, 6 - counts[t]), i, sum(1 << (p - 1) for p in t))
        for i, t in enumerate(TRIPLES)
        if counts[t] >= 2
    )
    found, nodes = [], 0

    def visit(start, chosen, used, remaining):
        nonlocal nodes
        nodes += 1
        need = 5 - len(chosen)
        if not need:
            found.append(sorted(chosen))
            return
        for index in range(start, len(eligible)):
            cost, triple_id, mask = eligible[index]
            # Every later cost is at least this cost. This only removes branches
            # that cannot fit even without disjointness restrictions.
            if cost * need > remaining:
                break
            if not mask & used:
                visit(index + 1, chosen + [triple_id], used | mask, remaining - cost)

    visit(0, [], 0, 4)
    found.sort()
    assert len(found) == len({tuple(row) for row in found})
    return [
        {
            "triple_ids": ids,
            "triples": [list(TRIPLES[i]) for i in ids],
            "counts": [counts[TRIPLES[i]] for i in ids],
            "total_deficit": sum(max(0, 6 - counts[TRIPLES[i]]) for i in ids),
        }
        for ids in found
    ], nodes


def images():
    result = {}
    swaps = [None] + list(itertools.combinations(range(1, 17), 2))
    for base_index, base in enumerate(MAPS):
        for swap in swaps:
            mapping = list(base)
            if swap is not None:
                a, b = swap
                mapping = [b if p == a else a if p == b else p for p in mapping]
            assert sorted(mapping) == list(range(1, 17))
            ids = tuple(
                sorted(RANK[tuple(sorted(mapping[p - 1] for p in block))] for block in CORE)
            )
            assert len(ids) == len(set(ids)) == 60
            result.setdefault(
                ids, {"base_map": base_index, "point_swap": swap, "map_images": mapping}
            )
    return result


IMAGES = images()


def check(ids):
    assert len(ids) == len(set(ids)) == 64 and all(0 <= i < 4368 for i in ids)
    counts = Counter(t for i in ids for t in itertools.combinations(BLOCKS[i], 3))
    necessary, nodes = partitions(counts)
    best, violations = 0, []
    for core, transport in IMAGES.items():
        overlap = len(set(ids) & set(core))
        best = max(best, overlap)
        if overlap > 55:
            violations.append({**transport, "core_global_ids": list(core), "overlap": overlap})
    assert not violations or necessary
    return {
        "all_relabel_cap55_certified_by_necessary_condition": not necessary,
        "necessary_partition_count": len(necessary),
        "necessary_partitions": necessary,
        "necessary_enumeration_nodes": nodes,
        "explicit_image_scope": (
            "Both named core images and every single point transposition of each"
        ),
        "explicit_map_attempts": 242,
        "distinct_explicit_core_images": len(IMAGES),
        "maximum_explicit_overlap": best,
        "explicit_core_violations": violations,
        "scope": (
            "No necessary partition proves cap55 for every point relabeling. "
            "A necessary partition alone is inconclusive. Explicit violations bind a full map."
        ),
    }


def selfcheck():
    # Compare the pruned enumeration against an unpruned exhaustive enumeration
    # on a deterministic small triple support. These are arithmetic controls,
    # not generated candidate families or optimization calls.
    support = list(CORE_HEAVY) + [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]
    support = list(dict.fromkeys(support))
    cases = []
    for shift in range(7):
        counts = Counter({t: 2 + (i + shift) % 6 for i, t in enumerate(support)})
        actual, _ = partitions(counts)
        brute = sorted(
            sorted(TRIPLES.index(t) for t in five)
            for five in itertools.combinations(support, 5)
            if len(set(itertools.chain.from_iterable(five))) == 15
            and sum(max(0, 6 - counts[t]) for t in five) <= 4
        )
        assert [r["triple_ids"] for r in actual] == brute
        cases.append({"shift": shift, "matches": len(brute)})
    positive, _ = partitions(CORE_COUNTS)
    assert any({tuple(t) for t in row["triples"]} == set(CORE_HEAVY) for row in positive)
    assert not partitions(Counter())[0]
    return {
        "passed": True,
        "core_sha256": CORE_SHA,
        "core_heavy_triples": CORE_HEAVY,
        "pruned_vs_exhaustive_controls": cases,
        "positive_core_control": True,
        "zero_count_negative_control": True,
        "distinct_explicit_core_images": len(IMAGES),
    }


if __name__ == "__main__":
    print(json.dumps(selfcheck(), indent=2))
