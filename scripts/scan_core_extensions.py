# Document:    Bounded core-removal extension scan
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      51c4a8b87159b60bd5dd1c2328903864b3cbebf4051e7c8af31610822210bc8a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compute checked residual duals for one extension of explicit removal sets."""

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
from pathlib import Path

import ortools

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from covering64.core import Universe  # noqa: E402
from scripts.check_core_orbit_certificate import core_actions  # noqa: E402
from scripts.residual_lp import residual_dual  # noqa: E402
from scripts.scan_core_five_removals import checked_bound  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parents", required=True, help="JSON list of explicit removal lists")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args()
    parents = json.loads(args.parents)
    if not isinstance(parents, list) or not 1 <= len(parents) <= 8:
        parser.error("Specify 1 to 8 parent removal sets")
    r = len(parents[0]) + 1
    for parent in parents:
        if (not isinstance(parent, list) or len(parent) != r - 1
                or any(type(i) is not int or not 1 <= i <= 60 for i in parent)
                or parent != sorted(set(parent)) or not 6 <= r <= 8):
            parser.error("Parents must be sorted distinct core indices for levels6 through8")
    args.output.mkdir(parents=True, exist_ok=True)
    args.raw.mkdir(parents=True, exist_ok=True)
    source_path = ROOT / "experiments/2026-10-03/core-orbit/core-remove-4.json.gz"
    source = json.loads(gzip.decompress(source_path.read_bytes()))
    core = [tuple(b) for b in source["core_blocks"]]
    actions = core_actions(core, source["generators"])
    universe = Universe.build()
    index = {b: i for i, b in enumerate(universe.blocks)}
    core_ids = [index[b] for b in core]
    metadata = {"started_utc": datetime.now(timezone.utc).isoformat(),
                "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                          text=True, cwd=ROOT).strip(),
                "python_version": platform.python_version(),
                "ortools_version": ortools.__version__,
                "source_certificate_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                "source_hashes": {}}
    for file in [Path(__file__), ROOT / "scripts/residual_lp.py",
                 ROOT / "scripts/scan_core_five_removals.py",
                 ROOT / "scripts/check_core_orbit_certificate.py"]:
        raw = file.read_bytes()
        metadata["source_hashes"][file.name] = hashlib.sha256(raw).hexdigest()
        (args.raw / file.name).write_bytes(raw)
    cases, candidates, seen = [], [], set()
    started = time.monotonic()
    with (args.raw / "cases.jsonl").open("w") as log:
        for parent in parents:
            for extra in range(1, 61):
                if extra in parent:
                    continue
                removed = [*parent, extra]
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
                if bound <= r + 4:
                    candidates.append({**case, "retained_block_ids": retained,
                                       "retained_core_blocks": [universe.blocks[i]
                                                                for i in retained]})
    metadata["elapsed_seconds"] = time.monotonic() - started
    cases.sort(key=lambda c: (Fraction(*c["lower_bound"]), c["removed"]))
    candidates.sort(key=lambda c: (Fraction(*c["lower_bound"]), c["removed"]))
    data = {"schema": "bounded-core-extension-scan-v1", "target": 64, "removed_count": r,
            "additional_blocks_allowed": r + 4, "core_sha256": source["core_sha256"],
            "core_blocks": core, "generators": source["generators"],
            "parent_removed_sets": parents, "cases": cases, "metadata": metadata,
            "scope": "Only subgroup classes of one-block extensions of the listed parents"}
    for filename, value in [("scan.json.gz", data), ("lp-candidates.json.gz", {
            "scope": "LP dual alone does not decide feasibility", "removed_count": r,
            "additional_blocks_allowed": r + 4, "candidate_count": len(candidates),
            "candidates": candidates})]:
        path = args.output / filename
        path.write_bytes(gzip.compress(json.dumps(value, separators=(",", ":")).encode(), mtime=0))
    print(json.dumps({"removed_count": r, "scanned_classes": len(cases),
                      "lp_candidates": len(candidates), "smallest_dual": cases[0]["lower_bound"],
                      "candidate_removed": [c["removed"] for c in candidates],
                      "elapsed_seconds": metadata["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
