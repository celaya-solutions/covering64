# Document:    Regular Thirteen-Point Local Family Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      866e5dc2f14502ad53717721478ff394741e10a3cfbeaed253e9e2a39e42b350
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Enumerate regular 13 quadruple families whose missing pairs form a matching.

The chosen hole-free point is 13. Its four blocks partition points 1..12 into
four triples. Enumerate all hole matchings modulo permutations of these groups
and their members, all compatible positive-excess matchings, then every exact
K4 decomposition of the residual pair-multiplicity multigraph. A time limit
makes a run explicitly incomplete. No CP/SAT solver is used.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import itertools
import json
import math
import pathlib
import subprocess
import time

import pynauty

PAIRS = list(itertools.combinations(range(12), 2))
PAIR_ID = {edge: index for index, edge in enumerate(PAIRS)}
GROUP_EDGES = list(itertools.combinations(range(4), 2))
GROUPS = [tuple(range(3 * i, 3 * i + 3)) for i in range(4)]
STAR = [tuple((*group, 12)) for group in GROUPS]
ALLOWED = {0: {()}, 3: {(3,)}, 4: {(2, 2)}, 5: {(5,)},
           6: {(2, 4), (3, 3)}}


def bareiss(matrix):
    """Exact integer determinant, with row pivoting."""
    matrix = [row[:] for row in matrix]
    divisor, sign = 1, 1
    for k in range(len(matrix) - 1):
        if not matrix[k][k]:
            pivot = next((i for i in range(k + 1, len(matrix)) if matrix[i][k]), None)
            if pivot is None:
                return 0
            matrix[pivot], matrix[k] = matrix[k], matrix[pivot]
            sign = -sign
        value = matrix[k][k]
        for i in range(k + 1, len(matrix)):
            for j in range(k + 1, len(matrix)):
                numerator = matrix[i][j] * value - matrix[i][k] * matrix[k][j]
                assert numerator % divisor == 0
                matrix[i][j] = numerator // divisor
            matrix[i][k] = 0
        divisor = value
    return sign * matrix[-1][-1]


def partitions(total, minimum=2):
    if total == 0:
        yield ()
    for value in range(minimum, total + 1):
        for tail in partitions(total - value, value):
            yield (value, *tail)


def determinant_table():
    rows = []
    for holes in range(7):
        for partition in partitions(holes):
            matrix = [[4 if i == j else 1 for j in range(13)] for i in range(13)]
            start = 0
            for half_length in partition:
                for i in range(2 * half_length):
                    a, b = start + i, start + (i + 1) % (2 * half_length)
                    matrix[a][b] += -1 if i % 2 == 0 else 1
                    matrix[b][a] = matrix[a][b]
                start += 2 * half_length
            value = bareiss(matrix)
            square = value >= 0 and math.isqrt(value) ** 2 == value
            assert square == (partition in ALLOWED.get(holes, set()))
            rows.append(dict(holes=holes, cycle_half_lengths=partition,
                             determinant=value, square=square))
    return rows


def hole_patterns():
    representatives = set()
    permutations = list(itertools.permutations(range(4)))
    for values in itertools.product(range(4), repeat=6):
        if sum(values) > 6:
            continue
        if any(sum(value for edge, value in zip(GROUP_EDGES, values)
                   if point in edge) > 3 for point in range(4)):
            continue
        orbit = []
        for permutation in permutations:
            image = [0] * 6
            for edge, value in zip(GROUP_EDGES, values):
                mapped = tuple(sorted(permutation[point] for point in edge))
                image[GROUP_EDGES.index(mapped)] = value
            orbit.append(tuple(image))
        representatives.add(min(orbit))
    return sorted(representatives, key=lambda values: (sum(values), values))


def matching_from_pattern(values):
    available = [list(group) for group in GROUPS]
    holes = []
    for (left, right), count in zip(GROUP_EDGES, values):
        for _ in range(count):
            holes.append(tuple(sorted((available[left].pop(), available[right].pop()))))
    return tuple(sorted(holes))


def positive_matchings(vertices, forbidden):
    if not vertices:
        yield ()
        return
    first = vertices[0]
    for index in range(1, len(vertices)):
        edge = (first, vertices[index])
        if edge in forbidden:
            continue
        rest = vertices[1:index] + vertices[index + 1:]
        for tail in positive_matchings(rest, forbidden):
            yield (edge, *tail)


def cycle_partition(holes, positive):
    adjacency = collections.defaultdict(list)
    for a, b in (*holes, *positive):
        adjacency[a].append(b)
        adjacency[b].append(a)
    unvisited = set(adjacency)
    sizes = []
    while unvisited:
        todo = [unvisited.pop()]
        size = 0
        while todo:
            point = todo.pop()
            size += 1
            for neighbor in adjacency[point]:
                if neighbor in unvisited:
                    unvisited.remove(neighbor)
                    todo.append(neighbor)
        sizes.append(size // 2)
    return tuple(sorted(sizes))


def pattern_certificate(holes, positive):
    adjacency = {i: [] for i in range(16 + 2 * len(holes))}
    for index, group in enumerate(GROUPS):
        for point in group:
            adjacency[point].append(12 + index)
            adjacency[12 + index].append(point)
    for index, edge in enumerate((*holes, *positive), 16):
        for point in edge:
            adjacency[index].append(point)
            adjacency[point].append(index)
    colors = [set(range(12)), set(range(12, 16))]
    if holes:
        colors += [set(range(16, 16 + len(holes))),
                   set(range(16 + len(holes), 16 + 2 * len(holes)))]
    graph = pynauty.Graph(len(adjacency), adjacency_dict=adjacency, vertex_coloring=colors)
    return pynauty.certificate(graph)


def family_certificate(blocks):
    adjacency = {i: [] for i in range(26)}
    for index, block in enumerate(blocks, 13):
        for point in block:
            adjacency[index].append(point)
            adjacency[point].append(index)
    graph = pynauty.Graph(26, adjacency_dict=adjacency,
                          vertex_coloring=[set(range(13)), set(range(13, 26))])
    return pynauty.certificate(graph)


def verify_family(blocks, holes, positive):
    assert len(blocks) == len(set(blocks)) == 13
    assert all(len(block) == len(set(block)) == 4 for block in blocks)
    degrees = collections.Counter(point for block in blocks for point in block)
    assert degrees == dict.fromkeys(range(13), 4)
    counts = collections.Counter(edge for block in blocks
                                 for edge in itertools.combinations(block, 2))
    assert {edge for edge in itertools.combinations(range(13), 2)
            if not counts[edge]} == set(holes)
    assert {edge for edge, count in counts.items() if count == 2} == set(positive)
    assert max(counts.values()) <= 2


def decompositions(holes, positive, deadline, stats):
    holes, positive = set(holes), set(positive)
    targets = [int(a // 3 != b // 3) - int((a, b) in holes)
               + int((a, b) in positive) for a, b in PAIRS]
    assert all(value >= 0 for value in targets) and sum(targets) == 54
    blocks, edges = [], []
    for block in itertools.combinations(range(12), 4):
        edge_ids = tuple(PAIR_ID[edge] for edge in itertools.combinations(block, 2))
        if all(targets[index] for index in edge_ids):
            blocks.append(block)
            edges.append(edge_ids)
    by_edge = [[] for _ in PAIRS]
    for index, edge_ids in enumerate(edges):
        for edge in edge_ids:
            by_edge[edge].append(index)
    selected = []
    used = set()

    def walk():
        stats['nodes'] += 1
        if stats['nodes'] % 256 == 0 and time.monotonic() >= deadline:
            raise TimeoutError
        if len(selected) == 9:
            assert not any(targets)
            yield tuple(sorted((*STAR, *(blocks[i] for i in selected))))
            return
        best, best_key = None, None
        for edge, need in enumerate(targets):
            if not need:
                continue
            options = [i for i in by_edge[edge] if i not in used
                       and all(targets[j] for j in edges[i])]
            if len(options) < need:
                return
            key = math.comb(len(options), need)
            if best_key is None or key < best_key:
                best, best_key = (need, options), key
                if key == 1:
                    break
        if best is None:
            return
        need, options = best
        for batch in itertools.combinations(options, need):
            consumption = collections.Counter(edge for i in batch for edge in edges[i])
            if any(value > targets[edge] for edge, value in consumption.items()):
                continue
            for edge, value in consumption.items():
                targets[edge] -= value
            selected.extend(batch)
            used.update(batch)
            yield from walk()
            used.difference_update(batch)
            del selected[-need:]
            for edge, value in consumption.items():
                targets[edge] += value

    yield from walk()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--holes', type=int, nargs='*', default=list(range(7)))
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    deadline = started + args.seconds
    stats = collections.Counter()
    families, patterns, seen = {}, [], set()
    complete = True
    all_patterns = hole_patterns()
    current = None
    try:
        for values in all_patterns:
            count = sum(values)
            if count not in args.holes or count not in ALLOWED:
                continue
            holes = matching_from_pattern(values)
            vertices = tuple(sorted(point for edge in holes for point in edge))
            row = dict(pattern=values, holes=count, raw_matchings=0,
                       determinant_survivors=0, distinct_pair_patterns=0,
                       completed_pair_patterns=0, decompositions=0)
            patterns.append(row)
            for positive in positive_matchings(vertices, set(holes)):
                if time.monotonic() >= deadline:
                    raise TimeoutError
                row['raw_matchings'] += 1
                if cycle_partition(holes, positive) not in ALLOWED[count]:
                    continue
                row['determinant_survivors'] += 1
                certificate = pattern_certificate(holes, positive)
                if certificate in seen:
                    continue
                seen.add(certificate)
                row['distinct_pair_patterns'] += 1
                current = dict(pattern=values, holes=holes, positive=positive)
                for blocks in decompositions(holes, positive, deadline, stats):
                    verify_family(blocks, holes, positive)
                    row['decompositions'] += 1
                    certificate = family_certificate(blocks)
                    if certificate not in families:
                        families[certificate] = dict(
                            blocks=[[point + 1 for point in block] for block in blocks],
                            holes=[[point + 1 for point in edge] for edge in holes],
                            positive=[[point + 1 for point in edge] for edge in positive],
                            certificate_sha256=hashlib.sha256(certificate).hexdigest())
                row['completed_pair_patterns'] += 1
                current = None
    except TimeoutError:
        complete = False
    output = dict(schema=1, scope='13 distinct quadruples, 13 points, degree 4, matching holes',
                  complete=complete, seconds=time.monotonic() - started,
                  budget_seconds=args.seconds, requested_hole_counts=args.holes,
                  source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip(),
                  pynauty_version=pynauty.__version__,
                  all_hole_pattern_counts=dict(collections.Counter(map(sum, all_patterns))),
                  determinant_table=determinant_table(), patterns=patterns,
                  unfinished=current, stats=dict(stats), families=list(families.values()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    for index, family in enumerate(output['families']):
        args.output.with_name(f'{args.output.stem}-family-{index:03}.txt').write_text(
            ''.join(' '.join(map(str, block)) + '\n' for block in family['blocks']))
    print(json.dumps({key: output[key] for key in ['complete', 'seconds', 'stats']}))
    print(json.dumps(dict(classes=len(families), patterns=patterns)))


if __name__ == '__main__':
    main()
