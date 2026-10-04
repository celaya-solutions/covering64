# Document:    Gated Native Compact Pair-Two Hint Recorder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      51ebe38504d922cfa40ec46bde035995e065c0f623d5a8f12c0fd6ca4dc8a510
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Run at most two gated calls and stop the entire pilot at the first zero D2max."""

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
RAW = ROOT / "experiments/scratch/native-pair-two-penalty-20261004"
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
    assert package["valid"] == (holes == 0) == (process.returncode == 0)
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
    pair_counts = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    quad_counts = Counter(q for b in blocks for q in itertools.combinations(b, 4))
    d3 = sum(
        max(0, 13 - 3 * pair_counts[p] + counts[t])
        for t in itertools.combinations(range(1, 17), 3)
        for p in itertools.combinations(t, 2)
    )
    d4 = sum(
        max(0, 12 - 3 * pair_counts[p] + 2 * quad_counts[q])
        for q in itertools.combinations(range(1, 17), 4)
        for p in itertools.combinations(q, 2)
    )
    d2max = 0
    d2sum = 0
    for pair in itertools.combinations(range(1, 17), 2):
        values = [counts[tuple(sorted((*pair, x)))] for x in range(1, 17) if x not in pair]
        explicit = [
            max(0, 12 - 3 * pair_counts[pair] + a + b) for a, b in itertools.combinations(values, 2)
        ]
        compact = max(0, 12 - 3 * pair_counts[pair] + sum(sorted(values, reverse=True)[:2]))
        assert compact == max(explicit)
        d2max += compact
        d2sum += sum(explicit)
    metrics = {
        "holes": holes,
        "D3": d3,
        "D4": d4,
        "D2max": d2max,
        "D2sum": d2sum,
        "energy": 20 * d2max + holes,
        "pair_min": min(pair_counts[p] for p in itertools.combinations(range(1, 17), 2)),
        "forbidden": bool(obstructions),
        "core_overlaps": overlaps,
    }
    return {
        "metrics": metrics,
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
        "max_runs": 2,
        "stop_after_first_D2max_zero": True,
        "unused_budget_reallocated": False,
        "additional_budget_on_phase_transition": 0,
        "seconds_per_run": 60,
        "seeds": [2026104501, 2026104502],
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
        HERE / "native_core_base.cpp",
        HERE / "native_pair_base.cpp",
        HERE / "fourth_core.hpp",
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
    for index, seed in enumerate(manifest["budget"]["seeds"]):
        directory = HERE / f"seed-{seed}"
        directory.mkdir()
        hint = next(row for row in manifest["hints"] if row["seed"] == seed)
        command = [
            str(binary),
            str(ROOT / hint["path"]),
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
            events = [json.loads(line) for line in stdout.splitlines()]
            record_events = [event for event in events if event["event"] == "record"]
            assert [e["serial"] for e in record_events] == list(range(1, len(record_events) + 1))
            assert len(list(directory.glob("search-record-*.txt"))) == len(record_events)
            seen = {"raw": [], "primary": [], "qualified": []}
            for event in record_events:
                role = event["role"]
                assert role in seen
                path = directory / f"search-record-{event['serial']}-{role}.txt"
                row = checked(path, manifest["core_rows"], role == "raw")
                assert row["metrics"] == event["metrics"]
                row["role"] = role
                if role == "qualified":
                    assert row["metrics"]["D2max"] == row["metrics"]["D2sum"] == 0
                    assert row["metrics"]["D3"] == row["metrics"]["D4"] == 0
                    assert row["metrics"]["pair_min"] >= 5
                seen[role].append(row)
                snapshots.append(row)
            assert seen["raw"] and seen["primary"]
            for role, rows in seen.items():
                keys = [
                    (r["metrics"]["D2max"], r["holes"]) if role == "primary" else (r["holes"],)
                    for r in rows
                ]
                assert all(a > b for a, b in zip(keys, keys[1:]))
            assert returncode in (0, 1) and not stderr
            final_event = events[-1]
            for role in ["current", "raw", "primary", "qualified"]:
                path = directory / f"search-final-{role}.txt"
                if role == "qualified" and not seen[role]:
                    assert final_event[role] is None and not path.exists()
                    continue
                row = checked(path, manifest["core_rows"], role == "raw")
                assert final_event[role] == row["metrics"]
                if role != "current":
                    assert row["sha256"] == seen[role][-1]["sha256"]
                row["role"] = f"final_{role}"
                snapshots.append(row)
            for key in ["iterations", "restarts", "core_rejections"]:
                assert type(final_event[key]) is int and final_event[key] >= 0
            assert final_event["core_rejections"] <= final_event["iterations"]
            assert 0 <= final_event["seconds"] <= elapsed + 1
            assert events[0] == {"event": "start", "seed": seed, "budget": 60}
            if returncode == 0:
                assert len(seen["qualified"]) == 1
                assert final_event["event"] in ("qualified_hint_found", "cover_found")
                assert all(
                    final_event[r]["D2max"] == 0 for r in ["current", "primary", "qualified"]
                )
                assert record_events[-1]["role"] == "qualified"
                assert record_events[-1]["iterations"] == final_event["iterations"]
                assert final_event["current"] == final_event["primary"] == final_event["qualified"]
                if final_event["event"] == "cover_found":
                    assert all(
                        final_event[r]["holes"] == 0
                        for r in ["current", "raw", "primary", "qualified"]
                    )
                    assert all(r["package"]["valid"] for r in snapshots if r["holes"] == 0)
                else:
                    assert final_event["current"]["holes"] > 0
            else:
                assert final_event["event"] in ("finished", "interrupted")
                assert final_event["current"]["D2max"] > 0 and not seen["qualified"]
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
            "qualified_holes": min(
                (
                    row["holes"]
                    for row in snapshots
                    if row["role"] in ("qualified", "final_qualified")
                ),
                default=None,
            ),
            "best_primary_D2max": min(
                (
                    row["metrics"]["D2max"]
                    for row in snapshots
                    if row["role"] in ("primary", "final_primary")
                ),
                default=None,
            ),
            "best_eligible_holes": min(
                (row["holes"] for row in snapshots if row["eligible_record"]), default=None
            ),
        }
        records.append(record)
        stop_reason = (
            "validation_error"
            if validation_error
            else "watchdog"
            if watchdog["fired"]
            else "cover_found"
            if record["best_eligible_holes"] == 0
            else "qualified_hint_found"
            if record["qualified_holes"] is not None
            else "budget_exhausted"
            if index + 1 == len(manifest["budget"]["seeds"])
            else None
        )
        skipped = (
            [
                {"seed": remaining, "reason": stop_reason}
                for remaining in manifest["budget"]["seeds"][index + 1 :]
            ]
            if stop_reason
            else []
        )
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "binary_sha256": sha(binary),
                "optimizer_calls": len(records),
                "stop_reason": stop_reason,
                "skipped_runs": skipped,
                "unused_budget_reallocated": False,
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
                        "best_primary_D2max",
                        "qualified_holes",
                        "validation_error",
                    ]
                }
            ),
            flush=True,
        )
        if stop_reason:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, metavar="GATE_JSON")
    main(parser.parse_args().run)
