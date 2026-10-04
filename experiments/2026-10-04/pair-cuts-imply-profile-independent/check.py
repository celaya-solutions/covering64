# Document:    Pair Local Cuts Imply the Five Heavy Profile Exclusion
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      be5db7659f070afae3b5ec9054941f0c120919ded473f8170d19a7dd747d3c87
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Audit the degree and hub contradiction for partial64-families; no solver."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
POINTS = tuple(range(1, 17))
PAIRS = list(itertools.combinations(POINTS, 2))
HEAVY = [tuple(range(3 * i + 1, 3 * i + 4)) for i in range(5)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lower_degree_bounds(roles, pair_floor=5, internal_floor=7, hub_floor=6):
    pairs = dict.fromkeys(PAIRS, pair_floor)
    for triple in HEAVY:
        for pair in itertools.combinations(triple, 2):
            pairs[pair] = max(pairs[pair], internal_floor)
    for triple_id, hub in roles:
        for point in HEAVY[triple_id]:
            pair = tuple(sorted((point, hub)))
            pairs[pair] = max(pairs[pair], hub_floor)
    degrees = [
        (sum(count for pair, count in pairs.items() if point in pair) + 3) // 4 for point in POINTS
    ]
    return degrees


def main():
    # These bounds use the audited pair floor and local cuts, not triple coverage.
    assert (13 + 6 + 2) // 3 == 7
    assert (12 + 2 * 2 + 2) // 3 == 6
    # Seven blocks containing a fixed triple supply14 incidences on13 outside points.
    assert 7 * 2 > 13
    baseline = lower_degree_bounds([])
    assert baseline == [20] * 15 + [19] and sum(baseline) == 319
    one_role = []
    for triple_id in range(5):
        for hub in POINTS:
            if hub not in HEAVY[triple_id]:
                degrees = lower_degree_bounds([(triple_id, hub)])
                assert sum(degrees) >= 320
                one_role.append((triple_id, hub, sum(degrees)))
    records = []
    for first, second in itertools.combinations(range(5), 2):
        for a in POINTS:
            if a in HEAVY[first]:
                continue
            for b in POINTS:
                if b in HEAVY[second]:
                    continue
                degrees = lower_degree_bounds([(first, a), (second, b)])
                assert sum(degrees) >= 321
                records.append(
                    {
                        "sevenfold_triples": [first, second],
                        "hubs": [a, b],
                        "degree_lower_bounds": degrees,
                        "sum": sum(degrees),
                    }
                )
    assert len(records) == 1690 and len(one_role) == 65
    # Directly check sum of incident pair counts =4*point degree on every block column.
    basis_checks = 0
    for block in itertools.combinations(POINTS, 5):
        pairs = list(itertools.combinations(block, 2))
        for point in POINTS:
            assert sum(point in pair for pair in pairs) == 4 * int(point in block)
            basis_checks += 1
    # Each removed premise destroys this particular degree contradiction.
    roles = [(0, 16), (1, 16)]
    assert sum(lower_degree_bounds(roles, pair_floor=4)) <= 320
    assert sum(lower_degree_bounds(roles, internal_floor=5)) <= 320
    assert sum(lower_degree_bounds(roles, hub_floor=5)) <= 320
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "optimizer_calls": 0,
        "role_cases": len(records),
        "one_role_cases": len(one_role),
        "point_pair_identity_basis_checks": basis_checks,
        "degree_sum_histogram": dict(sorted(Counter(r["sum"] for r in records).items())),
        "minimum_required_degree_sum": min(r["sum"] for r in records),
        "available_degree_sum": 64 * 5,
        "normalized_heavy_triples": HEAVY,
        "proof": [
            "Pair count>=5 implies degree>=ceil(75/4)=19 at every point.",
            "For any triple count>=6, the single-triple cut implies each internal pair>=7. "
            "Its anchors have pair sum>=2*7+13*5=79, hence degree>=20.",
            "Five disjoint heavy triples thus give degree sum>=319 before hub effects.",
            "A sevenfold triple has14 outside incidences on13 points, hence a repeated "
            "outside hub with common quadruple count>=2. Each of its3 cross-pairs is>=6 "
            "by3*c(P)-2*c(Q)>=12.",
            "All1690 choices of two sevenfold triples and their legal hub points force "
            "degree sum>=321; exact64-block incidence sum is320. Shared hub points "
            "and overlapping forced pairs are handled by maxima, never double counted.",
            "Any larger heavy profile contains five disjoint heavy triples and two "
            "sevenfold ones. Relabeling maps that chosen partition to the normalized one.",
        ],
        "premises": "Exact subset counts of64 five-point blocks, pair>=5, every single "
        "pair-triple cut, every pair-quadruple cut. Full triple coverage is not needed.",
        "stronger_model": "The two-triple cuts dominate every pair-quadruple cut, so the "
        "same exclusion holds in the stronger compact model withoutDP.",
        "dropped_premise_controls": ["pair floor4", "internal pair floor5", "hub pair floor5"],
        "records": records,
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "passed",
                    "role_cases",
                    "minimum_required_degree_sum",
                    "available_degree_sum",
                    "optimizer_calls",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
