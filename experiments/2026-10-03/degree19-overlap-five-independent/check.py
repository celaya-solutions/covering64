# Document:    Independent Five Overlap Factorization Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate all star maps separately and directly count each conjugation solution."""

import copy
import gzip
import hashlib
import json
from collections import Counter
from itertools import combinations, permutations, product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "degree19-overlap-five"
STAR = ((0, 1, 2), (0, 3, 4), (5, 6, 7), (8, 9, 10), (11, 12, 13))
FROZEN_SHA = "f9a8c81ef8bb7fb7fa113d113be17c446a1efd9ca8bb98b3110272a2d8c20064"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_star_group():
    group = []
    row_permutations = 0
    for targets in permutations(range(5)):
        if any(len(set(STAR[i]) & set(STAR[j])) !=
               len(set(STAR[targets[i]]) & set(STAR[targets[j]]))
               for i, j in combinations(range(5), 2)):
            continue
        row_permutations += 1
        sources = [tuple(point for point in row if point != 0) for row in STAR]
        options = [tuple(permutations(point for point in STAR[target] if point != 0))
                   for target in targets]
        for images in product(*options):
            mapping = {0: 0}
            for source, image in zip(sources, images):
                mapping.update(zip(source, image))
            permutation = tuple(mapping[i] for i in range(14))
            require(sorted(permutation) == list(range(14)), "constructed non-bijection")
            require({tuple(sorted(permutation[p] for p in row)) for row in STAR} == set(STAR),
                    "constructed map does not preserve star")
            group.append(permutation)
    require(row_permutations == 12 and len(group) == len(set(group)) == 10368,
            "wrong complete star group")
    return sorted(group)


def validate_group(payload, expected):
    actual = list(map(tuple, payload["mapping_group"]))
    require(len(actual) == len(set(actual)) and sorted(actual) == expected,
            "saved group differs from complete independently generated maps")


def validate_types(payload, roadmap):
    expected_keys = {(entry["shape"], min(orbit)) for entry in roadmap["classes"]
                     for orbit in entry["point_orbits"] if 2 not in orbit}
    actual_keys = [(item["shape"], item["distinguished_point"]) for item in payload["types"]]
    require(len(actual_keys) == len(set(actual_keys)) == 34 and set(actual_keys) == expected_keys,
            "missing, extra, or duplicate pointed-link type")
    stabilizers = {}
    for item in payload["types"]:
        shape, anchor = item["shape"], item["distinguished_point"]
        require(item["id"] == f"shape{shape}-point{anchor}", "wrong type ID")
        record = next(row for row in roadmap["classes"] if row["shape"] == shape)
        witness = HERE.parent / "link-classification" / f"shape-{shape}-class-0.txt"
        require(sha(witness) == record["witness_sha256"], "audited witness changed")
        full = sorted(tuple(map(int, line.split())) for line in witness.read_text().splitlines()
                      if line.strip())
        link = [block[1:] for block in full]
        require(list(map(tuple, item["full_first_link"])) == full
                and list(map(tuple, item["source_link"])) == link, "wrong full link")
        star = [block for block in link if anchor in block]
        require(list(map(tuple, item["source_star"])) == star, "wrong fivefold source star")
        target = [tuple(sorted((1, *(p for p in block if p != anchor)))) for block in star]
        require(list(map(tuple, item["target_star"])) == target, "wrong target star")
        coords = item["coordinates"]
        require(len(coords) == len(set(coords)) == 14
                and set(coords) == set(range(2, 17)) - {anchor}, "invalid coordinate chart")
        require({tuple(sorted(coords[i] for i in row)) for row in STAR} ==
                {tuple(p for p in block if p != anchor) for block in star}, "wrong star chart")
        maps = [dict(zip(range(2, 17), mapping)) for mapping in record["full_automorphisms"]]
        orbit = sorted({mapping[anchor] for mapping in maps})
        require(orbit == item["point_orbit"], "wrong distinguished-point orbit")
        fixing = [mapping for mapping in maps if mapping[anchor] == anchor]
        supplied = [{int(p): value for p, value in mapping.items()}
                    for mapping in item["stabilizer_point_permutations"]]
        require(sorted(tuple(mapping.items()) for mapping in supplied) ==
                sorted(tuple(mapping.items()) for mapping in fixing), "wrong full-link stabilizer")
        inverse_chart = {point: index for index, point in enumerate(coords)}
        projected = sorted(tuple(inverse_chart[mapping[point]] for point in coords)
                           for mapping in fixing)
        require(list(map(tuple, item["stabilizer_coordinate_permutations"])) == projected,
                "wrong projected stabilizer")
        require(item["full_automorphism_order"] == record["group_order"]
                and len(projected) * len(orbit) == record["group_order"], "orbit-stabilizer error")
        stabilizers[item["id"]] = projected
    return stabilizers


def conjugation_counts(group, elements):
    inverses = []
    for mapping in group:
        inverse = [0] * 14
        for source, target in enumerate(mapping):
            inverse[target] = source
        inverses.append(inverse)
    # Count g*h*g^-1=k directly. This does not infer counts from signatures.
    return {element: Counter(tuple(mapping[element[inverse[p]]] for p in range(14))
                             for mapping, inverse in zip(group, inverses)) for element in elements}


def validate_counts(payload, stabilizers, conjugates):
    needed = {element for subgroup in stabilizers.values() for element in subgroup}
    require({tuple(row["element"]) for row in payload["conjugacy"]} == needed
            and len(payload["conjugacy"]) == len(needed), "wrong conjugacy element inventory")
    for row in payload["conjugacy"]:
        element = tuple(row["element"])
        images = conjugates[element]
        require(tuple(row["signature"]) == min(images)
                and row["centralizer_order"] == images[element], "wrong conjugacy data")
    expected_pairs = set(product(stabilizers, repeat=2))
    seen, total_maps, total_links, total_classes = set(), 0, 0, 0
    for row in payload["counts"]:
        key = row["first_type"], row["source_type"]
        require(key in expected_pairs and key not in seen, "bad type pair inventory")
        seen.add(key)
        h, k = (stabilizers[item] for item in key)
        fixed_sum = sum(conjugates[left][right] for left, right in product(h, k))
        denominator = len(h) * len(k)
        require(fixed_sum % denominator == 0, "non-integral orbit count")
        expected = {"target_stabilizer_order": len(h), "source_stabilizer_order": len(k),
                    "compatible_maps": 10368, "distinct_second_links": 10368 // len(k),
                    "burnside_numerator": fixed_sum, "burnside_denominator": denominator,
                    "ordered_classes": fixed_sum // denominator}
        require(all(row[field] == value for field, value in expected.items()), "incorrect count")
        total_maps += 10368
        total_links += expected["distinct_second_links"]
        total_classes += expected["ordered_classes"]
    require(seen == expected_pairs, "missing type pairs")
    return total_maps, total_links, total_classes


def validate_pilots(payload, group):
    types = {item["id"]: item for item in payload["types"]}
    require(len(payload["pilots"]) == 4, "wrong explicit pilot count")
    for pilot in payload["pilots"]:
        first, source = (types[pilot[field]] for field in ("first_type", "source_type"))
        mapping = tuple(pilot["coordinate_mapping"])
        require(mapping in group, "pilot map not in complete star group")
        second_anchor = first["distinguished_point"]
        point_map = {source["distinguished_point"]: 1}
        point_map.update({p: first["coordinates"][mapping[i]]
                          for i, p in enumerate(source["coordinates"])})
        require(set(point_map.values()) == set(range(1, 17)) - {second_anchor},
                "pilot map not onto")
        first_blocks = set(map(tuple, first["full_first_link"]))
        second = {tuple(sorted((second_anchor, *(point_map[p] for p in block))))
                  for block in source["source_link"]}
        shared = first_blocks & second
        require(len(first_blocks) == len(second) == 19 and len(shared) == 5
                and len(first_blocks | second) == 33, "pilot union cardinality")
        require(shared == {block for block in first_blocks if second_anchor in block}
                and shared == {block for block in second if 1 in block}, "wrong shared blocks")
        require(pilot["anchors"] == [1, second_anchor]
                and pilot["source_to_second_point_map"] == {str(p): v for p, v in point_map.items()}
                and list(map(tuple, pilot["second_link_blocks"])) == sorted(second)
                and list(map(tuple, pilot["fixed_blocks"])) == sorted(first_blocks | second)
                and list(map(tuple, pilot["shared_blocks"])) == sorted(shared), "damaged pilot")


def main():
    factorization = INPUT / "factorization.json.gz"
    require(sha(factorization) == FROZEN_SHA, "frozen factorization changed")
    payload = json.loads(gzip.decompress(factorization.read_bytes()))
    summary = json.loads((INPUT / "summary.json").read_text())
    require(summary["factorization_sha256"] == FROZEN_SHA
            and summary["source_sha256"] == sha(INPUT / "derive.py"), "source hash mismatch")
    for name, digest in summary["inputs"].items():
        require(sha(ROOT / name) == digest, "input hash mismatch")
    roadmap_path = HERE.parent / "degree19-roadmap-independent/audit.json"
    roadmap = json.loads(roadmap_path.read_text())
    require(roadmap["passed"], "full automorphism audit prerequisite missing")
    group = independent_star_group()
    validate_group(payload, group)
    stabilizers = validate_types(payload, roadmap)
    elements = {element for subgroup in stabilizers.values() for element in subgroup}
    conjugates = conjugation_counts(group, elements)
    totals = validate_counts(payload, stabilizers, conjugates)
    require(totals == (11985408, 7402752, 4578210), "unexpected independently recovered totals")
    for field, value in zip(("compatible_maps_factorized",
                             "distinct_second_links_with_fixed_first_type",
                             "ordered_union_classes"), totals):
        require(summary[field] == value, "summary total mismatch")
    validate_pilots(payload, set(group))
    controls = []
    for control in ("missing_group_map", "duplicate_group_map", "missing_type", "wrong_chart",
                    "wrong_stabilizer", "missing_count", "wrong_count", "wrong_pilot"):
        damaged = copy.deepcopy(payload)
        validator = None
        if control == "missing_group_map":
            damaged["mapping_group"].pop()
            validator, arguments = validate_group, (damaged, group)
        elif control == "duplicate_group_map":
            damaged["mapping_group"][-1] = damaged["mapping_group"][0]
            validator, arguments = validate_group, (damaged, group)
        elif control == "missing_type":
            damaged["types"].pop()
            validator, arguments = validate_types, (damaged, roadmap)
        elif control == "wrong_chart":
            damaged["types"][0]["coordinates"][0] = 1
            validator, arguments = validate_types, (damaged, roadmap)
        elif control == "wrong_stabilizer":
            damaged["types"][0]["stabilizer_coordinate_permutations"].pop()
            validator, arguments = validate_types, (damaged, roadmap)
        elif control == "missing_count":
            damaged["counts"].pop()
            validator, arguments = validate_counts, (damaged, stabilizers, conjugates)
        elif control == "wrong_count":
            damaged["counts"][0]["ordered_classes"] += 1
            validator, arguments = validate_counts, (damaged, stabilizers, conjugates)
        else:
            damaged["pilots"][0]["fixed_blocks"].pop()
            validator, arguments = validate_pilots, (damaged, set(group))
        try:
            validator(*arguments)
        except ValueError:
            controls.append(control)
        else:
            raise ValueError(f"damaged factorization accepted: {control}")
    result = {"passed": True, "factorization_sha256": FROZEN_SHA,
              "checker_sha256": sha(Path(__file__)), "roadmap_audit_sha256": sha(roadmap_path),
              "star_group_order": len(group), "pointed_link_types": len(stabilizers),
              "conjugation_elements": len(elements), "type_pairs": len(payload["counts"]),
              "compatible_maps": totals[0], "distinct_pinned_second_links": totals[1],
              "ordered_union_classes": totals[2], "explicit_pilots_checked": 4,
              "damaged_controls_rejected": controls,
              "scope": "Complete factorized enumeration of ordered pointed degree19 links "
                       "sharing five blocks, conditional on the separate four-link classification. "
                       "No anchor reversal quotient, extension search, or cover claim."}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
