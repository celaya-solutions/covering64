# Document:    Near-Plane Invariants and Explicit Projective-Plane Switches
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3c0fc6a9aac40150034daf4f8223c66a515ed9db4cc8f4986ba8d19befad6b35
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import hashlib
import itertools
import json
import pathlib
from fractions import Fraction

import networkx as nx

ROOT = pathlib.Path(__file__).resolve().parent
CLASSIFICATION = ROOT.parent / 'local-family-classification'


def determinant(matrix):
    matrix = [[Fraction(value) for value in row] for row in matrix]
    result = Fraction(1)
    for column in range(len(matrix)):
        row = next((row for row in range(column, len(matrix)) if matrix[row][column]), None)
        if row is None:
            return 0
        if row != column:
            matrix[row], matrix[column] = matrix[column], matrix[row]
            result = -result
        pivot = matrix[column][column]
        result *= pivot
        for row in range(column + 1, len(matrix)):
            factor = matrix[row][column] / pivot
            for j in range(column, len(matrix)):
                matrix[row][j] -= factor * matrix[column][j]
    assert result.denominator == 1
    return result.numerator


def graph(blocks):
    graph = nx.Graph()
    graph.add_nodes_from(range(1, 14), kind='point')
    graph.add_nodes_from(range(14, 27), kind='block')
    for index, block in enumerate(blocks, 14):
        graph.add_edges_from((point, index) for point in block)
    return graph


def main():
    classes = json.loads((CLASSIFICATION / 'enumeration.json').read_text())['families']
    replay = json.loads((CLASSIFICATION / 'replay.json').read_text())
    planes = [set(map(tuple, family)) for row in replay['patterns'] if not any(row['pattern'])
              for family in row['families']]
    assert len(planes) == 72
    base = classes[0]['blocks']
    properties, trades = [], []
    for index, family in enumerate(classes):
        blocks = family['blocks']
        incidence = [[int(point in block) for block in blocks] for point in range(1, 14)]
        value = determinant(incidence)
        pair_counts = collections.Counter(edge for block in blocks
                                          for edge in itertools.combinations(block, 2))
        intersections = collections.Counter(len(set(a) & set(b))
                                            for a, b in itertools.combinations(blocks, 2))
        assert max(pair_counts.values()) <= 2 and max(intersections) <= 2
        holes = [edge for edge in itertools.combinations(range(1, 14), 2)
                 if not pair_counts[edge]]
        pure_points = 13 - len({point for edge in holes for point in edge})
        pure_lines = sum(all(len(set(a) & set(b)) == 1 for j, b in enumerate(blocks) if j != i)
                         for i, a in enumerate(blocks))
        properties.append(dict(holes=len(holes), incidence_determinant=value,
                               gram_determinant=value * value, pure_points=pure_points,
                               pure_lines=pure_lines, line_intersections=dict(intersections),
                               meets_prince_near_plane_definition=True))
        if index == 0:
            continue
        target = set(map(tuple, blocks))
        count, nearest = max((len(target & plane), tuple(sorted(plane))) for plane in planes)
        nearest_set = set(nearest)
        matcher = nx.algorithms.isomorphism.GraphMatcher(
            graph(base), graph(nearest), node_match=lambda a, b: a['kind'] == b['kind'])
        assert matcher.is_isomorphic()
        point_map = [matcher.mapping[point] for point in range(1, 14)]
        assert {tuple(sorted(point_map[point - 1] for point in block))
                for block in base} == nearest_set
        path = CLASSIFICATION / f'enumeration-family-{index:03}.txt'
        trades.append(dict(
            target_holes=len(holes), target_source=f'local-family-classification/{path.name}',
            target_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            searched_pg_families=len(planes), fixed_pg_star_point=13, shared_blocks=count,
            canonical_pg_to_nearest_pg=point_map, nearest_pg_blocks=nearest,
            pg_blocks_to_remove=sorted(nearest_set - target),
            target_blocks_to_add=sorted(target - nearest_set), shared=sorted(target & nearest_set)))
    result = dict(
        scope='Maximum shared blocks among the 72 PG families with the same normalized '
              'four-block star at point13; not a global nearest-PG claim.',
        source_pg='local-family-classification/enumeration-family-000.txt',
        networkx_version=nx.__version__, trades=trades)
    (ROOT / 'pg-trades.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'family-properties.json').write_text(json.dumps(dict(
        properties=properties, source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes())
        .hexdigest()), indent=2) + '\n')
    print(json.dumps(properties))


if __name__ == '__main__':
    main()
