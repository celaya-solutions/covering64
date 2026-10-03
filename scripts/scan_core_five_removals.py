# Document:    Restricted five-removal core extension scan
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cab7d0e78bc30f3f98cc52eb7abe9b52028e3accd7d83127042c9319d72ff03e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Scan extensions of a few smallest-bound four-removal representatives."""

import argparse
import gzip
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from covering64.core import Universe  # noqa: E402
from scripts.check_core_orbit_certificate import check_data, core_actions  # noqa: E402
from scripts.residual_lp import residual_dual  # noqa: E402


def checked_bound(core, removed, weights, denominator):
    """Check each dual directly using independent lexicographic enumeration."""
    triples = list(combinations(range(1, 17), 3))
    retained_coverage = {t for i, b in enumerate(core, 1) if i not in removed
                         for t in combinations(b, 3)}
    by_triple = {}
    for index, numerator in weights:
        triple = triples[index]
        if triple in retained_coverage or triple in by_triple or numerator <= 0:
            raise ValueError("Invalid weighted triple")
        by_triple[triple] = numerator
    if any(sum(by_triple.get(t, 0) for t in combinations(block, 3)) > denominator
           for block in combinations(range(1, 17), 5)):
        raise ValueError("Block capacity exceeded")
    return Fraction(sum(by_triple.values()), denominator)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parents", type=int, default=20)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "experiments/2026-10-03/core-five-scan")
    parser.add_argument("--raw", type=Path,
                        default=ROOT / "experiments/scratch/core-five-scan-20261003")
    args = parser.parse_args()
    if not 1 <= args.parents <= 100:
        parser.error("--parents must be between 1 and 100")
    args.output.mkdir(parents=True, exist_ok=True)
    args.raw.mkdir(parents=True, exist_ok=True)
    path = ROOT / "experiments/2026-10-03/core-orbit/core-remove-4.json.gz"
    source = json.loads(gzip.decompress(path.read_bytes()))
    checked = check_data(source)
    if not checked["complete_obstruction"]:
        raise ValueError("Source four-removal proof was not complete")
    core = [tuple(b) for b in source["core_blocks"]]
    actions = core_actions(core, source["generators"])
    parents = sorted(source["cases"], key=lambda c: (
        Fraction(sum(n for _, n in c["weights"]), c["denominator"]), c["removed"]
    ))[:args.parents]
    universe = Universe.build()
    index = {block: i for i, block in enumerate(universe.blocks)}
    core_ids = [index[block] for block in core]
    seen, cases, candidates = set(), [], []
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                  text=True, cwd=ROOT).strip(),
        "python_version": platform.python_version(), "ortools_version": ortools.__version__,
        "source_certificate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_hashes": {},
    }
    for file in [Path(__file__), ROOT / "scripts/residual_lp.py",
                 ROOT / "scripts/check_core_orbit_certificate.py"]:
        raw = file.read_bytes()
        metadata["source_hashes"][file.name] = hashlib.sha256(raw).hexdigest()
        (args.raw / file.name).write_bytes(raw)
    start = time.monotonic()
    with (args.raw / "cases.jsonl").open("w") as log:
        for parent_number, parent in enumerate(parents, 1):
            for extra in range(1, 61):
                if extra in parent["removed"]:
                    continue
                removed = tuple(sorted([*parent["removed"], extra]))
                representative = min(tuple(sorted(action[i - 1] for i in removed))
                                     for action in actions)
                if representative in seen:
                    continue
                seen.add(representative)
                retained = [b for i, b in enumerate(core_ids, 1) if i not in representative]
                dual = residual_dual(universe, retained)
                denominator = math.lcm(*(d for _, _, d in dual["weights"]))
                weights = [[t, n * (denominator // d)] for t, n, d in dual["weights"]]
                bound = checked_bound(core, representative, weights, denominator)
                case = {"removed": representative, "denominator": denominator,
                        "weights": weights, "lower_bound": [bound.numerator, bound.denominator],
                        "lp_status": dual["lp_status"]}
                cases.append(case)
                log.write(json.dumps(case, separators=(",", ":")) + "\n")
                if bound <= 9:
                    candidates.append({**case, "retained_block_ids": retained,
                                       "retained_core_blocks": [universe.blocks[i]
                                                                for i in retained]})
            print(json.dumps({"parents_done": parent_number, "cases": len(cases),
                              "dual_at_most_9": len(candidates),
                              "elapsed": time.monotonic() - start}), flush=True)
    metadata["elapsed_seconds"] = time.monotonic() - start
    data = {"schema": "restricted-core-five-removal-scan-v1", "target": 64,
            "removed_count": 5, "additional_blocks_allowed": 9,
            "scope": "Only extensions of explicitly listed four-removal representatives",
            "core_sha256": source["core_sha256"], "core_blocks": core,
            "generators": source["generators"],
            "parent_removed_sets": [parent["removed"] for parent in parents],
            "cases": cases, "metadata": metadata}
    output = args.output / "five-removal-scan.json.gz"
    output.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode(), mtime=0))
    candidates.sort(key=lambda c: (Fraction(*c["lower_bound"]), c["removed"]))
    candidate_output = args.output / "lp-uncertified-candidates.json.gz"
    candidate_output.write_bytes(gzip.compress(json.dumps({
        "scope": "LP dual does not rule out completion; feasibility remains unknown",
        "additional_blocks_allowed": 9, "candidate_count": len(candidates),
        "candidates": candidates,
    }, separators=(",", ":")).encode(), mtime=0))
    print(json.dumps({"scan": str(output),
                      "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                      "cases": len(cases), "lp_uncertified": len(candidates),
                      "best_dual": candidates[0]["lower_bound"] if candidates else None}),
          flush=True)


if __name__ == "__main__":
    main()
