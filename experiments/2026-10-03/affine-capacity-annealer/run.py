# Document:    Affine Circle Deletion Annealer Pilot Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      248aafe4c3626358e625e33f5d847d919f0bec64fdae56e9cfd4e8b2ddbf4306
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run one approved ten-second case; independently recount every saved candidate."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import preflight

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-capacity-annealer-20261003"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--removed", required=True, type=int, choices=range(9, 15))
    args = parser.parse_args()
    gate = json.loads((HERE / "preflight.json").read_text())
    assert gate["passed"] and gate["source_sha256"] == digest(HERE / "search.cpp") == digest(
        RAW / "search.cpp"
    )
    assert gate["preflight_source_sha256"] == digest(HERE / "preflight.py")
    assert gate["model_sha256"] == digest(RAW / "incidence.txt")
    assert gate["binary_sha256"] == digest(RAW / "search")
    assert gate["oracle_source_sha256"] == digest(preflight.PRIOR / "run_capacity.py")
    assert gate["geometry_source_sha256"] == digest(preflight.PRIOR / "check.py")
    assert gate["transitivity_sha256"] == digest(preflight.PRIOR_RAW / "affine-transitivity.json")
    destination = RAW / f"removed-{args.removed}"
    assert not destination.exists(), "preserve previous pilot"
    destination.mkdir()
    (destination / "run.py").write_bytes(Path(__file__).read_bytes())
    seed = 2026103991 + args.removed - 9
    command = [
        str(RAW / "search"),
        str(RAW / "incidence.txt"),
        "run",
        str(args.removed),
        str(seed),
        "10",
    ]
    native = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, timeout=15, check=True
    )
    assert not native.stderr
    (destination / "result.json").write_text(native.stdout)
    result = json.loads(native.stdout)
    preflight.verify_result(result, 10, args.removed, seed)
    circles, _ = preflight.load_oracle().geometry()
    result["survivor_circle_blocks"] = [
        {"mask": row["mask"], "circles": [c for i, c in enumerate(circles) if row["mask"] >> i & 1]}
        for row in result["survivors"]
    ]
    result.update(
        {
            "passed": True,
            "utc": datetime.now(timezone.utc).isoformat(),
            "source_sha256": digest(HERE / "search.cpp"),
            "binary_sha256": digest(RAW / "search"),
            "runner_sha256": digest(Path(__file__)),
            "preflight_sha256": digest(HERE / "preflight.json"),
            "native_result_sha256": digest(destination / "result.json"),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "scope": gate["scope"],
            "covering_witness_claim": False,
        }
    )
    (HERE / f"removed-{args.removed}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
