# Document:    Gated Variable Cardinality Pilot Recorder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ee35a075397d250b708fe991dc1cfe802f60cc5a86d44ab045d4950706450b81
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Launch only when called explicitly with a passing independent gate."""

import argparse
import hashlib
import itertools
import json
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/native-variable-cardinality-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}
BUDGET = {
    "max_runs": 2,
    "seconds_per_run": 120,
    "seeds": [2026104701, 2026104702],
    "watchdog_seconds": 135,
    "termination_grace_seconds": 5,
    "simultaneous_processes": 1,
    "stop_after_first_complete_at_most_64": True,
    "unused_budget_reallocated": False,
    "relaunch": False,
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def checked(path, cores):
    blocks = read_blocks(path)
    package = verify_cover(blocks)
    count = len(blocks)
    assert count == len(set(blocks))
    assert all(len(b) == 5 and len(set(b)) == 5 and all(1 <= p <= 16 for p in b) for b in blocks)
    ids = sorted(RANK[tuple(sorted(block))] for block in blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", str(count)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode in (0, 1) and not process.stderr, process.stderr
    standalone = json.loads(process.stdout)
    counts = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    holes = 560 - len(counts)
    assert holes == len(package["uncovered"]) == standalone["uncovered_count"]
    assert package["valid"] == (holes == 0) == (process.returncode == 0)
    assert standalone["blocks"] == count and standalone["cardinality_matches"]
    overlaps = [len(set(ids).intersection(core)) for core in cores]
    return {
        "path": str(Path(path).relative_to(ROOT)),
        "sha256": sha(path),
        "ids": ids,
        "metrics": {"cardinality": count, "holes": holes, "core_overlaps": overlaps},
        "cap_admissible": max(overlaps) <= 55,
        "package": package,
        "standalone": standalone,
    }


def execute_bounded(command):
    before = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    watchdog = {"fired": False, "terminate_sent": False, "kill_sent": False, "relaunch": False}
    try:
        stdout, stderr = process.communicate(timeout=BUDGET["watchdog_seconds"])
    except subprocess.TimeoutExpired:
        watchdog["fired"] = watchdog["terminate_sent"] = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=BUDGET["termination_grace_seconds"])
        except subprocess.TimeoutExpired:
            watchdog["kill_sent"] = True
            process.kill()
            stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr, watchdog, time.monotonic() - before


def validate(directory, stdout, returncode, stderr, elapsed, cores, seed):
    events = [json.loads(line) for line in stdout.splitlines()]
    assert events[0] == {"event": "start", "seed": seed, "budget": 120}
    assert returncode in (0, 1, 2) and not stderr
    records = [event for event in events if event["event"] == "record"]
    assert [e["serial"] for e in records] == list(range(1, len(records) + 1))
    assert len(list(directory.glob("search-record-*.txt"))) == len(records)
    seen = {"complete": [], "raw64": [], "admissible64": []}
    snapshots = []
    for event in records:
        role = event["role"]
        assert role in seen
        path = directory / f"search-record-{event['serial']}-{role}.txt"
        row = checked(path, cores)
        assert row["metrics"] == event["metrics"]
        m = row["metrics"]
        if role == "complete":
            assert m["holes"] == 0
            if seen[role]:
                assert m["cardinality"] < seen[role][-1]["metrics"]["cardinality"]
        else:
            assert m["cardinality"] == 64
            if seen[role]:
                assert m["holes"] < seen[role][-1]["metrics"]["holes"]
            if role == "admissible64":
                assert row["cap_admissible"]
        row["role"] = role
        seen[role].append(row)
        snapshots.append(row)
    assert seen["complete"] and seen["complete"][0]["metrics"]["cardinality"] == 65
    final = events[-1]
    final_rows = {}
    for role in ["current", "complete", "raw64", "admissible64"]:
        path = directory / f"search-final-{role}.txt"
        if role != "current" and not seen[role]:
            assert final[role] is None and not path.exists()
            final_rows[role] = None
            continue
        row = checked(path, cores)
        assert row["metrics"] == final[role]
        if role != "current":
            assert row["sha256"] == seen[role][-1]["sha256"]
        row["role"] = "final_" + role
        snapshots.append(row)
        final_rows[role] = row
    assert 0 <= final["seconds"] <= elapsed + 1
    for key in ["iterations", "mutations", "weight_updates", "fallbacks", "novelties"]:
        assert type(final[key]) is int and final[key] >= 0
    assert sum(final["action_counts"]) == final["iterations"]
    assert final["max_cardinality"] == 65 and 0 < final["min_cardinality"] <= 64
    success = final["current"]["holes"] == 0 and final["current"]["cardinality"] <= 64
    assert (returncode == 0) == success
    assert final["event"] == (
        "cover_found" if success else "finished" if returncode == 1 else "interrupted"
    )
    if success:
        assert final["complete"] == final["current"]
    return {"success": success, "final": final, "snapshots": snapshots, "final_rows": final_rows}


def main(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["budget"] == BUDGET
    for relative, digest in (
        manifest["source_files"] | manifest["input_files"] | manifest["raw_files"]
    ).items():
        assert sha(ROOT / relative) == digest, relative
    binary = ROOT / manifest["binary_path"]
    assert sha(binary) == manifest["binary_sha256"]
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    archive = RAW / "frozen-sources"
    archive.mkdir()
    for relative in manifest["source_files"]:
        path = ROOT / relative
        shutil.copyfile(path, archive / path.name)
    shutil.copyfile(manifest_path, archive / "manifest.json")
    shutil.copyfile(gate_path, archive / "gate.json")
    dump(
        RAW / "start.json",
        {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(manifest_path),
            "gate_sha256": sha(gate_path),
            "budget": BUDGET,
        },
    )
    records = []
    for seed in BUDGET["seeds"]:
        directory = HERE / f"seed-{seed}"
        directory.mkdir()
        command = [
            str(binary),
            str(ROOT / manifest["start_path"]),
            str(seed),
            "120",
            str(directory / "search"),
        ]
        started = datetime.now(timezone.utc).isoformat()
        rc, stdout, stderr, watchdog, elapsed = execute_bounded(command)
        outpath, errpath = RAW / f"seed-{seed}-stdout.jsonl", RAW / f"seed-{seed}-stderr.txt"
        outpath.write_text(stdout)
        errpath.write_text(stderr)
        row = {
            "seed": seed,
            "started_utc": started,
            "command": command,
            "returncode": rc,
            "elapsed_seconds": elapsed,
            "watchdog": watchdog,
            "stdout": {"path": str(outpath.relative_to(ROOT)), "sha256": sha(outpath)},
            "stderr": {"path": str(errpath.relative_to(ROOT)), "sha256": sha(errpath)},
        }
        try:
            row.update(
                validate(directory, stdout, rc, stderr, elapsed, manifest["core_rows"], seed)
            )
            row["validation_passed"] = True
        except Exception as error:
            row["validation_passed"] = False
            row["validation_error"] = f"{type(error).__name__}: {error}"
        records.append(row)
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "budget": BUDGET,
                "runs": records,
                "skipped_seeds": [
                    s for s in BUDGET["seeds"] if s not in [r["seed"] for r in records]
                ],
                "no_global_conclusion": True,
            },
        )
        if not row["validation_passed"] or row.get("success") or watchdog["fired"] or rc != 1:
            break
    assert all(row["validation_passed"] for row in records), "candidate or log verification failed"
    print(
        json.dumps(
            {
                "runs": len(records),
                "success": any(row["success"] for row in records),
                "result": str(HERE / "result.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    main(parser.parse_args().gate.resolve())
