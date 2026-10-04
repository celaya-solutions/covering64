#!/usr/bin/env python3
# Document:    Independent SQS Pool Greedy State and Replacement Recount
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Finite construction and complete replacement recount; no timed optimization."""

import hashlib
import json
from collections import Counter
from itertools import combinations, product
from pathlib import Path

POINTS = tuple(range(1, 17))
TRIPLES = list(combinations(POINTS, 3))
RANK = {triple: i for i, triple in enumerate(TRIPLES)}


def pool_blocks():
    affine = {tuple(sorted((a, b, c, ((a - 1) ^ (b - 1) ^ (c - 1)) + 1)))
              for a, b, c in TRIPLES}
    transversals = {tuple(sorted(choice))
                   for choice in product((1, 5), (2, 6), (3, 7), (4, 8))}
    traded = affine ^ transversals
    assert len(affine) == len(traded) == 140
    assert all(Counter(t for block in seed for t in combinations(block, 3))
               == Counter({t: 1 for t in TRIPLES}) for seed in (affine, traded))
    quads = affine | traded
    pool = [block for block in combinations(POINTS, 5)
            if any(q in quads for q in combinations(block, 4))]
    assert len(pool) == 1744
    return pool


def masks_for(pool):
    return [sum(1 << RANK[t] for t in combinations(block, 3)) for block in pool]


def greedy(pool):
    masks = masks_for(pool)
    selected, covered, trace = [], 0, []
    remaining = set(range(len(pool)))
    for step in range(64):
        chosen = min(remaining, key=lambda i: (-(masks[i] & ~covered).bit_count(), i))
        gain = (masks[chosen] & ~covered).bit_count()
        covered |= masks[chosen]
        selected.append(chosen)
        remaining.remove(chosen)
        trace.append({"step": step, "local_id": chosen, "block": pool[chosen],
                      "gain": gain, "holes": 560 - covered.bit_count()})
    return selected, trace


def full_counts(pool, selected):
    assert len(selected) == len(set(selected)) == 64
    assert all(type(i) is int and 0 <= i < len(pool) for i in selected)
    counts = Counter(t for i in selected for t in combinations(pool[i], 3))
    return [counts[t] for t in TRIPLES]


def initial_deltas(pool, selected):
    masks = masks_for(pool)
    before = 560 - len({t for i in selected for t in combinations(pool[i], 3)})
    incoming = sorted(set(range(len(pool))) - set(selected))
    for outgoing in selected:
        retained_union = 0
        for i in selected:
            if i != outgoing:
                retained_union |= masks[i]
        for added in incoming:
            after = 560 - (retained_union | masks[added]).bit_count()
            yield outgoing, added, after - before


def main():
    here = Path(__file__).resolve().parent
    pool = pool_blocks()
    selected, trace = greedy(pool)
    counts = full_counts(pool, selected)
    digest = hashlib.sha256()
    histogram = Counter()
    total = 0
    for old, new, delta in initial_deltas(pool, selected):
        digest.update(f"{old} {new} {delta}\n".encode())
        histogram[delta] += 1
        total += 1
    assert total == 107520
    report = {"pool_size": len(pool), "selected_in_greedy_order": selected,
              "greedy_trace": trace, "counts": counts, "holes": counts.count(0),
              "legal_replacements": total, "delta_histogram": dict(sorted(histogram.items())),
              "ordered_delta_sha256": digest.hexdigest(), "solver_calls": 0,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (here / "expected.json").write_text(json.dumps(report, indent=2) + "\n")
    (here / "expected-greedy.txt").write_text("".join(
        " ".join(map(str, pool[i])) + "\n" for i in sorted(selected)))
    compact = {k: v for k, v in report.items()
               if k not in ("selected_in_greedy_order", "greedy_trace", "counts")}
    print(json.dumps(compact), flush=True)


if __name__ == "__main__":
    main()
