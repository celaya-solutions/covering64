# Document:    Heavy-Link Odd-Set Blossom Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      132fbf0044bba5da294ac584ddc32c55aa7d4ee5c31a698bb3d2d197e04ec6b6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Append valid integer odd-set cuts in the normalized regular full-cover branch."""

from itertools import combinations

from four_seven_double_cuts import HUBS, validate_full_branch
from four_seven_search import ANCHORS

ROW_PREFIX = "four_seven_blossom_"


def templates(group):
    """Complement-canonical odd sets; omit only zero rows and unit bounds.

    The13 outside vertices have b(hub)=2 and all other b=1. For odd b(S),
    b(S)=2*x(E(S))+x(delta(S)) and integrality imply x(delta(S))>=1.
    Total b=14 makes complement inequalities equivalent. Exactly one subset
    in each complementary pair has at most6 vertices. Singleton non-hubs give
    0<=0; hub-plus-one gives x_e<=1. No other row is omitted.
    """
    if type(group) is not int or not 0 <= group < 4:
        raise ValueError("group index must be an integer from0 through3")
    outside = tuple(point for point in range(1, 17) if point not in ANCHORS[group])
    hub = HUBS[group]
    for size in range(3, 7):
        for subset in combinations(outside, size):
            degree_sum = size + int(hub in subset)
            if degree_sum % 2:
                yield subset, degree_sum // 2


def add_blossom_cuts(universe, model, xs, case):
    """Append8,096 rows, no variables; reject wrong scope before any mutation.

    Full coverage makes every outside heavy-link degree at least1. If an
    outside point p other than the own hub had degree d>=2, then the two
    triples through (anchor a,p) and either other anchor would each repeat
    d-1 times. But lambda(a,p)=5 covers14 triples with15 slots, allowing only
    one repeat in total. Hence d=1. Seven heavy edges have total degree14,
    forcing the own hub degree2. These facts follow from validated base rows;
    the double-triple auxiliary lift is not required.
    """
    validate_full_branch(universe, model, xs, case)
    if tuple(universe.blocks) != tuple(combinations(range(1, 17), 5)):
        raise ValueError("global lexicographic block ordering required")
    if any(row.name.startswith(ROW_PREFIX) for row in model.proto.constraints):
        raise ValueError("blossom cuts already present")
    before = len(model.proto.variables), len(model.proto.constraints)
    block_ids = {block: index for index, block in enumerate(universe.blocks)}
    planned = []
    for group, anchors in enumerate(ANCHORS):
        for subset, upper in templates(group):
            ids = sorted(block_ids[tuple(sorted((*anchors, *edge)))]
                         for edge in combinations(subset, 2))
            name = f"{ROW_PREFIX}group_{group}_set_" + "_".join(map(str, subset))
            planned.append((group, subset, upper, ids, name))
    if len(planned) != 8096:
        raise ValueError("incomplete canonical odd-set template")
    for _, _, upper, ids, name in planned:
        model.add(sum(xs[index] for index in ids) <= upper).with_name(name)
    return {
        "case": case,
        "new_variables": len(model.proto.variables) - before[0],
        "new_rows": len(model.proto.constraints) - before[1],
        "groups": 4,
        "canonical_subsets_per_group": 2048,
        "tautological_rows_omitted_per_group": 24,
        "rows_per_group": 2024,
        "rows": [{"group_index": group, "subset": subset, "upper": upper,
                  "variable_indices": ids, "row_name": name, "coefficient": 1}
                 for group, subset, upper, ids, name in planned],
        "proof": "b(S)=2*x(E(S))+x(delta(S)); odd integer b(S) forces x(delta(S))>=1.",
        "scope": "Only integer regular64 full covers in the normalized four-sevenfold branch; "
                 "elementary valid odd-set inequalities, no polyhedral completeness claim.",
    }
