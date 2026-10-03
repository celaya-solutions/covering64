# Document:    Independent Five-Heavy-Triple Degree-Budget Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1054ce508fcee9a0d44f5b8ff16b6941107fce5a57995ca254adde221835b222
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
TRIPLES = [tuple(range(3 * i + 1, 3 * i + 4)) for i in range(5)]


def feasible_budget(degrees, sevenfold, hubs):
    required = collections.defaultdict(int)
    for triple in TRIPLES:
        for edge in itertools.combinations(triple, 2):
            required[edge] = 2
    for index, hub in zip(sevenfold, hubs):
        if hub in TRIPLES[index]:
            raise ValueError('hub inside its own triple')
        for point in TRIPLES[index]:
            edge = tuple(sorted((point, hub)))
            required[edge] = max(required[edge], 1)
    used = collections.Counter()
    for edge, count in required.items():
        for point in edge:
            used[point] += count
    return all(used[point] <= 4 * degrees[point - 1] - 75 for point in range(1, 17))


def inspect_candidate(blocks):
    if (len(blocks) != 64 or len(set(blocks)) != 64
            or any(len(block) != 5 or tuple(sorted(set(block))) != block
                   or any(type(point) is not int or not 1 <= point <= 16 for point in block)
                   for block in blocks)):
        raise ValueError('malformed candidate')
    counts = collections.Counter(triple for block in blocks
                                 for triple in itertools.combinations(block, 3))
    heavy = sorted((triple, count) for triple, count in counts.items() if count >= 6)
    disjoint = [group for group in itertools.combinations(heavy, 5)
                if len({point for triple, _ in group for point in triple}) == 15]
    return dict(blocks=len(blocks), heavy=heavy, disjoint_five=disjoint,
                holes=[triple for triple in itertools.combinations(range(1, 17), 3)
                       if not counts[triple]],
                degrees=dict(sorted(collections.Counter(point for block in blocks
                                                        for point in block).items())))


def main():
    profiles = [[20] * 16]
    for high in range(15):
        degree = [20] * 16
        degree[high], degree[15] = 21, 19
        profiles.append(degree)
    checked = 0
    for degrees in profiles:
        assert sum(degrees) == 320
        for chosen in itertools.combinations(range(5), 2):
            options = [sorted(set(range(1, 17)) - set(TRIPLES[index])) for index in chosen]
            for hubs in itertools.product(*options):
                checked += 1
                assert not feasible_budget(degrees, chosen, hubs)
    assert checked == 27040
    assert feasible_budget([20] * 16, [0], [16])
    assert feasible_budget([20] * 15 + [25], [0, 1], [16, 16])
    for delta in range(1001):
        assert 2 * ((1 + 4 * delta) // 3) <= 3 * delta
    formulas = [dict(q=q, n7=n7, blocks=(304 + 3 * q + (2 * n7 + 2) // 3 + 4) // 5)
                for q in range(6) for n7 in range(q + 1)]
    path = ROOT.parent / 'heuristic-tabu-2026100301-deficit-3.txt'
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()
              if line.strip()]
    candidate = inspect_candidate(blocks)
    assert len(candidate['disjoint_five']) == 1
    assert sum(count >= 7 for _, count in candidate['disjoint_five'][0]) == 4
    assert candidate['holes'] == [(2, 7, 14), (2, 7, 15), (7, 14, 15)]
    verifiers = []
    for prefix in [['uv', 'run', 'covering64', 'verify'],
                   ['uv', 'run', 'python', 'scripts/check_cover.py']]:
        process = subprocess.run(prefix + [str(path), '--expected-blocks', '64'],
                                 capture_output=True, text=True)
        assert process.returncode == 1
        report = json.loads(process.stdout)
        assert not report['valid'] and report['uncovered'] == list(map(list, candidate['holes']))
        verifiers.append(report)
    assert verifiers[0]['canonical_sha256'] == verifiers[1]['canonical_sha256']
    controls = []
    for name, damaged in [('duplicate', [blocks[0], *blocks[:-1]]),
                          ('short', blocks[:-1]),
                          ('range', [(0, *blocks[0][1:]), *blocks[1:]])]:
        try:
            inspect_candidate(damaged)
        except ValueError:
            controls.append(dict(name=name, rejected=True))
        else:
            raise AssertionError('damaged candidate accepted')
    result = dict(complete=True, degree_profiles=len(profiles), assignments_checked=checked,
                  feasible_two_sevenfold_assignments=0, positive_arithmetic_controls=2,
                  capacity_values_checked=1001, conditional_bound_table=formulas,
                  candidate_path=str(path),
                  candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  candidate=candidate, verifiers=verifiers, damaged_controls=controls,
                  source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip())
    (ROOT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(assignments_checked=checked, five_disjoint_heavy=candidate['heavy'],
                         candidate_missing=candidate['holes'])))


if __name__ == '__main__':
    main()
