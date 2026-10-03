#!/usr/bin/env python3
# Document:    Independent Hub-Vertex Audit of Link Isomorphism Classes
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d1f7cd1279b72a4e999cae23e7788929530002707731610b95d2c0f55e1f7dd7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Enumerate isomorphisms through 720 hub-block permutations, not point maps.

The normalized excess graph has one degree-four hub, four leaves in its
component, and five separate matching edges. Its complete point stabilizer
has order 4!*5!*2**5 = 92160. Every link isomorphism preserves pair counts and
therefore lies in this group. If two links have the same hub blocks, their
isomorphisms are precisely the stabilizer of those six blocks in that group.

Independently enumerate this stabilizer by permuting the six hub blocks.
Each leaf image is forced by its two incident blocks. Matching edges must
map to matching edges having the corresponding endpoint blocks; parallel
edges may permute, and loops may swap their two endpoints. This constructs
all and only hub-preserving point bijections, without importing the primary
classifier or the CP hub builder.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def hub_bijections(source, target):
    source = sorted(tuple(b) for b in source)
    target = sorted(tuple(b) for b in target)
    require(len(source) == len(set(source)) == len(target) == len(set(target)) == 6,
            "six distinct hub blocks required")
    sloc = {x: tuple(i for i, block in enumerate(source) if x in block) for x in range(3, 17)}
    tloc = {x: tuple(i for i, block in enumerate(target) if x in block) for x in range(3, 17)}
    require(all(len(sloc[x]) == len(tloc[x]) == (2 if x < 7 else 1)
                for x in range(3, 17)), "hub point degree")
    target_leaves = {tloc[x]: x for x in range(3, 7)}
    require(len(target_leaves) == 4, "parallel target leaf edges")
    target_matching = defaultdict(list)
    for x in range(7, 17, 2):
        target_matching[tuple(sorted((tloc[x][0], tloc[x + 1][0])))].append((x, x + 1))
    maps = set()
    for vertices in itertools.permutations(range(6)):
        mapping = {2: 2}
        for x in range(3, 7):
            edge = tuple(sorted(vertices[i] for i in sloc[x]))
            if edge not in target_leaves:
                break
            mapping[x] = target_leaves[edge]
        if len(mapping) != 5:
            continue
        source_matching = defaultdict(list)
        for x in range(7, 17, 2):
            edge = tuple(sorted((vertices[sloc[x][0]], vertices[sloc[x + 1][0]])))
            source_matching[edge].append((x, x + 1))
        if {e: len(v) for e, v in source_matching.items()} != {
                e: len(v) for e, v in target_matching.items()}:
            continue
        groups = sorted(source_matching)

        def assign(group, partial):
            if group == len(groups):
                require(set(partial) == set(partial.values()) == set(range(2, 17)),
                        "constructed map is not a point bijection")
                mapped = {tuple(sorted(partial[x] for x in b)) for b in source}
                require(mapped == set(target), "constructed map does not preserve hub")
                maps.add(tuple(partial[x] for x in range(2, 17)))
                return
            edge = groups[group]
            source_pairs = source_matching[edge]
            for target_pairs in itertools.permutations(target_matching[edge]):
                orientations = []
                for spair, tpair in zip(source_pairs, target_pairs):
                    choices = []
                    for orientation in [tpair, tpair[::-1]]:
                        if all(vertices[sloc[s][0]] == tloc[t][0]
                               for s, t in zip(spair, orientation)):
                            choices.append(orientation)
                    orientations.append(choices)
                for choices in itertools.product(*orientations):
                    extended = partial.copy()
                    for spair, tpair in zip(source_pairs, choices):
                        extended.update(zip(spair, tpair))
                    assign(group + 1, extended)

        assign(0, mapping)
    return sorted(maps)


def image(link, mapping):
    # A bitset encoding differs from the primary classifier's tuple ordering.
    return tuple(sorted(sum(1 << mapping[x - 2] for x in block) for block in link))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("classification", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite output")
    raw = args.fixture.read_bytes()
    fixture = json.loads(gzip.decompress(raw))["body"]
    primary_raw = args.classification.read_bytes()
    primary = json.loads(primary_raw)
    require(sorted(s["shape"] for s in primary["shapes"]) == [1, 4, 44, 47],
            "missing or duplicate shape classification")
    groups = {}
    results = []
    for primary_shape in primary["shapes"]:
        shape = primary_shape["shape"]
        links = fixture["cp_solutions"][str(shape)]
        hub = fixture["metadata"]["shapes"][shape]["hub_blocks"]
        maps = hub_bijections(hub, hub)
        groups[shape] = maps
        require(len(maps) == primary_shape["hub_automorphisms"], "automorphism count differs")
        classes = {min(image(link, mapping) for mapping in maps) for link in links}
        require(len(classes) == primary_shape["classes"], "class count differs")
        require(len(links) == primary_shape["input_links"], "input link count")
        require([a["solution"] for a in primary_shape["assignments"]]
                == list(range(1, len(links) + 1)), "missing or duplicate assignment")
        canonical_path = args.classification.parent / f"shape-{shape}-class-0.txt"
        canonical = {tuple(x for x in map(int, row.split()) if x != 1)
                     for row in canonical_path.read_text().splitlines()}
        for link, assignment in zip(links, primary_shape["assignments"]):
            mapping = {int(k): v for k, v in assignment["mapping_to_canonical"].items()}
            require(set(mapping) == set(mapping.values()) == set(range(2, 17)),
                    "primary assignment not a bijection")
            require(tuple(mapping[x] for x in range(2, 17)) in maps,
                    "assignment outside stabilizer")
            require({tuple(sorted(mapping[x] for x in b)) for b in link} == canonical,
                    "primary canonical assignment mismatch")
        results.append({"shape": shape, "hub_automorphisms": len(maps),
                        "classes": len(classes), "links": len(links),
                        "automorphism_maps": maps, "canonical_class_hashes": sorted(
                            digest(c) for c in classes)})
    cross = []
    for left, right in itertools.combinations(sorted(groups), 2):
        lh = fixture["metadata"]["shapes"][left]["hub_blocks"]
        rh = fixture["metadata"]["shapes"][right]["hub_blocks"]
        maps = hub_bijections(lh, rh)
        require(not maps, "claimed distinct hub shapes are isomorphic")
        cross.append({"left_shape": left, "right_shape": right, "hub_maps": len(maps)})
    body = {"scope": "Complete isomorphism partition of the independently enumerated114 links",
            "excess_graph_stabilizer_order": 92160, "shape_results": results,
            "cross_shape_checks": cross, "fixture_sha256": hashlib.sha256(raw).hexdigest(),
            "primary_classification_sha256": hashlib.sha256(primary_raw).hexdigest(),
            "primary_classifier_source_sha256": primary["source_sha256"],
            "checker_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    header = {"Document": "Independent Link Isomorphism Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": digest(body), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    encoded = json.dumps({"document_header": header, "body": body},
                         sort_keys=True, separators=(",", ":")).encode()
    args.output.write_bytes(gzip.compress(encoded + b"\n", mtime=0))
    print(json.dumps({"classes": sum(r["classes"] for r in results),
                      "automorphism_counts": {r["shape"]: r["hub_automorphisms"] for r in results},
                      "negative_cross_shape_checks": len(cross),
                      "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
