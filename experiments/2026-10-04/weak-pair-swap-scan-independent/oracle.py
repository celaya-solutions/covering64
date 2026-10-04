# Document:    Independent Weak-Pair Swap Oracle
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4f9049b89d6e248f620bd1e296ecd9fe74524afcf510aea9c1c02dc7ed99af07
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Direct subset-inclusion recount; contains no optimizer or neighborhood scan."""

import itertools
from pathlib import Path

POINTS = tuple(range(1, 17))
SUBSETS = {size: tuple(itertools.combinations(POINTS, size)) for size in (2, 3, 4, 5)}
MASKS = {
    size: tuple(sum(1 << (p - 1) for p in row) for row in rows) for size, rows in SUBSETS.items()
}
RANK = {block: index for index, block in enumerate(SUBSETS[5])}
INDEX = {size: {row: i for i, row in enumerate(rows)} for size, rows in SUBSETS.items()}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def parse(path):
    rows = [
        tuple(map(int, line.split()))
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]
    require(rows == sorted(set(rows)), "duplicate or noncanonical family")
    require(all(row in RANK for row in rows), "malformed block")
    return [RANK[row] for row in rows]


def analyze(ids, cores):
    require(len(ids) == len(set(ids)), "duplicate IDs")
    require(all(type(index) is int and 0 <= index < 4368 for index in ids), "invalid ID")
    family = [MASKS[5][index] for index in ids]
    # Full direct inclusion recount, independent of producer incidence tables and updates.
    counts = {
        size: [sum(block & subset == subset for block in family) for subset in MASKS[size]]
        for size in (2, 3, 4)
    }
    d3 = d4 = d2max = d2sum = 0
    pair_metrics = []
    for index, pair in enumerate(SUBSETS[2]):
        r = counts[2][index]
        outside = [p for p in POINTS if p not in pair]
        triples = [counts[3][INDEX[3][tuple(sorted((*pair, p)))]] for p in outside]
        require(sum(triples) == 3 * r, "pair-triple incidence identity")
        single_deficits = [max(0, 13 - 3 * r + count) for count in triples]
        quad_deficits = []
        stronger_deficits = []
        for a, b in itertools.combinations(range(14), 2):
            quad = tuple(sorted((*pair, outside[a], outside[b])))
            quad_deficits.append(max(0, 12 - 3 * r + 2 * counts[4][INDEX[4][quad]]))
            stronger_deficits.append(max(0, 12 - 3 * r + triples[a] + triples[b]))
        d3 += sum(single_deficits)
        d4 += sum(quad_deficits)
        d2max += max(stronger_deficits)
        d2sum += sum(stronger_deficits)
        pair_metrics.append(
            {
                "single_deficit": sum(single_deficits),
                "quad_deficit": sum(quad_deficits),
                "D2max": max(stronger_deficits),
                "D2sum": sum(stronger_deficits),
            }
        )
    overlap = [len(set(ids).intersection(core)) for core in cores]
    metrics = {
        "holes": counts[3].count(0),
        "minimum_pair_count": min(counts[2]),
        "D3": d3,
        "D4": d4,
        "D2max": d2max,
        "D2sum": d2sum,
        "core_overlaps": overlap,
    }
    return {
        "counts": counts,
        "pair_metrics": pair_metrics,
        "metrics": metrics,
        "legal": len(ids) == 64 and min(counts[2]) >= 5 and d3 == d4 == 0 and max(overlap) <= 55,
    }
