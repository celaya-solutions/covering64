# Document:    Independent Inversive Plane Construction Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      964e8edd31d735b8326efc35ae35d6636976f5c5323b6f3a8d3e4534957d5665
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Construct and audit a different mother design; no solver or package imports.

Print a compact JSON report, including a 67-block witness. The witness still
requires the repository's package verifier and scripts/check_cover.py before
being accepted as a project candidate. This script does not search for 64.
"""

import json
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    return sha256(raw.encode()).hexdigest()


def multiply(a, b):
    """GF(16), polynomial basis, modulus X^4 + X + 1."""
    answer = 0
    while b:
        if b & 1:
            answer ^= a
        b >>= 1
        a <<= 1
        if a & 16:
            a ^= 19
    return answer


def power(a, exponent):
    answer = 1
    for _ in range(exponent):
        answer = multiply(answer, a)
    return answer


def canonical(blocks):
    return sorted(tuple(sorted(block)) for block in blocks)


def construct():
    field = range(16)
    subfield = [a for a in field if power(a, 4) == a]
    assert len(subfield) == 4
    circles = canonical(
        tuple(z + 1 for z in field if power(z ^ center, 5) == radius)
        for center in field
        for radius in subfield
        if radius
    )
    lines = sorted(
        {
            tuple(sorted((center ^ multiply(direction, a)) + 1 for a in subfield))
            for center in field
            for direction in range(1, 16)
        }
    )
    return circles, lines


def audit(circles, lines):
    assert len(circles) == len(set(circles)) == 48
    assert len(lines) == len(set(lines)) == 20
    for collection, size in ((circles, 5), (lines, 4)):
        for block in collection:
            assert len(block) == size
            assert block == tuple(sorted(set(block)))
            assert all(1 <= point <= 16 for point in block)
    line_pair_counts = Counter(pair for line in lines for pair in combinations(line, 2))
    assert len(line_pair_counts) == 120
    assert set(line_pair_counts.values()) == {1}
    triple_counts = Counter(
        triple for block in circles + lines for triple in combinations(block, 3)
    )
    assert len(triple_counts) == 560
    assert set(triple_counts.values()) == {1}
    secants = []
    nuclei = []
    for circle in circles:
        circle_set = set(circle)
        assert all(len(circle_set.intersection(line)) <= 2 for line in lines)
        circle_secants = [
            i for i, line in enumerate(lines) if len(circle_set.intersection(line)) == 2
        ]
        assert len(circle_secants) == 10
        counts = Counter(point for i in circle_secants for point in lines[i])
        assert all(counts[point] == 4 for point in circle)
        exterior = [point for point in range(1, 17) if point not in circle_set]
        nucleus = [point for point in exterior if counts[point] == 0]
        assert len(nucleus) == 1
        assert all(counts[point] == 2 for point in exterior if point != nucleus[0])
        nuclei.append(nucleus[0])
        secants.append(set(circle_secants))
    pair_obstructions = []
    intersection_counts = Counter()
    for i, j in combinations(range(48), 2):
        shared_points = set(circles[i]).intersection(circles[j])
        assert len(shared_points) <= 2
        intersection_counts[len(shared_points)] += 1
        incompatible = [
            k for k in sorted(secants[i].intersection(secants[j]))
            if shared_points.issubset(lines[k])
        ]
        assert incompatible, (i, j)
        pair_obstructions.append((i, j, incompatible[0]))
    assert len(pair_obstructions) == 1128
    return {
        "circles": len(circles),
        "lines": len(lines),
        "triple_partition": len(triple_counts),
        "circle_pair_intersections": dict(sorted(intersection_counts.items())),
        "incompatible_circle_pairs": len(pair_obstructions),
        "pair_obstructions_sha256": digest(pair_obstructions),
        "nuclei_sha256": digest(nuclei),
    }


def make_67_cover(circles, lines):
    removed = circles[0]
    # Five disjoint-edge pairs form a perfect matching in the Petersen graph.
    edge_pairs = [
        ((0, 1), (2, 3)),
        ((0, 2), (1, 4)),
        ((0, 3), (2, 4)),
        ((0, 4), (1, 3)),
        ((1, 2), (3, 4)),
    ]
    choices = {}
    for first, second in edge_pairs:
        outside = next(iter(set(range(5)).difference(first + second)))
        point = removed[outside]
        for edge in (first, second):
            pair = {removed[edge[0]], removed[edge[1]]}
            matching = [i for i, line in enumerate(lines) if pair.issubset(line)]
            assert len(matching) == 1
            i = matching[0]
            assert point not in lines[i]
            assert i not in choices
            choices[i] = point
    assert len(choices) == 10
    extensions = []
    for i, line in enumerate(lines):
        point = choices.get(i, next(p for p in range(1, 17) if p not in line))
        extensions.append(tuple(sorted(line + (point,))))
    cover = canonical(circles[1:] + extensions)
    assert len(cover) == len(set(cover)) == 67
    counts = Counter(triple for block in cover for triple in combinations(block, 3))
    assert len(counts) == 560
    return cover


def main():
    circles, lines = construct()
    report = audit(circles, lines)
    controls = []
    for name, damaged in (
        ("duplicate_circle", [circles[0]] + circles[:-1]),
        ("malformed_circle", [circles[0][:-1]] + circles[1:]),
        ("damaged_circle", [tuple(range(1, 6))] + circles[1:]),
    ):
        try:
            audit(damaged, lines)
        except AssertionError:
            controls.append(name)
        else:
            raise AssertionError("negative control accepted: " + name)
    cover = make_67_cover(circles, lines)
    pool = canonical(
        circles + [tuple(sorted(line + (point,))) for line in lines
                   for point in range(1, 17) if point not in line]
    )
    assert len(pool) == len(set(pool)) == 288
    report.update({
        "schema": "independent-inversive-audit-v1",
        "field_polynomial": "X^4 + X + 1",
        "point_labels": "polynomial-basis integer + 1",
        "canonical_json": "sorted keys, compact separators, trailing newline",
        "circles_sha256": digest(circles),
        "lines_sha256": digest(lines),
        "pool_blocks": len(pool),
        "pool_sha256": digest(pool),
        "pure_one_extension_per_line_minimum": 67,
        "negative_controls_rejected": controls,
        "witness_67_sha256": digest(cover),
        "witness_67": cover,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "pure-family minimum only; no 64-block result or general lower bound",
    })
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
