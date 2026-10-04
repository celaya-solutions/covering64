# Document:    Independent Affine Circle Transitivity Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
POOL = HERE.parent / "affine-extension-independent/pool.json"
EVIDENCE = ROOT / "experiments/scratch/affine-extension-capacity-20261003/affine-transitivity.json"


def validate(evidence, pool):
    circles = list(map(tuple, pool["circles"]))
    lines = set(map(tuple, pool["lines"]))
    assert evidence["fixed_circle"] == list(circles[0])
    assert len(evidence["maps"]) == 240
    seen, orbit = set(), set()
    for record in evidence["maps"] + evidence["to_fixed_witnesses"]:
        p = record["points_one_based"]
        assert sorted(p) == list(range(1, 17))
        assert {tuple(sorted(p[x - 1] for x in line)) for line in lines} == lines
        mapped = [tuple(sorted(p[x - 1] for x in c)) for c in circles]
        assert set(mapped) == set(circles)
        ids = [circles.index(c) for c in mapped]
        assert ids == record["circles_zero_based"]
        if "deleted_circle_zero_based" in record:
            assert ids[record["deleted_circle_zero_based"]] == 0
        else:
            seen.add(tuple(p))
            orbit.add(ids[0])
    assert len(seen) == 240 and orbit == set(range(48))
    assert len(evidence["to_fixed_witnesses"]) == 48
    assert {r["deleted_circle_zero_based"]
            for r in evidence["to_fixed_witnesses"]} == set(range(48))


def main():
    evidence, pool = json.loads(EVIDENCE.read_text()), json.loads(POOL.read_text())
    validate(evidence, pool)
    damaged = []
    d = copy.deepcopy(evidence)
    d["maps"][0]["points_one_based"][0] = d["maps"][0]["points_one_based"][1]
    damaged.append(d)
    d = copy.deepcopy(evidence)
    d["maps"][0]["circles_zero_based"][0] = 47
    damaged.append(d)
    d = copy.deepcopy(evidence)
    d["to_fixed_witnesses"].pop()
    damaged.append(d)
    for d in damaged:
        try:
            validate(d, pool)
        except AssertionError:
            continue
        raise AssertionError("damaged symmetry certificate accepted")
    report = {"passed": True, "point_permutations": 240, "circle_orbit": 48,
              "to_fixed_witnesses": 48, "damaged_controls_rejected": len(damaged),
              "evidence_sha256": hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(),
              "pool_sha256": hashlib.sha256(POOL.read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Transitivity of the fixed 48-circle pool only; no covering claim"}
    (HERE / "symmetry-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
