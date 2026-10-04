# Document:    Independent Affine Extension Capacity Audit Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools
import json
import math
import random
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-capacity-independent-v1.0.0"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pool_path = HERE.parent / "affine-extension-independent/pool.json"
    data = json.loads(pool_path.read_text())
    circles = list(map(set, data["circles"]))
    lines = list(map(set, data["lines"]))
    assert len(circles) == 48 and len(lines) == 20
    # Recount using actual triple sets rather than the native intersection mask.
    circle_triples = [{tuple(t) for t in itertools.combinations(sorted(c), 3)} for c in circles]
    assert len(set().union(*circle_triples)) == sum(map(len, circle_triples)) == 480
    extensions = [[line | {p} for p in range(1, 17) if p not in line] for line in lines]
    assert len({tuple(sorted(b)) for group in extensions for b in group}) == 240
    masks = []
    for group in extensions:
        row = []
        for block in group:
            triples = set(itertools.combinations(sorted(block), 3))
            hits = [len(triples & ts) for ts in circle_triples]
            assert set(hits) <= {0, 1} and sum(hits) == 6
            row.append(sum(value << i for i, value in enumerate(hits)))
        masks.append(row)
    input_path = RAW / "masks.txt"
    input_path.write_text("\n".join(" ".join(map(str, row)) for row in masks) + "\n")
    binary = RAW / "capacity"
    rng = random.Random(2026104201)
    cases, expected = [], []
    for size in [0, 1, 2, 4, 5, 6, 12, 24, 47, 48]:
        for _ in range(5):
            deleted = sorted(rng.sample(range(48), size))
            for extra in [0, 1, 2, 5, 20, 220]:
                # Independently materialize all 240 actual intersection scores,
                # sort each line, then sort its 11 remaining scores globally.
                rows = [sorted((sum(len(block & circles[i]) == 3 for i in deleted)
                                for block in group), reverse=True) for group in extensions]
                wanted = sum(row[0] for row in rows) + sum(
                    sorted((v for row in rows for v in row[1:]), reverse=True)[:extra])
                expected.append(wanted)
                cases.append((sum(1 << i for i in deleted), extra))
    queries = "".join(f"{mask} {extra}\n" for mask, extra in cases)
    control = subprocess.run([str(binary), str(input_path), "samples"], input=queries,
                             text=True, capture_output=True, check=True)
    assert list(map(int, control.stdout.split())) == expected
    invalid_inputs = ["", "0 " * 240, "63 " * 239, "63 " * 241,
                      f"{1 << 48} " * 240, "-1 " * 240, "garbage " * 240]
    for i, content in enumerate(invalid_inputs):
        path = RAW / f"invalid-{i}.txt"
        path.write_text(content)
        result = subprocess.run([str(binary), str(path), "samples"], capture_output=True)
        assert result.returncode == 2
    invalid_queries = [f"{1 << 48} 1\n", "1 -1\n", "1 221\n"]
    for query in invalid_queries:
        assert subprocess.run([str(binary), str(input_path), "samples"], input=query,
                              text=True, capture_output=True).returncode == 2
    start = time.monotonic()
    result = subprocess.run([str(binary), str(input_path), "all-five"], text=True,
                            capture_output=True, timeout=120, check=True)
    wall = time.monotonic() - start
    (RAW / "stdout.json").write_text(result.stdout)
    (RAW / "stderr.log").write_text(result.stderr)
    report = json.loads(result.stdout)
    assert report["deletion_sets"] == math.comb(48, 5)
    assert sum(report["histogram"].values()) == report["deletion_sets"]
    report.update({
        "passed": True, "maximum_capacity": max(map(int, report["histogram"])),
        "required_incidence": 50, "extensions": 21, "retained_circles": 43,
        "controls": len(cases), "damaged_controls_rejected": 10,
        "wall_seconds": wall, "pool_sha256": digest(pool_path),
        "native_source_sha256": digest(HERE / "capacity.cpp"),
        "binary_sha256": digest(binary), "runner_sha256": digest(Path(__file__)),
        "input_sha256": digest(input_path),
        "compiler": subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0],
        "compiler_flags": ["-std=c++20", "-O3", "-Wall", "-Wextra", "-Wpedantic"],
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "All five-circle omissions in this fixed 48-circle/240-extension pool; "
                 "no symmetry or pair pruning",
        "exclusion": max(map(int, report["histogram"])) < 50,
        "global_lower_bound_claim": False,
    })
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
