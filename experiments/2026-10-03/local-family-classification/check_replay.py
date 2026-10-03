# Document:    Local Family Enumeration Cross-Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d2ed44f56b64de353fbb58136c21db561aedcd547619b1bd1671dfc3139ff6e4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check every direct-replay witness and independently compare isomorphism classes."""

import collections
import hashlib
import itertools
import json
import pathlib
import subprocess
import tempfile

import pynauty

ROOT = pathlib.Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(blocks, pattern=None):
    require(len(blocks) == 13, 'block count')
    require(all(len(block) == 4 and sorted(set(block)) == block for block in blocks),
            'block format')
    require(all(type(point) is int and 1 <= point <= 13
                for block in blocks for point in block), 'point labels')
    require(len(set(map(tuple, blocks))) == 13, 'duplicate block')
    require(collections.Counter(point for block in blocks for point in block)
            == dict.fromkeys(range(1, 14), 4), 'point degrees')
    counts = collections.Counter(edge for block in blocks
                                 for edge in itertools.combinations(block, 2))
    holes = [edge for edge in itertools.combinations(range(1, 14), 2)
             if not counts[edge]]
    require(max(collections.Counter(point for edge in holes for point in edge).values(),
                default=0) <= 1, 'holes are not a matching')
    require(max(counts.values()) <= 2, 'excess above one')
    if pattern is not None:
        stars = {tuple([3 * g + 1, 3 * g + 2, 3 * g + 3, 13]) for g in range(4)}
        require(stars <= set(map(tuple, blocks)), 'normalized stars')
        group_pairs = list(itertools.combinations(range(4), 2))
        measured = [0] * 6
        for a, b in holes:
            require(b != 13 and (a - 1) // 3 != (b - 1) // 3, 'hole location')
            measured[group_pairs.index(((a - 1) // 3, (b - 1) // 3))] += 1
        require(measured == pattern, 'hole pattern')
    adjacency = {vertex: [] for vertex in range(26)}
    for index, block in enumerate(blocks, 13):
        for point in block:
            adjacency[index].append(point - 1)
            adjacency[point - 1].append(index)
    graph = pynauty.Graph(26, adjacency_dict=adjacency,
                          vertex_coloring=[set(range(13)), set(range(13, 26))])
    certificate = hashlib.sha256(pynauty.certificate(graph)).hexdigest()
    return holes, certificate


def main():
    replay = json.loads((ROOT / 'replay.json').read_text())
    primary = json.loads((ROOT / 'enumeration.json').read_text())
    require(replay['complete'] and primary['complete'], 'incomplete enumeration')
    require(len(replay['patterns']) == 26, 'hole pattern count')
    expected = {family['certificate_sha256']: len(family['holes'])
                for family in primary['families']}
    classes, checks = {}, []
    with tempfile.TemporaryDirectory(prefix='covering64-local-families-') as directory:
        witness = pathlib.Path(directory) / 'witness.txt'
        for row in replay['patterns']:
            require(row['complete'], 'incomplete pattern')
            for blocks in row['families']:
                holes, certificate = inspect(blocks, row['pattern'])
                classes[certificate] = len(holes)
                witness.write_text(''.join(' '.join(map(str, block)) + '\n'
                                           for block in sorted(blocks)))
                reports = []
                for prefix in [['uv', 'run', 'covering64', 'verify'],
                               ['uv', 'run', 'python', 'scripts/check_cover.py']]:
                    command = prefix + [str(witness), '--v', '13', '--k', '4',
                                        '--t', '2', '--expected-blocks', '13']
                    process = subprocess.run(command, capture_output=True, text=True)
                    report = json.loads(process.stdout)
                    require(process.returncode == int(bool(holes)), 'verifier exit')
                    require(report['uncovered'] == [list(edge) for edge in holes],
                            'verifier holes')
                    reports.append(report)
                require(reports[0]['canonical_sha256'] == reports[1]['canonical_sha256'],
                        'verifier hash mismatch')
                checks.append(dict(pattern=row['pattern'], holes=len(holes),
                                   canonical_sha256=reports[0]['canonical_sha256'],
                                   certificate_sha256=certificate,
                                   package_agrees=True, standalone_agrees=True))
    require(classes == expected, 'classification mismatch')
    controls = []
    blocks = primary['families'][1]['blocks']
    damages = {}
    damaged = [block[:] for block in blocks]
    damaged[1] = damaged[0][:]
    damages['duplicate block'] = damaged
    damaged = [block[:] for block in blocks]
    damaged[0][0] = 0
    damages['out of range label'] = damaged
    damaged = [block[:] for block in blocks]
    damaged[0].pop()
    damages['short block'] = damaged
    damaged = [block[:] for block in blocks]
    damaged[0][0] = 2
    damages['repeated label'] = damaged
    damaged = [block[:] for block in blocks]
    damaged[0] = [1, 2, 4, 13]
    damages['changed incidence'] = damaged
    for name, damaged in damages.items():
        try:
            inspect(damaged)
        except ValueError:
            controls.append(dict(control=name, rejected=True))
        else:
            raise ValueError(f'accepted damaged control: {name}')
    try:
        inspect(blocks, [0] * 6)
    except ValueError:
        controls.append(dict(control='wrong hole pattern', rejected=True))
    else:
        raise ValueError('accepted wrong hole pattern')
    result = dict(complete=True, labelled_families=len(checks), classes=classes,
                  checks=checks, damaged_controls=controls,
                  pynauty_version=pynauty.__version__,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip(),
                  input_hashes={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ['enumerate.py', 'enumeration.json',
                                             'replay.cpp', 'replay.json', 'check_replay.py']})
    (ROOT / 'cross-check.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(labelled_families=len(checks), classes=classes,
                          damaged_controls=len(controls))))


if __name__ == '__main__':
    main()
