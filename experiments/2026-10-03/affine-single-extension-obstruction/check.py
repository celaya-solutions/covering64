# Document:    Affine Single-Extension Obstruction Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check an obstruction only for one extension of each affine line."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
POOL = HERE.parent / "affine-extension-independent" / "pool.json"


def check(circles, lines):
    assert len(circles) == len(set(circles)) == 48
    assert len(lines) == len(set(lines)) == 20
    assert all(tuple(sorted(set(b))) == b and len(b) == 5 for b in circles)
    assert all(tuple(sorted(set(b))) == b and len(b) == 4 for b in lines)
    assert set().union(*map(set, circles), *map(set, lines)) == set(range(1, 17))
    pairs = Counter(p for line in lines for p in itertools.combinations(line, 2))
    assert len(pairs) == 120 and set(pairs.values()) == {1}
    circle_triples = Counter(t for c in circles for t in itertools.combinations(c, 3))
    line_triples = Counter(t for line in lines for t in itertools.combinations(line, 3))
    assert len(circle_triples) == 480 and set(circle_triples.values()) == {1}
    assert len(line_triples) == 80 and set(line_triples.values()) == {1}
    assert not set(circle_triples) & set(line_triples)
    assert len(set(circle_triples) | set(line_triples)) == 560
    cs, ls = list(map(set, circles)), list(map(set, lines))
    assert all(len(c & line) <= 2 for c in cs for line in ls)
    assert all(sum(len(c & line) == 2 for line in ls) == 10 for c in cs)
    # A line extension covers at most one triple of a given circle. It covers
    # one precisely when the line is secant and the added point is in the circle.
    for c in cs:
        for line in ls:
            for point in set(range(1, 17)) - line:
                shared = len(c & (line | {point}))
                actual = sum(set(t) <= line | {point}
                             for t in itertools.combinations(sorted(c), 3))
                expected = int(len(c & line) == 2 and point in c)
                assert shared <= 3 and actual == expected
    blockers, histogram = [], Counter()
    for i, j in itertools.combinations(range(48), 2):
        bad = [k for k, line in enumerate(ls)
               if len(cs[i] & line) == len(cs[j] & line) == 2
               and not ((cs[i] & cs[j]) - line)]
        assert bad, (i, j)
        blockers.append({"circle_ids_zero_based": [i, j], "line_ids_zero_based": bad})
        histogram[(len(cs[i] & cs[j]), len(bad))] += 1
    assert len(blockers) == 1128
    return {
        "passed": True,
        "scope": "48 specified circles plus exactly one extension of each of 20 lines",
        "minimum_retained_circles": 47,
        "restricted_block_lower_bound": 67,
        "incompatible_circle_pairs": len(blockers),
        "histogram": [{"circle_intersection": key[0], "bad_lines": key[1], "pairs": value}
                      for key, value in sorted(histogram.items())],
        "blockers": blockers,
        "global_lower_bound_claim": False,
    }


def main():
    data = json.loads(POOL.read_text())
    circles = list(map(tuple, data["circles"]))
    lines = list(map(tuple, data["lines"]))
    result = check(circles, lines)
    damaged = [
        (circles[:-1], lines),
        (circles + [circles[0]], lines),
        ([circles[0]] + circles[:-1], lines),
        (circles, lines[:-1]),
        (circles, [lines[0]] + lines[:-1]),
        ([(0,) + circles[0][1:]] + circles[1:], lines),
        (circles, [(lines[0][0],) * 4] + lines[1:]),
    ]
    for bad_circles, bad_lines in damaged:
        try:
            check(bad_circles, bad_lines)
        except AssertionError:
            continue
        raise AssertionError("damaged pool accepted")
    result["damaged_controls_rejected"] = len(damaged)
    result["pool_sha256"] = hashlib.sha256(POOL.read_bytes()).hexdigest()
    result["checker_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "blockers"}))


if __name__ == "__main__":
    main()
