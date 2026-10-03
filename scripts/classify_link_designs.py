#!/usr/bin/env python3
# Document:    Exact Isomorphism Classification of Nineteen Block Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Standard-library classification under the complete pair-excess graph group.

A nineteen-block (15,4,2) cover has one point of degree6, fourteen of degree5,
and pair excess K1,4 plus five disjoint edges. Every link isomorphism fixes the
unique hub, permutes its4 star leaves, and permutes/flips its5 matching edges.
The resulting24*120*32=92160 maps are exhaustive. For residual enumerations
sharing the same6 hub blocks, retain only the maps preserving those6 blocks.
This classifies supplied links only; it does not certify their enumeration.
"""

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations, permutations, product
from pathlib import Path


def structure(blocks):
    blocks = tuple(tuple(b) for b in blocks)
    if any(type(p) is not int or not 1 <= p <= 16 for b in blocks for p in b):
        raise ValueError("link labels must be integers in1..16")
    blocks = tuple(sorted(tuple(sorted(b)) for b in blocks))
    points = sorted({p for b in blocks for p in b})
    if (len(blocks) != 19 or len(set(blocks)) != 19 or len(points) != 15
            or any(len(b) != 4 or len(set(b)) != 4 for b in blocks)):
        raise ValueError("malformed nineteen-block link")
    pairs = Counter(pair for b in blocks for pair in combinations(b, 2))
    if len(pairs) != 105 or sorted(pairs.values()) != [1] * 96 + [2] * 9:
        raise ValueError("invalid pair coverage")
    degrees = Counter(p for b in blocks for p in b)
    if sorted(degrees.values()) != [5] * 14 + [6]:
        raise ValueError("invalid link degrees")
    hub = next(p for p in points if degrees[p] == 6)
    excess = {pair for pair, count in pairs.items() if count == 2}
    leaves = sorted(next(p for p in pair if p != hub) for pair in excess if hub in pair)
    matching = sorted(pair for pair in excess if hub not in pair)
    if (len(leaves) != 4 or len(matching) != 5
            or set(leaves) & {p for e in matching for p in e}
            or len({p for e in matching for p in e}) != 10):
        raise ValueError("invalid pair-excess graph")
    return blocks, hub, leaves, matching


def map_blocks(blocks, mapping):
    return tuple(sorted(tuple(sorted(mapping[p] for p in b)) for b in blocks))


def hub_maps(source, target):
    source, sh, sl, sm = structure(source)
    target, th, tl, tm = structure(target)
    source_hub = [b for b in source if sh in b]
    target_hub = {b for b in target if th in b}
    for leaves in permutations(tl):
        partial = {sh: th, **dict(zip(sl, leaves))}
        for edges in permutations(tm):
            for flips in product((0, 1), repeat=5):
                mapping = partial.copy()
                for left, right, flip in zip(sm, edges, flips):
                    mapping[left[0]] = right[flip]
                    mapping[left[1]] = right[1 - flip]
                if all(tuple(sorted(mapping[p] for p in b)) in target_hub for b in source_hub):
                    yield mapping


def isomorphism(source, target):
    target = tuple(sorted(tuple(sorted(b)) for b in target))
    for mapping in hub_maps(source, target):
        if map_blocks(source, mapping) == target:
            return mapping
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    shapes = []
    representatives = []
    for shape in (1, 4, 44, 47):
        source = args.folder / "enumeration" / f"{shape}.jsonl"
        rows = [json.loads(line) for line in source.read_text().splitlines()]
        base = rows[0]["link"]
        base_structure = structure(base)
        base_hub = {b for b in base_structure[0] if 2 in b}
        group = list(hub_maps(base, base))
        classes = {}
        assignments = []
        for row in rows:
            link_structure = structure(row["link"])
            if link_structure[1:] != base_structure[1:]:
                raise ValueError("links do not share the expected pair-excess graph")
            link = link_structure[0]
            if {b for b in link if 2 in b} != base_hub:
                raise ValueError("links do not share the expected fixed hub blocks")
            canonical, mapping = min((map_blocks(link, mapping), tuple(sorted(mapping.items())))
                                     for mapping in group)
            if canonical not in classes:
                label = f"shape-{shape}-class-{len(classes)}"
                classes[canonical] = label
                representatives.append((label, canonical))
                (args.output / f"{label}.txt").write_text(
                    "".join(" ".join(map(str, (1, *block))) + "\n" for block in canonical))
            assignments.append({"solution": row["number"], "class": classes[canonical],
                                "mapping_to_canonical": dict(mapping)})
        shapes.append({"shape": shape,
                       "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "input_links": len(rows), "hub_automorphisms": len(group),
                       "classes": len(classes), "assignments": assignments})
        print(json.dumps({k: shapes[-1][k] for k in
                          ("shape", "input_links", "hub_automorphisms", "classes")}), flush=True)
    comparisons = []
    cross_shape_checks = []
    for (left_label, left), (right_label, right) in combinations(representatives, 2):
        mapping = isomorphism(left, right)
        cross_shape_checks.append({"left": left_label, "right": right_label,
                                   "isomorphic": mapping is not None, "mapping": mapping})
        if mapping is not None:
            raise ValueError("distinct supplied hub shapes contain isomorphic links")
    all_blocks = list(combinations(range(1, 17), 5))
    for old in ("lns-fixed-link-20261003", "lns-fixed-link-alt15-20261003"):
        meta = json.loads((Path("experiments/scratch") / old / "metadata.json").read_text())
        link = [tuple(p for p in all_blocks[i] if p != 16) for i in meta["fixed_ids"]]
        structure(link)
        matches = []
        for label, target in representatives:
            mapping = isomorphism(link, target)
            if mapping is not None:
                matches.append({"class": label, "mapping": mapping})
        comparisons.append({"earlier_link": old, "matches": matches})
        print(json.dumps(comparisons[-1]), flush=True)
    result = {"scope": "exact isomorphism classification of supplied links only",
              "completeness_basis": __doc__, "shapes": shapes,
              "cross_shape_checks": cross_shape_checks,
              "earlier_link_comparisons": comparisons,
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "source.py").write_bytes(Path(__file__).read_bytes())
    (args.output / "classification.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
