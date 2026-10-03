# Document:    Symmetry-reduced exact residual dual certificate generation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e92f8113173b3e615bf8ae85fecfd8180f4aa99164a985534d53fd9570a6bccb
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Generate exact rational duals; the separate checker establishes their validity."""

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
from scripts.check_core_orbit_certificate import core_actions  # noqa: E402
from scripts.residual_lp import residual_dual  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--removed", type=int, choices=[3, 4], required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/2026-10-03/core-orbit")
    parser.add_argument(
        "--raw", type=Path, default=ROOT / "experiments/scratch/core-orbit-20261003")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.raw.mkdir(parents=True, exist_ok=True)
    prior = ROOT / "experiments/scratch/web-research-1803"
    source = json.loads((prior / "core-automorphisms.json").read_text())
    core_certificate = json.loads((prior / "fixed-core-certificate.json").read_text())
    core = [tuple(b) for b in core_certificate["core_blocks"]]
    generators = source["generators_images_of_1_to_16"]
    actions = core_actions(core, generators)
    unseen = set(combinations(range(1, 61), args.removed))
    representatives = []
    for representative in combinations(range(1, 61), args.removed):
        if representative not in unseen:
            continue
        orbit = {tuple(sorted(action[i - 1] for i in representative)) for action in actions}
        if not orbit <= unseen:
            raise RuntimeError("Invalid orbit partition")
        unseen -= orbit
        representatives.append((representative, len(orbit)))
    universe = Universe.build()
    index = {b: i for i, b in enumerate(universe.blocks)}
    core_ids = [index[b] for b in core]
    cases, failed = [], []
    threshold = args.removed + 4
    started = time.monotonic()
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                   cwd=ROOT, text=True).strip(),
        "python_version": platform.python_version(), "ortools_version": ortools.__version__,
        "solver": "GLOP; floating output converted to exact checked rational weights",
        "sources": {},
    }
    for file in [Path(__file__), ROOT / "scripts/residual_lp.py",
                 ROOT / "scripts/check_core_orbit_certificate.py"]:
        data = file.read_bytes()
        metadata["sources"][file.name] = hashlib.sha256(data).hexdigest()
        (args.raw / f"remove-{args.removed}-{file.name}").write_bytes(data)
    with (args.raw / f"remove-{args.removed}-cases.jsonl").open("w") as log:
        for number, (removed, orbit_size) in enumerate(representatives, 1):
            retained = [b for i, b in enumerate(core_ids, 1) if i not in removed]
            dual = residual_dual(universe, retained)
            denominator = math.lcm(*(w[2] for w in dual["weights"])) if dual["weights"] else 1
            weights = [[t, n * (denominator // d)] for t, n, d in dual["weights"]]
            case = {"removed": list(removed), "orbit_size": orbit_size,
                    "denominator": denominator, "weights": weights,
                    "lp_status": dual["lp_status"]}
            bound = Fraction(sum(n for _, n in weights), denominator)
            if bound <= threshold:
                failed.append({"removed": removed, "bound": str(bound)})
            cases.append(case)
            log.write(json.dumps(case, separators=(",", ":")) + "\n")
            if number % 100 == 0 or number == len(representatives):
                print(json.dumps({"removed": args.removed, "done": number,
                                  "total": len(representatives), "uncertified": len(failed),
                                  "elapsed": time.monotonic() - started}), flush=True)
    metadata["elapsed_seconds"] = time.monotonic() - started
    data = {"schema": "core-orbit-dual-v1", "target": 64, "removed_count": args.removed,
            "core_sha256": core_certificate["core_sha256"], "core_blocks": core,
            "generators": generators, "claimed_complete": not failed,
            "cases": cases, "metadata": metadata}
    raw = json.dumps(data, separators=(",", ":")).encode()
    target = args.output / f"core-remove-{args.removed}.json.gz"
    target.write_bytes(gzip.compress(raw, mtime=0))
    (args.raw / f"remove-{args.removed}-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"certificate": str(target),
                      "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                      "bytes": target.stat().st_size, "uncertified": failed}), flush=True)


if __name__ == "__main__":
    main()
