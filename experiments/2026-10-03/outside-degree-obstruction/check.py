# Document:    Exact Outside-Pair Degree Obstruction Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2ce4e8a4ab452be3445639fe971a8b8f1d5bd7c15441729a9a6a14f761d3a5dd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import hashlib
import itertools
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent
POINTS = tuple(range(4, 17))
PAIRS = tuple(itertools.combinations(POINTS, 2))
TRIPLES = tuple(itertools.combinations(POINTS, 3))
G = {(4, 5), (4, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)}
COMMON = {(1, 2, 3, *edge) for edge in G}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(blocks):
    require(len(blocks) == len(set(blocks)) == 64, 'block count or duplicates')
    require(all(len(block) == 5 and tuple(sorted(set(block))) == block
                and all(type(point) is int and 1 <= point <= 16 for point in block)
                for block in blocks), 'malformed block')
    require({block for block in blocks if len(set(block) & {1, 2, 3}) >= 2} == COMMON,
            'shared blocks')
    families = [[tuple(point for point in block if point != anchor) for block in blocks
                 if set(block) & {1, 2, 3} == {anchor}] for anchor in range(1, 4)]
    for family in families:
        require(len(family) == len(set(family)) == 13, 'local block count')
        require(collections.Counter(point for block in family for point in block)
                == dict.fromkeys(POINTS, 4), 'local point degrees')
        holes = {pair for pair in PAIRS if not any(set(pair) <= set(block) for block in family)}
        require(holes <= G, 'local hole outside G')
        require(max(collections.Counter(point for edge in holes for point in edge).values(),
                    default=0) <= 1, 'local holes not matching')
    outside = [block for block in blocks if not set(block) & {1, 2, 3}]
    degrees = collections.Counter(point for block in outside for point in block)
    require(len(outside) == 18 and degrees == {point: 6 if point == 4 else 7 for point in POINTS},
            'outside block counts or degrees')
    all_holes = [triple for triple in itertools.combinations(range(1, 17), 3)
                 if not any(set(triple) <= set(block) for block in blocks)]
    local_quads = [block for family in families for block in family]
    full_residual = [triple for triple in TRIPLES
                     if not any(set(triple) <= set(block) for block in local_quads)]
    partial_residual = [triple for triple in full_residual if triple not in all_holes]
    modes = {}
    for name, residual in [('full_completion', full_residual),
                           ('partial_hint', partial_residual)]:
        pair_rows = []
        for pair in PAIRS:
            needed = [next(point for point in triple if point not in pair)
                      for triple in residual if set(pair) <= set(triple)]
            lower = (len(needed) + 2) // 3
            actual = sum(set(pair) <= set(block) for block in outside)
            if name == 'partial_hint':
                require(actual >= lower, 'invalid partial residual bound')
            pair_rows.append(dict(pair=pair, needed_third_points=needed,
                                  lower=lower, actual_outside_pair_count=actual))
        point_rows = [dict(point=point, lower_sum=sum(row['lower'] for row in pair_rows
                                                    if point in row['pair']),
                           budget=4 * degrees[point]) for point in POINTS]
        violations = [row for row in point_rows if row['lower_sum'] > row['budget']]
        modes[name] = dict(residual_triples=residual, pairs=pair_rows,
                           point_rows=point_rows, violations=violations)
    require(modes['full_completion']['violations']
            == [dict(point=4, lower_sum=25, budget=24)], 'expected obstruction changed')
    require(not modes['partial_hint']['violations'], 'partial hint falsely rejected')
    return dict(families=families, outside_degrees=dict(degrees),
                global_holes=all_holes, modes=modes)


def main():
    source = ROOT.parent / 'first-family-independent/normalized-h14.txt'
    blocks = [tuple(map(int, line.split())) for line in source.read_text().splitlines()
              if line.strip()]
    result = inspect(blocks)
    verifiers = []
    for prefix in [['uv', 'run', 'covering64', 'verify'],
                   ['uv', 'run', 'python', 'scripts/check_cover.py']]:
        process = subprocess.run(prefix + [str(source), '--expected-blocks', '64'],
                                 capture_output=True, text=True)
        require(process.returncode == 1, 'unexpected verifier exit')
        report = json.loads(process.stdout)
        require(report['uncovered'] == list(map(list, result['global_holes'])),
                'cover verifier mismatch')
        verifiers.append(report)
    controls = []
    for name, damaged in [('duplicate', [blocks[0], *blocks[:-1]]),
                          ('short', blocks[:-1]),
                          ('bad label', [(0, *blocks[0][1:]), *blocks[1:]])]:
        try:
            inspect(damaged)
        except ValueError:
            controls.append(dict(control=name, rejected=True))
        else:
            raise AssertionError('damaged candidate accepted')
    result.update(complete=True, source=str(source),
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip(),
                  verifiers=verifiers, damaged_controls=controls)
    (ROOT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({name: mode['point_rows'] for name, mode in result['modes'].items()}))


if __name__ == '__main__':
    main()
