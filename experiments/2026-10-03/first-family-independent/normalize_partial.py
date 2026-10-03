# Document:    Normalize a Partial Candidate to a First Family
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Relabel an explicit partial candidate and record unmet strict-model properties."""

import argparse
import gzip
import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from covering64.core import read_blocks, verify_cover, write_blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output_prefix", type=Path)
    args = parser.parse_args()
    root = Path("experiments/2026-10-03/local-template-orbits")
    representatives = json.loads((root / "first-families.json").read_text())
    blocks = read_blocks(args.candidate)
    original = verify_cover(blocks)
    outside_pairs = set(itertools.combinations(range(4, 17), 2))
    selected = None
    for anchor in (1, 2, 3):
        family = [tuple(p for p in b if p >= 4) for b in blocks if set(b) & {1, 2, 3} == {anchor}]
        missing = outside_pairs - {p for b in family for p in itertools.combinations(b, 2)}
        if (4, 5) in missing or (4, 6) in missing:
            selected = anchor, (4, 5) in missing
            break
    if selected is None:
        raise ValueError("no spoke-omitting first family")
    anchor, already_first = selected
    first_map = {p: p for p in range(1, 17)}
    first_map[1], first_map[anchor] = anchor, 1
    if not already_first:
        first_map[5], first_map[6] = 6, 5
    interim = sorted(tuple(sorted(first_map[p] for p in b)) for b in blocks)
    quads = list(itertools.combinations(range(4, 17), 4))
    quad_ids = {b: i + 1 for i, b in enumerate(quads)}
    family_ids = sorted(
        quad_ids[tuple(p for p in b if p >= 4)] for b in interim if set(b) & {1, 2, 3} == {1}
    )
    archive = Path(representatives["maps_archive"]["path"])
    if (
        hashlib.sha256(archive.read_bytes()).hexdigest()
        != representatives["maps_archive"]["sha256"]
    ):
        raise ValueError("map archive hash mismatch")
    found = None
    with gzip.open(archive, "rt") as stream:
        next(stream)
        for line in stream:
            row = json.loads(line)
            if row["block_ids"] == family_ids:
                found = row
                break
    if found is None:
        raise ValueError("first family absent from complete representatives archive")
    mapping = {
        p: found["family_to_representative"][first_map[p] - 4]
        if first_map[p] >= 4
        else first_map[p]
        for p in range(1, 17)
    }
    if sorted(mapping.values()) != list(range(1, 17)):
        raise ValueError("normalization is not a point permutation")
    transformed = sorted(tuple(sorted(mapping[p] for p in b)) for b in blocks)
    record = next(
        r for r in representatives["representatives"] if r["id"] == found["representative"]
    )
    if not {tuple(b) for b in record["full_twenty_blocks"]} <= set(transformed):
        raise ValueError("normalized candidate does not contain the twenty fixed blocks")
    path = args.output_prefix.with_suffix(".txt")
    write_blocks(path, transformed)
    package = verify_cover(transformed)
    run = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        capture_output=True,
        text=True,
    )
    standalone = json.loads(run.stdout)
    if (
        package["canonical_sha256"] != standalone["canonical_sha256"]
        or len(package["uncovered"]) != standalone["uncovered_count"]
        or len(package["uncovered"]) != len(original["uncovered"])
    ):
        raise ValueError("coverage disagrees after normalization")
    pairs = Counter(p for b in transformed for p in itertools.combinations(b, 2))
    triples = Counter(t for b in transformed for t in itertools.combinations(b, 3))
    unsupported = []
    for i, block in enumerate(transformed):
        supported = {p for t in itertools.combinations(block, 3) if triples[t] == 1 for p in t}
        unsupported.extend(
            {"block_index": i, "block": block, "point": p} for p in block if p not in supported
        )
    local_holes = {}
    for a in (1, 2, 3):
        family = [tuple(p for p in b if p >= 4) for b in transformed if set(b) & {1, 2, 3} == {a}]
        local_holes[a] = sorted(
            outside_pairs - {p for b in family for p in itertools.combinations(b, 2)}
        )
    deficits = [
        {"pair": pair, "count": pairs[pair], "deficit": 5 - pairs[pair]}
        for pair in itertools.combinations(range(1, 17), 2)
        if pairs[pair] < 5
    ]
    result = {
        "source": str(args.candidate),
        "source_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "normalizer_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "representative": record["id"],
        "point_map": mapping,
        "package": package,
        "standalone": standalone,
        "pair_deficits": deficits,
        "total_pair_deficit": sum(r["deficit"] for r in deficits),
        "local_missing_pairs": local_holes,
        "opposite_spoke_omitted": any((4, 6) in local_holes[a] for a in (2, 3)),
        "unsupported_block_point_occurrences": unsupported,
        "scope": "Relabeling of one partial candidate; no claim that it fits the strict model",
    }
    args.output_prefix.with_suffix(".json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "representative": record["id"],
                "holes": len(package["uncovered"]),
                "pair_deficit": result["total_pair_deficit"],
                "opposite_spoke_omitted": result["opposite_spoke_omitted"],
                "unsupported_points": len(unsupported),
                "candidate": str(path),
            }
        )
    )


if __name__ == "__main__":
    main()
