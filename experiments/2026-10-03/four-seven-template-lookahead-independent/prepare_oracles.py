# Document:    Fresh Heavy-Tuple Lookahead Oracle Fixtures
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e0f39d65cf705bd6528d94d9e0a70229a2b6da8db750e99dc79bb346040e6fea
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import json
import random
from pathlib import Path

from oracle import ANCHORS, ORDINARY, analyze, heavy_blocks, require

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-lookahead-independent-v1.0.0"
SOFT = HERE.parent / "four-seven-template-native-soft"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    require(not RAW.exists(), "fresh oracle directory required")
    RAW.mkdir(parents=True)
    inputs = json.loads((SOFT / "seeds.json").read_text())["cases"]
    summary = json.loads((SOFT / "summary.json").read_text())
    rng = random.Random(2026104201)
    reports = []
    for case in inputs:
        name = case["name"]
        catalog_path = ROOT / case["source_catalog_path"]
        require(sha(catalog_path) == case["source_catalog_sha256"], "catalog changed")
        catalog = json.loads(gzip.decompress(catalog_path.read_bytes()))
        seed_path = SOFT / (name + "-raw-best.txt")
        baseline = next(c for c in summary["cases"] if c["name"] == name)["bests"]["raw"]
        require(sha(seed_path) == baseline["sha256"], "baseline changed")
        blocks = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
        heavy_blocks(blocks)
        free = [block for block in blocks if block in ORDINARY]
        require(len(free) == 36, "baseline ordinary count")
        for trial in range(16):
            indices = [rng.randrange(len(group["templates"])) for group in catalog]
            fixed = []
            for group, index in enumerate(indices):
                fixed.extend(
                    tuple(sorted(ANCHORS[group] | set(edge)))
                    for edge in catalog[group]["templates"][index]
                )
            fixture = sorted(fixed + free)
            verified_heavy = heavy_blocks(fixture)
            path = RAW / f"{name}-tuple-{trial:02d}.txt"
            path.write_text("".join(" ".join(map(str, block)) + "\n" for block in fixture))
            expected = analyze(verified_heavy)
            expected_path = path.with_suffix(".expected.json.gz")
            expected_path.write_bytes(gzip.compress(json.dumps(expected).encode(), mtime=0))
            reports.append(
                {
                    "case": name,
                    "trial": trial,
                    "template_ids_1based": [i + 1 for i in indices],
                    "state": str(path.relative_to(ROOT)),
                    "state_sha256": sha(path),
                    "expected": str(expected_path.relative_to(ROOT)),
                    "expected_sha256": sha(expected_path),
                    "catalog": case["catalog_path"],
                    "catalog_sha256": case["catalog_sha256"],
                    "allowed_ordinary": expected["allowed_ordinary"],
                    "unsupported_count": expected["unsupported_count"],
                }
            )
    result = {
        "seed": 2026104201,
        "generator_sha256": sha(Path(__file__)),
        "oracle_sha256": sha(HERE / "oracle.py"),
        "fresh_tuples": reports,
        "scope": "Fresh independent oracle fixtures only; native comparison pending.",
    }
    (HERE / "oracle-fixtures.json").write_text(json.dumps(result, indent=2) + "\n")
    (RAW / "oracle-fixtures.json").write_text(json.dumps(result, indent=2) + "\n")
    (RAW / "oracle.py").write_bytes((HERE / "oracle.py").read_bytes())
    (RAW / "prepare_oracles.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "fresh_tuples": len(reports),
                "unsupported_counts": [r["unsupported_count"] for r in reports],
            }
        )
    )


if __name__ == "__main__":
    main()
