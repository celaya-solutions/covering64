#!/usr/bin/env python3
# Document:    Standalone exact core obstruction checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check rational dual certificates with only the Python standard library."""

import argparse
import gzip
import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations
from pathlib import Path


def integer(value):
    if type(value) is not int:
        raise ValueError("Expected an integer")
    return value


def check(path):
    raw = path.read_bytes()
    data = json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)
    if tuple(data.get(k) for k in ("v", "k", "t", "target")) != (16, 5, 3, 64):
        raise ValueError("Unsupported parameters")
    core = []
    for row in data["core"]:
        block = tuple(integer(p) for p in row)
        if len(block) != 5 or tuple(sorted(set(block))) != block:
            raise ValueError("Malformed core block")
        if not all(1 <= p <= 16 for p in block):
            raise ValueError("Core label out of range")
        core.append(block)
    if len(core) != 60 or len(set(core)) != 60:
        raise ValueError("Expected 60 distinct core blocks")
    triples = list(combinations(range(1, 17), 3))
    lookup = {t: i for i, t in enumerate(triples)}
    containing = [[] for _ in triples]
    for b, block in enumerate(combinations(range(1, 17), 5)):
        for triple in combinations(block, 3):
            containing[lookup[triple]].append(b)
    maximum = integer(data["maximum_removed"])
    if not 0 <= maximum <= 3:
        raise ValueError("Unsupported removal budget")
    expected = {c for r in range(maximum + 1) for c in combinations(range(60), r)}
    if len(data["records"]) != len(expected):
        raise ValueError("Certificate is incomplete")
    minimum = None
    for record in data["records"]:
        removed = tuple(integer(i) for i in record["removed_core_indices"])
        if removed not in expected:
            raise ValueError("Repeated, malformed, or unexpected neighborhood")
        expected.remove(removed)
        covered = {lookup[t] for i, b in enumerate(core) if i not in removed
                   for t in combinations(b, 3)}
        weights = {}
        for t, n, d in record["weights"]:
            t, n, d = integer(t), integer(n), integer(d)
            if not 0 <= t < 560 or t in weights or t in covered or n <= 0 or d <= 0:
                raise ValueError("Invalid positive weight on an uncovered triple")
            weights[t] = Fraction(n, d)
        denominator = math.lcm(*(w.denominator for w in weights.values()))
        loads = [0] * 4368
        for t, w in weights.items():
            numerator = w.numerator * (denominator // w.denominator)
            for block in containing[t]:
                loads[block] += numerator
        if max(loads) > denominator:
            raise ValueError("A possible added block exceeds unit dual capacity")
        bound = sum(weights.values(), Fraction(0))
        n, d = map(integer, record["lower_bound"])
        if d <= 0 or Fraction(n, d) != bound:
            raise ValueError("Claimed bound differs from exact sum")
        budget = 64 - (60 - len(removed))
        margin = bound - budget
        if margin <= 0:
            raise ValueError("Weights do not rule out this neighborhood")
        minimum = margin if minimum is None else min(minimum, margin)
    if expected:
        raise ValueError("Not all requested neighborhoods were checked")
    return {"valid": True, "checked_neighborhoods": len(data["records"]),
            "minimum_exact_margin": str(minimum), "required_core_deletions": maximum + 1,
            "scope": "Any 64-block cover must omit this many of these specific 60 core blocks",
            "certificate_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.certificate), indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        raise SystemExit(1) from exc
