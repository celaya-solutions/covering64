# Document:    H6 Exact-Distance-Four Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      56f996ba28702f89cd6d73d31605b61e6f08350934ac5e6b40506695a97e2995
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved runtime evidence; no native search or prefix is rerun."""

import csv
import hashlib
import itertools
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = HERE.parent / "h6-strict-hole-radius4-prefix-pilot"
RAW = ROOT / "experiments/scratch/h6-strict-hole-radius4-prefix-pilot-20261004"
MANIFEST_SHA = "05d72d833e4005aad2b06af0bc4064bd03fac53a2c3030009f2665efd9c77111"
RESULT_SHA = "88690b98d6bafba7955139e5f059a2ff0a6433301b9acd184e33318b0adcadb6"
GATE_SHA = "57dbbdc7d8cf7eb51cf8df6a9bea8d59c4f5642d9ef71ef1ed2d41c6b10fc4c5"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recount_family(row, manifest):
    path = ROOT / row["path"]
    assert sha(path) == row["sha256"]
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert blocks == sorted(set(blocks)) and len(blocks) == 64
    assert all(
        len(b) == 5 and b == tuple(sorted(set(b))) and 1 <= b[0] <= b[-1] <= 16 for b in blocks
    )
    ids = [RANK[b] for b in blocks]
    assert ids == row["ids"]
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode in (0, 1) and not process.stderr
    standalone = json.loads(process.stdout)
    counts = {
        n: Counter(q for b in blocks for q in itertools.combinations(b, n)) for n in (2, 3, 4)
    }
    holes = 560 - len(counts[3])
    assert len(package["uncovered"]) == standalone["uncovered_count"] == holes
    assert package["valid"] == standalone["valid"] == (process.returncode == 0) == (holes == 0)
    assert standalone["cardinality_matches"] and standalone["blocks"] == 64
    d2max = d2sum = d3 = d4 = 0
    for pair in itertools.combinations(range(1, 17), 2):
        support = counts[2][pair]
        remaining = [p for p in range(1, 17) if p not in pair]
        deficits = []
        for a, b in itertools.combinations(remaining, 2):
            ca = counts[3][tuple(sorted((*pair, a)))]
            cb = counts[3][tuple(sorted((*pair, b)))]
            deficits.append(max(0, 12 - 3 * support + ca + cb))
            q = counts[4][tuple(sorted((*pair, a, b)))]
            d4 += max(0, 12 - 3 * support + 2 * q)
        d2max += max(deficits)
        d2sum += sum(deficits)
        d3 += sum(
            max(0, 13 - 3 * support + counts[3][tuple(sorted((*pair, p)))]) for p in remaining
        )
    overlaps = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
    sixth = len(set(ids) & set(manifest["sixth_cap"]["ids"]))
    minimum = min(counts[2][p] for p in itertools.combinations(range(1, 17), 2))
    metrics = {"cardinality": 64, "holes": holes, "core_overlaps": overlaps}
    weak = {
        "cardinality": 64,
        "holes": holes,
        "core_overlaps": overlaps[:4],
        "D2max": d2max,
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "minimum_pair_count": minimum,
    }
    assert row["metrics"] == metrics and row["weak_metrics"] == weak
    assert manifest["sixth_cap"]["threshold"] == 59
    sixth_pass = sixth <= 59
    six_pass = all(x <= cap for x, cap in zip(overlaps, (55, 55, 55, 55, 56))) and sixth_pass
    qualified = six_pass and holes <= 11 and minimum >= 5 and d3 == d4 == 0
    assert row["sixth_named_overlap"] == sixth
    assert row["sixth_named_cap_applies"] is True and row["sixth_named_cap_pass"] == sixth_pass
    assert row["six_named_caps_pass"] == six_pass and row["weak_six_cap_qualified"] == qualified
    assert row["qualified_rank"] == ([holes, d2max] if qualified else None)
    assert row["complete_at_most64"] == (holes == 0)
    return {
        "path": row["path"],
        "sha256": row["sha256"],
        "metrics": metrics,
        "weak_metrics": weak,
        "six_overlaps": [*overlaps, sixth],
        "six_caps_pass": six_pass,
        "weak_six_cap_qualified": qualified,
        "package": package,
        "standalone": standalone,
        "pair_histogram": dict(
            sorted(Counter(counts[2][p] for p in itertools.combinations(range(1, 17), 2)).items())
        ),
    }


def main():
    assert sha(PILOT / "manifest.json") == MANIFEST_SHA
    assert sha(PILOT / "result.json") == RESULT_SHA
    manifest = json.loads((PILOT / "manifest.json").read_text())
    result = json.loads((PILOT / "result.json").read_text())
    launch = json.loads((PILOT / "launch.json").read_text())
    for path, digest in manifest["pins"].items():
        assert sha(ROOT / path) == digest, path
    assert len(manifest["pins"]) == 180
    gate_path = Path(result["gate_path"])
    assert sha(gate_path) == result["gate_sha256"] == GATE_SHA
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["launch_permitted"] and gate["manifest_sha256"] == MANIFEST_SHA
    assert result["manifest_sha256"] == launch["manifest_sha256"] == MANIFEST_SHA
    for key, value in launch.items():
        if key not in ("validation_passed", "complete_exact_distance4"):
            assert result[key] == value
    assert not launch["validation_passed"] and not launch["complete_exact_distance4"]
    assert result["validation_passed"]
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
    assert len(native["shells"]) == 1
    shell = native["shells"][0]
    assert shell["distance"] == 4 and shell["complete"] and result["complete_exact_distance4"]
    assert shell["deletions"] == math.comb(64, 4) == 635376
    assert shell["excluded"] == 633208
    assert shell["prefix_nodes"] == 31516 and shell["prefix_excluded"] == 28021
    assert shell["gain_evaluations"] == 1047902 and shell["tuples"] == 0
    assert 0 <= shell["prefix_excluded"] <= shell["prefix_nodes"] <= shell["gain_evaluations"]
    assert shell["prefix_nodes"] >= shell["deletions"] - shell["excluded"]
    with (RAW / "native/candidates.tsv").open() as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert [int(r["candidate"]) for r in rows] == list(range(1, len(rows) + 1))
    assert len(rows) == native["candidates"] == shell["candidates"] == result["candidate_count"]
    assert len(rows) == len(result["candidates"]) == 0
    assert (RAW / "native/candidates.tsv").read_bytes() == (
        b"candidate\tdistance\tholes\tdrop_ids\tadd_ids\n"
    )
    assert list((RAW / "native").iterdir()) == [RAW / "native/candidates.tsv"]
    assert list((PILOT / "candidates").iterdir()) == []
    assert result["unledgered_raw_candidate_files"] == 0 and not result["complete_at_most64"]
    initial = recount_family(result["initial"], manifest)
    assert initial["metrics"]["holes"] == 6
    screen_path = HERE.parent / "h6-radius4-screen-independent/audit.json"
    screen = json.loads(screen_path.read_text())
    assert screen["passed"] and screen["deletion_rows_recounted_twice"] == shell["deletions"]
    assert screen["all_survivor_pools_directly_recounted"] == (
        shell["deletions"] - shell["excluded"]
    )
    prior_path = HERE.parent / "h6-strict-hole-radius3-pilot/result.json"
    assert sha(prior_path) == "075a3f18257a88e3d2a3df2ae759cd3d38ccf79c0fd56caa8a32c37ecb519de8"
    prior = json.loads(prior_path.read_text())
    assert (
        prior["validation_passed"] and prior["complete_radius3"] and prior["candidate_count"] == 0
    )
    assert prior["initial"]["sha256"] == initial["sha256"]
    prior_audit_path = HERE.parent / "h6-strict-hole-radius3-runtime-audit/audit.json"
    prior_audit = json.loads(prior_audit_path.read_text())
    assert prior_audit["passed"] and prior_audit["result_sha256"] == sha(prior_path)
    audit = {
        "passed": True,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "result_sha256": RESULT_SHA,
        "gate_sha256": GATE_SHA,
        "rehash_pin_count": 180,
        "launch_sha256": sha(PILOT / "launch.json"),
        "native": native,
        "ledger_sha256": sha(RAW / "native/candidates.tsv"),
        "screen_audit_sha256": sha(screen_path),
        "prior_radius3_result_sha256": sha(prior_path),
        "prior_radius3_audit_sha256": sha(prior_audit_path),
        "initial_recount": initial,
        "candidate_audits": [],
        "complete_exact_distance4": True,
        "combined_complete_radius4": True,
        "strict_improvement_candidates": 0,
        "search_or_prefix_reruns": 0,
        "scope": "Runtime evidence and accounting checked against frozen source/gate. "
        "All635376 deletion sets completed; safe prefix bounds excluded every survivor "
        "branch before a full addition tuple. No at-most5-hole neighbor exists at "
        "exact distance4; combined with the separately audited1,2,3 shells this covers "
        "radius4 of the named H6 family. Prefix counters are checked from saved output, "
        "not independently rerun. Equal-hole moves and larger neighborhoods are outside scope.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                k: audit[k]
                for k in (
                    "passed",
                    "rehash_pin_count",
                    "combined_complete_radius4",
                    "strict_improvement_candidates",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
