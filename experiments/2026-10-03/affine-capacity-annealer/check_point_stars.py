# Document:    Exact Capacity Check for Point-Star Circle Deletions
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b4232c8600826c4e179b64a0112dbf36027dc88e7935337b7cea9ceda984947c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check all16 point-star deletions at31 extensions, without a search."""

import hashlib
import json
import subprocess
from pathlib import Path

import preflight

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-capacity-annealer-20261003"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    gate = json.loads((HERE / "preflight.json").read_text())
    assert gate["passed"] and gate["binary_sha256"] == digest(RAW / "search")
    assert gate["model_sha256"] == digest(RAW / "incidence.txt")
    assert gate["oracle_source_sha256"] == digest(preflight.PRIOR / "run_capacity.py")
    assert gate["geometry_source_sha256"] == digest(preflight.PRIOR / "check.py")
    module = preflight.load_oracle()
    circles, lines = module.geometry()
    rows = []
    for point in range(1, 17):
        ids = [i for i, circle in enumerate(circles) if point in circle]
        assert len(ids) == 15
        mask = sum(1 << i for i in ids)
        value = module.oracle(mask, 11, circles, lines)
        rows.append(
            {
                "point": point,
                "deleted_circles_zero_based": ids,
                "mask": mask,
                "extensions": 31,
                "capacity": value,
                "required_capacity": 150,
            }
        )
    query = "".join(f"{row['mask']} 11\n" for row in rows)
    result = subprocess.run(
        [str(RAW / "search"), str(RAW / "incidence.txt"), "samples"],
        input=query,
        text=True,
        capture_output=True,
        check=True,
        timeout=5,
    )
    assert not result.stderr
    assert list(map(int, result.stdout.split())) == [row["capacity"] for row in rows]
    assert all(row["capacity"] < row["required_capacity"] for row in rows)
    best_intersections = []
    for removed in range(9, 15):
        prior = json.loads((HERE / f"removed-{removed}.json").read_text())
        chosen = [set(circle) for i, circle in enumerate(circles) if prior["best_mask"] >> i & 1]
        common = sorted(set.intersection(*chosen))
        best_intersections.append(
            {
                "removed": removed,
                "best_mask": prior["best_mask"],
                "common_points": common,
                "maximum_point_incidence": max(sum(p in c for c in chosen) for p in range(1, 17)),
            }
        )
    report = {
        "passed": True,
        "source_sha256": digest(Path(__file__)),
        "gate_sha256": digest(HERE / "preflight.json"),
        "point_stars": rows,
        "best_candidate_intersections": best_intersections,
        "solver_calls": 0,
        "scope": "All16 specified point-star deletion sets fail the necessary capacity test. "
        "This does not enumerate all15-circle deletion sets.",
        "global_lower_bound_claim": False,
    }
    (HERE / "point-stars.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "capacities": [r["capacity"] for r in rows],
                "best_candidate_intersections": best_intersections,
                "source_sha256": report["source_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
