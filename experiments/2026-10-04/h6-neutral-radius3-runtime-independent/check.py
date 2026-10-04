# Document:    H6 Neutral Radius-Three Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      426def204b4f90ef0cdfd85fb775a141d50b5e19e44f0ae7e73520c975c32cb8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit saved neutral families and classifications without running a search."""

import csv
import hashlib
import importlib.util
import itertools
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = HERE.parent / "h6-neutral-radius3-pilot"
RAW = ROOT / "experiments/scratch/h6-neutral-radius3-pilot-20261004"
MANIFEST_SHA = "8fe4a7f2d272e62e9594c888f9c995271689476c69c51bed84a8f31618cc0acf"
RESULT_SHA = "2278e972b73f823f454502eaa7a750b2a809831954382562bf90d850ce6e16e6"
GATE_SHA = "4b07b30815a96e8f2d50c1c512347dadb397f951143a6557970a151c10382ec3"
COUNTER_PATH = HERE.parent / "h6-radius4-runtime-independent/check.py"
COUNTER_SHA = "28621d4eb7d63971206f5ba4e1d99fa855222cd291b52242f636f318bc835ab2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(PILOT / "manifest.json") == MANIFEST_SHA
    assert sha(PILOT / "result.json") == RESULT_SHA
    assert sha(COUNTER_PATH) == COUNTER_SHA
    spec = importlib.util.spec_from_file_location("independent_neutral_metrics", COUNTER_PATH)
    counter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(counter)
    manifest = json.loads((PILOT / "manifest.json").read_text())
    result = json.loads((PILOT / "result.json").read_text())
    launch = json.loads((PILOT / "launch.json").read_text())
    for path, digest in manifest["pins"].items():
        assert sha(ROOT / path) == digest, path
    assert len(manifest["pins"]) == 178
    assert manifest["budget"] == {
        "native_seconds": 30,
        "watchdog_seconds": 35,
        "termination_grace_seconds": 5,
        "processes": 1,
        "runs": 1,
        "relaunch": False,
        "seed": None,
    }
    gate_path = Path(result["gate_path"])
    assert sha(gate_path) == result["gate_sha256"] == GATE_SHA
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["launch_permitted"] and gate["manifest_sha256"] == MANIFEST_SHA
    assert result["manifest_sha256"] == launch["manifest_sha256"] == MANIFEST_SHA
    for key, value in launch.items():
        if key not in ("validation_passed", "complete_neutral_radius3"):
            assert result[key] == value
    assert not launch["validation_passed"] and not launch["complete_neutral_radius3"]
    assert result["validation_passed"] and result["complete_neutral_radius3"]
    assert result["returncode"] == 0 and not result["watchdog"]
    assert not result["watchdog_terminated"] and not result["watchdog_killed"]
    assert 0 < result["elapsed_seconds"] < 35
    assert result["command"] == [
        str(ROOT / manifest["binary_path"]),
        str(ROOT / manifest["input_path"]),
        "6",
        "6",
        str(RAW / "native"),
        "30",
        "64",
    ]
    assert sha(RAW / "stdout.json") == result["stdout_sha256"]
    assert sha(RAW / "stderr.txt") == result["stderr_sha256"]
    assert (RAW / "stderr.txt").read_bytes() == b""
    native = json.loads((RAW / "stdout.json").read_text())
    assert native == result["native_summary"]
    assert native["status"] == "complete" and 0 < native["seconds"] < 30
    assert len(native["shells"]) == 3
    screen_path = HERE.parent / "h6-neutral-radius3-deletion-screen/receipt.json"
    assert sha(screen_path) == "eedf9fd83631aa3d9540333ce463d6319d1d9451b4927179be51acb2c2954978"
    screen = json.loads(screen_path.read_text())["summary"]
    for distance, (shell, before) in enumerate(
        zip(native["shells"], screen["shells"], strict=True), 1
    ):
        assert shell["distance"] == before["distance"] == distance and shell["complete"]
        assert shell["deletions"] == before["deletions"] == math.comb(64, distance)
        assert shell["excluded"] == before["excluded"]
        assert shell["tuples"] == before["necessary_tuples"]
    with (RAW / "native/candidates.tsv").open() as handle:
        ledger = list(csv.DictReader(handle, delimiter="\t"))
    assert [int(row["candidate"]) for row in ledger] == [1, 2, 3]
    assert native["candidates"] == result["candidate_count"] == len(result["candidates"]) == 3
    assert result["unledgered_raw_candidate_files"] == 0
    initial = counter.recount_family(result["initial"], manifest)
    original = set(result["initial"]["ids"])
    families, audited = set(), []
    for index, (row, saved) in enumerate(zip(ledger, result["candidates"], strict=True), 1):
        native_path = RAW / f"native/candidate-{index}.txt"
        saved_path = PILOT / f"candidates/candidate-{index}.txt"
        assert sha(native_path) == sha(saved_path) == saved["sha256"]
        assert saved["path"] == str(saved_path.relative_to(ROOT))
        report = counter.recount_family(saved, manifest)
        assert json.loads(json.dumps(report["package"])) == saved["package"]
        assert report["standalone"] == saved["standalone"]
        ids = tuple(saved["ids"])
        assert ids not in families
        families.add(ids)
        removed, added = sorted(original - set(ids)), sorted(set(ids) - original)
        assert removed == saved["dropped"] == list(map(int, row["drop_ids"].split(",")))
        assert added == saved["added"] == list(map(int, row["add_ids"].split(",")))
        assert len(removed) == len(added) == saved["distance"] == int(row["distance"]) == 1
        assert report["metrics"]["holes"] == int(row["holes"]) == 6
        weak = report["weak_metrics"]
        endpoint = weak["minimum_pair_count"] >= 5 and weak["D3"] == weak["D4"] == 0
        assert endpoint == saved["endpoint_weak_qualified"]
        blocks = [counter.BLOCKS[bid] for bid in ids]
        triples = Counter(t for block in blocks for t in itertools.combinations(block, 3))
        degrees = Counter(p for block in blocks for p in block)
        holes = [t for t in itertools.combinations(range(1, 17), 3) if not triples[t]]
        report.update(
            {
                "distance": 1,
                "removed_ids": removed,
                "added_ids": added,
                "removed_blocks": [counter.BLOCKS[i] for i in removed],
                "added_blocks": [counter.BLOCKS[i] for i in added],
                "endpoint_weak_qualified": endpoint,
                "triple_histogram": dict(sorted(Counter(triples.values()).items())),
                "maximum_triple_multiplicity": max(triples.values()),
                "degree_histogram": dict(sorted(Counter(degrees.values()).items())),
                "holes": holes,
            }
        )
        audited.append(report)
    expected_names = {f"candidate-{i}.txt" for i in (1, 2, 3)}
    assert {p.name for p in (RAW / "native").iterdir()} == expected_names | {"candidates.tsv"}
    assert {p.name for p in (PILOT / "candidates").iterdir()} == expected_names
    for distance, shell in enumerate(native["shells"], 1):
        assert shell["candidates"] == sum(row["distance"] == distance for row in audited)
    assert result["weak_endpoint_count"] == sum(r["endpoint_weak_qualified"] for r in audited) == 0
    assert result["weak_six_cap_count"] == sum(r["weak_six_cap_qualified"] for r in audited) == 0
    assert not result["complete_at_most64"]
    # All three new families share the same63-block retained core with the start.
    intersection = original.intersection(*(set(f) for f in families))
    assert len(intersection) == 63 and original - intersection == {3209}
    assert {tuple(sorted(set(f) - intersection)) for f in families} == {(3102,), (3104,), (3124,)}
    prior_path = HERE.parent / "h6-radius4-runtime-independent/audit.json"
    assert sha(prior_path) == "f40fc017b296c70dfbe9fdc0095ab788bb8f572e205d109d2aa6bcce5f615b1f"
    prior = json.loads(prior_path.read_text())
    assert prior["passed"] and prior["combined_complete_radius4"]
    assert prior["initial_recount"]["sha256"] == initial["sha256"]
    audit = {
        "passed": True,
        "checker_sha256": sha(__file__),
        "counter_sha256": COUNTER_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "result_sha256": RESULT_SHA,
        "gate_sha256": GATE_SHA,
        "rehash_pin_count": 178,
        "native": native,
        "initial": initial,
        "candidates": audited,
        "candidate_count": 3,
        "endpoint_weak_count": 0,
        "complete_neutral_radius3": True,
        "all_three_pairwise_distance1": True,
        "shared_core_size": 63,
        "prior_strict_radius4_audit_sha256": sha(prior_path),
        "search_reruns": 0,
        "scope": "Full saved runtime and candidate audit. Exactly3 non-original H<=6 "
        "families occur within replacement distance3; all are one-block neighbors, "
        "pair-bad, and tied on D2/D3/D4. A radius3 call from any cannot reach H<=5 "
        "because it stays inside the original strict-radius4 exclusion. "
        "A strict4 improvement from any would necessarily be at original distance5.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: audit[key]
                for key in (
                    "passed",
                    "candidate_count",
                    "endpoint_weak_count",
                    "complete_neutral_radius3",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
