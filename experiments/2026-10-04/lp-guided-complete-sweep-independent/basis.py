#!/usr/bin/env python3
# Document:    Independent Heavy Link Switch Basis
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Pure combinations and endpoint-degree reconstruction; no optimizer imports."""

import hashlib
import itertools as it
import json
from collections import Counter

INF = 2**63 - 1


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def rebuild():
    blocks = list(it.combinations(range(1, 17), 5))
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    ordinary = [b for b in blocks if all(len(set(b) & a) <= 1 for a in anchors)]
    heavy = [b for b in blocks if sum(a <= set(b) for a in anchors) == 1
             and all(len(set(b) & a) != 2 for a in anchors)]
    supports = [((), 64, 64)]
    supports += [(t, 1, INF if frozenset(t) in anchors else 2)
                 for t in it.combinations(range(1, 17), 3)]
    supports += [((p,), 20, 20) for p in range(1, 17)]
    for pair in it.combinations(range(1, 17), 2):
        targets = {7 if q in a else 6 if q == max(a) + 1 else 5
                   for a in anchors for p, q in (pair, pair[::-1]) if p in a}
        assert len(targets) <= 1
        supports.append((pair, min(targets) if targets else 5, max(targets) if targets else 7))
    rows = [([i for i, b in enumerate(ordinary) if set(s) <= set(b)],
             [i for i, b in enumerate(heavy) if set(s) <= set(b)], lo, hi)
            for s, lo, hi in supports]
    assert (len(blocks), len(ordinary), len(heavy), len(rows)) == (4368, 1200, 276, 697)
    return blocks, anchors, ordinary, heavy, rows


def shifted(rows, heavy, chosen):
    selected = {i for i, b in enumerate(heavy) if b in set(chosen)}
    return [[oi, [1] * len(oi), lower - len(selected & set(hi)),
             upper if upper == INF else upper - len(selected & set(hi))]
            for oi, hi, lower, upper in rows]


def neighbors(chosen, anchors, heavy):
    selected, allowed = set(chosen), set(heavy)
    result = {}
    assert len(selected) == 28 and selected <= allowed
    for anchor in anchors:
        local = sorted(b for b in selected if anchor <= set(b))
        assert len(local) == 7
        assert Counter(p for b in local for p in set(b) - anchor) == {
            p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor}
        for outgoing in it.combinations(local, 2):
            degree = Counter(p for b in outgoing for p in set(b) - anchor)
            edges = list(it.combinations(sorted(degree), 2))
            for replacement in it.combinations(edges, 2):
                if Counter(p for edge in replacement for p in edge) != degree:
                    continue
                incoming = {tuple(sorted(anchor | set(edge))) for edge in replacement}
                if incoming == set(outgoing) or len(incoming - selected) != 2:
                    continue
                next_state = selected - set(outgoing) | incoming
                if len(next_state) != 28 or not next_state <= allowed:
                    continue
                counts = Counter(t for b in next_state for t in it.combinations(b, 3))
                if any(n > 2 and frozenset(t) not in anchors for t, n in counts.items()):
                    continue
                key = tuple(sorted(next_state))
                assert key not in result
                result[key] = {"anchor": sorted(anchor),
                               "removed": [list(b) for b in sorted(outgoing)],
                               "added": [list(b) for b in sorted(incoming)]}
    return result
