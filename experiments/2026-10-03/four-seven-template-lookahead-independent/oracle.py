# Document:    Independent Native Anchor-Pair Lookahead Oracle
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      27a499a0b90bf9ec938916c62002e45abf12084b6e3a86896ba1f58df6f01a56
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount H plus each candidate from scratch; use no native count or cache code."""

import itertools as it
from collections import Counter

POINTS = range(1, 17)
ANCHORS = [frozenset(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
TRIPLES = set(it.combinations(POINTS, 3))
ORDINARY = [b for b in it.combinations(POINTS, 5) if all(len(set(b) & a) <= 1 for a in ANCHORS)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def budgets():
    result = {}
    for pair in it.combinations(POINTS, 2):
        anchor_point = next((p for p in pair if p % 4), None)
        if anchor_point is None:
            continue
        group = next(a for a in ANCHORS if anchor_point in a)
        other = next(p for p in pair if p != anchor_point)
        count = 7 if other in group else 6 if other == max(group) + 1 else 5
        result[pair] = 3 * count - 14
    require(len(result) == 114, "anchor-pair inventory")
    return result


def heavy_blocks(blocks):
    require(len(blocks) == len(set(blocks)) == 64, "state inventory")
    require(Counter(p for b in blocks for p in b) == {p: 20 for p in POINTS}, "state degrees")
    groups = [[b for b in blocks if a <= set(b)] for a in ANCHORS]
    require(all(len(g) == 7 for g in groups), "template size")
    heavy = sorted({b for g in groups for b in g})
    require(len(heavy) == 28, "heavy overlap")
    require(len(set(blocks) - set(heavy)) == 36, "ordinary count")
    require(set(blocks) - set(heavy) <= set(ORDINARY), "ordinary legality")
    for anchor, group in zip(ANCHORS, groups, strict=True):
        require(
            Counter(p for b in group for p in set(b) - anchor)
            == {p: 2 if p == max(anchor) + 1 else 1 for p in POINTS if p not in anchor},
            "template outside degrees",
        )
    return heavy


def analyze(heavy):
    require(len(heavy) == len(set(heavy)) == 28, "heavy inventory")
    heavy_count = Counter(t for b in heavy for t in it.combinations(b, 3))
    pair_limits = budgets()
    permitted, candidate_failures = [], []
    for block in ORDINARY:
        # A complete rebuild from H plus B, rather than the native incremental formula.
        counts = Counter(t for b in [*heavy, block] for t in it.combinations(b, 3))
        excess = Counter()
        for triple, count in counts.items():
            if count > 1:
                for pair in it.combinations(triple, 2):
                    excess[pair] += count - 1
        failures = [pair for pair, limit in pair_limits.items() if excess[pair] > limit]
        if failures:
            candidate_failures.append((block, failures))
        else:
            permitted.append(block)
    missing = TRIPLES - heavy_count.keys()
    covered = {t for b in permitted for t in it.combinations(b, 3)}
    unsupported = sorted(missing - covered)
    return {
        "heavy_uncovered": len(missing),
        "allowed_ordinary": len(permitted),
        "admissible_blocks": permitted,
        "unsupported_count": len(unsupported),
        "unsupported": unsupported,
        "rejected_ordinary": len(candidate_failures),
    }
