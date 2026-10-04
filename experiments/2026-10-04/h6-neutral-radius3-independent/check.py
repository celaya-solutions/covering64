# Document:    Independent Neutral H6 Radius Three Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      0690ea208c7240f5a166de5b3e2b9c444bbf603aeea7fd4d5bdfaddfaa69e6cd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay fixture families by whole-family enumeration; never launch the native search."""

import csv
import hashlib
import importlib.util
import itertools
import json
import math
import subprocess
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-neutral-radius3-pilot"
MANIFEST_SHA = "8fe4a7f2d272e62e9594c888f9c995271689476c69c51bed84a8f31618cc0acf"
SOURCE_SHA = "ced6fccc4e33f893819f2a011bee637c98400b5c8361012984d2b651af9c7d69"
RUNNER_SHA = "5010cb10efb5b4286e39eaaea3f1b8a6eb5d4ed6dfed8367e38defeca32fde72"
BINARY_SHA = "5469b30c3648033d8f365ca982d5cd7cf5ebd7bee157461d8f73d5ad1ec039b1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main():
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "search.cpp") == SOURCE_SHA
    assert sha(PRODUCER / "run.py") == RUNNER_SHA
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    for name, digest in manifest["pins"].items():
        assert sha(ROOT / name) == digest, name
    assert sha(ROOT / manifest["binary_path"]) == BINARY_SHA
    old_path = HERE.parent / "h6-strict-hole-radius3-pilot/search.cpp"
    assert sha(old_path) == "095ef928c61e3af42de8651407f576074679a9f9074331f7caae021c83a6093e"
    expected_body = old_path.read_text().split("\n\n", 1)[1]
    for before, after in (
        ("target!=5", "target!=6"),
        ("seconds>59", "seconds>30"),
        ("target!=expected-1", "target!=expected"),
        ("raw H6 exact64 strict H5", "raw H6 exact64 neutral H6"),
        ("budget/strict target/family size", "budget/neutral target/family size"),
    ):
        expected_body = expected_body.replace(before, after)
    assert (PRODUCER / "search.cpp").read_text().split("\n\n", 1)[1] == expected_body
    controls = json.loads((PRODUCER / "controls.json").read_text())
    assert controls["passed"] and controls["production_replacement_tuples"] == 0
    assert controls["production_search_launched"] is False
    assert len(controls["rejected_controls"]) == 17
    assert controls["zero_budget"]["status"] == "timeout"
    assert all(
        not s["complete"] and s["deletions"] == s["tuples"] == 0
        for s in controls["zero_budget"]["shells"]
    )
    blocks = list(itertools.combinations(range(1, 8), 5))
    triples = list(itertools.combinations(range(1, 8), 3))
    masks = [sum(1 << triples.index(t) for t in itertools.combinations(b, 3)) for b in blocks]
    rank = {b: i for i, b in enumerate(blocks)}

    def holes(ids):
        union = 0
        for i in ids:
            union |= masks[i]
        return 35 - union.bit_count()

    fixtures = []
    for fixture in controls["fixtures"]:
        original = set(fixture["fixture_ids"])
        size = len(original)
        initial_holes = holes(original)
        assert initial_holes == fixture["initial_holes"]
        assert sha(ROOT / fixture["input_path"]) == fixture["input_sha256"]
        expected = {}
        neighborhood_count = 0
        all_families = 0
        for candidate in itertools.combinations(range(21), size):
            all_families += 1
            distance = len(original - set(candidate))
            if not 1 <= distance <= 3:
                continue
            neighborhood_count += 1
            missing = holes(candidate)
            if missing <= initial_holes:
                expected[candidate] = (
                    distance,
                    missing,
                    tuple(sorted(original - set(candidate))),
                    tuple(sorted(set(candidate) - original)),
                )
        assert neighborhood_count == fixture["unpruned_oracle_tuples"]
        folder = ROOT / fixture["output_path"]
        assert sha(folder / "candidates.tsv") == fixture["ledger_sha256"]
        rows = list(csv.DictReader((folder / "candidates.tsv").open(), delimiter="\t"))
        assert [int(row["candidate"]) for row in rows] == list(range(1, len(rows) + 1))
        actual = {}
        for row in rows:
            path = folder / f"candidate-{row['candidate']}.txt"
            parsed = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
            assert parsed == sorted(set(parsed)) and len(parsed) == size
            candidate = tuple(rank[b] for b in parsed)
            assert candidate not in actual
            actual[candidate] = (
                int(row["distance"]),
                int(row["holes"]),
                tuple(map(int, row["drop_ids"].split(","))),
                tuple(map(int, row["add_ids"].split(","))),
            )
        assert actual == expected
        inventory = [(path.name, sha(path)) for path in sorted(folder.glob("candidate-*.txt"))]
        assert len(inventory) == len(actual) == fixture["candidate_count"]
        assert (
            hashlib.sha256(json.dumps(inventory, separators=(",", ":")).encode()).hexdigest()
            == fixture["witness_inventory_sha256"]
        )
        for distance, shell in enumerate(fixture["native"]["shells"], 1):
            assert shell["distance"] == distance and shell["complete"]
            assert shell["deletions"] == math.comb(size, distance)
            assert shell["candidates"] == sum(row[0] == distance for row in expected.values())
        redundant = [i for i in original if holes(original - {i}) == initial_holes]
        fixtures.append(
            {
                "initial_ids": sorted(original),
                "initial_holes": initial_holes,
                "whole_families_checked": all_families,
                "neighborhood_tuples": neighborhood_count,
                "candidates": len(actual),
                "redundant_block_ids": redundant,
                "exact_identity_hole_drop_add_match": True,
            }
        )
    assert [f["candidates"] for f in fixtures] == [3551, 450, 6880]
    assert any(f["redundant_block_ids"] for f in fixtures)
    spec = importlib.util.spec_from_file_location("neutral_independent_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    watchdog_checks = []
    for name, responses in (
        ("normal", [("done", "")]),
        ("terminate", [None, ("partial", "")]),
        ("kill", [None, None, ("partial", "")]),
    ):
        events = []

        class Process:
            returncode = 0

            def communicate(self, timeout=None):
                events.append(["communicate", timeout])
                response = responses.pop(0)
                if response is None:
                    raise subprocess.TimeoutExpired("mock only", timeout)
                return response

            def terminate(self):
                events.append(["terminate"])

            def kill(self):
                events.append(["kill"])

        with patch.object(runner.subprocess, "Popen", return_value=Process()) as mocked:
            outcome = runner.execute_bounded(["not-a-native-launch"])
            assert mocked.call_count == 1
        assert outcome["watchdog"] == outcome["terminated"] == (name != "normal")
        assert outcome["killed"] == (name == "kill")
        assert (
            events
            == {
                "normal": [["communicate", 35]],
                "terminate": [["communicate", 35], ["terminate"], ["communicate", 5]],
                "kill": [
                    ["communicate", 35],
                    ["terminate"],
                    ["communicate", 5],
                    ["kill"],
                    ["communicate", None],
                ],
            }[name]
        )
        watchdog_checks.append({"case": name, "events": events})
    assert not (runner.RAW / "native").exists() and not (PRODUCER / "result.json").exists()
    review = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "checker_sha256": sha(__file__),
        "pins_verified": len(manifest["pins"]),
        "native_body_only_target_budget_changes": True,
        "fixtures": fixtures,
        "watchdog_checks": watchdog_checks,
        "malformed_controls_receipt_count": len(controls["rejected_controls"]),
        "real_native_launches": 0,
        "actual_H6_replacement_tuples": 0,
        "scope": "Coverage-only exact distances 1,2,3 with H<=6. Original-complement "
        "additions, complete distinct tuple enumeration, safe top-sum/floor including "
        "zero demand. One 30s native call, 35s watchdog plus 5s grace. Weak endpoints "
        "and six named caps are separate postclassification; no global conclusion.",
    }
    dump(HERE / "review.json", review)
    dump(
        HERE / "gate.json",
        {
            "passed": True,
            "launch_permitted": True,
            "manifest_sha256": MANIFEST_SHA,
            "review_sha256": sha(HERE / "review.json"),
            "source_sha256": SOURCE_SHA,
            "runner_sha256": RUNNER_SHA,
            "binary_sha256": BINARY_SHA,
            "scope": review["scope"],
            "real_native_launches_during_review": 0,
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "review_sha256": sha(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
