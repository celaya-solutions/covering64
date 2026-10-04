# Document:    Gated Native Three-Core Escape Pilot Recorder
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      55783e850a5f604e2645dc4453befcd1a0e5e271225b3bef172212faf6c0f98a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Run exactly two authorized native calls only after an independent frozen gate."""

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
RAW = ROOT / "experiments/scratch/native-core-cap-escape-v2-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: index for index, block in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def checked(path, cores, require_eligible, expected_holes=None):
    blocks = read_blocks(path)
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode in (0, 1), process.stderr
    standalone = json.loads(process.stdout)
    assert len(blocks) == len(set(blocks)) == 64
    ids = sorted(RANK[tuple(block)] for block in blocks)
    counts = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
    holes = 560 - len(counts)
    assert holes == len(package["uncovered"]) == standalone["uncovered_count"]
    if expected_holes is not None:
        assert holes == expected_holes
    heavy = [triple for triple, count in counts.items() if count >= 6]
    obstructions = [
        list(map(list, choice))
        for choice in itertools.combinations(heavy, 5)
        if len(set().union(*map(set, choice))) == 15
        and sum(counts[triple] >= 7 for triple in choice) >= 2
    ]
    overlaps = [len(set(ids) & set(core)) for core in cores]
    assert all(value <= 55 for value in overlaps)
    if require_eligible:
        assert not obstructions
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "ids": ids,
        "holes": holes,
        "core_overlaps": overlaps,
        "global_profile_obstructions": obstructions,
        "eligible_record": not obstructions,
        "package": package,
        "standalone": standalone,
    }


def execute_bounded(command, deadline=75, grace=5):
    before = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    watchdog = {
        "deadline_seconds": deadline,
        "fired": False,
        "terminate_sent": False,
        "kill_sent": False,
        "relaunch": False,
    }
    try:
        stdout, stderr = process.communicate(timeout=deadline)
    except subprocess.TimeoutExpired:
        watchdog["fired"] = watchdog["terminate_sent"] = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            watchdog["kill_sent"] = True
            process.kill()
            stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr, watchdog, time.monotonic() - before


def main(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["runner_sha256"] == sha(__file__)
    assert manifest["budget"] == {
        "runs": 2,
        "seconds_per_run": 60,
        "seeds": [2026104201, 2026104202],
        "watchdog_seconds": 75,
        "termination_grace_seconds": 5,
        "simultaneous_processes": 1,
        "relaunch": False,
    }
    for relative, digest in (manifest["input_files"] | manifest["raw_files"]).items():
        assert sha(ROOT / relative) == digest
    binary = ROOT / manifest["binary_path"]
    assert sha(binary) == manifest["binary_sha256"]
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    archive = RAW / "frozen-sources"
    archive.mkdir()
    for path in [
        HERE / "search.cpp",
        HERE / "heuristic_search.cpp",
        HERE / "cores.hpp",
        HERE / "control.cpp",
        HERE / "prepare.py",
        HERE / "run.py",
        manifest_path,
    ]:
        shutil.copyfile(path, archive / path.name)
    shutil.copyfile(gate_path, archive / "gate.json")
    dump(
        RAW / "start.json",
        {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(manifest_path),
            "gate_sha256": sha(gate_path),
            "seeds": manifest["budget"]["seeds"],
            "relaunch": False,
        },
    )
    records = []
    for seed in manifest["budget"]["seeds"]:
        directory = HERE / f"seed-{seed}"
        directory.mkdir()
        command = [
            str(binary),
            str(ROOT / manifest["hint_path"]),
            str(seed),
            "60",
            str(directory / "search"),
        ]
        started = datetime.now(timezone.utc).isoformat()
        returncode, stdout, stderr, watchdog, elapsed = execute_bounded(command)
        stdout_path, stderr_path = (
            RAW / f"seed-{seed}-stdout.jsonl",
            RAW / f"seed-{seed}-stderr.txt",
        )
        stdout_path.write_text(stdout)
        stderr_path.write_text(stderr)
        snapshots = []
        validation_error = None
        try:
            for path in sorted(directory.glob("search-h*.txt")):
                expected = int(path.stem.removeprefix("search-h"))
                row = checked(path, manifest["core_rows"], True, expected)
                row["role"] = "eligible_improvement"
                snapshots.append(row)
            for suffix, eligible in [("current", False), ("best", True)]:
                path = directory / f"search-final-{suffix}.txt"
                row = checked(path, manifest["core_rows"], eligible)
                row["role"] = f"final_{suffix}"
                snapshots.append(row)
            events = [json.loads(line) for line in stdout.splitlines()]
            improvements = [row["missing"] for row in events if row["event"] == "improvement"]
            assert sorted(improvements) == sorted(
                row["holes"] for row in snapshots if row["role"] == "eligible_improvement"
            )
            assert returncode in (0, 1) and not stderr
            final_event = events[-1]
            current = next(row for row in snapshots if row["role"] == "final_current")
            best = next(row for row in snapshots if row["role"] == "final_best")
            assert final_event["final_profile_forbidden"] == bool(
                current["global_profile_obstructions"]
            )
            assert final_event["final_core_overlaps"] == current["core_overlaps"]
            assert final_event["best_core_overlaps"] == best["core_overlaps"]
            assert final_event["best"] == best["holes"]
            assert final_event["current_missing"] == current["holes"]
            for key in ["iterations", "restarts", "core_rejections"]:
                assert type(final_event[key]) is int and final_event[key] >= 0
            assert final_event["core_rejections"] <= final_event["iterations"]
            assert 0 <= final_event["seconds"] <= elapsed + 1
            if returncode == 0:
                assert final_event["event"] == "cover_found"
                assert best["holes"] == current["holes"] == 0
            else:
                assert final_event["event"] in ("finished", "interrupted")
        except (AssertionError, ValueError, KeyError, OSError) as error:
            validation_error = f"{type(error).__name__}: {error}"
        record = {
            "seed": seed,
            "command": command,
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(),
            "wall_seconds": elapsed,
            "exit_code": returncode,
            "watchdog": watchdog,
            "snapshots": snapshots,
            "validation_error": validation_error,
            "raw_files": {
                str(path.relative_to(ROOT)): sha(path) for path in [stdout_path, stderr_path]
            },
            "best_eligible_holes": min(
                (row["holes"] for row in snapshots if row["eligible_record"]), default=None
            ),
        }
        records.append(record)
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "binary_sha256": sha(binary),
                "optimizer_calls": len(records),
                "cases": records,
                "global_lower_bound_claim": False,
            },
        )
        print(
            json.dumps(
                {
                    key: record[key]
                    for key in [
                        "seed",
                        "wall_seconds",
                        "exit_code",
                        "best_eligible_holes",
                        "validation_error",
                    ]
                }
            ),
            flush=True,
        )
        if validation_error or watchdog["fired"] or record["best_eligible_holes"] == 0:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, metavar="GATE_JSON")
    main(parser.parse_args().run)
