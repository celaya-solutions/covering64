# Document:    Residual Pair Cuts for Covering Construction
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3c9dc86553648fa3b423a4cef4440f074e630b1e9b99215e167685bf54c77499
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Exact residual-pair bounds, retaining globally uncovered triples in partial models."""

from collections import Counter
from itertools import combinations

ANCHORS = {1, 2, 3}
OUTSIDE = tuple(range(4, 17))


def add_residual_pair_cuts(universe, model, xs, holes):
    """Require each covered triple missed by anchor blocks in an outside block.

    An outside block through a pair covers three outside triples through it.
    Thus its pair count is at least ceil(residual demand/3). Summing those
    lower bounds at a point cannot exceed four times its outside block degree.
    All original block and hole variables are preserved, in their original order.
    """
    residuals = {}
    for index, triple in enumerate(universe.triples):
        if ANCHORS.intersection(triple):
            continue
        local = sum(xs[i] for i in universe.containing[index]
                    if ANCHORS.intersection(universe.blocks[i]))
        residual = model.new_bool_var(f"residual_triple_{index}")
        model.add(local == 0).only_enforce_if(residual)
        model.add(holes[index] == 0).only_enforce_if(residual)
        model.add(local + holes[index] >= 1).only_enforce_if(residual.Not())
        residuals[triple] = residual
    needs = {}
    outside_ids = [i for i, b in enumerate(universe.blocks) if not ANCHORS.intersection(b)]
    for pair in combinations(OUTSIDE, 2):
        demand = sum(flag for t, flag in residuals.items() if set(pair) <= set(t))
        need = model.new_int_var(0, 4, f"residual_pair_need_{pair[0]}_{pair[1]}")
        model.add(3 * need >= demand)
        model.add(3 * need <= demand + 2)
        model.add(sum(xs[i] for i in outside_ids if set(pair) <= set(universe.blocks[i])) >= need)
        needs[pair] = need
    for point in OUTSIDE:
        model.add(sum(need for pair, need in needs.items() if point in pair)
                  <= 4 * sum(xs[i] for i in outside_ids if point in universe.blocks[i]))


def residual_hint_values(universe, blocks):
    """Compute auxiliary values directly from a candidate's two coverage counts."""
    total = Counter(t for b in blocks for t in combinations(b, 3))
    local = Counter(t for b in blocks if ANCHORS.intersection(b) for t in combinations(b, 3))
    residuals = {t: int(total[t] > 0 and local[t] == 0)
                 for t in universe.triples if not ANCHORS.intersection(t)}
    values = {f"residual_triple_{i}": residuals[t]
              for i, t in enumerate(universe.triples) if t in residuals}
    for pair in combinations(OUTSIDE, 2):
        demand = sum(value for t, value in residuals.items() if set(pair) <= set(t))
        values[f"residual_pair_need_{pair[0]}_{pair[1]}"] = (demand + 2) // 3
    return values
