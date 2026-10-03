# Document:    Independent bounded extension scan checker
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      27e5d3f05f16f8ae6f429552224e152a47da4659773154e5fd9577dce8033632
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def check(path):
    data = json.loads(gzip.decompress(path.read_bytes()))
    core = [tuple(b) for b in data['core_blocks']]
    raw = ''.join(' '.join(map(str, b)) + '\n' for b in core).encode()
    assert hashlib.sha256(raw).hexdigest() == (
        '7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db')
    identity = tuple(range(1, 17))
    group, queue = {identity}, [identity]
    for p in data['generators']:
        assert sorted(p) == list(identity) and all(type(i) is int for i in p)
    for permutation in queue:
        for generator in data['generators']:
            q = tuple(generator[p - 1] for p in permutation)
            if q not in group:
                group.add(q)
                queue.append(q)
        assert len(group) <= 60
    assert len(group) == 60
    actions = []
    for p in group:
        image = [tuple(sorted(p[i - 1] for i in b)) for b in core]
        assert set(image) == set(core)
        actions.append([core.index(b) + 1 for b in image])
    level = data['removed_count']
    assert type(level) is int and level in [6, 7, 8]
    assert data['additional_blocks_allowed'] == level + 4
    expected = set()
    for parent in data['parent_removed_sets']:
        assert len(parent) == level - 1 and parent == sorted(set(parent))
        assert all(type(i) is int and 1 <= i <= 60 for i in parent)
        for extra in set(range(1, 61)) - set(parent):
            expected.add(min(tuple(sorted(a[i - 1] for i in [*parent, extra]))
                             for a in actions))
    triples = list(combinations(range(1, 17), 3))
    blocks = list(combinations(range(1, 17), 5))
    rows = [set(combinations(b, 3)) for b in blocks]
    candidates = []
    for case in data['cases']:
        removed = tuple(case['removed'])
        assert removed in expected
        expected.remove(removed)
        denominator = case['denominator']
        assert type(denominator) is int and denominator > 0
        retained = [b for i, b in enumerate(core, 1) if i not in removed]
        covered = {t for b in retained for t in combinations(b, 3)}
        weights = {}
        for index, numerator in case['weights']:
            assert type(index) is int and 0 <= index < 560
            assert type(numerator) is int and 0 < numerator <= denominator
            triple = triples[index]
            assert triple not in covered and triple not in weights
            weights[triple] = numerator
        assert max(sum(weights.get(t, 0) for t in row) for row in rows) <= denominator
        bound = Fraction(sum(weights.values()), denominator)
        assert [bound.numerator, bound.denominator] == case['lower_bound']
        if bound <= level + 4:
            candidates.append(removed)
    assert not expected
    return {'valid_scan': True, 'removed_count': level,
            'verified_classes': len(data['cases']), 'lp_uncertified': len(candidates),
            'all_sets_at_this_level_checked': False,
            'scan_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(check(Path(sys.argv[1])), indent=2))
