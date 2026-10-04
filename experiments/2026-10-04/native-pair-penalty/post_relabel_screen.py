# Document:    Native Pair Penalty Post-Run Relabeled Core Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e913bc9c7ba9b9847854e464aad60561903a644f9192e6c001895f26f8115b84
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Read-only post-run screen using the existing independently audited module."""

import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "six-hole-strong-core-release-independent/relabels.py"
PROOF = HERE.parent / "relabeled-core-filter-proof/audit.json"
POSTCHECK = HERE.parent / "native-pair-penalty-independent/postcheck.json"
EXPECTED = {
    2026104401: "630461e4c8805916ac515114b308d6ed05b2a43da16605ea452150d7e3a784d3",
    2026104402: "a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "post-relabel-screen.json").exists()
    assert sha(SOURCE) == "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"
    assert sha(PROOF) == "dff87420f7dace9498134726725ce6589c306dc01130335a1c868581545872a4"
    assert sha(POSTCHECK) == "7c58bbd14d7a07dafd92fa776e23adcc7d24cd1d2c622755da8c6b7454c8ca32"
    proof, postcheck = json.loads(PROOF.read_text()), json.loads(POSTCHECK.read_text())
    assert proof["passed"] and postcheck["passed"]
    assert proof["scanner_sha256"] == sha(SOURCE)
    spec = importlib.util.spec_from_file_location("audited_relabel_screen", SOURCE)
    screen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(screen)
    records = []
    for seed, digest in EXPECTED.items():
        path = HERE / f"seed-{seed}/search-final-qualified.txt"
        assert sha(path) == digest
        previous = next(
            row
            for row in postcheck["checked"]
            if row["seed"] == seed and row["role"] == "final_qualified"
        )
        assert previous["sha256"] == digest
        assert previous["metrics"]["D3"] == previous["metrics"]["D4"] == 0
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        ids = [screen.RANK[block] for block in blocks]
        result = screen.check(ids)
        counts = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
        pairs = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
        degrees = Counter(point for block in blocks for point in block)
        maximum = max(counts.values())
        if maximum <= 5:
            assert result["necessary_partition_count"] == 0
        result.update(
            seed=seed,
            witness_path=str(path.relative_to(ROOT)),
            witness_sha256=digest,
            checked_metrics=previous["metrics"],
            maximum_triple_multiplicity=maximum,
            pair_count_histogram=dict(sorted(Counter(pairs.values()).items())),
            point_degrees=dict(sorted(degrees.items())),
            elementary_max5_certificate=(
                "Every triple count is at most5, so each of five triples contributes "
                "at least1 to the deficit sum. The sum is at least5 and cannot be at most4."
                if maximum <= 5
                else None
            ),
        )
        records.append(result)
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "caller_sha256": sha(__file__),
        "screen_source_sha256": sha(SOURCE),
        "filter_proof_sha256": sha(PROOF),
        "covering_verifier_postcheck_sha256": sha(POSTCHECK),
        "records": records,
        "scope": (
            "Exact necessary-partition filter for every point relabeling of the particular "
            "audited original60-block core. No construction search or extendability claim. "
            "The242 explicit images are a separate limited check."
        ),
    }
    (HERE / "post-relabel-screen.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({"result_sha256": sha(HERE / "post-relabel-screen.json"), "records": records}))


if __name__ == "__main__":
    main()
