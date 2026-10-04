# Document:    Factorized Enumeration of Degree-Nineteen Links with Five Shared Blocks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      4964b357638832b4f959a7394cfaf036630e3f55ca743c40b0eb5244b16b4a4f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Enumerate shared-star maps and count ordered link pairs by exact double cosets."""

import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROWS = ((0, 1, 2), (0, 3, 4), (5, 6, 7), (8, 9, 10), (11, 12, 13))
IDENTITY = tuple(range(14))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose(left, right):
    return tuple(left[point] for point in right)


def inverse(mapping):
    result = [0] * len(mapping)
    for point, target in enumerate(mapping):
        result[target] = point
    return tuple(result)


def coordinates(star, distinguished):
    triples = tuple(sorted(tuple(point for point in block if point != distinguished)
                           for block in star))
    assert len(triples) == len(set(triples)) == 5
    counts = Counter(point for triple in triples for point in triple)
    assert sorted(counts.values()) == [1] * 13 + [2]
    repeated = next(point for point, count in counts.items() if count == 2)
    twins = sorted(tuple(point for point in triple if point != repeated)
                   for triple in triples if repeated in triple)
    isolated = sorted(triple for triple in triples if repeated not in triple)
    assert len(twins) == 2 and len(isolated) == 3
    result = (repeated, *twins[0], *twins[1], *isolated[0], *isolated[1], *isolated[2])
    assert len(set(result)) == 14
    assert {tuple(sorted(result[index] for index in row)) for row in ROWS} == set(triples)
    return result


def mapping_group():
    twin_rows = ((1, 2), (3, 4))
    isolated_rows = ((5, 6, 7), (8, 9, 10), (11, 12, 13))
    p2 = tuple(itertools.permutations(range(2)))
    p3 = tuple(itertools.permutations(range(3)))
    group = set()
    for twin_order, inner_twins, isolated_order, inner_isolated in itertools.product(
            p2, itertools.product(p2, repeat=2), p3, itertools.product(p3, repeat=3)):
        mapping = list(IDENTITY)
        for row, points in enumerate(twin_rows):
            for position, point in enumerate(points):
                mapping[point] = twin_rows[twin_order[row]][inner_twins[row][position]]
        for row, points in enumerate(isolated_rows):
            for position, point in enumerate(points):
                mapping[point] = isolated_rows[isolated_order[row]][inner_isolated[row][position]]
        group.add(tuple(mapping))
    assert len(group) == 10368
    for mapping in group:
        assert sorted(mapping) == list(IDENTITY) and inverse(mapping) in group
        assert {tuple(sorted(mapping[index] for index in row)) for row in ROWS} == set(ROWS)
    return sorted(group)


def load_types():
    folder = ROOT / "experiments/2026-10-03/link-classification"
    path = folder / "automorphisms.json"
    automorphisms = json.loads(path.read_text())
    result = []
    inputs = {str(path.relative_to(ROOT)): sha(path)}
    for entry in automorphisms["classes"]:
        shape = entry["shape"]
        path = folder / f"shape-{shape}-class-0.txt"
        inputs[str(path.relative_to(ROOT))] = sha(path)
        full = sorted(tuple(map(int, line.split())) for line in path.read_text().splitlines()
                      if line.strip())
        link = [tuple(point for point in block if point != 1) for block in full]
        assert len(full) == len(set(full)) == 19
        degrees = Counter(point for block in link for point in block)
        assert degrees == Counter({point: 6 if point == 2 else 5 for point in range(2, 17)})
        autos = [{int(point): int(target) for point, target in mapping.items()}
                 for mapping in entry["maps"]]
        assert len(autos) == entry["automorphism_count"]
        for mapping in autos:
            assert sorted(mapping.values()) == list(range(2, 17))
            assert {tuple(sorted(mapping[point] for point in block)) for block in link} == set(link)
        for orbit in entry["point_orbits"]:
            if 2 in orbit:
                continue
            distinguished = min(orbit)
            assert set(orbit) == {mapping[distinguished] for mapping in autos}
            star = [block for block in link if distinguished in block]
            coord = coordinates(star, distinguished)
            coord_ids = {point: index for index, point in enumerate(coord)}
            stabilizers = [mapping for mapping in autos if mapping[distinguished] == distinguished]
            group = sorted(tuple(coord_ids[mapping[point]] for point in coord)
                           for mapping in stabilizers)
            assert IDENTITY in group and len(set(group)) == len(group)
            assert len(group) * len(orbit) == len(autos)
            for left in group:
                for right in group:
                    assert compose(left, right) in group
            result.append({"id": f"shape{shape}-point{distinguished}", "shape": shape,
                           "distinguished_point": distinguished, "point_orbit": orbit,
                           "full_first_link": full, "source_link": link,
                           "source_star": star,
                           "target_star": [tuple(sorted((1, *(point for point in block
                                                               if point != distinguished))))
                                           for block in star],
                           "coordinates": coord, "stabilizer_coordinate_permutations": group,
                           "stabilizer_point_permutations": stabilizers,
                           "full_automorphism_order": len(autos)})
    assert len(result) == 34
    return result, inputs


def regenerate(first, source, mapping):
    second_anchor = first["distinguished_point"]
    point_map = {source["distinguished_point"]: 1}
    point_map.update({point: first["coordinates"][mapping[index]]
                      for index, point in enumerate(source["coordinates"])})
    assert set(point_map.values()) == set(range(1, 17)) - {second_anchor}
    second = {tuple(sorted((second_anchor, *(point_map[point] for point in block))))
              for block in source["source_link"]}
    initial = set(map(tuple, first["full_first_link"]))
    shared = initial & second
    assert len(initial) == len(second) == 19 and len(shared) == 5
    assert shared == {block for block in initial if second_anchor in block}
    assert shared == {block for block in second if 1 in block}
    union = sorted(initial | second)
    assert len(union) == 33
    return {"first_type": first["id"], "source_type": source["id"],
            "anchors": [1, second_anchor], "coordinate_mapping": mapping,
            "source_to_second_point_map": point_map, "second_link_blocks": sorted(second),
            "fixed_blocks": union, "shared_blocks": sorted(shared)}


def main():
    folder = Path(__file__).resolve().parent
    group = mapping_group()
    group_set = set(group)
    types, inputs = load_types()
    needed = {tuple(mapping) for item in types for mapping in
              item["stabilizer_coordinate_permutations"]}
    assert needed <= group_set
    conjugacy = {}
    for element in sorted(needed):
        images = [compose(inverse(mapping), compose(element, mapping)) for mapping in group]
        signature = min(images)
        centralizer = images.count(element)
        assert centralizer * len(set(images)) == len(group)
        conjugacy[element] = (signature, centralizer)
    counts = []
    for first, source in itertools.product(types, repeat=2):
        h_group = first["stabilizer_coordinate_permutations"]
        k_group = source["stabilizer_coordinate_permutations"]
        numerator = sum(conjugacy[left][1] for left, right in itertools.product(h_group, k_group)
                        if conjugacy[left][0] == conjugacy[right][0])
        denominator = len(h_group) * len(k_group)
        assert numerator % denominator == 0
        counts.append({"first_type": first["id"], "source_type": source["id"],
                       "target_stabilizer_order": len(h_group),
                       "source_stabilizer_order": len(k_group), "compatible_maps": len(group),
                       "distinct_second_links": len(group) // len(k_group),
                       "burnside_numerator": numerator, "burnside_denominator": denominator,
                       "ordered_classes": numerator // denominator})
    pilots = []
    shapes = [1, 4, 44, 47]
    for index, shape in enumerate(shapes):
        first = next(item for item in types if item["shape"] == shape)
        source = next(item for item in types if item["shape"] == shapes[(index + 1) % 4])
        pilots.append(regenerate(first, source, IDENTITY))
    payload = {"types": types, "mapping_group": group,
               "conjugacy": [{"element": element, "signature": signature,
                               "centralizer_order": centralizer}
                              for element, (signature, centralizer) in conjugacy.items()],
               "counts": counts, "pilots": pilots}
    encoded = (json.dumps(payload) + "\n").encode()
    path = folder / "factorization.json.gz"
    path.write_bytes(gzip.compress(encoded, mtime=0))
    summary = {
        "scope": "All ordered pairs of degree19 links sharing five blocks, conditional on the "
                 "independently complete four-link classification. "
                 "Anchor reversal is not quotiented. "
                 "No extension search or impossibility conclusion.",
        "source_sha256": sha(Path(__file__)), "inputs": inputs,
        "factorization_sha256": sha(path), "first_anchor_types": len(types),
        "source_vertex_types": len(types), "type_pairs": len(counts),
        "shared_star_group_order": len(group),
        "compatible_maps_factorized": sum(item["compatible_maps"] for item in counts),
        "distinct_second_links_with_fixed_first_type": sum(item["distinct_second_links"]
                                                          for item in counts),
        "ordered_union_classes": sum(item["ordered_classes"] for item in counts),
        "per_first_type": [{"id": item["id"],
                            "distinct_second_links": sum(row["distinct_second_links"]
                                                         for row in counts
                                                         if row["first_type"] == item["id"]),
                            "ordered_classes": sum(row["ordered_classes"] for row in counts
                                                   if row["first_type"] == item["id"])}
                           for item in types],
        "explicit_pilot_unions": len(pilots),
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ("inputs", "per_first_type")}, indent=2))


if __name__ == "__main__":
    main()
