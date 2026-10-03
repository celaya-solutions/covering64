# Document:    Independent incidence-graph audit of double-hub links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      0dff05be23103e887446ffd74674839f63e52369b8c5a7e1050ad76dd693cdd9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / 'experiments/scratch/double-hub-links-20261003'
TEMPLATES = ROOT / 'experiments/2026-10-03/link-classification'
SHAPES = ['1', '4', '44', '47']
ALL_BLOCKS = list(combinations(range(1, 17), 5))
BLOCK_ID = {b: i for i, b in enumerate(ALL_BLOCKS)}
ALL_TRIPLES = set(combinations(range(1, 17), 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def normalize(blocks, k, allowed, count):
    require(len(blocks) == count, 'wrong block count')
    for b in blocks:
        require(len(b) == k and all(type(p) is int for p in b), 'malformed block')
        require(len(set(b)) == k and set(b) <= set(allowed), 'bad block labels')
    normalized = tuple(sorted(tuple(sorted(b)) for b in blocks))
    require(len(set(normalized)) == count, 'duplicate blocks')
    return normalized


def point_mapping(mapping, domain, codomain):
    result = {int(k): v for k, v in mapping.items()}
    require(set(result) == set(domain), 'map domain')
    require(all(type(v) is int for v in result.values()), 'map type')
    require(set(result.values()) == set(codomain) and len(result) == len(set(result.values())),
            'map not bijective')
    return result


def apply(blocks, mapping):
    return tuple(sorted(tuple(sorted(mapping[p] for p in b)) for b in blocks))


def link_check(blocks, labels, expected_hub):
    blocks = normalize(blocks, 4, labels, 19)
    counts = Counter(pair for b in blocks for pair in combinations(b, 2))
    require(set(counts) == set(combinations(sorted(labels), 2)), 'link misses pairs')
    require(Counter(counts.values()) == {1: 96, 2: 9}, 'wrong pair excess')
    reps = Counter(p for b in blocks for p in b)
    require(reps[expected_hub] == 6 and sorted(reps.values()) == [5] * 14 + [6],
            'wrong link degrees')
    repeated = {pair for pair, n in counts.items() if n == 2}
    excess_degree = Counter(p for pair in repeated for p in pair)
    require(excess_degree[expected_hub] == 4
            and all(excess_degree[p] == 1 for p in labels if p != expected_hub),
            'wrong excess graph')
    matching = tuple(sorted(pair for pair in repeated if expected_hub not in pair))
    return blocks, matching


def incidence_graph(blocks):
    graph = nx.Graph()
    for p in sorted(set().union(*map(set, blocks))):
        graph.add_node(('p', p), kind='point')
    for i, b in enumerate(blocks):
        graph.add_node(('b', i), kind='block')
        graph.add_edges_from((('p', p), ('b', i)) for p in b)
    return graph


def graph_maps(source, target):
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        incidence_graph(source), incidence_graph(target),
        node_match=nx.algorithms.isomorphism.categorical_node_match('kind', None))
    domain = sorted(set().union(*map(set, source)))
    seen = set()
    for mapping in matcher.isomorphisms_iter():
        points = tuple((p, mapping[('p', p)][1]) for p in domain)
        require(points not in seen, 'duplicate graph point map')
        seen.add(points)
        yield dict(points)


def canonical_hash(blocks):
    text = ''.join(' '.join(map(str, b)) + '\n' for b in sorted(blocks))
    return hashlib.sha256(text.encode()).hexdigest()


def build_reference():
    templates = {}
    for shape in SHAPES:
        path = TEMPLATES / f'shape-{shape}-class-0.txt'
        lifted = normalize([list(map(int, row.split())) for row in path.read_text().splitlines()],
                           5, range(1, 17), 19)
        require(all(1 in b for b in lifted), 'template anchor')
        templates[shape] = link_check([tuple(p for p in b if p != 1) for b in lifted],
                                     range(2, 17), 2)[0]
    reference = {}
    for shape, first in templates.items():
        first_blocks = tuple(sorted((1, *b) for b in first))
        target_hub = tuple(sorted(tuple(sorted((1, *(p for p in b if p != 2))))
                                  for b in first if 2 in b))
        second_set, map_counts = set(), {}
        for label, source in templates.items():
            maps = list(graph_maps([b for b in source if 2 in b], target_hub))
            map_counts[label] = len(maps)
            for mapping in maps:
                require(mapping[2] == 1, 'graph map hub')
                second_set.add(apply(source, mapping))
        group = [{1: 1, **mapping} for mapping in graph_maps(first, first)]
        group_signatures = {tuple(sorted(mapping.items())) for mapping in group}
        unions = {tuple(sorted(set(first_blocks) | {tuple(sorted((2, *b))) for b in second}))
                  for second in second_set}
        unseen, orbits, canonical = set(unions), [], {}
        while unseen:
            seed = min(unseen)
            orbit = {apply(seed, mapping) for mapping in group}
            require(orbit <= unseen, 'orbit partition not closed/disjoint')
            representative = min(orbit)
            for member in orbit:
                canonical[member] = representative
            orbits.append(orbit)
            unseen.difference_update(orbit)
        reference[shape] = {'first': first, 'first_blocks': first_blocks,
                            'target_hub': target_hub, 'second_set': second_set,
                            'map_counts': map_counts, 'group': group_signatures,
                            'orbits': orbits, 'canonical': canonical,
                            'representatives': set(canonical.values())}
    return templates, reference


def audit(rows, candidate_data, templates, reference):
    candidates = candidate_data['candidates']
    by_id = {row['identifier']: row for row in candidates}
    require(len(by_id) == len(candidates), 'duplicate candidate identifiers')
    expected_count = sum(len(ref['orbits']) for ref in reference.values())
    require(len(candidates) == expected_count, 'candidate count differs')
    all_referenced = set()
    summaries = []
    for shape, ref in reference.items():
        row = rows[shape]
        require(row['first_class'] == shape, 'first class label')
        require(row['raw_hub_maps'] == ref['map_counts'], 'hub map count mismatch')
        supplied_group = [point_mapping(mapping, range(1, 17), range(1, 17))
                          for mapping in row['first_link_automorphisms']]
        require(len(supplied_group) == len(ref['group']), 'automorphism count mismatch')
        require({tuple(sorted(m.items())) for m in supplied_group} == ref['group'],
                'automorphism group incomplete or invalid')
        seen_seconds, seen_reps, matchings = set(), set(), set()
        for number, assignment in enumerate(row['assignments']):
            require(assignment['number'] == number, 'assignment order')
            second, matching = link_check(assignment['second_link'], [1, *range(3, 17)], 1)
            require(second not in seen_seconds, 'duplicate second link')
            seen_seconds.add(second)
            matchings.add(matching)
            require(second in ref['second_set'], 'unexpected second link')
            require(tuple(b for b in second if 1 in b) == ref['target_hub'], 'shared hub rows')
            source = templates[assignment['source_class']]
            mapping = point_mapping(assignment['source_mapping'], range(2, 17),
                                    [1, *range(3, 17)])
            require(apply(source, mapping) == second, 'source mapping does not produce second link')
            second_blocks = {tuple(sorted((2, *b))) for b in second}
            require(len(set(ref['first_blocks']) & second_blocks) == 6, 'common block count')
            union = tuple(sorted(set(ref['first_blocks']) | second_blocks))
            require(len(union) == 32, 'union block count')
            identifier = assignment['class']
            require(identifier in by_id, 'unknown class identifier')
            all_referenced.add(identifier)
            candidate = by_id[identifier]
            require(candidate['first_class'] == shape, 'candidate first class')
            retained = normalize(candidate['retained_blocks'], 5, range(1, 17), 32)
            require(retained == ref['canonical'][union], 'wrong orbit representative')
            seen_reps.add(retained)
            mapping = point_mapping(assignment['stabilizer_mapping'], range(1, 17), range(1, 17))
            require(tuple(sorted(mapping.items())) in ref['group'],
                    'invalid first-link automorphism')
            require(apply(union, mapping) == retained, 'wrong canonicalizing map')
            expected_ids = [BLOCK_ID[b] for b in retained]
            require(candidate['retained_block_ids'] == expected_ids, 'block IDs mismatch')
            counts = Counter(p for b in retained for p in b)
            require(counts[1] == counts[2] == 19, 'union anchor degrees')
            uncovered = ALL_TRIPLES - {t for b in retained for t in combinations(b, 3)}
            require(len(uncovered) == candidate['uncovered'], 'uncovered count mismatch')
            require(bool(uncovered), 'partial union incorrectly complete')
            for key in ['package_verification', 'standalone_verification']:
                report = candidate[key]
                require(report['valid'] is False and report['blocks'] == 32,
                        'wrong partial verification status')
                require(report['canonical_sha256'] == canonical_hash(retained),
                        'partial canonical hash mismatch')
            local = {p: i + 1 for i, p in enumerate([1, *range(3, 17)])}
            require(assignment['canonical_sha256'] == canonical_hash(apply(second, local)),
                    'second link canonical hash mismatch')
            require(assignment['package_valid'] is True and assignment['standalone_valid'] is True,
                    'second link verification status')
        require(seen_seconds == ref['second_set'], 'second-link enumeration incomplete')
        require(seen_reps == ref['representatives'], 'orbit representatives incomplete')
        require(row['distinct_second_links'] == len(seen_seconds), 'second link count')
        require(row['distinct_second_matchings'] == len(matchings), 'matching count')
        require(row['union_classes'] == len(seen_reps), 'class count')
        summaries.append({'first_class': shape, 'hub_maps': ref['map_counts'],
                          'second_links': len(seen_seconds), 'distinct_matchings': len(matchings),
                          'automorphism_order': len(ref['group']), 'orbits': len(seen_reps),
                          'orbit_size_histogram': dict(sorted(
                              Counter(map(len, ref['orbits'])).items()))})
    require(all_referenced == set(by_id), 'unreferenced candidates')
    return summaries


templates, reference = build_reference()
rows = {shape: json.loads(gzip.decompress(
    (RAW / f'shape-{shape}/enumeration.json.gz').read_bytes())) for shape in SHAPES}
candidate_path = RAW / 'candidates.json.gz'
candidate_data = json.loads(gzip.decompress(candidate_path.read_bytes()))
metadata = candidate_data['metadata']
require(metadata['source_sha256'] == hashlib.sha256((RAW / 'source.py').read_bytes()).hexdigest(),
        'source snapshot hash mismatch')
require(metadata['classifier_sha256']
        == hashlib.sha256((RAW / 'classifier.py').read_bytes()).hexdigest(),
        'classifier snapshot hash mismatch')
summary = audit(rows, candidate_data, templates, reference)
require(metadata['total_union_classes'] == sum(row['orbits'] for row in summary),
        'metadata total mismatch')
controls = {}
for name in ['omitted_second_link', 'duplicate_second_link', 'damaged_source_map',
             'incomplete_automorphism_group', 'damaged_block_id', 'wrong_orbit_assignment',
             'malformed_second_block', 'duplicate_block_within_link',
             'fixed_second_matching']:
    damaged_rows = copy.deepcopy(rows)
    damaged_candidates = copy.deepcopy(candidate_data)
    first = damaged_rows['1']
    if name == 'omitted_second_link':
        first['assignments'].pop()
    elif name == 'duplicate_second_link':
        first['assignments'][-1]['second_link'] = first['assignments'][0]['second_link']
    elif name == 'damaged_source_map':
        mapping = first['assignments'][0]['source_mapping']
        keys = list(mapping)
        mapping[keys[0]] = mapping[keys[1]]
    elif name == 'malformed_second_block':
        first['assignments'][0]['second_link'][0].pop()
    elif name == 'duplicate_block_within_link':
        link = first['assignments'][0]['second_link']
        link[0] = link[1]
    elif name == 'incomplete_automorphism_group':
        first['first_link_automorphisms'].pop()
    elif name == 'damaged_block_id':
        damaged_candidates['candidates'][0]['retained_block_ids'][0] = -1
    elif name == 'wrong_orbit_assignment':
        first['assignments'][0]['class'] = next(a['class'] for a in first['assignments']
                                               if a['class'] != first['assignments'][0]['class'])
    else:
        chosen = link_check(first['assignments'][0]['second_link'], [1, *range(3, 17)], 1)[1]
        first['assignments'] = [a for a in first['assignments'] if
                               link_check(a['second_link'], [1, *range(3, 17)], 1)[1] == chosen]
        for number, assignment in enumerate(first['assignments']):
            assignment['number'] = number
    try:
        audit(damaged_rows, damaged_candidates, templates, reference)
    except ValueError as error:
        controls[name] = str(error)
    else:
        raise RuntimeError(f'damaged control accepted: {name}')

result = {'valid': True, 'method': 'Independent complete colored incidence-graph isomorphisms',
          'networkx_version': nx.__version__, 'shapes': summary,
          'total_second_links': sum(row['second_links'] for row in summary),
          'total_first_link_automorphism_orbits': sum(row['orbits'] for row in summary),
          'damage_controls_rejected': controls,
          'candidate_archive_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
          'source_snapshot_sha256': hashlib.sha256((RAW / 'source.py').read_bytes()).hexdigest(),
          'classifier_snapshot_sha256': hashlib.sha256(
              (RAW / 'classifier.py').read_bytes()).hexdigest(),
          'template_sha256': {shape: hashlib.sha256(
              (TEMPLATES / f'shape-{shape}-class-0.txt').read_bytes()).hexdigest()
              for shape in SHAPES},
          'enumeration_sha256': {shape: hashlib.sha256(
              (RAW / f'shape-{shape}/enumeration.json.gz').read_bytes()).hexdigest()
              for shape in SHAPES},
          'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'scope': ('Two degree-19 points with pair incidence6; '
                    'conditional on complete four-class links; no global lower bound')}
print(json.dumps(result, indent=2))
