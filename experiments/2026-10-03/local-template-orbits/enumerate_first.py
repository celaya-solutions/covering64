# Document:    Complete Fixed-Spoke First Local Family Quotient
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a582885fdf471ac4e92c3117c66e875e3209f3c3d3232c1d7d155a5c0bbd4447
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Generate every r4/r6 first family and quotient by explicit G automorphisms.

Internal points are 0..12. Output points are 4..16; the fixed omitted spoke
is {4,5}. All block IDs index lexicographic quadruples on 4..16, starting at 1.
"""

import argparse
import collections
import gzip
import hashlib
import itertools
import json
import pathlib
import platform
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parent
QUADS = tuple(itertools.combinations(range(13), 4))
QUAD_ID = {block: index for index, block in enumerate(QUADS)}
MATCHING = tuple((point, point + 1) for point in range(3, 13, 2))
G = {(0, 1), (0, 2), *MATCHING}
COMMON = [(1, 2, 3, 4, 5), (1, 2, 3, 4, 6), (1, 2, 3, 7, 8),
          (1, 2, 3, 9, 10), (1, 2, 3, 11, 12), (1, 2, 3, 13, 14),
          (1, 2, 3, 15, 16)]


def image(family, point_map):
    return tuple(sorted(QUAD_ID[tuple(sorted(point_map[point] for point in QUADS[index]))]
                        for index in family))


def inverse(point_map):
    result = [0] * 13
    for point, target in enumerate(point_map):
        result[target] = point
    return tuple(result)


def hole_set(family):
    counts = collections.Counter(edge for index in family
                                 for edge in itertools.combinations(QUADS[index], 2))
    return {edge for edge in itertools.combinations(range(13), 2) if not counts[edge]}


def g_automorphisms():
    result = []
    for edge_order in itertools.permutations(MATCHING):
        for orientations in itertools.product(range(2), repeat=5):
            point_map = [0, 1, 2] + [-1] * 10
            for source, target, reverse in zip(MATCHING, edge_order, orientations):
                point_map[source[0]], point_map[source[1]] = target[:: -1 if reverse else 1]
            result.append(tuple(point_map))
    assert len(result) == len(set(result)) == 3840
    for point_map in result:
        assert point_map[:3] == (0, 1, 2)
        assert {tuple(sorted(point_map[v] for v in edge)) for edge in G} == G
    return result


def labelled_families(source, deadline):
    holes = sorted(hole_set(source))
    free = sorted(set(range(13)) - {point for edge in holes for point in edge})
    pool = {}
    maps = 0
    for chosen in itertools.combinations(MATCHING, len(holes) - 1):
        targets = ((0, 1), *chosen)
        target_free = sorted(set(range(13)) - {point for edge in targets for point in edge})
        for edge_order in itertools.permutations(targets):
            for orientations in itertools.product(range(2), repeat=len(holes)):
                edge_map = [-1] * 13
                for old, new, reverse in zip(holes, edge_order, orientations):
                    edge_map[old[0]], edge_map[old[1]] = new[:: -1 if reverse else 1]
                for free_order in itertools.permutations(target_free):
                    maps += 1
                    if maps % 8192 == 0 and time.monotonic() >= deadline:
                        raise TimeoutError('labelled family budget exhausted')
                    point_map = edge_map[:]
                    for old, new in zip(free, free_order):
                        point_map[old] = new
                    key = image(source, point_map)
                    if key not in pool:
                        pool[key] = tuple(point_map)
    return pool, maps


def verify_representative(representative, name, directory):
    outside = [[point + 4 for point in QUADS[index]] for index in representative]
    blocks = sorted(COMMON + [tuple([1, *quad]) for quad in outside])
    assert len(blocks) == len(set(blocks)) == 20
    link = sorted(tuple(point - 1 for point in block if point != 1) for block in blocks)
    path = directory / f'{name}-point-link.txt'
    path.write_text(''.join(' '.join(map(str, block)) + '\n' for block in link))
    reports = []
    for prefix in [['uv', 'run', 'covering64', 'verify'],
                   ['uv', 'run', 'python', 'scripts/check_cover.py']]:
        command = prefix + [str(path), '--v', '15', '--k', '4', '--t', '2',
                            '--expected-blocks', '20']
        process = subprocess.run(command, capture_output=True, text=True)
        assert process.returncode == 0, process.stdout + process.stderr
        report = json.loads(process.stdout)
        assert report['valid'] and not report['uncovered']
        reports.append(report)
    assert reports[0]['canonical_sha256'] == reports[1]['canonical_sha256']
    return outside, blocks, dict(package=reports[0], standalone=reports[1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=float, default=120)
    parser.add_argument('--archive', type=pathlib.Path,
                        default=pathlib.Path('experiments/scratch/first-family-orbits-20261003/maps.jsonl.gz'))
    args = parser.parse_args()
    started = time.monotonic()
    deadline = started + args.seconds
    group = g_automorphisms()
    records, summaries = [], []
    args.archive.parent.mkdir(parents=True, exist_ok=True)
    archive_records = 0
    with args.archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as archive:
        header = dict(schema=1, block_order='lexicographic quadruples on 4..16',
                      block_ids='one-based', family_to_representative='entry i maps point i+4',
                      source_to_family='entry i maps source point i+1')
        archive.write((json.dumps(header) + '\n').encode())
        for source_index, hole_count in [(1, 4), (2, 6)]:
            path = (ROOT.parent / 'local-family-classification'
                    / f'enumeration-family-{source_index:03}.txt')
            source = tuple(sorted(QUAD_ID[tuple(int(point) - 1 for point in line.split())]
                                  for line in path.read_text().splitlines()))
            pool, raw_maps = labelled_families(source, deadline)
            expected = {4: (460800, 28800), 6: (46080, 15360)}[hole_count]
            assert (raw_maps, len(pool)) == expected
            unseen = set(pool)
            orbit_sizes = []
            class_records = []
            while unseen:
                if time.monotonic() >= deadline:
                    raise TimeoutError('orbit budget exhausted')
                representative = min(unseen)
                name = f'r{hole_count}-{len(orbit_sizes):03}'
                orbit = {}
                stabilizer = 0
                for point_map in group:
                    mapped = image(representative, point_map)
                    assert mapped in pool
                    if mapped == representative:
                        stabilizer += 1
                    if mapped not in orbit:
                        orbit[mapped] = inverse(point_map)
                assert len(orbit) * stabilizer == 3840
                assert set(orbit) <= unseen
                for family, point_map in sorted(orbit.items()):
                    assert image(family, point_map) == representative
                    assert image(source, pool[family]) == family
                    missing = hole_set(family)
                    assert len(missing) == hole_count and (0, 1) in missing and missing <= G
                    row = dict(representative=name, block_ids=[index + 1 for index in family],
                               family_to_representative=[point + 4 for point in point_map],
                               source_to_family=[point + 4 for point in pool[family]])
                    archive.write((json.dumps(row, separators=(',', ':')) + '\n').encode())
                    archive_records += 1
                unseen.difference_update(orbit)
                outside, full_blocks, checks = verify_representative(representative, name, ROOT)
                source_map = [point + 4 for point in pool[representative]]
                missing_pairs = [[a + 4, b + 4] for a, b in sorted(hole_set(representative))]
                record = dict(id=name, source=str(path.relative_to(pathlib.Path.cwd())),
                              source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                              source_to_representative=source_map,
                              quadruples=outside, full_twenty_blocks=full_blocks,
                              missing_pairs=missing_pairs,
                              orbit_size=len(orbit), stabilizer_order=stabilizer,
                              point_link_checks=checks)
                records.append(record)
                class_records.append(name)
                orbit_sizes.append(len(orbit))
            summary = dict(holes=hole_count, raw_point_maps=raw_maps, distinct_families=len(pool),
                           representatives=class_records, orbit_sizes=orbit_sizes)
            summaries.append(summary)
            print(json.dumps(summary), flush=True)
    result = dict(schema=1, complete=True, seconds=time.monotonic() - started,
                  budget_seconds=args.seconds, deterministic=True, seed=None,
                  source_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                          text=True).strip(),
                  source_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                  python_version=platform.python_version(), group_order=3840,
                  fixed_omitted_spoke=[4, 5], other_spoke=[4, 6],
                  matching=[[a + 4, b + 4] for a, b in MATCHING],
                  classes=summaries, representatives=records,
                  maps_archive=dict(path=str(args.archive), records=archive_records,
                                    bytes=args.archive.stat().st_size,
                                    sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest()))
    (ROOT / 'first-families.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(complete=True, representatives=len(records),
                          labelled_families=archive_records, seconds=result['seconds'])))


if __name__ == '__main__':
    main()
