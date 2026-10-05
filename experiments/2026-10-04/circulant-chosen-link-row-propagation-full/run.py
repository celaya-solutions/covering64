# Document:    Full Bounded Row Propagation for Chosen Circulant Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b8ce285b5739383fbf9703aef3b1e9f9e96645428a7f2811262ea1ea82b175f3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare only until root review; import the frozen benchmark propagator unchanged."""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import platform
import signal
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BENCHMARK = HERE.parent / "circulant-chosen-link-row-propagation"
RAW = ROOT / "experiments/scratch/circulant-chosen-link-row-propagation-full-v1.0.0"
BENCHMARK_SOURCE_SHA = "ce9792cb21e26c29f87a208454a3a52fd241dfe322fd71ed8b50f71cd8893152"
BENCHMARK_MANIFEST_SHA = "2421efc7f297a65c53dd587a44cd56e9e2c0d29161434226e3dcb5d98a0f719e"
BENCHMARK_RESULT_SHA = "1c1320160351c5d5ddfa0df5b10475846a444e6d58035e3a6621fafbb6572fa1"
BENCHMARK_FILES_SHA = "fef48bba59d59ef84e1bc8ba29cd7e8f3d23dfa7877720141e7bf1a5e12481ec"
COUNT = 10228
SECONDS = 45.0
STOP_NEW = 44.5
WATCHDOG = 50.0
GRACE = 5.0


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def atomic_dump(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    dump(temporary, data)
    temporary.replace(path)


def relative(path):
    return str(path.relative_to(ROOT))


def frozen_propagator():
    require(sha(BENCHMARK / "run.py") == BENCHMARK_SOURCE_SHA, "benchmark source pin")
    spec = importlib.util.spec_from_file_location(
        "frozen_iterative_benchmark", BENCHMARK / "run.py"
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    loaded.pins()
    return loaded


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    expected = {
        "run.py": BENCHMARK_SOURCE_SHA,
        "manifest.json": BENCHMARK_MANIFEST_SHA,
        "benchmark.json": BENCHMARK_RESULT_SHA,
        "files.json": BENCHMARK_FILES_SHA,
    }
    for name, expected_sha in expected.items():
        require(sha(BENCHMARK / name) == expected_sha, "frozen benchmark evidence")
    benchmark = json.loads((BENCHMARK / "benchmark.json").read_text())
    benchmark_manifest = json.loads((BENCHMARK / "manifest.json").read_text())
    require(
        benchmark["complete_benchmark"] and benchmark["completed_cases"] == 1000,
        "complete bounded benchmark",
    )
    producer = frozen_propagator()
    _, _, survivors, _ = producer.load_inputs()
    require(len(survivors) == COUNT, "all input survivors")
    dependencies = dict(benchmark_manifest["dependencies"])
    dependencies.update({relative(BENCHMARK / name): value for name, value in expected.items()})
    dependencies[benchmark["trace_file"]] = benchmark["trace_file_sha256"]
    for path in (HERE / "README.md", HERE / "check_preparation.py"):
        dependencies[relative(path)] = sha(path)
    for path, expected_sha in dependencies.items():
        require(sha(ROOT / path) == expected_sha, "every preparation dependency")
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(__file__),
            "dependencies": dependencies,
            "python_version": platform.python_version(),
            "benchmark_source": relative(BENCHMARK / "run.py"),
            "benchmark_source_sha256": BENCHMARK_SOURCE_SHA,
            "case_count": COUNT,
            "case_order": "Input survivors in saved ascending pair_ordinal order",
            "wall_budget_seconds": SECONDS,
            "stop_starting_new_cases_at_seconds": STOP_NEW,
            "row_deadline_seconds": STOP_NEW,
            "process_watchdog_seconds": WATCHDOG,
            "termination_grace_seconds": GRACE,
            "remaining_domain_per_case": 3003,
            "exact_rows_per_case": 456,
            "cardinality_demand": 44,
            "operation": "Import and call the frozen benchmark propagate function unchanged",
            "initial_assignments": "Empty selected and removed sets for each case",
            "trace_encoding": "One deterministic gzip member per JSON line, compression level6",
            "cursor_encoding": "Atomic cursor with committed trace/survivor byte offsets",
            "cursor_on_cap": "next_survivor_index; complete prefix is exactly [0,cursor)",
            "interrupted_case": "Saved trace prefix; same input index remains uncompleted",
            "retry_or_automatic_resume": False,
            "full_passes_maximum": 1,
            "optimizer_calls": 0,
            "failed_literal_probing": False,
            "launch_requires_root_review": True,
            "scope": benchmark_manifest["scope"],
        },
    )
    print(json.dumps({"prepared": True, "manifest_sha256": sha(HERE / "manifest.json")}))


def pins():
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "full runner source pin")
    require(
        manifest["case_count"] == COUNT
        and manifest["wall_budget_seconds"] == SECONDS
        and manifest["stop_starting_new_cases_at_seconds"] == STOP_NEW
        and manifest["row_deadline_seconds"] == STOP_NEW
        and manifest["process_watchdog_seconds"] == WATCHDOG
        and manifest["termination_grace_seconds"] == GRACE,
        "frozen workload and budgets",
    )
    for path, expected in manifest["dependencies"].items():
        require(sha(ROOT / path) == expected, "frozen full-pass dependency")
    return manifest


def write_member(handle, record):
    payload = (json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n").encode()
    handle.write(gzip.compress(payload, compresslevel=6, mtime=0))
    handle.flush()
    return handle.tell()


def initial_cursor():
    return {
        "next_survivor_index": 0,
        "completed_prefix": [0, 0],
        "completed_prefix_convention": "Half-open input survivor index interval",
        "interrupted_case": None,
        "trace_committed_bytes": 0,
        "survivor_committed_bytes": 0,
        "trace_records": 0,
        "survivor_records": 0,
        "outcomes": {},
        "total_forcing_steps": 0,
        "row_visits": 0,
        "verified_full_cover_candidates": [],
    }


def worker():
    started = time.monotonic()
    manifest = pins()
    launch = json.loads((HERE / "launch.json").read_text())
    require(launch["supervisor_pid"] == os.getppid(), "only the sole live supervisor may launch")
    require(launch["manifest_sha256"] == sha(HERE / "manifest.json"), "launch manifest")
    producer = frozen_propagator()
    arithmetic, data, survivors, _ = producer.load_inputs()
    cursor = json.loads((RAW / "cursor.json").read_text())
    require(cursor == initial_cursor(), "fresh worker cursor; no resume")
    trace_path = RAW / "traces.jsonl.gz"
    survivor_path = RAW / "survivors.jsonl.gz"
    outcomes = Counter()
    with trace_path.open("xb") as traces, survivor_path.open("xb") as remaining:
        for index, original in enumerate(survivors):
            if time.monotonic() - started >= STOP_NEW:
                break
            require(index == cursor["next_survivor_index"], "complete ordered prefix")
            record = producer.propagate(arithmetic, data, original, started + STOP_NEW)
            record["survivor_index"] = index
            if record["outcome"] == "complete_cover_candidate":
                record["verified_cover"] = producer.verify_cover_candidate(
                    arithmetic, record, RAW / f"cover-{record['pair_ordinal']}"
                )
                cursor["verified_full_cover_candidates"].append(record["verified_cover"])
            cursor["trace_committed_bytes"] = write_member(traces, record)
            cursor["trace_records"] += 1
            cursor["total_forcing_steps"] += len(record["trace"])
            cursor["row_visits"] += record["row_visits"]
            if record["outcome"] == "incomplete_wall_budget":
                cursor["interrupted_case"] = {
                    "survivor_index": index,
                    "pair_ordinal": record["pair_ordinal"],
                    "trace_prefix_saved": True,
                    "next_row": record["final_evidence"]["next_row"],
                    "pass": record["final_evidence"]["pass"],
                }
                atomic_dump(RAW / "cursor.json", cursor)
                break
            if record["outcome"] == "survives_row_propagation":
                residual = {
                    key: record[key]
                    for key in (
                        "survivor_index",
                        "pair_ordinal",
                        "partial_id",
                        "profile_id",
                        "selected_count",
                        "removed_count",
                        "selected_mask_sha256",
                        "removed_mask_sha256",
                    )
                }
                cursor["survivor_committed_bytes"] = write_member(remaining, residual)
                cursor["survivor_records"] += 1
            outcomes[record["outcome"]] += 1
            cursor["outcomes"] = dict(outcomes)
            cursor["next_survivor_index"] = index + 1
            cursor["completed_prefix"] = [0, index + 1]
            atomic_dump(RAW / "cursor.json", cursor)
    completed = cursor["next_survivor_index"]
    require(sum(outcomes.values()) == completed, "outcome accounting")
    result = {
        **cursor,
        "manifest_sha256": sha(HERE / "manifest.json"),
        "source_sha256": sha(__file__),
        "propagator_source_sha256": BENCHMARK_SOURCE_SHA,
        "complete": completed == COUNT,
        "requested_cases": COUNT,
        "completed_cases": completed,
        "stop_reason": "complete" if completed == COUNT else "cooperative_wall_budget",
        "proof_records": relative(trace_path),
        "proof_records_sha256": sha(trace_path),
        "survivor_records_path": relative(survivor_path),
        "survivor_records_sha256": sha(survivor_path),
        "cursor_file": relative(RAW / "cursor.json"),
        "cursor_file_sha256": sha(RAW / "cursor.json"),
        "wall_budget_seconds": SECONDS,
        "full_iterative_passes": 1,
        "optimizer_calls": 0,
        "survivor_meaning": "Row-bound fixed point only; no feasibility claim",
        "scope": manifest["scope"],
    }
    elapsed = time.monotonic() - started
    result["elapsed_seconds_including_load_output_and_hashes"] = elapsed
    result["wall_budget_respected"] = elapsed <= SECONDS
    dump(HERE / "result.json", result)
    print(json.dumps({key: result[key] for key in ("complete", "completed_cases", "outcomes")}))


def terminate_group(process, sig):
    try:
        os.killpg(process.pid, sig)
    except ProcessLookupError:
        pass


def bounded_child(command, stdout, stderr):
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True
    )
    watchdog_fired = False
    kill_required = False
    try:
        code = process.wait(timeout=WATCHDOG)
    except subprocess.TimeoutExpired:
        watchdog_fired = True
        terminate_group(process, signal.SIGTERM)
        try:
            code = process.wait(timeout=GRACE)
        except subprocess.TimeoutExpired:
            kill_required = True
            terminate_group(process, signal.SIGKILL)
            code = process.wait()
    return {
        "returncode": code,
        "watchdog_fired": watchdog_fired,
        "kill_required": kill_required,
        "elapsed_seconds": time.monotonic() - started,
        "watchdog_seconds": WATCHDOG,
        "grace_seconds": GRACE,
    }


def run():
    pins()
    require(not (HERE / "result.json").exists() and not RAW.exists(), "one fresh full pass")
    descriptor = os.open(HERE / "launch.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(
            {"manifest_sha256": sha(HERE / "manifest.json"), "supervisor_pid": os.getpid()},
            handle,
        )
        handle.write("\n")
    RAW.mkdir(parents=True)
    atomic_dump(RAW / "cursor.json", initial_cursor())
    with (RAW / "stdout.log").open("xb") as stdout, (RAW / "stderr.log").open("xb") as stderr:
        execution = bounded_child([sys.executable, str(HERE / "run.py"), "worker"], stdout, stderr)
    execution["manifest_sha256"] = sha(HERE / "manifest.json")
    execution["result_present"] = (HERE / "result.json").exists()
    execution["cursor"] = json.loads((RAW / "cursor.json").read_text())
    execution["cursor_file_sha256"] = sha(RAW / "cursor.json")
    execution["stdout_sha256"] = sha(RAW / "stdout.log")
    execution["stderr_sha256"] = sha(RAW / "stderr.log")
    if execution["result_present"]:
        execution["result_sha256"] = sha(HERE / "result.json")
    execution["retry_or_automatic_resume"] = False
    execution["raw_tail_policy"] = "Only committed byte prefixes are certified; retain any tail"
    dump(HERE / "execution.json", execution)
    print(json.dumps(execution, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["run"]:
        run()
    elif sys.argv[1:] == ["worker"]:
        worker()
    else:
        raise SystemExit("Usage: run.py prepare|run; worker is supervisor-only")
