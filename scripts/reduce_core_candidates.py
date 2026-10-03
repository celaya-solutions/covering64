# Document:    Exact dual reduction of retained-core candidate pools
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3c0dd8bea2774cf642ace6ad595e56ed37a16aa377e1b290a70e2e56ad7f6d87
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Limit added blocks by an independently checked exact residual dual."""

import argparse
import gzip
import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def reduce_candidates(source):
    slots = source['additional_blocks_allowed']
    triples = list(combinations(range(1, 17), 3))
    blocks = list(combinations(range(1, 17), 5))
    reduced = []
    for candidate in source['candidates']:
        original = {triples[i]: Fraction(n, candidate['denominator'])
                    for i, n in candidate['weights']}
        weights = {t: w.limit_denominator(1000) for t, w in original.items()}
        # Reconstruction is only a proposal. Exact capacity checks determine
        # whether it can replace the already checked original certificate.
        for attempt in range(2):
            denominator = math.lcm(*(w.denominator for w in weights.values()))
            numerators = {t: w.numerator * (denominator // w.denominator)
                          for t, w in weights.items()}
            loads = [sum(numerators.get(t, 0) for t in combinations(b, 3)) for b in blocks]
            if max(loads) <= denominator and all(n > 0 for n in numerators.values()):
                break
            weights = original
        else:
            raise ValueError('Original dual is not feasible')
        total = sum(numerators.values())
        if not (slots - 1) * denominator < total <= slots * denominator:
            raise ValueError('Dual is outside the intended near-tight candidate range')
        retained = [tuple(b) for b in candidate['retained_core_blocks']]
        if len(retained) != 64 - slots or len(set(retained)) != len(retained):
            raise ValueError('Wrong retained-core size or duplicate blocks')
        covered = {t for b in retained for t in combinations(b, 3)}
        if set(numerators) & covered:
            raise ValueError('Dual weights an already covered triple')
        threshold = total - (slots - 1) * denominator
        allowed = [i for i, load in enumerate(loads) if load >= threshold]
        bound = Fraction(total, denominator)
        reduced.append({
            'removed': candidate['removed'],
            'retained_block_ids': candidate['retained_block_ids'],
            'retained_core_blocks': candidate['retained_core_blocks'],
            'denominator': denominator,
            'weights': [[triples.index(t), n] for t, n in sorted(numerators.items())],
            'exact_lower_bound': [bound.numerator, bound.denominator],
            'minimum_block_load_numerator': threshold,
            'allowed_block_ids': allowed, 'allowed_blocks': [blocks[i] for i in allowed],
            'allowed_block_count': len(allowed),
        })
    return {
        'scope': f'Only{len(reduced)} specified retained-core neighborhoods',
        'additional_blocks_allowed': slots,
        'rule': (f'Each selected block load >= dual_bound - {slots - 1}; '
                 'every other block has load <=1'),
        'candidates': reduced,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = json.loads(gzip.decompress(args.input.read_bytes()))
    data = reduce_candidates(source)
    encoded = json.dumps(data, separators=(',', ':')).encode()
    args.output.write_bytes(gzip.compress(encoded, mtime=0))
    print(json.dumps({'candidates': len(data['candidates']),
                      'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
