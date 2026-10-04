# Document:    H6 Strict-Hole Radius-Three Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ff688ca1184f0ab7d546e72ce750079fd12ecd4b32d40339371dba5f5fcdc8f8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only runtime accounting check; never invokes the search binary."""

import hashlib
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = HERE.parent / "h6-strict-hole-radius3-pilot"
SCREEN = HERE.parent / "three-deletion-upper-screen"
RAW = ROOT / "experiments/scratch/h6-strict-hole-radius3-pilot-20261004"
MANIFEST_SHA = "e2f01d7116d8795fff4f540a5b3a62eadb5db81f097afc86a7fc1091b3f96ef8"
RESULT_SHA = "075a3f18257a88e3d2a3df2ae759cd3d38ccf79c0fd56caa8a32c37ecb519de8"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(PILOT / "manifest.json") == MANIFEST_SHA
    assert sha(PILOT / "result.json") == RESULT_SHA
    manifest = json.loads((PILOT / "manifest.json").read_text())
    result = json.loads((PILOT / "result.json").read_text())
    launch = json.loads((PILOT / "launch.json").read_text())
    for relative, digest in manifest["pins"].items():
        assert sha(ROOT / relative) == digest, relative
    assert result["manifest_sha256"] == launch["manifest_sha256"] == MANIFEST_SHA
    gate = Path(result["gate_path"])
    assert sha(gate) == result["gate_sha256"]
    gate_data = json.loads(gate.read_text())
    assert gate_data["passed"] and gate_data["launch_permitted"]
    assert gate_data["manifest_sha256"] == MANIFEST_SHA
    for key, value in launch.items():
        if key not in ("validation_passed", "complete_radius3"):
            assert result[key] == value, key
    assert not launch["validation_passed"] and not launch["complete_radius3"]
    assert result["validation_passed"] and result["complete_radius3"]
    assert result["returncode"] == 0 and not result["watchdog"]
    assert 0 < result["elapsed_seconds"] < 60
    assert result["command"] == [
        str(ROOT / manifest["binary_path"]),
        str(ROOT / manifest["input_path"]),
        "6",
        "5",
        str(RAW / "native"),
        "59",
        "64",
    ]
    assert sha(RAW / "stdout.json") == result["stdout_sha256"]
    assert sha(RAW / "stderr.txt") == result["stderr_sha256"]
    assert (RAW / "stderr.txt").read_bytes() == b""
    native = json.loads((RAW / "stdout.json").read_text())
    assert native == result["native_summary"]
    assert native["status"] == "complete" and 0 < native["seconds"] < 59
    assert native["candidates"] == result["candidate_count"] == 0
    assert result["candidates"] == [] and not result["complete_at_most64"]
    assert result["unledgered_raw_candidate_files"] == 0
    assert list((RAW / "native").iterdir()) == [RAW / "native/candidates.tsv"]
    assert not list((PILOT / "candidates").iterdir())
    assert (RAW / "native/candidates.tsv").read_bytes() == (
        b"candidate\tdistance\tholes\tdrop_ids\tadd_ids\n"
    )
    for distance, shell in enumerate(native["shells"], 1):
        assert shell["distance"] == distance and shell["complete"]
        assert shell["deletions"] == math.comb(64, distance)
        assert 0 <= shell["excluded"] <= shell["deletions"]
        assert shell["candidates"] == 0
    assert len(native["shells"]) == 3
    assert [row["excluded"] for row in native["shells"]] == [64, 2011, 41555]
    assert [row["tuples"] for row in native["shells"]] == [0, 22, 31891]
    assert sha(SCREEN / "runs.json") == (
        "1037a8f8a33aa89585800dfffc784815db06f7c1b6d92e3e53d3aff708b74a54"
    )
    replay = json.loads((SCREEN / "replay.json").read_text())
    assert replay["passed"] and replay["checker_sha256"] == sha(SCREEN / "replay.py")
    previous = next(row for row in replay["runs"] if row["name"] == "2d018f-h6")
    shell = native["shells"][2]
    assert shell["deletions"] == previous["deletion_rows_recounted"]
    assert shell["excluded"] == previous["excluded_deletions"]
    assert shell["deletions"] - shell["excluded"] == previous["surviving_deletions"]
    assert shell["tuples"] == previous["necessary_addition_triples"]
    initial_path = ROOT / manifest["input_path"]
    blocks = read_blocks(initial_path)
    assert len(blocks) == len(set(blocks)) == 64
    package = verify_cover(blocks)
    triples = set(itertools.chain.from_iterable(itertools.combinations(b, 3) for b in blocks))
    assert 560 - len(triples) == len(package["uncovered"]) == 6 and not package["valid"]
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(initial_path), "--expected-blocks", "64"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 1 and not process.stderr
    standalone = json.loads(process.stdout)
    assert standalone["blocks"] == 64 and standalone["cardinality_matches"]
    assert standalone["uncovered_count"] == 6 and not standalone["valid"]
    audit = {
        "passed": True,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "result_sha256": RESULT_SHA,
        "rehash_pin_count": len(manifest["pins"]),
        "gate_sha256": sha(gate),
        "launch_sha256": sha(PILOT / "launch.json"),
        "screen_replay_sha256": sha(SCREEN / "replay.json"),
        "ledger_sha256": sha(RAW / "native/candidates.tsv"),
        "native": native,
        "initial_package": package,
        "initial_standalone": standalone,
        "complete_radius3": True,
        "strict_improvement_candidates": 0,
        "screen_k3_counters_match": True,
        "search_reruns": 0,
        "scope": "Runtime receipt, frozen pins, empty candidate ledger and files, shell "
        "completion counters, and prior k3 screen accounting checked. With the separately "
        "reviewed enumerator and independent fixture gate, no at-most5-hole family exists "
        "at exact replacement distance1,2,3 from this named H6 family. "
        "Equal-hole moves and larger neighborhoods remain outside this result.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: audit[key]
                for key in (
                    "passed",
                    "rehash_pin_count",
                    "complete_radius3",
                    "strict_improvement_candidates",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
