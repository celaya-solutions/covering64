#!/usr/bin/env python3
# Document:    Complete Double Hub Link Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate two degree19 point links sharing six blocks, using the four classes.

Completeness is conditional on the separately checked complete classification
of (15,4,2) nineteen-block links. Every second link's unique degree6 vertex is
the first anchor. Its six hub blocks are prescribed. Enumerate all720 maps of
the six hub blocks; a double-used leaf is identified by its two incident blocks,
while single-use points permute freely inside their one incident block. This
does not constrain the second link's perfect matching. Canonicalization uses
only explicitly checked automorphisms of the first entire nineteen-block link.
The result covers this double-degree19, pair-degree6 branch only.
"""

import argparse
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import permutations, product
from pathlib import Path

from covering64.core import Universe, verify_cover, write_blocks

spec = importlib.util.spec_from_file_location(
    "link_classification", Path(__file__).with_name("classify_link_designs.py"))
classification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(classification)


def unrestricted_hub_maps(source, target_hub_blocks):
    source, source_hub, _, _ = classification.structure(source)
    source_rows = [b for b in source if source_hub in b]
    target_rows = tuple(sorted(tuple(sorted(b)) for b in target_hub_blocks))
    counts = Counter(p for b in target_rows for p in b)
    if (len(target_rows) != 6 or len(set(target_rows)) != 6
            or any(len(b) != 4 or len(set(b)) != 4 for b in target_rows)
            or any(type(p) is not int or not 1 <= p <= 16 for p in counts)
            or sorted(counts.values()) != [1] * 10 + [2] * 4 + [6]):
        raise ValueError("invalid prescribed six hub blocks")
    target_hub = next(p for p, n in counts.items() if n == 6)
    source_incidence = {p: tuple(i for i, b in enumerate(source_rows) if p in b)
                        for p in sorted({p for b in source for p in b} - {source_hub})}
    target_groups = defaultdict(list)
    for p in sorted(set(counts) - {target_hub}):
        target_groups[tuple(i for i, b in enumerate(target_rows) if p in b)].append(p)
    for row_map in permutations(range(6)):
        source_groups = defaultdict(list)
        for p, rows in source_incidence.items():
            source_groups[tuple(sorted(row_map[i] for i in rows))].append(p)
        if set(source_groups) != set(target_groups):
            continue
        signatures = sorted(source_groups)
        if any(len(source_groups[s]) != len(target_groups[s]) for s in signatures):
            continue
        choices = [tuple(permutations(target_groups[s])) for s in signatures]
        for targets in product(*choices):
            mapping = {source_hub: target_hub}
            for signature, images in zip(signatures, targets):
                mapping.update(zip(source_groups[signature], images))
            yield mapping


def enumerate_second_links(templates, first_link):
    first_link, hub, _, _ = classification.structure(first_link)
    if hub != 2 or {p for b in first_link for p in b} != set(range(2, 17)):
        raise ValueError("first link must use2..16 with hub2 and external anchor1")
    target_hub = tuple(sorted(tuple(sorted((1, *(p for p in b if p != 2))))
                              for b in first_link if 2 in b))
    unique = {}
    map_counts = {}
    for label, source in templates.items():
        count = 0
        for mapping in unrestricted_hub_maps(source, target_hub):
            count += 1
            second = classification.map_blocks(source, mapping)
            classification.structure(second)
            if {b for b in second if 1 in b} != set(target_hub):
                raise RuntimeError("hub map did not preserve the prescribed blocks")
            if second not in unique:
                unique[second] = {"source_class": label, "mapping": mapping}
        map_counts[label] = count
    return unique, map_counts


def independent_check(path, v, k, t, expected, must_cover):
    command = [sys.executable, str(Path(__file__).with_name("check_cover.py")), str(path),
               "--v", str(v), "--k", str(k), "--t", str(t),
               "--expected-blocks", str(expected)]
    run = subprocess.run(command, capture_output=True, text=True, check=False)
    result = json.loads(run.stdout)
    if (result["blocks"] != expected or not result["cardinality_matches"]
            or (must_cover and not result["valid"]) or run.returncode not in (0, 1)):
        raise RuntimeError("independent verifier rejected the candidate")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("templates", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    templates = {}
    for label in (1, 4, 44, 47):
        path = args.templates / f"shape-{label}-class-0.txt"
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        if any(len(b) != 5 or b[0] != 1 for b in blocks):
            raise ValueError("template blocks must begin with anchor1")
        templates[str(label)] = classification.structure([b[1:] for b in blocks])[0]
    universe = Universe.build()
    lookup = {b: i for i, b in enumerate(universe.blocks)}
    all_candidates = []
    summary = []
    for label, first in templates.items():
        folder = args.output / f"shape-{label}"
        folder.mkdir(exist_ok=True)
        unique, map_counts = enumerate_second_links(templates, first)
        first_blocks = {tuple(sorted((1, *b))) for b in first}
        group = [{1: 1, **mapping} for mapping in classification.hub_maps(first, first)
                 if classification.map_blocks(first, mapping) == first]
        classes = {}
        assignments = []
        matchings = set()
        for number, (second, origin) in enumerate(sorted(unique.items())):
            labels = {p: i + 1 for i, p in enumerate(sorted({p for b in second for p in b}))}
            local = classification.map_blocks(second, labels)
            package = verify_cover(local, 15, 4, 2)
            if not package["valid"]:
                raise RuntimeError("second link failed package verification")
            path = folder / f"second-{number:03}.txt"
            write_blocks(path, local)
            standalone = independent_check(path, 15, 4, 2, 19, True)
            if standalone["canonical_sha256"] != package["canonical_sha256"]:
                raise RuntimeError("link checker hashes disagree")
            second_blocks = {tuple(sorted((2, *b))) for b in second}
            if len(first_blocks & second_blocks) != 6:
                raise RuntimeError("the two links do not share exactly six blocks")
            union = tuple(sorted(first_blocks | second_blocks))
            if len(union) != 32:
                raise RuntimeError("double-hub union does not have32 distinct blocks")
            canonical, stabilizer = min((classification.map_blocks(union, mapping),
                                         tuple(sorted(mapping.items()))) for mapping in group)
            if canonical not in classes:
                identifier = f"shape-{label}-class-{len(classes):03}"
                classes[canonical] = identifier
                seed_path = folder / f"{identifier}.txt"
                write_blocks(seed_path, canonical)
                package_union = verify_cover(canonical)
                standalone_union = independent_check(seed_path, 16, 5, 3, 32, False)
                if (package_union["replication"][1] != 19
                        or package_union["replication"][2] != 19
                        or standalone_union["canonical_sha256"] != package_union["canonical_sha256"]
                        or standalone_union["uncovered_count"] != len(package_union["uncovered"])):
                    raise RuntimeError("double-hub verification mismatch")
                all_candidates.append({"identifier": identifier, "first_class": label,
                                       "retained_block_ids": [lookup[b] for b in canonical],
                                       "retained_blocks": canonical,
                                       "uncovered": len(package_union["uncovered"]),
                                       "package_verification": package_union,
                                       "standalone_verification": standalone_union})
            matchings.add(tuple(classification.structure(second)[3]))
            assignments.append({"number": number, "second_link": second,
                                "source_class": origin["source_class"],
                                "source_mapping": origin["mapping"],
                                "class": classes[canonical], "stabilizer_mapping": dict(stabilizer),
                                "canonical_sha256": package["canonical_sha256"],
                                "package_valid": True, "standalone_valid": True})
        row = {"first_class": label, "raw_hub_maps": map_counts,
               "distinct_second_links": len(unique), "distinct_second_matchings": len(matchings),
               "first_link_automorphisms": group, "union_classes": len(classes),
               "assignments": assignments}
        (folder / "enumeration.json.gz").write_bytes(
            gzip.compress(json.dumps(row, indent=2).encode() + b"\n", mtime=0))
        summary.append({k: row[k] for k in ("first_class", "raw_hub_maps", "distinct_second_links",
                                           "distinct_second_matchings", "union_classes")})
        print(json.dumps(summary[-1]), flush=True)
    source = Path(__file__)
    metadata = {"scope": __doc__, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "classifier_sha256": hashlib.sha256(
                    source.with_name("classify_link_designs.py").read_bytes()).hexdigest(),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "total_union_classes": len(all_candidates), "shapes": summary}
    (args.output / "source.py").write_bytes(source.read_bytes())
    classifier_source = source.with_name("classify_link_designs.py").read_bytes()
    (args.output / "classifier.py").write_bytes(classifier_source)
    (args.output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (args.output / "candidates.json.gz").write_bytes(gzip.compress(
        json.dumps({"metadata": metadata, "candidates": all_candidates}, indent=2).encode()
        + b"\n", mtime=0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
