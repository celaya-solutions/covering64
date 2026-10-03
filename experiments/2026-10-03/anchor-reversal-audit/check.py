# Document:    Independent graph audit of double-hub anchor reversal
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      27f9fc697273b4aea1b81dabb3d3b55f70b9f873dad5e988040f2a069ef2bd0d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import pynauty

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / 'experiments/scratch/double-hub-links-20261003'
archive = RAW / 'candidates.json.gz'
quotient_path = RAW / 'anchor-reversal-quotient.json'
cases = json.loads(gzip.decompress(archive.read_bytes()))['candidates']
quotient = json.loads(quotient_path.read_text())
blocks = [tuple(sorted(tuple(b) for b in case['retained_blocks'])) for case in cases]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def graph(bs):
    adjacency = {i: [] for i in range(48)}
    for i, block in enumerate(bs, 16):
        for point in block:
            adjacency[i].append(point - 1)
            adjacency[point - 1].append(i)
    return pynauty.Graph(48, adjacency_dict=adjacency,
                         vertex_coloring=[set(range(16)), set(range(16, 48))])


# All points share one color. The two anchors are not distinguished.
buckets = defaultdict(list)
for i, bs in enumerate(blocks):
    buckets[pynauty.certificate(graph(bs))].append(i)
expected = sorted(tuple(sorted(group)) for group in buckets.values())


def audit(data):
    require(data['input_sha256'] == hashlib.sha256(archive.read_bytes()).hexdigest(),
            'input hash mismatch')
    require(data['input_cases'] == len(cases), 'input count mismatch')
    edges = data['reversal_maps']
    require(len(edges) == len(cases), 'reversal edge count')
    targets = {}
    for i, edge in enumerate(edges):
        require(edge['source'] == i, 'wrong source index')
        j = edge['target']
        require(type(j) is int and 0 <= j < len(cases), 'bad target index')
        require(edge['source_identifier'] == cases[i]['identifier']
                and edge['target_identifier'] == cases[j]['identifier'], 'identifier mismatch')
        for k in [i, j]:
            degrees = Counter(p for b in blocks[k] for p in b)
            require({p for p, n in degrees.items() if n == 19} == {1, 2}
                    and all(degrees[p] in [8, 9] for p in range(3, 17)), 'anchor degree profile')
        mapping = {int(p): q for p, q in edge['mapping'].items()}
        require(set(mapping) == set(range(1, 17))
                and all(type(q) is int for q in mapping.values())
                and set(mapping.values()) == set(range(1, 17)), 'nonbijective map')
        require(mapping[1] == 2 and mapping[2] == 1, 'anchors not reversed')
        require({tuple(sorted(mapping[p] for p in b)) for b in blocks[i]}
                == set(blocks[j]), 'saved reversal map fails direct block check')
        targets[i] = j
    require(all(targets[targets[i]] == i for i in range(len(cases))), 'not an involution')
    orbits = sorted({tuple(sorted({i, j})) for i, j in targets.items()})
    require(orbits == expected, 'reversal orbits differ from unmarked graph classes')
    require(data['orbits'] == [list(group) for group in expected], 'saved orbit list mismatch')
    require(data['representative_case_ids'] == [group[0] for group in expected],
            'wrong representative list')
    require(data['union_isomorphism_classes'] == len(expected), 'wrong class count')


audit(quotient)
controls = {}
for name in ['damaged_mapping', 'wrong_target', 'omitted_reversal', 'merged_classes',
             'omitted_representative']:
    bad = copy.deepcopy(quotient)
    if name == 'damaged_mapping':
        bad['reversal_maps'][0]['mapping']['3'] = bad['reversal_maps'][0]['mapping']['4']
    elif name == 'wrong_target':
        bad['reversal_maps'][0]['target'] = (bad['reversal_maps'][0]['target'] + 1) % len(cases)
    elif name == 'omitted_reversal':
        bad['reversal_maps'].pop()
    elif name == 'merged_classes':
        bad['orbits'][0] += bad['orbits'].pop()
    else:
        bad['representative_case_ids'].pop()
    try:
        audit(bad)
    except ValueError as error:
        controls[name] = str(error)
    else:
        raise RuntimeError('damaged control accepted: ' + name)

result = {
    'valid': True, 'input_cases': len(cases), 'unmarked_union_isomorphism_classes': len(expected),
    'class_size_histogram': dict(sorted(Counter(map(len, expected)).items())),
    'method': 'Unmarked point-block incidence graph canonical certificates from nauty',
    'all_saved_maps_directly_verified': True, 'orbits': expected,
    'canonical_certificate_hashes': {str(min(group)): hashlib.sha256(cert).hexdigest()
                                     for cert, group in buckets.items()},
    'rejected_damage_controls': controls,
    'pynauty_version': pynauty.__version__,
    'input_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
    'quotient_sha256': hashlib.sha256(quotient_path.read_bytes()).hexdigest(),
    'quotient_source_sha256': quotient['source_sha256'],
    'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'scope': ('Exact isomorphism quotient of these 270 double-hub partial seeds; '
              'conditional on the separately audited enumeration; no search bound'),
}
print(json.dumps(result, indent=2))
