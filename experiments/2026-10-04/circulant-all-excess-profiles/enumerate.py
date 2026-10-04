"""Exact finite enumeration of excess profiles for one named pair graph."""

import json
import platform
import subprocess
import time
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from math import lcm
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    started = time.monotonic()
    vertices = range(16)
    edges = sorted({tuple(sorted((a, (a + d) % 16))) for a in vertices for d in (1, 3, 8, 13, 15)})
    adjacent = [{b for b in vertices if tuple(sorted((a, b))) in edges} for a in vertices]
    cuts = [
        set(side)
        for side in combinations(vertices, 8)
        if 0 in side and sum((a in side) != (b in side) for a, b in edges) == 32
    ]
    forced, choices = [], []
    for a, b in combinations(vertices, 2):
        if (a, b) in edges:
            continue
        centers = [
            c
            for c in sorted(adjacent[a] & adjacent[b])
            if not any(set((a, b, c)) <= side or not set((a, b, c)) & side for side in cuts)
        ]
        assert len(centers) in (1, 2)
        (forced if len(centers) == 1 else choices).append((a, b, centers))
    assert len(edges) == 40 and len(cuts) == 9
    assert len(forced) == 32 and len(choices) == 48

    def uses(edge, a, b, c):
        return int(edge in (tuple(sorted((a, c))), tuple(sorted((b, c)))))

    matrix, targets = [], []
    for edge in edges:
        baseline = sum(uses(edge, a, b, centers[0]) for a, b, centers in forced + choices)
        matrix.append(
            [
                uses(edge, a, b, centers[1]) - uses(edge, a, b, centers[0])
                for a, b, centers in choices
            ]
        )
        targets.append(4 - baseline)
    reduced = [[Fraction(v) for v in row + [b]] for row, b in zip(matrix, targets)]
    pivots = []
    for col in range(48):
        pivot = next((r for r in range(len(pivots), 40) if reduced[r][col]), None)
        if pivot is None:
            continue
        row = len(pivots)
        reduced[row], reduced[pivot] = reduced[pivot], reduced[row]
        divisor = reduced[row][col]
        reduced[row] = [x / divisor for x in reduced[row]]
        for r in range(40):
            if r != row and reduced[r][col]:
                multiplier = reduced[r][col]
                reduced[r] = [x - multiplier * y for x, y in zip(reduced[r], reduced[row])]
        pivots.append(col)
    free = [col for col in range(48) if col not in pivots]
    assert len(pivots) == 30 and len(free) == 18
    assert all(not any(row) for row in reduced[30:])

    def subset_sums(coefficients):
        values = [0] * (1 << len(coefficients))
        for mask in range(1, len(values)):
            bit = mask & -mask
            values[mask] = values[mask ^ bit] + coefficients[bit.bit_length() - 1]
        return values

    equations = []
    for row in reduced[:30]:
        denominator = lcm(*(x.denominator for x in row))
        coefficients = [int(row[col] * denominator) for col in free]
        equations.append(
            (
                denominator,
                int(row[-1] * denominator),
                subset_sums(coefficients[:9]),
                subset_sums(coefficients[9:]),
            )
        )
    accepted = []
    rejected_at = Counter()
    for mask in range(1 << 18):
        if mask % 4096 == 0 and time.monotonic() - started > 60:
            raise TimeoutError("Finite enumeration incomplete; no completion receipt written")
        low, high = mask & 511, mask >> 9
        pivot_values = []
        for row_id, (denominator, constant, left, right) in enumerate(equations):
            value = constant - left[low] - right[high]
            if value not in (0, denominator):
                rejected_at[row_id] += 1
                break
            pivot_values.append(value // denominator)
        else:
            values = [0] * 48
            for i, col in enumerate(free):
                values[col] = (mask >> i) & 1
            for col, value in zip(pivots, pivot_values):
                values[col] = value
            assert all(
                sum(a * x for a, x in zip(row, values)) == b for row, b in zip(matrix, targets)
            )
            triples = [tuple(sorted((a, b, centers[0]))) for a, b, centers in forced]
            triples += [
                tuple(sorted((a, b, centers[x]))) for (a, b, centers), x in zip(choices, values)
            ]
            assert len(set(triples)) == 80
            pair_counts = Counter(pair for triple in triples for pair in combinations(triple, 2))
            assert all(
                pair_counts[p] == (4 if p in edges else 1) for p in combinations(vertices, 2)
            )
            accepted.append(sum(x << i for i, x in enumerate(values)))
    assert len(set(accepted)) == len(accepted)
    assert len(accepted) + sum(rejected_at.values()) == 1 << 18
    dump(
        "geometry.json",
        {
            "labels": "one-based; choice indices are zero-based",
            "edges": [[a + 1, b + 1] for a, b in edges],
            "tight_cuts": [sorted(a + 1 for a in side) for side in cuts],
            "forced": [[a + 1, b + 1, [c + 1 for c in centers]] for a, b, centers in forced],
            "choices": [[a + 1, b + 1, [c + 1 for c in centers]] for a, b, centers in choices],
            "matrix": matrix,
            "targets": targets,
            "pivots": pivots,
            "free_columns": free,
            "rref": [[str(x) for x in row] for row in reduced],
        },
    )
    dump("profiles.json", {"choice_masks": sorted(accepted)})
    summary = {
        "scope": "All P3 excess profiles for the named circulant pair graph, after tight cuts",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "completed": True,
        "optimizer_calls": 0,
        "cover_search_calls": 0,
        "cover_found": False,
        "global_exclusion": False,
        "rank": 30,
        "free_dimension": 18,
        "free_assignments_checked": 1 << 18,
        "profiles": len(accepted),
        "rejected_at_pivot_row": dict(sorted(rejected_at.items())),
        "finite_budget_seconds": 60,
        "elapsed_seconds": time.monotonic() - started,
        "geometry_sha256": sha256((HERE / "geometry.json").read_bytes()).hexdigest(),
        "profiles_sha256": sha256((HERE / "profiles.json").read_bytes()).hexdigest(),
    }
    dump("summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
