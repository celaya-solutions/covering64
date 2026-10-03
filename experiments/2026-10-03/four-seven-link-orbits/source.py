# Document:    First Heavy-Link Orbits in the Four-Sevenfold Branch
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      56e4ef126328d779141004cbc418f46e7d043a677662fa09f9f3df677d6cb7c5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Enumerate all normalized first heavy links; quotient only by valid relabeling."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

OUTSIDE = tuple(range(4, 17))
TRIPLES = ((5, 6, 7), (9, 10, 11), (13, 14, 15))
FORBIDDEN = {pair for group in TRIPLES for pair in combinations(group, 2)}


def matchings(points):
    if not points:
        yield ()
        return
    first = points[0]
    for index, second in enumerate(points[1:], start=1):
        if (first, second) in FORBIDDEN:
            continue
        rest = points[1:index] + points[index + 1:]
        for tail in matchings(rest):
            yield ((first, second),) + tail


def families():
    for leaves in combinations(OUTSIDE[1:], 2):
        rest = tuple(p for p in OUTSIDE[1:] if p not in leaves)
        for matching in matchings(rest):
            yield tuple(sorted(((4, leaves[0]), (4, leaves[1])) + matching))


def generators(case):
    if case not in ("cycle", "matching"):
        raise ValueError("unknown pair-count case")
    result = []
    for group in TRIPLES:
        for a, b in zip(group, group[1:]):
            perm = list(range(1, 17))
            perm[a - 1], perm[b - 1] = b, a
            result.append(tuple(perm))
    # The nontrivial group permutation fixing group1 in each hub graph.
    ga, gb = (1, 3) if case == "cycle" else (2, 3)
    perm = list(range(1, 17))
    for offset in range(4):
        a, b = 4 * ga + offset + 1, 4 * gb + offset + 1
        perm[a - 1], perm[b - 1] = b, a
    result.append(tuple(perm))
    return tuple(result)


def transform(family, perm):
    return tuple(sorted(tuple(sorted(perm[p - 1] for p in edge)) for edge in family))


def enumerate_orbits(case):
    all_families = set(families())
    pending = set(all_families)
    reps, maps = [], []
    gens = generators(case)
    while pending:
        representative = min(pending)
        orbit_maps = {representative: tuple(range(1, 17))}
        queue = deque([representative])
        while queue:
            family = queue.popleft()
            mapping = orbit_maps[family]
            for generator in gens:
                image = transform(family, generator)
                if image not in orbit_maps:
                    orbit_maps[image] = tuple(generator[p - 1] for p in mapping)
                    queue.append(image)
        if not set(orbit_maps) <= pending:
            raise RuntimeError("orbits overlap or leave the enumerated family space")
        for family, mapping in orbit_maps.items():
            if transform(representative, mapping) != family:
                raise RuntimeError("incorrect relabeling certificate")
        reps.append({"id": f"{case}-{len(reps):03d}", "edges": representative,
                     "orbit_size": len(orbit_maps)})
        maps.append({"id": reps[-1]["id"], "maps": [
            {"edges": f, "from_representative": p} for f, p in sorted(orbit_maps.items())
        ]})
        pending.difference_update(orbit_maps)
    return {
        "case": case,
        "labeled_families": len(all_families),
        "representatives": reps,
        "orbit_size_counts": dict(sorted(Counter(r["orbit_size"] for r in reps).items())),
    }, maps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory must be new")
    args.output.mkdir(parents=True)
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    results, certificates = [], []
    for case in ("cycle", "matching"):
        result, certificate = enumerate_orbits(case)
        results.append(result)
        certificates.append({"case": case, "orbits": certificate})
        print(case, result["labeled_families"], len(result["representatives"]), flush=True)
    raw = (json.dumps(certificates, separators=(",", ":")) + "\n").encode()
    archive = gzip.compress(raw, mtime=0)
    (args.output / "relabelings.json.gz").write_bytes(archive)
    metadata = {
        "scope": "Complete first-link classification within each regular four-sevenfold branch; "
                 "not a classification of covers and not an automorphism assumption.",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "relabelings_sha256": hashlib.sha256(archive).hexdigest(),
        "independent_audit": "pending",
        "cases": results,
    }
    (args.output / "result.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
