# Document:    Certified Signed Feature Facets for the Four-Sevenfold Branch
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      9f8a1f5709d1a4f8472582bec6da9eafe55ade5979adc55a58a8a2cd9fd94647
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Append the thirteen new certified facet families to a validated full branch."""

from itertools import combinations

from four_seven_double_cuts import validate_full_branch
from four_seven_search import ANCHORS

PROOF_MANIFEST_SHA256 = "7f79089fd414539551863b367b161ee1b8a5dffbaf1e5bd9013ee6ac33cc3e51"
PROOF_DERIVATION_SHA256 = "dafaf4413349ea73fc1fbe97607614ff05fe155c25eb16802196356a6002d2cc"
LP_RESULTS_SHA256 = "f96c156276584f72e6134aa2cd6a68cc81d1c0f1164f3cc205f240720cae4207"
LP_AUDIT_SHA256 = "aec2287a1ecc4e127625db7d6374585050f2daae036b8d42a4043d49fbed89e4"
ROW_PREFIX = "four_seven_facet_"
FEATURE_COORDINATES = ("hub_hub", "own_anchor_hub", "adjacent_anchor_hub", "adjacent_anchor_anchor")
FACETS = {
    "cycle": (
        ((-2, 0, 1, 1), 4),
        ((0, -1, 0, -1), -1),
        ((1, 0, 1, -1), 2),
        ((2, 0, 1, -1), 3),
    ),
    "matching": (
        ((-4, -2, 1, 0), -2),
        ((-3, -1, 1, 1), 1),
        ((-2, -1, 1, -1), -1),
        ((-1, -1, 1, -2), -1),
        ((0, 0, 1, -1), 1),
        ((1, -1, 1, -2), 1),
        ((1, 0, 1, -1), 2),
        ((1, 0, 1, 0), 3),
        ((3, 1, 3, 1), 11),
    ),
}


def _edge_coefficient(edge, normal, case):
    a, b = edge
    ga, gb = (a - 1) // 4, (b - 1) // 4
    ha, hb = a % 4 == 0, b % 4 == 0
    adjacent = (ga - gb) % 4 in (1, 3) if case == "cycle" else ga ^ 1 == gb
    features = (
        ha and hb,
        ha != hb and ga == gb,
        ha != hb and adjacent,
        not ha and not hb and adjacent,
    )
    return sum(coefficient * present for coefficient, present in zip(normal, features, strict=True))


def add_facet_cuts(universe, model, xs, case):
    """Add 16 cycle or 36 matching rows, preserving all previous model fields.

    These integer-valid inequalities do not require the earlier five feature
    rules to be present. The full normalized regular covering branch is required.
    No new variables or cover-invariance restrictions are introduced.
    """
    if case not in FACETS:
        raise ValueError("unknown four-sevenfold hub case")
    validate_full_branch(universe, model, xs, case)
    if tuple(universe.blocks) != tuple(combinations(range(1, 17), 5)):
        raise ValueError("global lexicographic block ordering required")
    if any(row.name.startswith(ROW_PREFIX) for row in model.proto.constraints):
        raise ValueError("facet cuts already present")
    before = len(model.proto.variables), len(model.proto.constraints)
    block_ids = {block: i for i, block in enumerate(universe.blocks)}
    planned = []
    for facet_index, (normal, bound) in enumerate(FACETS[case]):
        for group, anchors in enumerate(ANCHORS):
            outside = [point for point in range(1, 17) if point not in anchors]
            coefficients = []
            for edge in combinations(outside, 2):
                coefficient = _edge_coefficient(edge, normal, case)
                if coefficient:
                    index = block_ids[tuple(sorted((*anchors, *edge)))]
                    coefficients.append((index, coefficient))
            planned.append((facet_index, normal, bound, group, sorted(coefficients)))
    applied = []
    for facet_index, normal, bound, group, coefficients in planned:
        expression = sum(coefficient * xs[index] for index, coefficient in coefficients)
        name = f"{ROW_PREFIX}{case}_{facet_index:02d}_group_{group}"
        model.add(expression <= bound).with_name(name)
        applied.append(
            {
                "rule_id": f"{case}:facet_{facet_index:02d}",
                "normal": list(normal),
                "group_index": group,
                "row_name": name,
                "sense": "<=",
                "bound": bound,
                "coefficients": [{"variable_index": i, "coefficient": c} for i, c in coefficients],
            }
        )
    return {
        "case": case,
        "new_variables": len(model.proto.variables) - before[0],
        "new_rows": len(model.proto.constraints) - before[1],
        "feature_coordinates": list(FEATURE_COORDINATES),
        "proof_manifest_sha256": PROOF_MANIFEST_SHA256,
        "proof_derivation_sha256": PROOF_DERIVATION_SHA256,
        "source_lp_results_sha256": LP_RESULTS_SHA256,
        "source_lp_audit_sha256": LP_AUDIT_SHA256,
        "rows": applied,
        "scope": "Only integer regular 64-block full covers in the normalized "
        "four-sevenfold branch; "
        "signed feature hull facets transported by hub-graph relabeling.",
    }
