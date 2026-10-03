# Document:    Constructive Clebsch Excess Profiles
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      dac4b562fe6162aecb680e38bf81f4dce3051abc53f8892a4ab5b0726deaa3cd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Construct eighty excess triples without running a covering-design solver.

The vertex labels 1..16 correspond to increasing even-weight five-bit integers.
Two vertices are adjacent in the Clebsch graph exactly when their XOR has weight
four. The construction uses a regular tournament on its five generators, then
independently orients ten four-cycles. See docs/independent-excess-ideas.md.

Every output is a simple triple family H with pair codegree four on graph edges
and one elsewhere. This is an excess profile, not a five-block cover.
"""

from __future__ import annotations

import random
from itertools import combinations

VERTEX_BITS = tuple(value for value in range(32) if value.bit_count() % 2 == 0)
GENERATOR_BITS = tuple(31 ^ (1 << bit) for bit in range(5))

Edge = tuple[int, int]
Triple = tuple[int, int, int]
Square = tuple[int, int, int, int]


def make_profile(seed: int) -> list[Triple]:
    """Return a deterministic, lexicographically sorted Clebsch excess profile.

    The seed varies the regular tournament and the ten cycle orientations.
    Different seeds can produce the same profile; the procedure is not a
    uniform sampler of all admissible profiles and makes no completeness claim.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    rng = random.Random(seed)
    labels = {value: index + 1 for index, value in enumerate(VERTEX_BITS)}
    order = list(range(5))
    rng.shuffle(order)
    position = {direction: index for index, direction in enumerate(order)}

    # Vertices of this auxiliary graph are the forty Clebsch edges. Each square
    # selects one pair of opposite edges, according to the tournament winner.
    auxiliary: dict[Edge, list[tuple[Edge, Square]]] = {}
    for left, right in combinations(range(5), 2):
        winner = left if (position[right] - position[left]) % 5 in (1, 2) else right
        first, second = GENERATOR_BITS[left], GENERATOR_BITS[right]
        squares = {
            tuple(sorted((value, value ^ first, value ^ second, value ^ first ^ second)))
            for value in VERTEX_BITS
        }
        for vertices in sorted(squares):
            opposite = sorted(
                (labels[a], labels[b])
                for a, b in combinations(vertices, 2)
                if a ^ b == GENERATOR_BITS[winner]
            )
            if len(opposite) != 2:
                raise AssertionError("a square must have two edges in its winning direction")
            edge_a, edge_b = opposite
            square = tuple(labels[value] for value in vertices)
            auxiliary.setdefault(edge_a, []).append((edge_b, square))
            auxiliary.setdefault(edge_b, []).append((edge_a, square))

    if len(auxiliary) != 40 or any(len(neighbors) != 2 for neighbors in auxiliary.values()):
        raise AssertionError("the tournament must select a two-regular auxiliary graph")

    # There are two disjoint four-cycles in each generator's component. A
    # directed cycle gives each Clebsch edge one positive and one negative use.
    remaining = set(auxiliary)
    excess: set[Triple] = set()
    cycle_count = 0
    while remaining:
        start = min(remaining)
        previous: Edge | None = None
        current = start
        transitions: list[tuple[Edge, Edge, Square]] = []
        while True:
            remaining.remove(current)
            next_edge, square = min(
                entry for entry in auxiliary[current] if entry[0] != previous
            )
            transitions.append((current, next_edge, square))
            previous, current = current, next_edge
            if current == start:
                break
        if len(transitions) != 4:
            raise AssertionError("each selected component must be a four-cycle")
        reverse = bool(rng.getrandbits(1))
        for source, target, square in transitions:
            positive = source if reverse else target
            for vertex in square:
                if vertex not in positive:
                    excess.add(tuple(sorted((*positive, vertex))))
        cycle_count += 1

    if cycle_count != 10 or len(excess) != 80:
        raise AssertionError("the construction must yield ten cycles and eighty triples")
    return sorted(excess)
