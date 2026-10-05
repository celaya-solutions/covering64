# Document:    Prescribed-Group Orbit Covering Search
# Version:     v1.2.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3be3be1c16737c25f4140ce5d28f89850bc8894103b21833a6753eaba2eee082
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Search for C(16,5,3) covers that are unions of orbits of a prescribed group.

For a permutation group G on labels 1..16, a G-invariant cover is a union of
G-orbits of 5-subsets. One block orbit covers a whole triple orbit as soon as
one of its blocks contains one triple of that orbit, so the covering problem
shrinks to one Boolean per block orbit and one row per triple orbit. CP-SAT
minimizes the total number of blocks. A result applies only to covers invariant
under that exact group; a better-than-target result is a candidate until both
covering checkers accept it.
"""

import argparse
import json
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from multiprocessing import get_context
from pathlib import Path

from ortools import __version__ as ORTOOLS_VERSION
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = 64
POINTS = 16
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))


def to_mask(labels):
    return sum(1 << (label - 1) for label in labels)


BLOCK_MASKS = tuple(to_mask(block) for block in BLOCKS)
TRIPLE_MASKS = tuple(to_mask(triple) for triple in TRIPLES)
BLOCK_ID = {mask: index for index, mask in enumerate(BLOCK_MASKS)}
TRIPLE_ID = {mask: index for index, mask in enumerate(TRIPLE_MASKS)}
BLOCK_TRIPLES = tuple(
    tuple(TRIPLE_ID[to_mask(triple)] for triple in combinations(block, 3)) for block in BLOCKS
)
IDENTITY = tuple(range(POINTS))


# ---------------------------------------------------------------- permutations
# A permutation is a 16-tuple p of 0-based images: label x maps to p[x - 1] + 1.


def from_cycles(*cycles):
    image = list(IDENTITY)
    for cycle in cycles:
        for a, b in zip(cycle, cycle[1:] + cycle[:1]):
            image[a - 1] = b - 1
    perm = tuple(image)
    if sorted(perm) != list(IDENTITY):
        raise ValueError("cycles do not define a permutation")
    return perm


def from_map(mapping):
    """Permutation from a dict or list of 0-based images over 16 points."""
    perm = tuple(mapping[i] for i in range(POINTS))
    if sorted(perm) != list(IDENTITY):
        raise ValueError("map is not a permutation")
    return perm


def compose(p, q):
    """Apply p first, then q."""
    return tuple(q[p[i]] for i in range(POINTS))


def inverse(p):
    result = [0] * POINTS
    for i, image in enumerate(p):
        result[image] = i
    return tuple(result)


def power(p, exponent):
    result = IDENTITY
    for _ in range(exponent):
        result = compose(result, p)
    return result


def element_order(p):
    seen = [False] * POINTS
    order = 1
    for start in range(POINTS):
        if seen[start]:
            continue
        length, point = 0, start
        while not seen[point]:
            seen[point] = True
            point = p[point]
            length += 1
        order = order * length // _gcd(order, length)
    return order


def _gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def cycle_type(p):
    seen = [False] * POINTS
    lengths = []
    for start in range(POINTS):
        if seen[start]:
            continue
        length, point = 0, start
        while not seen[point]:
            seen[point] = True
            point = p[point]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def group_order(gens, cap=400_000):
    """Exact order by closure, or None when the group exceeds the cap."""
    seen = {IDENTITY}
    frontier = [IDENTITY]
    while frontier:
        following = []
        for element in frontier:
            for g in gens:
                product = compose(element, g)
                if product not in seen:
                    seen.add(product)
                    following.append(product)
                    if len(seen) > cap:
                        return None
        frontier = following
    return len(seen)


class RandomElements:
    """Product-replacement generator of pseudo-random group elements."""

    def __init__(self, gens, rng, slots=12, warmup=80):
        self.rng = rng
        base = [g for g in gens if g != IDENTITY] or [IDENTITY]
        self.state = [base[i % len(base)] for i in range(slots)]
        self.accumulator = IDENTITY
        for _ in range(warmup):
            self.next()

    def next(self):
        i, j = self.rng.sample(range(len(self.state)), 2)
        other = self.state[j] if self.rng.random() < 0.5 else inverse(self.state[j])
        if self.rng.random() < 0.5:
            self.state[i] = compose(self.state[i], other)
        else:
            self.state[i] = compose(other, self.state[i])
        self.accumulator = compose(self.accumulator, self.state[i])
        return self.accumulator


# ---------------------------------------------------------------- orbit model


def tables(p):
    low, high = [0] * 256, [0] * 256
    for byte in range(256):
        lo_value = hi_value = 0
        for bit in range(8):
            if byte >> bit & 1:
                lo_value |= 1 << p[bit]
                hi_value |= 1 << p[bit + 8]
        low[byte], high[byte] = lo_value, hi_value
    return low, high


def orbit_partition(gens, masks, ids):
    tabs = [tables(g) for g in gens]
    label = [-1] * len(masks)
    sizes = []
    for index, mask in enumerate(masks):
        if label[index] >= 0:
            continue
        orbit = len(sizes)
        label[index] = orbit
        stack, size = [mask], 1
        while stack:
            current = stack.pop()
            for low, high in tabs:
                image = low[current & 255] | high[current >> 8]
                target = ids[image]
                if label[target] < 0:
                    label[target] = orbit
                    stack.append(image)
                    size += 1
        sizes.append(size)
    return label, sizes


def point_orbits(gens):
    label = list(IDENTITY)

    def find(x):
        while label[x] != x:
            label[x] = label[label[x]]
            x = label[x]
        return x

    for g in gens:
        for i in range(POINTS):
            a, b = find(i), find(g[i])
            if a != b:
                label[max(a, b)] = min(a, b)
    groups = Counter(find(i) for i in range(POINTS))
    return tuple(sorted(groups.values(), reverse=True))


def orbit_model(gens):
    block_label, block_sizes = orbit_partition(gens, BLOCK_MASKS, BLOCK_ID)
    triple_label, triple_sizes = orbit_partition(gens, TRIPLE_MASKS, TRIPLE_ID)
    representative = {}
    for index, orbit in enumerate(block_label):
        representative.setdefault(orbit, index)
    covers = []
    for orbit in range(len(block_sizes)):
        rep = representative[orbit]
        covers.append(tuple(sorted({triple_label[t] for t in BLOCK_TRIPLES[rep]})))
    # Implied rows: each point lies in at least 19 blocks and each pair in at
    # least 5 (the blocks through a pair must meet all 14 other points in
    # triples). By invariance one row per point orbit or pair orbit suffices.
    point_masks = tuple(1 << i for i in range(POINTS))
    point_label, _ = orbit_partition(gens, point_masks, {m: i for i, m in enumerate(point_masks)})
    pair_masks = tuple(to_mask(p) for p in combinations(range(1, 17), 2))
    pair_label, _ = orbit_partition(gens, pair_masks, {m: i for i, m in enumerate(pair_masks)})
    point_rep, pair_rep = {}, {}
    for index, orbit in enumerate(point_label):
        point_rep.setdefault(orbit, index)
    for index, orbit in enumerate(pair_label):
        pair_rep.setdefault(orbit, pair_masks[index])
    degree_rows = {o: Counter() for o in point_rep}
    pair_rows = {o: Counter() for o in pair_rep}
    for index, mask in enumerate(BLOCK_MASKS):
        orbit = block_label[index]
        for o, point in point_rep.items():
            if mask >> point & 1:
                degree_rows[o][orbit] += 1
        for o, pair in pair_rep.items():
            if mask & pair == pair:
                pair_rows[o][orbit] += 1
    return {
        "block_label": block_label,
        "block_sizes": block_sizes,
        "covers": covers,
        "triple_sizes": triple_sizes,
        "degree_rows": list(degree_rows.values()),
        "pair_rows": list(pair_rows.values()),
    }


def largest_total(sizes, cap):
    """Largest sum of distinct orbits not exceeding cap (bounded subset sum)."""
    reachable = 1
    for size in sizes:
        if size <= cap:
            reachable |= reachable << size
            reachable &= (1 << (cap + 1)) - 1
    return reachable.bit_length() - 1


def signature(gens, model):
    return json.dumps(
        [
            point_orbits(gens),
            sorted(Counter(model["triple_sizes"]).items()),
            sorted(Counter(model["block_sizes"]).items()),
            sorted(
                Counter((s, len(c)) for s, c in zip(model["block_sizes"], model["covers"])).items()
            ),
        ]
    )


def reduce_dominated(sizes, covers):
    """Drop block orbits whose covered rows are a subset of a no-larger orbit's rows.

    Any cover using a dropped orbit stays a cover, with no more blocks, after
    swapping in the dominating orbit, so the minimum is unchanged.
    """
    as_sets = [frozenset(c) for c in covers]
    order = sorted(range(len(sizes)), key=lambda j: (-len(as_sets[j]), sizes[j], j))
    kept = []
    for j in order:
        if any(sizes[k] <= sizes[j] and as_sets[j] <= as_sets[k] for k in kept):
            continue
        kept.append(j)
    return sorted(kept)


def lp_bound(model, kept, rows):
    """Numerical LP minimum with implied rows; a screening value, not a certificate."""
    sizes = model["block_sizes"]
    solver = pywraplp.Solver.CreateSolver("GLOP")
    x = {j: solver.NumVar(0, 1, "") for j in kept}
    for row in rows:
        solver.Add(sum(x[j] for j in row) >= 1)
    for coefficients, minimum in implied_rows(model):
        solver.Add(sum(c * x[j] for j, c in coefficients.items() if j in x) >= minimum)
    solver.Minimize(sum(sizes[j] * x[j] for j in kept))
    if solver.Solve() != pywraplp.Solver.OPTIMAL:
        return None
    return solver.Objective().Value()


def implied_rows(model):
    for row in model["degree_rows"]:
        yield row, 19
    for row in model["pair_rows"]:
        yield row, 5


def solve(model, seconds, seed, workers=1, cap=TARGET):
    """Decide whether some union of block orbits with at most `cap` blocks covers."""
    sizes, covers = model["block_sizes"], model["covers"]
    kept = reduce_dominated(sizes, covers)
    rows = [[] for _ in model["triple_sizes"]]
    for j in kept:
        for row in covers[j]:
            rows[row].append(j)
    if any(not row for row in rows):
        return {"status": "INFEASIBLE_EMPTY_ROW", "kept_orbits": len(kept)}
    reachable = largest_total([sizes[j] for j in kept], cap)
    outcome = {"kept_orbits": len(kept), "largest_total_at_most_cap": reachable}
    if reachable < 61:
        # Every C(16,5,3) cover has at least 61 blocks (Schoenheim bound).
        outcome["status"] = "ORBIT_SIZES_BELOW_61"
        return outcome
    bound = lp_bound(model, kept, rows)
    outcome["lp_bound"] = bound
    if bound is not None and bound > reachable + 1e-6:
        outcome["status"] = "LP_BOUND_ABOVE_REACHABLE"
        return outcome
    cp = cp_model.CpModel()
    variables = {j: cp.NewBoolVar(f"o{j}") for j in kept}
    for row in rows:
        cp.AddBoolOr([variables[j] for j in row])
    for coefficients, minimum in implied_rows(model):
        terms = [c * variables[j] for j, c in coefficients.items() if j in variables]
        cp.Add(sum(terms) >= minimum)
    total = sum(sizes[j] * variables[j] for j in kept)
    cp.Add(total <= reachable)
    cp.Add(total >= 61)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    status = solver.Solve(cp)
    outcome.update(status=solver.StatusName(status), wall_seconds=solver.WallTime())
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        chosen = [j for j in kept if solver.Value(variables[j])]
        outcome["objective"] = sum(sizes[j] for j in chosen)
        outcome["chosen_orbits"] = chosen
    return outcome


def witness_blocks(model, chosen):
    wanted = set(chosen)
    return [BLOCKS[i] for i, orbit in enumerate(model["block_label"]) if orbit in wanted]


# ---------------------------------------------------------------- ambient groups


def gf16():
    """F16 = F2[x]/(x^4 + x + 1), elements as 4-bit integers."""

    def mul(a, b):
        result = 0
        while b:
            if b & 1:
                result ^= a
            b >>= 1
            a <<= 1
            if a & 16:
                a ^= 0b10011
        return result

    return mul


def affine_points_gens():
    """AGL(4,2) on vectors v -> label v + 1."""
    translate = from_map([v ^ 1 for v in range(16)])

    def linear(images):
        def apply(v):
            out = 0
            for bit in range(4):
                if v >> bit & 1:
                    out ^= images[bit]
            return out

        return from_map([apply(v) for v in range(16)])

    transvection = linear([0b0011, 0b0010, 0b0100, 0b1000])
    rotate = linear([0b0010, 0b0100, 0b1000, 0b0001])
    return [translate, transvection, rotate]


def clebsch_gens():
    """2^4:S5, the automorphism group of the folded five-cube on F2^4."""
    translate = from_map([v ^ 1 for v in range(16)])

    def linear(images):
        def apply(v):
            out = 0
            for bit in range(4):
                if v >> bit & 1:
                    out ^= images[bit]
            return out

        return from_map([apply(v) for v in range(16)])

    swap = linear([0b0010, 0b0001, 0b0100, 0b1000])
    cycle = linear([0b0010, 0b0100, 0b1000, 0b0001])
    fifth = linear([0b0001, 0b0010, 0b0100, 0b1111])
    return [translate, swap, cycle, fifth]


def agaml_gens():
    """AGammaL(1,16): x -> a x^(2^i) + b on F16."""
    mul = gf16()
    translate = from_map([v ^ 1 for v in range(16)])
    times = from_map([mul(2, v) for v in range(16)])
    frobenius = from_map([mul(v, v) for v in range(16)])
    return [translate, times, frobenius]


def agaml24_gens():
    """AGammaL(2,4) on F4^2, points (a, b) -> label 4a + b + 1."""
    mul4 = [[0, 0, 0, 0], [0, 1, 2, 3], [0, 2, 3, 1], [0, 3, 1, 2]]
    square = [0, 1, 3, 2]

    def point(a, b):
        return 4 * a + b

    def perm(fn):
        return from_map([point(*fn(v // 4, v % 4)) for v in range(16)])

    return [
        perm(lambda a, b: (a ^ 1, b)),
        perm(lambda a, b: (mul4[2][a], b)),
        perm(lambda a, b: (b, a)),
        perm(lambda a, b: (a ^ b, b)),
        perm(lambda a, b: (square[a], square[b])),
    ]


def sylow2_gens():
    return [
        from_cycles((1, 2)),
        from_cycles((1, 3), (2, 4)),
        from_cycles((1, 5), (2, 6), (3, 7), (4, 8)),
        from_cycles(*[(i, i + 8) for i in range(1, 9)]),
    ]


def wreath_4_4_gens():
    return [
        from_cycles((1, 2)),
        from_cycles((1, 2, 3, 4)),
        from_cycles((1, 5), (2, 6), (3, 7), (4, 8)),
        from_cycles((1, 5, 9, 13), (2, 6, 10, 14), (3, 7, 11, 15), (4, 8, 12, 16)),
    ]


def grid_4x4_gens():
    """S4 wr S2 in product action on a 4 x 4 grid."""

    def perm(fn):
        return from_map([4 * fn(v // 4, v % 4)[0] + fn(v // 4, v % 4)[1] for v in range(16)])

    return [
        perm(lambda r, c: ((1, 0, 2, 3)[r], c)),
        perm(lambda r, c: ((1, 2, 3, 0)[r], c)),
        perm(lambda r, c: (c, r)),
    ]


def wreath_8_2_gens():
    return [
        from_cycles((1, 2)),
        from_cycles(tuple(range(1, 9))),
        from_cycles(*[(i, i + 8) for i in range(1, 9)]),
    ]


def wreath_2_8_gens():
    return [
        from_cycles((1, 2)),
        from_cycles((1, 3), (2, 4)),
        from_cycles((1, 3, 5, 7, 9, 11, 13, 15), (2, 4, 6, 8, 10, 12, 14, 16)),
    ]


def s6_on_6_plus_10_gens():
    """S6 on six points and the ten splittings into two triples."""
    halves = []
    for triple in combinations(range(6), 3):
        pair = frozenset([frozenset(triple), frozenset(set(range(6)) - set(triple))])
        if pair not in halves:
            halves.append(pair)

    def perm(sigma):
        images = [sigma[i] for i in range(6)]
        for split in halves:
            image = frozenset(frozenset(sigma[x] for x in part) for part in split)
            images.append(6 + halves.index(image))
        return from_map(images)

    return [perm([1, 0, 2, 3, 4, 5]), perm([1, 2, 3, 4, 5, 0])]


def s6_on_pairs_gens():
    pairs = list(combinations(range(6), 2))

    def perm(sigma):
        images = [pairs.index(tuple(sorted((sigma[a], sigma[b])))) for a, b in pairs]
        return from_map(images + [15])

    return [perm([1, 0, 2, 3, 4, 5]), perm([1, 2, 3, 4, 5, 0])]


def s5_on_1_5_10_gens():
    pairs = list(combinations(range(5), 2))

    def perm(sigma):
        images = [0] + [1 + sigma[i] for i in range(5)]
        images += [6 + pairs.index(tuple(sorted((sigma[a], sigma[b])))) for a, b in pairs]
        return from_map(images)

    return [perm([1, 0, 2, 3, 4]), perm([1, 2, 3, 4, 0])]


def projective_line_gens(q, offset, total_fixed_tail=True):
    """PGL(2,q) on q+1 points, placed at 0-based labels offset .. offset+q."""
    inf = q

    def act(fn):
        images = list(IDENTITY)
        for x in range(q + 1):
            images[offset + x] = offset + fn(x)
        return images

    def inv_mod(a):
        return pow(a, q - 2, q)

    def mobius(a, b, c, d):
        def fn(x):
            if x == inf:
                return inf if c == 0 else a * inv_mod(c) % q
            denominator = (c * x + d) % q
            if denominator == 0:
                return inf
            return (a * x + b) * inv_mod(denominator) % q

        return fn

    primitive = next(
        g for g in range(2, q) if all(pow(g, (q - 1) // r, q) != 1 for r in _primes(q - 1))
    )
    gens = [act(mobius(1, 1, 0, 1)), act(mobius(primitive, 0, 0, 1)), act(mobius(0, 1, 1, 0))]
    return gens


def _primes(n):
    result, p = [], 2
    while p * p <= n:
        if n % p == 0:
            result.append(p)
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        result.append(n)
    return result


def pgl27_twice_gens():
    first = projective_line_gens(7, 0)
    second = projective_line_gens(7, 8)
    return [from_map([a[i] if i < 8 else b[i] for i in range(16)]) for a, b in zip(first, second)]


def psl213_gens():
    return [from_map(g) for g in projective_line_gens(13, 0)]


def pgl211_gens():
    return [from_map(g) for g in projective_line_gens(11, 0)]


def pg23_gens():
    """PGL(3,3) on the 13 points of PG(2,3), with labels 14..16 fixed."""
    points = []
    for v in ((a, b, c) for a in range(3) for b in range(3) for c in range(3)):
        if v == (0, 0, 0):
            continue
        lead = next(x for x in v if x)
        normal = tuple((x * lead) % 3 for x in v)
        if normal not in points:
            points.append(normal)

    def normalize(v):
        lead = next(x for x in v if x)
        return tuple((x * lead) % 3 for x in v)

    def perm(matrix):
        images = []
        for v in points:
            w = tuple(sum(matrix[r][c] * v[c] for c in range(3)) % 3 for r in range(3))
            images.append(points.index(normalize(w)))
        return from_map(images + [13, 14, 15])

    return [
        perm([[1, 1, 0], [0, 1, 0], [0, 0, 1]]),
        perm([[0, 0, 1], [1, 0, 0], [0, 1, 0]]),
        perm([[2, 0, 0], [0, 1, 0], [0, 0, 1]]),
    ]


def gl42_on_nonzero_gens():
    gens = affine_points_gens()[1:]
    return gens


def fano_points_lines_gens():
    """GL(3,2) on the seven points and seven lines of the Fano plane; two fixed."""
    points = list(range(1, 8))
    lines = [frozenset(p for p in points if bin(p & line).count("1") % 2 == 0) for line in points]

    def perm(matrix_images):
        def apply(v):
            out = 0
            for bit in range(3):
                if v >> bit & 1:
                    out ^= matrix_images[bit]
            return out

        images = [apply(p) - 1 for p in points]
        for line in lines:
            image = frozenset(apply(p) for p in line)
            images.append(7 + lines.index(image))
        return from_map(images + [14, 15])

    return [perm([0b011, 0b010, 0b100]), perm([0b010, 0b100, 0b001])]


AMBIENTS = {
    "AGL(4,2)": affine_points_gens,
    "Clebsch 2^4:S5": clebsch_gens,
    "AGammaL(1,16)": agaml_gens,
    "AGammaL(2,4)": agaml24_gens,
    "Sylow2(S16)": sylow2_gens,
    "S4 wr S4": wreath_4_4_gens,
    "S4 wr S2 grid": grid_4x4_gens,
    "S8 wr S2": wreath_8_2_gens,
    "S2 wr S8": wreath_2_8_gens,
    "S6 on 6+10": s6_on_6_plus_10_gens,
    "S6 on pairs+1": s6_on_pairs_gens,
    "S5 on 1+5+10": s5_on_1_5_10_gens,
    "PGL(2,7) on 8+8": pgl27_twice_gens,
    "PGL(2,13) on 14+2": psl213_gens,
    "PGL(2,11) on 12+4": pgl211_gens,
    "PGL(3,3) on 13+3": pg23_gens,
    "GL(4,2) on 15+1": gl42_on_nonzero_gens,
    "GL(3,2) on 7+7+2": fano_points_lines_gens,
}


def partitions(n, largest=None):
    largest = n if largest is None else largest
    if n == 0:
        yield ()
        return
    for part in range(min(n, largest), 0, -1):
        for rest in partitions(n - part, part):
            yield (part, *rest)


def cyclic_candidates():
    for shape in partitions(POINTS):
        if shape == (1,) * POINTS:
            continue
        cycles, start = [], 1
        for length in shape:
            if length > 1:
                cycles.append(tuple(range(start, start + length)))
            start += length
        yield f"cyclic {'.'.join(map(str, shape))}", [from_cycles(*cycles)]


def sampled_subgroups(name, gens, rng, samples, max_gens=3):
    """Chains <g1>, <g1,g2>, ... built from random elements and their powers."""
    source = RandomElements(gens, rng)
    for sample in range(samples):
        chain = []
        for _ in range(rng.randint(1, max_gens)):
            element = source.next()
            order = element_order(element)
            divisors = [d for d in range(1, order + 1) if order % d == 0 and d < order]
            if divisors and rng.random() < 0.6:
                element = power(element, rng.choice(divisors))
            if element == IDENTITY:
                continue
            chain.append(element)
            yield f"{name} sample {sample} gens {len(chain)}", list(chain)


# ---------------------------------------------------------------- campaign


def candidate_stream(rng, samples):
    for name, gens in cyclic_candidates():
        yield name, gens
    for name, factory in AMBIENTS.items():
        gens = factory()
        yield f"{name} full", gens
        yield from sampled_subgroups(name, gens, rng, samples)


def evaluate(task):
    name, gens, seconds, seed, *rest = task
    solver_workers = rest[0] if rest else 1
    started = time.monotonic()
    model = orbit_model(gens)
    record = {
        "name": name,
        "generators": [[x + 1 for x in g] for g in gens],
        "point_orbits": point_orbits(gens),
        "order": group_order(gens, cap=200_000),
        "block_orbits": len(model["block_sizes"]),
        "triple_orbits": len(model["triple_sizes"]),
        "seed": seed,
        "seconds_budget": seconds,
    }
    record["solver_workers"] = solver_workers
    record.update(solve(model, seconds, seed, workers=solver_workers))
    if record.get("objective") is not None and record["objective"] <= TARGET:
        record["witness"] = [list(b) for b in witness_blocks(model, record["chosen_orbits"])]
    record.pop("chosen_orbits", None)
    record["elapsed_seconds"] = time.monotonic() - started
    return record


def check_witness(blocks, folder, name):
    path = folder / f"{name}.txt"
    path.write_text("".join(" ".join(map(str, b)) + "\n" for b in sorted(blocks)))
    results = {}
    for label, command in (
        (
            "package",
            ["uv", "run", "covering64", "verify", str(path), "--expected-blocks", str(len(blocks))],
        ),
        (
            "standalone",
            [
                sys.executable,
                str(ROOT / "scripts/check_cover.py"),
                str(path),
                "--expected-blocks",
                str(len(blocks)),
            ],
        ),
    ):
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        results[label] = {"exit": done.returncode, "stdout": done.stdout[-2000:]}
    return str(path), results


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(args.seed)
    source = Path(__file__).read_bytes()
    manifest = {
        "source_sha256": sha256(source).hexdigest(),
        "seed": args.seed,
        "samples_per_ambient": args.samples,
        "seconds_per_group": args.seconds,
        "workers": args.workers,
        "max_block_orbits": args.max_block_orbits,
        "python": platform.python_version(),
        "ortools": ORTOOLS_VERSION,
        "target": TARGET,
        "scope": "Only covers invariant under each listed generator set; no global claim.",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    seen, tasks, skipped = set(), [], Counter()
    if args.rerun_unknown:
        # Second pass: only groups whose earlier bounded call returned UNKNOWN.
        manifest["rerun_of"] = str(args.rerun_unknown)
        manifest["rerun_input_sha256"] = sha256(Path(args.rerun_unknown).read_bytes()).hexdigest()
        manifest["solver_workers_per_group"] = args.solver_workers
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
        with open(args.rerun_unknown) as handle:
            earlier = [json.loads(line) for line in handle]
        for index, row in enumerate(r for r in earlier if r["status"] == "UNKNOWN"):
            gens = [tuple(x - 1 for x in g) for g in row["generators"]]
            tasks.append((row["name"], gens, args.seconds, args.seed + index, args.solver_workers))
    candidates = [] if args.rerun_unknown else candidate_stream(rng, args.samples)
    for index, (name, gens) in enumerate(candidates):
        model = orbit_model(gens)
        key = signature(gens, model)
        if key in seen:
            skipped["duplicate signature"] += 1
            continue
        seen.add(key)
        if len(model["block_sizes"]) > args.max_block_orbits:
            skipped["too many block orbits"] += 1
            continue
        tasks.append((name, gens, args.seconds, args.seed + index))
    print(f"{len(tasks)} distinct groups queued; skipped {dict(skipped)}", flush=True)
    best = None
    witnesses = out / "witnesses"
    witnesses.mkdir()
    with get_context("spawn").Pool(args.workers) as pool, open(out / "results.jsonl", "w") as log:
        for record in pool.imap_unordered(evaluate, tasks):
            if "witness" in record:
                path, checks = check_witness(
                    record["witness"], witnesses, f"group-{len(list(witnesses.iterdir()))}"
                )
                record["witness_file"], record["witness_checks"] = path, checks
                print("CANDIDATE", record["name"], record["objective"], checks, flush=True)
            log.write(json.dumps(record, sort_keys=True) + "\n")
            log.flush()
            value = record.get("objective")
            if value is not None and (best is None or value < best[0]):
                best = (value, record["name"])
                print(f"best so far {value} from {record['name']}", flush=True)
    summary = {"distinct_groups": len(tasks), "skipped": dict(skipped), "best": best}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-block-orbits", type=int, default=2500)
    parser.add_argument("--rerun-unknown", help="results.jsonl whose UNKNOWN groups are retried")
    parser.add_argument("--solver-workers", type=int, default=1)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
