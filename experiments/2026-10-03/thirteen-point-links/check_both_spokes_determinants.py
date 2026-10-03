# Document:    Exact determinant obstruction for two missing star spokes
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a95df32120871a0579769647e3d0ed34117d5d593ee4c235ede49eb0af10caab
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import math
import time
from collections import Counter
from itertools import combinations
from pathlib import Path


def matchings(vertices):
    if not vertices:
        yield ()
        return
    first, rest = vertices[0], vertices[1:]
    for other in rest:
        remain = tuple(v for v in rest if v != other)
        for matching in matchings(remain):
            yield (tuple(sorted((first, other))), *matching)


def determinant(matrix):
    a = [row[:] for row in matrix]
    previous, sign = 1, 1
    for k in range(len(a) - 1):
        if a[k][k] == 0:
            pivot = next((i for i in range(k + 1, len(a)) if a[i][k]), None)
            if pivot is None:
                return 0
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        pivot = a[k][k]
        for i in range(k + 1, len(a)):
            for j in range(k + 1, len(a)):
                numerator = a[i][j] * pivot - a[i][k] * a[k][j]
                assert numerator % previous == 0
                a[i][j] = numerator // previous
            a[i][k] = 0
        previous = pivot
    return sign * a[-1][-1]


started = time.monotonic()
results, square_cases = [], []
for m in range(6):
    negative = {(1, 2), (1, 3)} | {(4 + 2*i, 5 + 2*i) for i in range(m)}
    vertices = tuple(range(2, 4 + 2*m))
    available_hub_neighbors = tuple(range(4, 4 + 2*m))
    counts, examples = Counter(), {}
    seen = set()
    for neighbors in combinations(available_hub_neighbors, 2):
        remaining = tuple(v for v in vertices if v not in neighbors)
        for matching in matchings(remaining):
            positive = {(1, q) for q in neighbors} | set(matching)
            if positive & negative:
                continue
            frozen = tuple(sorted(positive))
            assert frozen not in seen
            seen.add(frozen)
            assert Counter(p for edge in positive for p in edge) == Counter(
                p for edge in negative for p in edge)
            matrix = [[4 if i == j else 1 for j in range(1, 14)] for i in range(1, 14)]
            for edges, sign in [(negative, -1), (positive, 1)]:
                for i, j in edges:
                    matrix[i-1][j-1] += sign
                    matrix[j-1][i-1] += sign
            assert all(sum(row) == 16 for row in matrix)
            det = determinant(matrix)
            counts[det] += 1
            examples.setdefault(det, {'negative': sorted(negative), 'positive': frozen})
            if det >= 0 and math.isqrt(det)**2 == det:
                square_cases.append({'m': m, 'determinant': det,
                                     'negative': sorted(negative), 'positive': frozen})
    result = {'matching_edges': m, 'positive_graphs_checked': len(seen),
              'determinant_histogram': dict(sorted(counts.items())),
              'examples': examples}
    results.append(result)
    print(json.dumps({k:v for k,v in result.items() if k!='examples'}), flush=True)
result = {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'elapsed_seconds': time.monotonic()-started, 'cases': results,
          'total_positive_graphs_checked': sum(r['positive_graphs_checked'] for r in results),
          'square_cases': square_cases,
          'scope': ('Necessary Gram determinant condition for regular 13-quad families '
                    'with both P3 spokes missing')}
Path(__file__).with_name('both-spokes-determinants.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'total': result['total_positive_graphs_checked'],
                  'square_cases': len(square_cases), 'seconds': result['elapsed_seconds']}))
