# Document:    Independent Point and Pair Count Diagnostics
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c8f5474fd4edb12f910fcba7ff7ed0a8ceead970d4b8d49c0c1ae34caf3f3ecd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Record necessary-cover count diagnostics without modifying any solver model."""

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "three-core-profile-release"
PAIRS = list(itertools.combinations(range(1, 17), 2))
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recount(path, checksum, expected_holes):
    assert sha(path) == checksum
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
    assert all(
        len(b) == 5 and list(b) == sorted(set(b)) and 1 <= min(b) <= max(b) <= 16 for b in blocks
    )
    degrees = Counter(p for b in blocks for p in b)
    pairs = Counter(pair for b in blocks for pair in itertools.combinations(b, 2))
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    assert sum(degrees.values()) == 320 and sum(pairs.values()) == 640
    assert sum(triples[t] == 0 for t in TRIPLES) == expected_holes
    assert all(
        sum(pairs[tuple(sorted((p, q)))] for q in range(1, 17) if q != p) == 4 * degrees[p]
        for p in range(1, 17)
    )
    below_points = [{"point": p, "degree": degrees[p]} for p in range(1, 17) if degrees[p] < 19]
    below_pairs = [{"pair": list(pair), "count": pairs[pair]} for pair in PAIRS if pairs[pair] < 5]
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": checksum,
        "holes": expected_holes,
        "minimum_point_degree": min(degrees[p] for p in range(1, 17)),
        "minimum_pair_count": min(pairs[pair] for pair in PAIRS),
        "point_degrees": [{"point": p, "degree": degrees[p]} for p in range(1, 17)],
        "pair_counts": [{"pair": list(pair), "count": pairs[pair]} for pair in PAIRS],
        "points_below_19": below_points,
        "number_of_points_below_19": len(below_points),
        "pairs_below_5": below_pairs,
        "number_of_pairs_below_5": len(below_pairs),
        "point_degree_total": 320,
        "pair_count_total": 640,
    }


def main():
    assert not (HERE / "degree-pair-diagnostics.json").exists()
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    post = json.loads((HERE / "postcheck.json").read_text())
    assert post["passed"] and post["manifest_sha256"] == sha(SOURCE / "manifest.json")
    records = []
    for case, audit in zip(manifest["cases"], post["cases"], strict=True):
        assert case["name"] == audit["name"]
        hint = recount(ROOT / case["hint_source_path"], case["hint_sha256"], case["hint_holes"])
        records.append({"case": case["name"], "role": "hint", **hint})
        final = audit["final"]
        checked = recount(ROOT / final["path"], final["sha256"], final["holes"])
        records.append({"case": case["name"], "role": "native_final", **checked})
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "model_changes": False,
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "postcheck_sha256": sha(HERE / "postcheck.json"),
        "records": records,
        "necessary_bounds": {"minimum_point_degree": 19, "minimum_pair_count": 5},
        "proof": (
            "A fixed pair must cover 14 choices of a third point. Each five-block containing "
            "that pair covers three choices, so its count is at least ceil(14/3)=5. For each "
            "point, the sum of its 15 incident pair counts equals four times its degree. "
            "Hence four times its degree is at least 75, so its degree is at least19."
        ),
        "scope": (
            "Exact counts for two existing hints and two checked native finals. These are "
            "necessary conditions for full covers, not for partial candidates. Passing them "
            "would not prove coverage. No constraint was added to the completed pilot."
        ),
    }
    (HERE / "degree-pair-diagnostics.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "passed": True,
                "sha256": sha(HERE / "degree-pair-diagnostics.json"),
                "summary": [
                    {
                        k: r[k]
                        for k in (
                            "case",
                            "role",
                            "holes",
                            "minimum_point_degree",
                            "minimum_pair_count",
                            "number_of_points_below_19",
                            "number_of_pairs_below_5",
                        )
                    }
                    for r in records
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
