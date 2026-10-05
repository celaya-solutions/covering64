# Document:    Orbit Enumeration of Doubled Triples at the Degree-20 Point
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-05
# SHA256:      a1f0582bf387f0c15070613416b1302783bdb0bd1328c75422083b873fdf58a8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""List the graphs X_z of a 61-block cover up to the symmetries of E.

Labels: z = 16, A = 11..15, M = 1..10 with E-matching (1,2),(3,4),(5,6),(7,8),
(9,10). X_z is the graph on A and M whose edges uw are the doubled triples
{z,u,w}: degree 4 at every point of A and degree 1 at every point of M
(Lemma 6 of docs/lower-bound-61-structure.md).

The symmetry group H = Sym(A) x W has order 120 * 3840, where W permutes the
five E-pairs and flips points within pairs. The enumeration first takes the
graphs G on A (edges of X_z inside A) up to Sym(A). For each representative G it
lists every labeled way to attach M: each point a of A takes 4 - deg_G(a)
private M-points, and the remaining M-points carry a perfect matching. Each
labeled configuration is reduced to its least image under Aut(G) x W. Every
X_z arises from exactly one representative G after a relabeling of A, so the
union of these orbit lists is complete; the census below cross-checks it
against an exact count of all labeled X_z.
"""

import json
import sys
from itertools import combinations, permutations, product
from math import factorial
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A = (11, 12, 13, 14, 15)
M = tuple(range(1, 11))
A_PAIRS = list(combinations(A, 2))


def double_factorial_odd(n):
    """(n-1)!! perfect matchings of n points (n even), 1 for n = 0."""
    result = 1
    for k in range(n - 1, 0, -2):
        result *= k
    return result


def w_group():
    """All 3840 elements of W as arrays mapping M-point (1..10) to M-point."""
    maps = []
    for perm in permutations(range(5)):
        for flips in product((0, 1), repeat=5):
            image = [0] * 11
            for k in range(5):
                for b in (0, 1):
                    image[2 * k + 1 + b] = 2 * perm[k] + 1 + (b ^ flips[k])
            maps.append(image)
    return np.array(maps, dtype=np.int64)


def graph_reps():
    """Graphs on A with 5..10 edges, one per Sym(A) orbit, with automorphisms."""
    perms = list(permutations(A))
    reps = {}
    for size in range(5, 11):
        for edges in combinations(A_PAIRS, size):
            best = None
            for p in perms:
                m = dict(zip(A, p))
                image = tuple(sorted(tuple(sorted((m[u], m[v]))) for u, v in edges))
                if best is None or image < best:
                    best = image
            reps.setdefault(best, None)
    out = []
    for edges in sorted(reps, key=lambda e: (len(e), e)):
        auts = [p for p in perms if _maps_to(edges, dict(zip(A, p))) == set(edges)]
        out.append((edges, auts))
    return out


def _maps_to(edges, m):
    return {tuple(sorted((m[u], m[v]))) for u, v in edges}


def labeled_count(edges):
    deg = {a: sum(a in e for e in edges) for a in A}
    need = [4 - deg[a] for a in A]
    if min(need) < 0 or sum(need) > 10:
        return 0
    rest = 10 - sum(need)
    ways = factorial(10)
    for c in need:
        ways //= factorial(c)
    ways //= factorial(rest)
    return ways * double_factorial_odd(rest)


def configurations(edges):
    """Every labeled attachment: label[m] in A or 0, plus a matching on label-0 points."""
    deg = {a: sum(a in e for e in edges) for a in A}
    need = [(a, 4 - deg[a]) for a in A]

    def assign(i, free, label):
        if i == len(need):
            yield from matchings(sorted(free), label, [])
            return
        a, c = need[i]
        for chosen in combinations(sorted(free), c):
            for m in chosen:
                label[m] = a
            yield from assign(i + 1, free - set(chosen), label)
            for m in chosen:
                label[m] = 0

    def matchings(points, label, pairs):
        if not points:
            yield dict(label), list(pairs)
            return
        first = points[0]
        for j in range(1, len(points)):
            pairs.append((first, points[j]))
            yield from matchings(points[1:j] + points[j + 1 :], label, pairs)
            pairs.pop()

    yield from assign(0, set(M), {m: 0 for m in M})


def canonical(label, pairs, auts, wmaps):
    """Least image under Aut(G) x W of (labels on M, matching on unlabeled M)."""
    best = None
    lab = np.array([label[m] for m in M], dtype=np.int64)
    pa = np.array(pairs, dtype=np.int64).reshape(-1, 2)
    for p in auts:
        sigma = {a: b for a, b in zip(A, p)}
        relabeled = np.array([sigma.get(v, 0) for v in lab], dtype=np.int64)
        # image label at point wmaps[g, m] is relabeled[m - 1]
        images = np.zeros((len(wmaps), 10), dtype=np.int64)
        rows = np.arange(len(wmaps))[:, None]
        images[rows, wmaps[:, 1:] - 1] = relabeled[None, :]
        if len(pa):
            u, v = wmaps[:, pa[:, 0]], wmaps[:, pa[:, 1]]
            lo, hi = np.minimum(u, v), np.maximum(u, v)
            codes = np.sort(lo * 16 + hi, axis=1)
            key = np.concatenate([images, codes], axis=1)
        else:
            key = images
        order = np.lexsort(key.T[::-1])
        candidate = tuple(int(x) for x in key[order[0]])
        if best is None or candidate < best:
            best = candidate
    return best


def main():
    wmaps = w_group()
    total_labeled = 0
    for size in range(0, 11):
        for edges in combinations(A_PAIRS, size):
            total_labeled += labeled_count(edges)
    reps = graph_reps()
    records, census = [], []
    for gi, (edges, auts) in enumerate(reps):
        seen = {}
        count = 0
        for label, pairs in configurations(edges):
            count += 1
            key = canonical(label, pairs, auts, wmaps)
            seen[key] = seen.get(key, 0) + 1
        group = len(auts) * len(wmaps)
        for key, hits in sorted(seen.items()):
            # orbit size in the labeled set for fixed G equals hits; stabilizer = group / hits
            assert group % hits == 0, "orbit size divides the group order"
            records.append(
                {
                    "graph": gi,
                    "graph_edges": edges,
                    "key": key,
                    "labeled_hits": hits,
                    "stabilizer_order": group // hits,
                }
            )
        census.append(
            {
                "graph": gi,
                "edges": len(edges),
                "aut_order": len(auts),
                "labeled": count,
                "orbits": len(seen),
                "expected_labeled": labeled_count(edges),
            }
        )
        print(gi, len(edges), len(auts), count, len(seen), flush=True)
    orbit_sum = sum((120 // c["aut_order"]) * c["labeled"] for c in census)
    summary = {
        "total_labeled_xz": total_labeled,
        "sum_over_graph_reps_of_orbit_times_labeled": orbit_sum,
        "graph_reps": len(reps),
        "xz_orbits": len(records),
        "census": census,
    }
    (HERE / "orbits.json").write_text(json.dumps({"summary": summary, "orbits": records}) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "census"}))
    return summary


if __name__ == "__main__":
    sys.exit(main())
