# Document:    Affine Capacity Annealer Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      276684d166d55ebdeb2fbe6360cba99bb72660a26aba7e785ea98015f5c0a6cc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read every completed pilot and reject damaged candidate/result controls."""

import copy
import hashlib
import json
from pathlib import Path

import preflight

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-capacity-annealer-20261003"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result, removed):
    preflight.verify_result(result, 10, removed, 2026103991 + removed - 9)
    directory = RAW / f"removed-{removed}"
    raw = json.loads((directory / "result.json").read_text())
    assert all(result[key] == value for key, value in raw.items())
    assert result["passed"] is True and result["covering_witness_claim"] is False
    assert result["source_sha256"] == digest(HERE / "search.cpp") == digest(RAW / "search.cpp")
    assert result["binary_sha256"] == digest(RAW / "search")
    assert result["runner_sha256"] == digest(HERE / "run.py") == digest(directory / "run.py")
    assert result["preflight_sha256"] == digest(HERE / "preflight.json")
    assert result["native_result_sha256"] == digest(directory / "result.json")
    circles, _ = preflight.load_oracle().geometry()
    expected = [
        {
            "mask": row["mask"],
            "circles": [list(c) for i, c in enumerate(circles) if row["mask"] >> i & 1],
        }
        for row in result["survivors"]
    ]
    assert result["survivor_circle_blocks"] == expected


def main():
    results = []
    controls = 0
    for removed in range(9, 15):
        path = HERE / f"removed-{removed}.json"
        result = json.loads(path.read_text())
        inspect(result, removed)
        mutations = [
            ("best_capacity", result["best_capacity"] + 1),
            ("best_mask", result["best_mask"] ^ 1),
            ("seed", 1),
            ("requested_seconds", 9),
            ("accepted", result["accepted"] + 1),
            ("covering_witness_claim", True),
            ("native_result_sha256", "0" * 64),
        ]
        for key, value in mutations:
            damaged = copy.deepcopy(result)
            damaged[key] = value
            try:
                inspect(damaged, removed)
            except (AssertionError, ValueError, KeyError):
                controls += 1
                continue
            raise AssertionError("damaged result accepted")
        results.append(
            {
                "removed": removed,
                "best_capacity": result["best_capacity"],
                "required_capacity": result["required_capacity"],
                "survivors": len(result["survivors"]),
                "iterations": result["iterations"],
                "elapsed_seconds": result["elapsed_seconds"],
                "result_sha256": digest(path),
            }
        )
    report = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "runs": results,
        "damaged_results_rejected": controls,
        "total_proposals": sum(r["iterations"] for r in results),
        "total_native_seconds": sum(r["elapsed_seconds"] for r in results),
        "capacity_survivors": sum(r["survivors"] for r in results),
        "scope": "Heuristic necessary-candidate search only; absence of survivors is inconclusive.",
    }
    (HERE / "readback.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
