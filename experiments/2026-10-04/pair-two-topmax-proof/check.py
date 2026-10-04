# Document:    Independent Pair Top-Two Deficit Equivalence and Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4fbbce9450909bb7010ed92ac7c406cd53d43097e36b8ba5a9ac9c5fadc59e41
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Arithmetic controls for a proposed metric only; no native implementation or optimizer."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
POSITIONS = tuple(itertools.combinations(range(14), 2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def top_two(values):
    assert len(values) == 14 and all(type(value) is int and value >= 0 for value in values)
    first = second = -1
    for value in values:
        if value >= first:
            second, first = first, value
        elif value > second:
            second = value
    return first, second


def row_deficits(pair_count, values):
    return [max(0, 12 - 3 * pair_count + values[a] + values[b]) for a, b in POSITIONS]


def link_counts(outside_triples):
    assert len(outside_triples) == len(set(outside_triples)) == 5
    assert all(
        len(set(triple)) == 3 and set(triple) <= set(range(3, 17)) for triple in outside_triples
    )
    counts = Counter(point for triple in outside_triples for point in triple)
    return [counts[point] for point in range(3, 17)]


def main():
    extremal_checks = feasible_extremal_profiles = zero_profiles = 0
    zero_pair_counts = Counter()
    extremal_digest = hashlib.sha256()
    for pair_count in range(65):
        for first in range(pair_count + 1):
            for second in range(first + 1):
                extremal_checks += 1
                mass = 3 * pair_count
                # Necessary and sufficient for a nonnegative14-vector bounded by pair_count
                # to have these two leading values and the correct total mass.
                if not first + second <= mass <= first + 13 * second:
                    continue
                remainder = mass - first - second
                tail = []
                for _ in range(12):
                    value = min(second, remainder)
                    tail.append(value)
                    remainder -= value
                values = [first, second, *tail]
                assert remainder == 0 and sum(values) == 3 * pair_count
                assert all(0 <= value <= pair_count for value in values)
                assert top_two(values) == (first, second)
                if pair_count:
                    assert sum(value > 0 for value in values) >= 3
                deficits = row_deficits(pair_count, values)
                maximum = max(0, 12 - 3 * pair_count + first + second)
                assert maximum == max(deficits)
                assert maximum <= sum(deficits) <= 91 * maximum
                assert (maximum == 0) == (sum(deficits) == 0)
                if maximum == 0:
                    assert pair_count >= 5
                    assert second >= 1 and first <= 3 * pair_count - 13
                    assert all(max(0, 13 - 3 * pair_count + value) == 0 for value in values)
                    zero_profiles += 1
                    zero_pair_counts[pair_count] += 1
                feasible_extremal_profiles += 1
                extremal_digest.update(bytes([pair_count, first, second]))
    assert extremal_checks == 47905 and feasible_extremal_profiles > 0 and zero_profiles > 0
    binary_tie_checks = 0
    for high in [1, 2, 6, 7, 63, 64]:
        for mask in range(1 << 14):
            values = [high if mask & (1 << position) else 0 for position in range(14)]
            first, second = top_two(values)
            assert first + second == max(values[a] + values[b] for a, b in POSITIONS)
            binary_tie_checks += 1
    assert binary_tie_checks == 98304
    boundary_checks = 0
    boundary_digest = hashlib.sha256()
    levels = [0, 1, 2, 5, 6, 7, 63, 64]
    for sorted_values in itertools.combinations_with_replacement(levels, 14):
        pair_maximum = max(sorted_values[a] + sorted_values[b] for a, b in POSITIONS)
        shift = sum(sorted_values) % 14
        rotated = sorted_values[shift:] + sorted_values[:shift]
        for values in [sorted_values, sorted_values[::-1], rotated]:
            assert sum(top_two(values)) == pair_maximum
        boundary_digest.update(bytes(sorted_values))
        boundary_checks += 1
    assert boundary_checks == 116280
    tied_link = [(3, 4, 5), (3, 6, 7), (4, 8, 9), (10, 11, 12), (13, 14, 15)]
    tied_values = link_counts(tied_link)
    assert sorted(tied_values, reverse=True) == [2, 2, *([1] * 11), 0]
    correct = max(row_deficits(5, tied_values))
    wrong_distinct_values = sorted(set(tied_values), reverse=True)[:2]
    assert correct == 1 and max(0, 12 - 15 + sum(wrong_distinct_values)) == 0
    one_repeat_link = [(3, 4, 5), (3, 6, 7), (8, 9, 10), (11, 12, 13), (14, 15, 16)]
    one_repeat = link_counts(one_repeat_link)
    assert max(row_deficits(5, one_repeat)) == 0
    assert max(0, 12 - 15 + 2 * max(one_repeat)) == 1
    three_repeat_link = [(3, 4, 5), (3, 6, 7), (4, 8, 9), (5, 10, 11), (12, 13, 14)]
    three_repeat = link_counts(three_repeat_link)
    deficits = row_deficits(5, three_repeat)
    assert max(deficits) == 1 and sum(deficits) == 3
    forged = [0] * 14
    assert max(row_deficits(4, forged)) == 0 and sum(forged) != 3 * 4
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "optimizer_calls": 0,
        "production_implementation_changed": False,
        "definition": "For each pairP, take the largest and second-largest values among "
        "its14 distinct triple positions. Equal values at distinct positions count twice. "
        "D2max=sum_P max(0,12-3*c(P)+top1(P)+top2(P)).",
        "full_definition": "D2sum=sum_P sum_{a<b outsideP}max(0,12-3*c(P)+c(Pa)+c(Pb)).",
        "equivalence_proof": "For any two distinct positions, their sum is at most the sum "
        "of the two largest positions, and the maximizing two positions are one of the91 "
        "rows. Adding the common constant12-3*c(P) and applying max(0,.) preserves the "
        "maximum. Thus D2max=0 iff all10920 rows hold, iff D2sum=0. Ties in values do "
        "not change this argument because positions, not values, must be distinct.",
        "metric_bound": "0<=D2max<=D2sum<=91*D2max. The positive scores are generally different.",
        "actual_family_identity": "Each selected five-point block throughP contributes to "
        "exactly three of its14 triple positions. Hence sum c(Px)=3*c(P), each c(Px)<=c(P), "
        "and c(P)>0 gives at least three positive positions.",
        "pair_floor_proof": "D2max=0 makes top1+top2<=3*c(P)-12. If c(P)<=3 the right side "
        "is negative. If c(P)=4 it is zero, but the mass identity gives total12 and thus "
        "a positive top1. Both contradict nonnegative top counts. Therefore c(P)>=5.",
        "single_cut_proof": "For an actual family with D2max=0, c(P)>=5. At least three "
        "positions are positive, so top2>=1. Thus every c(Px)<=top1<=3*c(P)-13, proving "
        "every single-triple deficit is zero. No separate hard pair floor is needed "
        "for zero-deficit qualification when all counts are exact.",
        "scope": "General counting proof for actual five-point block families on16 points. "
        "Finite count-bound controls cover c(P)=0..64, the native64-block scope.",
        "extremal_triples_checked": extremal_checks,
        "compatible_extremal_profiles": feasible_extremal_profiles,
        "zero_extremal_profiles": zero_profiles,
        "zero_profile_pair_counts": dict(sorted(zero_pair_counts.items())),
        "extremal_profile_sha256": extremal_digest.hexdigest(),
        "binary_tie_position_profiles": binary_tie_checks,
        "boundary_histogram_profiles": boundary_checks,
        "boundary_profile_orders_checked": 3 * boundary_checks,
        "boundary_profile_sha256": boundary_digest.hexdigest(),
        "damaged_controls_rejected": [
            "deduplicating tied count values",
            "reusing the maximum position",
            "equating positive D2max with D2sum",
            "omitting actual mass identity",
        ],
        "five_block_pair_link_controls": {
            "tied_maxima": tied_link,
            "one_repeated_point": one_repeat_link,
            "different_positive_scores": three_repeat_link,
        },
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "extremal_profiles": feasible_extremal_profiles,
                "zero_extremal_profiles": zero_profiles,
                "binary_ties": binary_tie_checks,
                "boundary_histograms": boundary_checks,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
