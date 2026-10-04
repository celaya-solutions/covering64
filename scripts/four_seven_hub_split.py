# Document:    Exhaustive Hub Counts in the Four-Sevenfold Branch
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      60e25333922894da0df171fd138f762a2470f72a952d363108d72bfd409280db
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Split integer full-branch covers by four-hub blocks and doubled hub triples."""

from itertools import combinations
from math import comb

from four_seven_double_cuts import validate_full_branch

HUBS = frozenset((4, 8, 12, 16))
CASES = tuple((m4, z) for m4 in (0, 1) for z in range(3))
ROW_PREFIX = "four_seven_hub_split_"


def add_hub_count_split(universe, model, xs, case, four_hub_blocks, double_hub_triples):
    """Add exactly two count rows for one of six exhaustive integer cases.

    Every hub triple contains a multiplicity-five pair. The fourteen covered
    triples through that pair use fifteen incidences, so each hub triple has
    multiplicity at most two. Write z for the number doubled. A cycle hub
    triple consumes one of two nonedge-pair excess units when doubled; a
    matching hub triple consumes two of four such units. Hence 0<=z<=2.
    A block with h hubs supplies C(h,3) hub triples, so m3+4*m4=4+z<=6.
    Thus m4<=1. Both counts are nonnegative integers.
    Each integer cover belongs to exactly one CASES entry. No single entry is
    equivalent to the full branch, and infeasibility needs all six entries.
    """
    if (type(four_hub_blocks) is not int or type(double_hub_triples) is not int
            or (four_hub_blocks, double_hub_triples) not in CASES):
        raise ValueError("one of the six exhaustive integer hub cases is required")
    validate_full_branch(universe, model, xs, case)
    if tuple(universe.blocks) != tuple(combinations(range(1, 17), 5)):
        raise ValueError("global lexicographic block ordering required")
    if any(row.name.startswith(ROW_PREFIX) for row in model.proto.constraints):
        raise ValueError("hub count split already present")
    counts = [len(HUBS.intersection(block)) for block in universe.blocks]
    four_ids = [i for i, count in enumerate(counts) if count == 4]
    triple_terms = [(i, comb(count, 3)) for i, count in enumerate(counts) if count >= 3]
    model.add(sum(xs[i] for i in four_ids) == four_hub_blocks).with_name(
        ROW_PREFIX + "four_hub_blocks")
    model.add(sum(coefficient * xs[i] for i, coefficient in triple_terms)
              == 4 + double_hub_triples).with_name(ROW_PREFIX + "hub_triple_incidences")
    return {"case": case, "four_hub_blocks": four_hub_blocks,
            "double_hub_triples": double_hub_triples, "new_variables": 0, "new_rows": 2,
            "four_hub_block_ids": four_ids, "hub_triple_terms": triple_terms,
            "complete_case_partition": [list(pair) for pair in CASES]}
