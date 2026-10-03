# Document:    Independent Reduced Family Heuristic Verification
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f1bb9ee262a46e5a26bf5477c2d0130ac0324a3a720d18626de6b6495579dfb0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Verify a reduced-family snapshot, even when it is an incomplete cover."""

import argparse
import hashlib
import itertools as it
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDGES = {(4, 5), (4, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)}


def require(value, message):
    if not value:
        raise ValueError(message)


def analyze(text):
    blocks = [tuple(map(int, line.split())) for line in text.splitlines()]
    require(len(blocks) == 64, "expected64 blocks")
    require(all(len(b) == len(set(b)) == 5 and all(1 <= p <= 16 for p in b)
                for b in blocks), "malformed block")
    blocks = sorted(tuple(sorted(b)) for b in blocks)
    require(len(set(blocks)) == 64, "duplicate block")
    require(Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)},
            "not degree20")
    heavy = [b for b in blocks if {1, 2, 3} <= set(b)]
    require(heavy == sorted((1, 2, 3, a, b) for a, b in EDGES), "wrong normalized heavy blocks")
    require(not any(len(set(b) & {1, 2, 3}) == 2 for b in blocks), "two-anchor block")
    local_holes = []
    for anchor in (1, 2, 3):
        family = [tuple(p for p in b if p != anchor) for b in blocks
                  if anchor in b and len(set(b) & {1, 2, 3}) == 1]
        require(len(family) == 13, "wrong local family size")
        require(Counter(p for b in family for p in b) == {p: 4 for p in range(4, 17)},
                "local family degree mismatch")
        pairs = {p for b in family for p in it.combinations(b, 2)}
        missing = set(it.combinations(range(4, 17), 2)) - pairs
        require(missing <= EDGES, "local holes outside allowed graph")
        require(len({p for pair in missing for p in pair}) == 2 * len(missing),
                "local holes not a matching")
        local_holes.append(sorted(missing))
    outside = [b for b in blocks if min(b) >= 4]
    require(len(outside) == 18, "wrong outside block count")
    require(Counter(p for b in outside for p in b) == {p: 6 if p == 4 else 7
                                                    for p in range(4, 17)},
            "wrong outside degrees")
    counts = Counter(t for b in blocks for t in it.combinations(b, 3))
    missing = sorted(set(it.combinations(range(1, 17), 3)) - set(counts))
    require(all(min(t) >= 4 for t in missing), "anchor triple missing")
    canonical = "".join(" ".join(map(str, b)) + "\n" for b in blocks)
    return {"blocks": 64, "holes": len(missing), "missing": missing, "degree20": True,
            "outside_blocks": 18, "normalized_heavy_blocks": 7, "local_holes": local_holes,
            "triple_histogram": dict(Counter(counts[t] for t in
                it.combinations(range(1, 17), 3))),
            "high_triples": [{"triple": t, "multiplicity": n}
                             for t, n in sorted(counts.items()) if n >= 6],
            "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest()}


def verify(path):
    result = analyze(path.read_text())
    match = re.search(r"-h(\d+)\.txt$", path.name)
    if match:
        require(int(match.group(1)) == result["holes"], "filename holes disagree")
    checks = []
    for prefix in [["uv", "run", "covering64", "verify"],
                   [sys.executable, "scripts/check_cover.py"]]:
        command = prefix + [str(path.resolve()), "--expected-blocks", "64"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        data = json.loads(process.stdout)
        require(process.returncode == int(result["holes"] != 0), "verifier exit mismatch")
        require(data["blocks"] == 64 and data["valid"] == (result["holes"] == 0),
                "verifier validity mismatch")
        require(sorted(map(tuple, data["uncovered"])) == result["missing"], "missing list mismatch")
        require(data["canonical_sha256"] == result["canonical_sha256"], "hash mismatch")
        checks.append({"command": command, "exit": process.returncode, "result": data})
    result.update(path=str(path), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  checks=checks)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.candidate)))
