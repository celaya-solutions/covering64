# Document:    Native SQS Pool Heuristic Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e2f9d57ef2b4048a55b8bbc913b66ec4f2fa43f2820ce016c6e5975fe63eb3bd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recheck recorded artifacts and covering status; do not run optimization."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PILOT = ROOT / "experiments/scratch/sqs-pool-heuristic-20261003/pilot-2026104021"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result):
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert result["manifest_sha256"] == sha(HERE / "manifest.json")
    assert result["runner_sha256"] == sha(HERE / "run_pilot.py") == sha(PILOT / "run_pilot.py")
    assert result["gate_sha256"] == sha(PILOT / "independent-gate.json")
    gate = json.loads((PILOT / "independent-gate.json").read_text())
    assert gate["passed"] is True and gate["manifest_sha256"] == result["manifest_sha256"]
    for recorded in (manifest["artifacts"], gate["verified_inputs"]):
        for relative, expected in recorded.items():
            assert sha(ROOT / relative) == expected
    start = json.loads((PILOT / "start.json").read_text())
    assert all(result[key] == value for key, value in start.items())
    assert (
        result["seed"] == 2026104021
        and result["requested_seconds"] == 60
        and result["processes"] == 1
    )
    assert set(result["artifact_sha256"]) == {
        str(path.relative_to(PILOT)) for path in PILOT.rglob("*") if path.is_file()
    }
    for relative, expected in result["artifact_sha256"].items():
        assert sha(PILOT / relative) == expected
    native = json.loads((PILOT / "native/result.json").read_text())
    assert native == result["native"] and native["global_lower_bound_claim"] is False
    assert (
        native["seed"] == result["seed"] and native["budget_seconds"] == result["requested_seconds"]
    )
    assert native["proposals"] == native["accepted"] + native["rejected"] + native["selected_skips"]
    assert result["global_lower_bound_claim"] is False and result["scope"] == manifest["scope"]
    assert result["cover_found"] == (native["best_holes"] == 0)
    assert result["initial_holes"] == manifest["initial_holes"]
    events = [json.loads(line) for line in (PILOT / "native/events.jsonl").read_text().splitlines()]
    best_events = [event for event in events if event["event"] == "best"]
    assert best_events[0]["holes"] == result["initial_holes"]
    assert [event["holes"] for event in best_events] == sorted(
        {event["holes"] for event in best_events}, reverse=True
    )
    assert best_events[-1]["holes"] == native["best_holes"]
    recounts = [event for event in events if event["event"] == "recount"]
    assert [event["accepted"] for event in recounts] == list(
        range(4096, native["accepted"] + 1, 4096)
    )
    assert native["full_recounts"] == 2 + len(recounts) + len(best_events) - 1
    pool = set(read_blocks(ROOT / manifest["pool_path"]))
    assert {Path(candidate["path"]).name for candidate in result["candidates"]} == {
        f"best-{event['holes']}.txt" for event in best_events
    }
    for candidate in [*result["candidates"], result["final"]]:
        path = ROOT / candidate["path"]
        blocks = list(read_blocks(path))
        assert len(blocks) == len(set(blocks)) == candidate["blocks"] == 64
        assert all(block in pool for block in blocks) and sha(path) == candidate["sha256"]
        package = verify_cover(blocks)
        process = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert process.returncode in (0, 1)
        standalone = json.loads(process.stdout)
        assert [list(triple) for triple in package["uncovered"]] == standalone["uncovered"]
        assert (
            candidate["canonical_sha256"]
            == package["canonical_sha256"]
            == standalone["canonical_sha256"]
        )
        assert (
            package["valid"]
            == standalone["valid"]
            == candidate["cover"]
            == (candidate["holes"] == 0)
        )
        assert (
            len(package["uncovered"]) == candidate["holes"]
            and candidate["both_verifiers_agree"] is True
        )
        assert process.returncode == (0 if candidate["cover"] else 1)
    assert min(candidate["holes"] for candidate in result["candidates"]) == native["best_holes"]
    assert result["final"]["holes"] == native["final_holes"]


def main():
    result = json.loads((HERE / "pilot-result.json").read_text())
    inspect(result)
    mutations = [
        ("manifest_sha256", "0" * 64),
        ("runner_sha256", "0" * 64),
        ("gate_sha256", "0" * 64),
        ("seed", 1),
        ("requested_seconds", 59),
        ("processes", 2),
        ("initial_holes", result["initial_holes"] + 1),
        ("cover_found", not result["cover_found"]),
        ("global_lower_bound_claim", True),
        ("artifact_sha256", {}),
        ("candidates", []),
    ]
    for key, value in mutations:
        damaged = copy.deepcopy(result)
        damaged[key] = value
        try:
            inspect(damaged)
        except (AssertionError, ValueError, KeyError):
            continue
        raise AssertionError(f"damaged result accepted: {key}")
    report = {
        "passed": True,
        "result_sha256": sha(HERE / "pilot-result.json"),
        "checker_sha256": sha(Path(__file__)),
        "initial_holes": result["initial_holes"],
        "best_holes": result["native"]["best_holes"],
        "cover_found": result["cover_found"],
        "damaged_results_rejected": len(mutations),
        "global_lower_bound_claim": False,
    }
    (HERE / "pilot-readback.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
