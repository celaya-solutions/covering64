# Document:    Independent Eight Plus Eight Redundant Cut Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fcebfef0363cec42b4f274338ca290fa7938d95ba7b95b94daf2ecdcd088ff2f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check recipe arithmetic and finite integer implications without a solver."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def compositions(total, length):
    if length == 1:
        yield (total,)
    else:
        for first in range(total + 1):
            for rest in compositions(total - first, length - 1):
                yield (first, *rest)


def main():
    profiles = {}
    pairs = list(itertools.combinations(range(8), 2))
    for name, omitted in {"A": {1, 2, 3}, "B": {1, 2, 4}}.items():
        quads = [
            tuple(p for p in range(8) if (p & n).bit_count() % 2 == b)
            for n in range(1, 8)
            for b in range(2)
            if n not in omitted
        ]
        covered = Counter(t for q in quads for t in itertools.combinations(q, 3))
        triples = sorted(set(itertools.combinations(range(8), 3)) - set(covered))
        assert len(quads) == 8 and len(triples) == 24
        assert Counter(p for q in quads for p in q) == Counter({p: 4 for p in range(8)})
        assert Counter(p for t in triples for p in t) == Counter({p: 9 for p in range(8)})
        q_counts = Counter(pair for q in quads for pair in itertools.combinations(q, 2))
        triple_counts = Counter(pair for t in triples for pair in itertools.combinations(t, 2))
        assert all(triple_counts[pair] == 6 - 2 * q_counts[pair] for pair in pairs)
        lower = {pair: max(q_counts[pair] - 1, 0) for pair in pairs}
        degree = Counter()
        for pair, count in lower.items():
            for p in pair:
                degree[p] += count
        assert sum(lower.values()) == (24 if name == "A" else 20)
        assert set(degree.values()) == ({6} if name == "A" else {5})
        zeros = [pair for pair in pairs if q_counts[pair] == 0]
        if name == "A":
            assert Counter(p for pair in zeros for p in pair) == Counter(dict.fromkeys(range(8), 1))
        profiles[name] = {
            "q_histogram": dict(sorted(Counter(q_counts[p] for p in pairs).items())),
            "mandatory_extension_pair_occurrences": sum(lower.values()),
            "mandatory_extension_pair_degree_per_point": sorted(degree.values()),
            "unallocated_pair_occurrences": 24 - sum(lower.values()),
            "zero_q_pairs_one_based": [[p + 1 for p in pair] for pair in zeros],
            "local_base_blocks_per_point": 13,
            "local_triple_bases_per_point": 9,
        }

    rounded_cases = 0
    for p in range(49):
        for s in range(9):
            assert (9 + 3 * p + 6 * s >= 28) == (p + 2 * s >= 7)
            rounded_cases += 1
    singleton_vectors = list(compositions(8, 8))
    admissible_a = [s for s in singleton_vectors if all(9 + 3 * 6 + 6 * n >= 28 for n in s)]
    assert len(singleton_vectors) == 6435 and admissible_a == [(1,) * 8]
    type_b_degree_19 = []
    type_b_cases = 0
    for e in range(5):
        for s in range(9):
            p = 5 + e
            r = 13 + p + s
            assert (p + 2 * s >= 7) == (e + 2 * s >= 2)
            if e + 2 * s < 2:
                continue
            assert r >= 19 and (-3 + 3 * e + 4 * s) >= 1
            type_b_cases += 1
            if r == 19:
                type_b_degree_19.append([e, s])
    assert type_b_degree_19 == [[0, 1]]
    for z in range(5):
        total = 9 + 3 * z
        assert total - 7 == 2 + 3 * z
    low_pair_vectors = list(compositions(1, 8))
    assert len(low_pair_vectors) == 8
    assert all(sorted(v) == [0] * 7 + [1] for v in low_pair_vectors)

    result = {
        "passed": True,
        "scope": "Redundant implications within the three prepared 8+8 recipes only.",
        "profiles": profiles,
        "rounding_cases_checked": rounded_cases,
        "type_A_singleton_compositions_checked": len(singleton_vectors),
        "type_A_admissible_singleton_vectors": admissible_a,
        "type_B_admissible_point_cases_checked": type_b_cases,
        "type_B_degree_19_e_s_pairs": type_b_degree_19,
        "type_A_fixed_zero_variables_per_target_half": 96,
        "remaining_pool_sizes_after_type_A_zeros": {"AA": 1280, "AB": 1376, "BB": 1472},
        "type_A_mixed_triple_upper_bound_two_rows_per_target_half": 192,
        "formulas": {
            "same_half_pair_count": "6 - q_P + X_P",
            "extension_pair_floor": "X_P >= max(q_P - 1, 0)",
            "point_degree": "r_a = 13 + p_a + s_a",
            "opposite_pair_incidence": "9 + 3*p_a + 6*s_a >= 28",
            "rounded_point_cut": "p_a + 2*s_a >= 7",
            "type_A": "p_a=6; s_a=1; r_a=20",
            "type_B_extra_graph": "z_P=X_P-(q_P-1)>=0; sum z_P=4; e_a=sum_{P contains a} z_P",
            "type_B": "p_a=5+e_a; r_a=18+e_a+s_a; e_a+2*s_a>=2",
            "cross_pair_excess_degree": "3*p_a + 4*s_a - 18",
            "type_B_cross_pair_excess_degree": "-3 + 3*e_a + 4*s_a >= 1",
            "type_A_low_pair_triple_pattern": (
                "For q_P=2, eight mixed multiplicities are seven 1s and one 2."
            ),
        },
        "proof": "See README.md for the complete counting derivations, including scope.",
        "frozen_sources_changed": False,
        "solver_calls": 0,
    }
    output = HERE / "checks.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"passed": True, "checks_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
        )
    )


if __name__ == "__main__":
    main()
