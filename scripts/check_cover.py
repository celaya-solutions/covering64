#!/usr/bin/env python3
"""Check covering witnesses independently by exhaustive subset containment.

Rebuilt from retained conversation context after a filesystem reset. This file
imports only the standard library and shares no package parser or mask code.
"""

import argparse
import json
import re
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from math import comb
from pathlib import Path


class InvalidWitness(ValueError):
    """Malformed parameters or witness structure."""


def parse_witness(text):
    """Parse integer rows or JSON blocks without coercing JSON label types."""
    stripped = text.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidWitness(f"invalid JSON: {exc}") from exc
        if isinstance(value, dict):
            if "blocks" not in value:
                raise InvalidWitness("JSON object must contain a 'blocks' list")
            value = value["blocks"]
        if not isinstance(value, list):
            raise InvalidWitness("JSON blocks must be a list")
        return value
    blocks = []
    for number, line in enumerate(text.splitlines(), 1):
        tokens = line.split("#", 1)[0].split()
        if not tokens:
            continue
        if any(re.fullmatch(r"[+-]?[0-9]+", token) is None for token in tokens):
            raise InvalidWitness(f"line {number}: labels must be integers")
        blocks.append([int(token) for token in tokens])
    return blocks


def verify_cover(blocks, v=16, k=5, t=3, expected_blocks=None):
    """Validate strict integer structure, then count every required subset."""
    if any(type(value) is not int for value in (v, k, t)):
        raise InvalidWitness("v, k, and t must be integers")
    if not 1 <= t <= k <= v:
        raise InvalidWitness("parameters must satisfy 1 <= t <= k <= v")
    if expected_blocks is not None and (
        type(expected_blocks) is not int or expected_blocks < 0
    ):
        raise InvalidWitness("expected block count must be a nonnegative integer")
    if not isinstance(blocks, (list, tuple)):
        raise InvalidWitness("blocks must be a list or tuple")
    normalized = []
    seen = set()
    for number, block in enumerate(blocks, 1):
        if not isinstance(block, (list, tuple)) or len(block) != k:
            raise InvalidWitness(f"block {number} must contain exactly {k} labels")
        if any(type(label) is not int for label in block):
            raise InvalidWitness(f"block {number}: every label must be an integer")
        if any(label < 1 or label > v for label in block):
            raise InvalidWitness(f"block {number}: labels must lie in 1..{v}")
        if len(set(block)) != k:
            raise InvalidWitness(f"block {number}: labels must be distinct")
        row = tuple(sorted(block))
        if row in seen:
            raise InvalidWitness(f"block {number}: duplicate block")
        seen.add(row)
        normalized.append(row)
    canonical = "".join(
        " ".join(str(label) for label in block) + "\n"
        for block in sorted(normalized)
    ).encode("ascii")
    block_sets = [set(block) for block in normalized]
    multiplicities = Counter()
    uncovered = []
    subset_count = 0
    total_incidences = 0
    for subset in combinations(range(1, v + 1), t):
        required = set(subset)
        count = sum(required <= block for block in block_sets)
        multiplicities[count] += 1
        subset_count += 1
        total_incidences += count
        if count == 0:
            uncovered.append(list(subset))
    cardinality_matches = expected_blocks is None or len(normalized) == expected_blocks
    return {
        "parameters": {"v": v, "k": k, "t": t},
        "blocks": len(normalized),
        "expected_blocks": expected_blocks,
        "cardinality_matches": cardinality_matches,
        "required_subsets": subset_count,
        "covered_subsets": subset_count - len(uncovered),
        "uncovered_count": len(uncovered),
        "uncovered": uncovered,
        "coverage_multiplicities": dict(sorted(multiplicities.items())),
        "total_subset_incidences": total_incidences,
        "expected_subset_incidences": len(normalized) * comb(k, t),
        "point_replication": {
            point: sum(point in block for block in block_sets)
            for point in range(1, v + 1)
        },
        "covers_all_subsets": not uncovered,
        "valid": not uncovered and cardinality_matches,
        "canonical_sha256": sha256(canonical).hexdigest(),
        "canonical_format": "sorted blocks, sorted labels, ASCII space separated, LF terminated",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--v", type=int, default=16)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--t", type=int, default=3)
    parser.add_argument("--expected-blocks", type=int)
    args = parser.parse_args(argv)
    source_hash = None
    try:
        source = args.witness.read_bytes()
        source_hash = sha256(source).hexdigest()
        blocks = parse_witness(source.decode("utf-8"))
        report = verify_cover(blocks, args.v, args.k, args.t, args.expected_blocks)
    except (InvalidWitness, OSError, UnicodeError) as exc:
        print(json.dumps({
            "valid": False, "error": str(exc), "source_sha256": source_hash,
        }, indent=2, sort_keys=True))
        return 2
    report["source_sha256"] = source_hash
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
