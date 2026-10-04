# Document:    Certified Heavy-Link Feature Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d4a98f05624ec785bec63364bb4a910298464bc2c1633df02f49e34048535283
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Append proved feature rows only to the normalized regular full four-seven branch."""

from itertools import combinations

from four_seven_double_cuts import validate_full_branch
from four_seven_search import ANCHORS

PROOF_MANIFEST_SHA256 = "7e67ffde630c9ba27b40f6c3345ff42b2de45288dd891bd3a95dd5876a83785a"
LP_RESULTS_SHA256 = "f96c156276584f72e6134aa2cd6a68cc81d1c0f1164f3cc205f240720cae4207"
LP_AUDIT_SHA256 = "aec2287a1ecc4e127625db7d6374585050f2daae036b8d42a4043d49fbed89e4"
ROW_PREFIX = "four_seven_feature_"
RULES = {
    "cycle": (("adjacent_anchor_hub", "<=", 3),
              ("nonadjacent_anchor_anchor", "<=", 2)),
    "matching": (("hub_hub_or_own_anchor_hub", ">=", 1),
                 ("adjacent_anchor_hub", "<=", 2),
                 ("adjacent_anchor_anchor", "<=", 2)),
}


def _matches(edge, predicate, case):
    a, b = edge
    ga, gb = (a - 1) // 4, (b - 1) // 4
    ha, hb = a % 4 == 0, b % 4 == 0
    adjacent = (ga - gb) % 4 in (1, 3) if case == "cycle" else ga ^ 1 == gb
    if predicate == "adjacent_anchor_hub":
        return ha != hb and adjacent
    if predicate == "nonadjacent_anchor_anchor":
        return not ha and not hb and ga != gb and not adjacent
    if predicate == "adjacent_anchor_anchor":
        return not ha and not hb and adjacent
    if predicate == "hub_hub_or_own_anchor_hub":
        return ha and hb or ha != hb and ga == gb
    raise ValueError("unknown proved predicate")


def add_feature_cuts(universe, model, xs, case):
    """Preserve every prior field; add8 cycle or12 matching rows and no variables.

    Proof provenance is embedded so this helper needs no checkout-relative files.
    Each inequality is invariant under the hub-graph automorphisms transporting
    the first heavy triple to the target. No cover-invariance assumption is made.
    """
    validate_full_branch(universe, model, xs, case)
    if tuple(universe.blocks) != tuple(combinations(range(1, 17), 5)):
        raise ValueError("global lexicographic block ordering required")
    if any(row.name.startswith(ROW_PREFIX) for row in model.proto.constraints):
        raise ValueError("feature cuts already present")
    before = len(model.proto.variables), len(model.proto.constraints)
    block_ids = {block: i for i, block in enumerate(universe.blocks)}
    planned = []
    for predicate, sense, bound in RULES[case]:
        for group, anchors in enumerate(ANCHORS):
            outside = [point for point in range(1, 17) if point not in anchors]
            ids = sorted(block_ids[tuple(sorted((*anchors, *edge)))]
                         for edge in combinations(outside, 2) if _matches(edge, predicate, case))
            planned.append((predicate, sense, bound, group, ids))
    applied = []
    for predicate, sense, bound, group, ids in planned:
        expression = sum(xs[i] for i in ids)
        row = model.add(expression <= bound if sense == "<=" else expression >= bound)
        name = f"{ROW_PREFIX}{case}_{predicate}_group_{group}"
        row.with_name(name)
        applied.append({"rule_id": f"{case}:{predicate}", "group_index": group,
                        "row_name": name, "sense": sense, "bound": bound,
                        "variable_indices": ids, "coefficient": 1})
    return {
        "case": case,
        "new_variables": len(model.proto.variables) - before[0],
        "new_rows": len(model.proto.constraints) - before[1],
        "rule_ids": [f"{case}:{predicate}" for predicate, _, _ in RULES[case]],
        "proof_manifest_sha256": PROOF_MANIFEST_SHA256,
        "source_lp_results_sha256": LP_RESULTS_SHA256,
        "source_lp_audit_sha256": LP_AUDIT_SHA256,
        "rows": applied,
        "scope": "Only integer regular64 full covers in the normalized four-sevenfold branch; "
                 "finite certified first-link exclusions transported by hub-graph relabeling.",
    }
