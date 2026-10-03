# Document:    Independent Hub-Edge Overlap Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      753333a9f8332984c5459f25981a58a46e397b839688ee7c1681c7711ad51df8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import hashlib
import itertools
import json
import pathlib
import subprocess
import time


def main():
    started = time.monotonic()
    rows = []
    for q in range(6):
        triples = [tuple(range(3 * i + 1, 3 * i + 4)) for i in range(q)]
        outside = [sorted(set(range(1, 17)) - set(triple)) for triple in triples]
        internal = {pair for triple in triples for pair in itertools.combinations(triple, 2)}
        histogram = collections.Counter()
        minimum_assignment = None
        for hubs in itertools.product(*outside):
            edges = {tuple(sorted((point, hub))) for triple, hub in zip(triples, hubs)
                     for point in triple}
            assert not edges & internal
            assert len(edges) >= 3 * q - q // 2
            histogram[len(edges)] += 1
            if len(edges) == 3 * q - q // 2 and minimum_assignment is None:
                minimum_assignment = hubs
        assert sum(histogram.values()) == 13 ** q
        assert min(histogram) == 3 * q - q // 2
        rows.append(dict(q=q, assignments=sum(histogram.values()),
                         union_size_counts=dict(histogram),
                         minimum_hubs=minimum_assignment,
                         minimum_pair_excess=9 * q - q // 2,
                         resulting_block_bound=(600 + 9 * q - q // 2 + 9) // 10))
    result = dict(complete=True, deterministic=True, seed=None,
                  seconds=time.monotonic() - started, rows=rows,
                  source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip())
    pathlib.Path(__file__).with_name('result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
