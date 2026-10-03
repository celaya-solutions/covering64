#!/usr/bin/env python3
# Document:    Anchor Reversal Quotient for Double Hub Seeds
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Merge already classified union seeds by explicitly checked anchor reversal.

In each partial32-block union, only points1 and2 have degree19; all other point
degrees are8 or9. Hence every union isomorphism either preserves or reverses
the two anchors. Ordered-anchor equivalence was already exhaustively removed
by the four complete link classes and the first full-link automorphism groups.
The explicit reversal below supplies the other coset. No search bound follows.
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "link_classification", Path(__file__).with_name("classify_link_designs.py"))
classification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classification)


def reverse_map(source_mapping, stabilizer_mapping):
    for raw in (source_mapping, stabilizer_mapping):
        if any(type(v) is not int or not (type(k) is int or type(k) is str and k.isdecimal())
               for k, v in raw.items()):
            raise ValueError("mapping labels must be integers")
    source = {int(k): int(v) for k, v in source_mapping.items()}
    stabilizer = {int(k): int(v) for k, v in stabilizer_mapping.items()}
    if (set(source) != set(range(2, 17))
            or set(source.values()) != set(range(1, 17)) - {2}
            or set(stabilizer) != set(range(1, 17))
            or set(stabilizer.values()) != set(range(1, 17))):
        raise ValueError("incomplete or nonbijective point mapping")
    mapping = {stabilizer[source[p]]: p for p in source}
    mapping[2] = 1
    if (set(mapping) != set(range(1, 17)) or mapping[1] != 2
            or set(mapping.values()) != set(range(1, 17))):
        raise ValueError("invalid anchor reversal")
    return mapping


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--templates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = (args.folder / "candidates.json.gz").read_bytes()
    cases = json.loads(gzip.decompress(raw))["candidates"]
    lookup = {tuple(map(tuple, case["retained_blocks"])): i for i, case in enumerate(cases)}
    if len(lookup) != len(cases):
        raise ValueError("duplicate canonical seeds")
    assignments = {}
    groups = {}
    for label in ("1", "4", "44", "47"):
        data = json.loads(gzip.decompress(
            (args.folder / f"shape-{label}" / "enumeration.json.gz").read_bytes()))
        for assignment in data["assignments"]:
            assignments.setdefault(assignment["class"], assignment)
        path = args.templates / f"shape-{label}-class-0.txt"
        link = tuple(tuple(map(int, line.split()))[1:] for line in path.read_text().splitlines())
        groups[label] = [{1: 1, **m} for m in classification.hub_maps(link, link)
                         if classification.map_blocks(link, m) == link]
    edges = []
    for i, case in enumerate(cases):
        blocks = tuple(map(tuple, case["retained_blocks"]))
        degrees = Counter(p for b in blocks for p in b)
        if (len(blocks) != 32 or {p for p, n in degrees.items() if n == 19} != {1, 2}
                or any(degrees[p] not in (8, 9) for p in range(3, 17))):
            raise ValueError("the union does not distinguish exactly two anchors")
        assignment = assignments[case["identifier"]]
        base = reverse_map(assignment["source_mapping"], assignment["stabilizer_mapping"])
        alternatives = []
        for m in groups[assignment["source_class"]]:
            mapping = {p: m[base[p]] for p in range(1, 17)}
            alternatives.append((classification.map_blocks(blocks, mapping),
                                 tuple(mapping.items())))
        canonical, mapping = min(alternatives)
        if canonical not in lookup:
            raise ValueError("anchor reversal left the enumerated seed collection")
        j = lookup[canonical]
        edges.append({"source": i, "target": j, "source_identifier": case["identifier"],
                      "target_identifier": cases[j]["identifier"], "mapping": dict(mapping)})
    if any(edges[edge["target"]]["target"] != edge["source"] for edge in edges):
        raise ValueError("reversal on canonical classes is not an involution")
    orbits = sorted({tuple(sorted({edge["source"], edge["target"]})) for edge in edges})
    result = {"scope": __doc__, "input_sha256": hashlib.sha256(raw).hexdigest(),
              "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "input_cases": len(cases), "union_isomorphism_classes": len(orbits),
              "orbits": orbits, "representative_case_ids": [orbit[0] for orbit in orbits],
              "reversal_maps": edges}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    counts = {k: result[k] for k in ("input_cases", "union_isomorphism_classes")}
    print(json.dumps(counts), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
