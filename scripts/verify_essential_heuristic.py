#!/usr/bin/env python3
# Document:    Independent Verification of Essential Regular Heuristic Candidates
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cd4cab7fb33223a8a829596517253c0200da7077bd9f298af9d689fe88b4520a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount regularity, private triples and pair deficits, then run both verifiers.

Distinct invariant fingerprints certify nonisomorphism. Equal fingerprints do
not certify isomorphism and no completeness claim about near-covers is made.
"""

import argparse
import gzip
import hashlib
import itertools
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"-h(\d+)-u(\d+)-p(\d+)\.txt$")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def analyze(text):
    blocks = [tuple(map(int, row.split())) for row in text.splitlines()]
    require(len(blocks) == 64, "expected64 blocks")
    require(all(len(b) == len(set(b)) == 5 and all(1 <= x <= 16 for x in b)
                for b in blocks), "malformed block")
    normalized = sorted(tuple(sorted(b)) for b in blocks)
    require(len(set(normalized)) == 64, "duplicate block")
    replication = Counter(x for b in normalized for x in b)
    require(replication == {x: 20 for x in range(1, 17)}, "not degree20")
    triple_counts = Counter(t for b in normalized for t in itertools.combinations(b, 3))
    pair_counts = Counter(p for b in normalized for p in itertools.combinations(b, 2))
    missing = [t for t in itertools.combinations(range(1, 17), 3) if not triple_counts[t]]
    unsupported = []
    private_histogram = Counter()
    for index, block in enumerate(normalized):
        private = [t for t in itertools.combinations(block, 3) if triple_counts[t] == 1]
        private_histogram[len(private)] += 1
        supported_points = {x for triple in private for x in triple}
        unsupported.extend((index + 1, x) for x in block if x not in supported_points)
    pair_deficit = sum(max(0, 5 - pair_counts[p])
                       for p in itertools.combinations(range(1, 17), 2))
    triple_histogram = Counter(triple_counts[t]
                               for t in itertools.combinations(range(1, 17), 3))
    heavy_excess = max(0, 3 * triple_histogram[6] + 4 * triple_histogram[7] - 16)
    heavy_excess += sum(8 * max(0, count - 7) for count in triple_counts.values())
    pair_histogram = Counter(pair_counts[p]
                             for p in itertools.combinations(range(1, 17), 2))
    missing_degree = Counter(x for t in missing for x in t)
    fingerprint = (
        [triple_histogram[i] for i in range(65)]
        + [pair_histogram[i] for i in range(65)]
        + [private_histogram[i] for i in range(11)]
        + sorted(missing_degree[x] for x in range(1, 17))
    )
    canonical = "".join(" ".join(map(str, b)) + "\n" for b in normalized).encode()
    return {"holes": len(missing), "unsupported_count": len(unsupported),
            "pair_deficit": pair_deficit, "degree20": True, "missing": missing,
            "unsupported_incidences": unsupported, "pair_histogram": dict(pair_histogram),
            "triple_histogram": dict(triple_histogram),
            "heavy_excess": heavy_excess,
            "private_count_histogram": dict(private_histogram),
            "invariant_fingerprint": fingerprint, "invariant_sha256": digest(fingerprint),
            "canonical_sha256": hashlib.sha256(canonical).hexdigest()}


def verify(path):
    raw = path.read_bytes()
    result = analyze(raw.decode())
    heavy_match = re.search(r"-heavy-e(\d+)-h", path.name)
    if heavy_match:
        require(int(heavy_match.group(1)) == result["heavy_excess"],
                "filename heavy score mismatch")
    match = NAME.search(path.name)
    if match:
        require(list(map(int, match.groups())) == [result["holes"], result["unsupported_count"],
                                                  result["pair_deficit"]],
                "filename score mismatch")
    checks = []
    for prefix in [["uv", "run", "covering64", "verify"],
                   ["uv", "run", "python", "scripts/check_cover.py"]]:
        command = prefix + [str(path.resolve()), "--expected-blocks", "64"]
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        data = json.loads(process.stdout)
        require(process.returncode == int(result["holes"] != 0), "verifier exit disagreement")
        require(data["blocks"] == 64 and data["valid"] == (result["holes"] == 0),
                "verifier validity disagreement")
        require(data["canonical_sha256"] == result["canonical_sha256"], "verifier hash mismatch")
        require(sorted(map(tuple, data["uncovered"])) == result["missing"], "coverage mismatch")
        covered = data["covered"] if "covered" in data else data["covered_subsets"]
        require(covered == 560 - result["holes"], "covered count mismatch")
        checks.append({"command": command, "exit": process.returncode, "result": data})
    result.update({"path": str(path), "source_sha256": hashlib.sha256(raw).hexdigest(),
                   "checks": checks})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite report")
    paths = sorted(p for p in args.directory.rglob("*.txt") if NAME.search(p.name))
    results = [verify(path) for path in paths]
    essential = [r for r in results if r["unsupported_count"] == r["pair_deficit"] == 0]
    invariant_representatives = {}
    for r in essential:
        invariant_representatives.setdefault(r["invariant_sha256"], r["path"])
    body = {"scope": "Checked saved candidates only; no completeness or impossibility claim",
            "candidate_count": len(results), "valid_covers": sum(r["holes"] == 0 for r in results),
            "point_essential_pair_feasible_candidates": len(essential),
            "distinct_invariant_classes": len(invariant_representatives),
            "invariant_representatives": invariant_representatives,
            "best_essential_pair_feasible_holes": min(
                (r["holes"] for r in essential), default=None),
            "checker_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "candidate_checks": results}
    header = {"Document": "Independent Essential Regular Candidate Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": digest(body), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    encoded = json.dumps({"document_header": header, "body": body},
                         sort_keys=True, separators=(",", ":")).encode()
    args.output.write_bytes(gzip.compress(encoded + b"\n", mtime=0))
    print(json.dumps({k: body[k] for k in ["candidate_count", "valid_covers",
          "distinct_invariant_classes", "best_essential_pair_feasible_holes"]}))


if __name__ == "__main__":
    main()
