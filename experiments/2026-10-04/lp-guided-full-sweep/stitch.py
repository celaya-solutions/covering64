# Document:    Cover Checks for Heavy-Tuple Improvements with Original Ordinary Blocks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c30c88663989778994494a25cc5d758380a0cd9775838d3c7bd7bfe6989c19fd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Report integer stitched families separately from elastic LP objectives."""

import argparse
import hashlib
import itertools as it
import json
import subprocess
import sys
from pathlib import Path

from covering64.core import read_blocks, verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]
SEED = (
    ROOT / "experiments/2026-10-03/four-seven-template-native-lookahead/performance-cycle-best.txt"
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text())
    assert not args.output.exists()
    args.output.mkdir()
    assert sha(SEED) == "8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3"
    anchors = [set(range(a, a + 3)) for a in (1, 5, 9, 13)]
    ordinary = [b for b in read_blocks(SEED) if all(len(set(b) & a) <= 1 for a in anchors)]
    assert len(ordinary) == 36
    universe = list(it.combinations(range(1, 17), 5))
    required = set(it.combinations(range(1, 17), 3))
    best = data["initial_objective"]
    checked = []
    records = data.get("records")
    if records is None:
        records = [record for round_result in data["rounds"] for record in round_result["records"]]
    for record in records:
        if record["status"] != "OPTIMAL" or record["objective"] >= best - 1e-7:
            continue
        best = record["objective"]
        heavy = [universe[index] for index in record["heavy_global_ids"]]
        blocks = sorted(heavy + ordinary)
        assert len(blocks) == len(set(blocks)) == 64
        missing = sorted(
            required - {triple for block in blocks for triple in it.combinations(block, 3)}
        )
        path = args.output / f"improvement-{len(checked) + 1:02d}-h{len(missing)}.txt"
        write_blocks(path, blocks)
        package = verify_cover(blocks)
        standalone = subprocess.run(
            [
                sys.executable,
                "-I",
                str(ROOT / "scripts/check_cover.py"),
                str(path),
                "--expected-blocks",
                "64",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert standalone.returncode == (1 if missing else 0) and not standalone.stderr
        separate = json.loads(standalone.stdout)
        assert package["uncovered"] == missing and separate["uncovered"] == [
            list(t) for t in missing
        ]
        assert package["valid"] == separate["valid"] == (not missing)
        assert package["canonical_sha256"] == separate["canonical_sha256"] == sha(path)
        checked.append(
            {
                "elastic_objective": best,
                "rank": record["rank"],
                "heavy_sha256": record["heavy_sha256"],
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "blocks": 64,
                "uncovered": missing,
                "holes": len(missing),
                "cover": not missing,
                "both_verifiers_agree": True,
            }
        )
    report = {
        "source_sha256": sha(__file__),
        "result_sha256": sha(args.result),
        "ordinary_source_sha256": sha(SEED),
        "original_ordinary_blocks": ordinary,
        "accepted_improvements": checked,
        "scope": (
            "Original 36 ordinary blocks stitched to each accepted improving heavy tuple; "
            "no integer search."
        ),
    }
    (args.output / "checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "accepted_improvements": len(checked),
                "hole_counts": [row["holes"] for row in checked],
                "cover_found": any(row["cover"] for row in checked),
            }
        )
    )


if __name__ == "__main__":
    main()
