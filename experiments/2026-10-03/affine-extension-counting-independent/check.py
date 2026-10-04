# Document:   Independent Affine Extension Counting Audit
# Version:    v1.0.0
# Author:     Celaya Solutions
# Contact:    hello@celayasolutions.com
# Date:       2026-10-03
# SHA256:     9514d6d0ec60d8ac082dfa85eb903c848d4121a2562ebabf820d160f817ed4fd
# Chain:      n/a
# Tx:         [not anchored]
# License:    All Rights Reserved / Celaya Solutions

"""Regenerate the geometry and check the exact20/exact21 restricted cases."""

import hashlib
import itertools
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
POINTS = range(1, 17)
EMBED = (0, 1, 6, 7)


def mul(a, b):
    """Polynomial multiplication in F2[w]/(w*w+w+1)."""
    value = 0
    for _ in range(2):
        if b & 1:
            value ^= a
        b >>= 1
        a <<= 1
        if a & 4:
            a ^= 7
    return value


def label(u, v):
    return (EMBED[u] ^ (EMBED[v] << 1)) + 1


def construct():
    lines = {tuple(sorted(label(u, v) for v in range(4))) for u in range(4)}
    lines.update(
        tuple(sorted(label(u, mul(m, u) ^ b) for u in range(4))) for m in range(4) for b in range(4)
    )
    families = {}
    for a, c in itertools.product(range(1, 4), repeat=2):
        product = mul(a, c)
        if product ^ mul(product, product) != 1:
            continue
        circles = set()
        for h, k, radius in itertools.product(range(4), range(4), range(1, 4)):
            circle = []
            for u, v in itertools.product(range(4), repeat=2):
                x, y = u ^ h, v ^ k
                if mul(a, mul(x, x)) ^ mul(x, y) ^ mul(c, mul(y, y)) == radius:
                    circle.append(label(u, v))
            circles.add(tuple(sorted(circle)))
        families[(a, c)] = sorted(circles)
    return sorted(lines), families


def validate_geometry(circles, lines):
    assert len(circles) == len(set(circles)) == 48
    assert len(lines) == len(set(lines)) == 20
    assert all(tuple(sorted(set(c))) == c and len(c) == 5 for c in circles)
    assert all(tuple(sorted(set(line))) == line and len(line) == 4 for line in lines)
    assert set().union(*map(set, circles), *map(set, lines)) == set(POINTS)
    pairs = Counter(pair for line in lines for pair in itertools.combinations(line, 2))
    assert len(pairs) == 120 and set(pairs.values()) == {1}
    triples = Counter(t for b in circles + lines for t in itertools.combinations(b, 3))
    assert len(triples) == 560 and set(triples.values()) == {1}
    return list(map(set, circles)), list(map(set, lines))


def analyze_family(circles, lines):
    cs, ls = validate_geometry(circles, lines)
    masks = []
    for line in ls:
        row = []
        for point in POINTS:
            if point in line:
                continue
            extension = line | {point}
            mask = 0
            for i, circle in enumerate(cs):
                hits = sum(set(t) <= extension for t in itertools.combinations(circle, 3))
                expected = int(len(circle & line) == 2 and point in circle)
                assert hits == expected and hits in (0, 1)
                if hits:
                    mask |= 1 << i
            assert mask.bit_count() == 6
            row.append(mask)
        assert len(row) == 12
        masks.append(row)
    assert all(sum(len(circle & line) == 2 for line in ls) == 10 for circle in cs)
    pair_histogram = Counter()
    adjacent = [0] * 48
    blockers = []
    for i, j in itertools.combinations(range(48), 2):
        bad = [
            k
            for k, line in enumerate(ls)
            if len(cs[i] & line) == len(cs[j] & line) == 2 and not ((cs[i] & cs[j]) - line)
        ]
        assert bad
        blockers.append({"circle_ids_zero_based": [i, j], "line_ids_zero_based": bad})
        pair_histogram[(len(cs[i] & cs[j]), len(bad))] += 1
        if len(bad) <= 3:
            adjacent[i] |= 1 << j
            adjacent[j] |= 1 << i
    capacities = Counter()

    def visit(mask, size, candidates):
        if size == 5:
            baseline = 0
            extra = 0
            for row in masks:
                weights = sorted(((mask & m).bit_count() for m in row), reverse=True)
                baseline += weights[0]
                extra = max(extra, weights[1])
            capacities[baseline + extra] += 1
            assert baseline + extra < 50
            return
        if candidates.bit_count() < 5 - size:
            return
        while candidates:
            bit = candidates & -candidates
            candidates ^= bit
            vertex = bit.bit_length() - 1
            visit(mask | bit, size + 1, candidates & adjacent[vertex])

    visit(0, 0, (1 << 48) - 1)
    return {
        "exact20": {"incompatible_pairs": len(blockers), "minimum_retained_circles": 47},
        "exact21": {
            "pair_compatible_sets_of_five": sum(capacities.values()),
            "capacity_histogram": {str(k): v for k, v in sorted(capacities.items())},
            "maximum_capacity": max(capacities),
            "required_capacity": 50,
            "survivors": 0,
        },
        "pair_histogram": [
            {"circle_intersection": k[0], "bad_lines": k[1], "pairs": n}
            for k, n in sorted(pair_histogram.items())
        ],
    }, blockers


def main():
    started = time.monotonic()
    lines, families = construct()
    assert len(families) == 6
    reference = HERE.parent / "affine-extension-independent" / "pool.json"
    existing = json.loads(reference.read_text())
    assert lines == list(map(tuple, existing["lines"]))
    assert families[(1, 2)] == list(map(tuple, existing["circles"]))
    prior_file = HERE.parent / "affine-single-extension-obstruction" / "audit.json"
    prior = json.loads(prior_file.read_text())
    results = []
    for form, circles in families.items():
        result, blockers = analyze_family(circles, lines)
        if form == (1, 2):
            assert blockers == prior["blockers"]
            assert result["pair_histogram"] == prior["histogram"]
        results.append({"form": list(form), **result})
    assert all(r["exact21"] == results[0]["exact21"] for r in results)
    circles = families[(1, 2)]
    controls = [
        (circles[:-1], lines),
        (circles + [circles[0]], lines),
        ([circles[0]] + circles[:-1], lines),
        (circles, lines[:-1]),
        (circles, [lines[0]] + lines[:-1]),
        ([(0,) + circles[0][1:]] + circles[1:], lines),
        (circles, [(lines[0][0],) * 4] + lines[1:]),
    ]
    for damaged_circles, damaged_lines in controls:
        try:
            validate_geometry(damaged_circles, damaged_lines)
        except AssertionError:
            continue
        raise AssertionError("damaged geometry accepted")
    report = {
        "passed": True,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "reference_pool_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "prior_audit_sha256": hashlib.sha256(prior_file.read_bytes()).hexdigest(),
        "families": results,
        "damaged_geometry_controls_rejected": len(controls),
        "solver_calls": 0,
        "seconds": time.monotonic() - started,
        "scope": "One of six individual48-circle families plus240 affine line extensions; "
        "exact20 extensions permits at most one deleted circle; exact21 extensions "
        "cannot replace five circles, so cannot give64 total blocks.",
        "global_lower_bound_claim": False,
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "families"}))


if __name__ == "__main__":
    main()
