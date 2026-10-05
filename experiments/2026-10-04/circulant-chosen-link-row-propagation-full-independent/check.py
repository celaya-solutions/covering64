# Document:    Independent Full Row Propagation Launch Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b1f9f4a31d2bdac66cb26cc22b10bc012476e848c9054caba69b6fe027265b21
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read frozen inputs and exercise only mocked processes and synthetic records."""

import contextlib
import gzip
import importlib.util
import io
import json
import os
import signal
import subprocess
import tempfile
from collections import Counter
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "circulant-chosen-link-row-propagation-full"
BENCHMARK = HERE.parent / "circulant-chosen-link-row-propagation"
BENCHMARK_AUDIT = HERE.parent / "circulant-row-propagation-independent/benchmark-audit.json"
RUNNER_SHA = "f2f92fee793b23803ee4dc71bd536f345d0e1d3a154735cf889b607b55184173"
MANIFEST_SHA = "b7110cbdd8db86b27d1c302267bc843f50aa0b40ae240b8862ebe4f2b5679ec2"
FILES_SHA = "5b931c607fe5acd605568af83ecc41f2b45da93703c7886d0fe3110c4456c8c0"
PROPAGATOR_SHA = "ce9792cb21e26c29f87a208454a3a52fd241dfe322fd71ed8b50f71cd8893152"
AUDIT_SHA = "dcd303e56b7474a6155ac644603c3b3baa55adb0b2936ba624848d826510360a"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    payload = json.dumps(value, sort_keys=True, indent=2) + "\n"
    require(len(payload.encode()) < 1_000_000, "small receipt")
    Path(path).write_text(payload)


def load_runner():
    spec = importlib.util.spec_from_file_location("mocked_full_row_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


class MockCrash(RuntimeError):
    """Synthetic process interruption; never a real signal."""


def record(original, outcome):
    return {
        **original,
        "outcome": outcome,
        "trace": [{"row": 0, "value": 0, "global_ids": [1]}],
        "row_visits": 2,
        "passes": 1,
        "final_evidence": {"pass": 1, "next_row": 1},
        "selected_count": 0,
        "removed_count": 1,
        "selected_mask_sha256": "synthetic-selected",
        "removed_mask_sha256": "synthetic-removed",
    }


def prefix_check(folder, total=3):
    cursor = read(folder / "cursor.json")
    count = cursor["next_survivor_index"]
    require(type(count) is int and 0 <= count <= total, "bounded integer cursor")
    require(cursor["completed_prefix"] == [0, count], "half-open completed prefix")
    records = {}
    tails = {}
    for label, filename in (("trace", "traces.jsonl.gz"), ("survivor", "survivors.jsonl.gz")):
        data = (folder / filename).read_bytes()
        offset = cursor[label + "_committed_bytes"]
        require(type(offset) is int and 0 <= offset <= len(data), "committed byte boundary")
        payload = gzip.decompress(data[:offset]) if offset else b""
        require(not payload or payload.endswith(b"\n"), "complete JSON line boundary")
        records[label] = [json.loads(line) for line in payload.splitlines()]
        require(len(records[label]) == cursor[label + "_records"], "committed record count")
        tails[label] = len(data) - offset
    traces = records["trace"]
    require(
        [r["survivor_index"] for r in traces[:count]] == list(range(count)), "ordered trace prefix"
    )
    completed = traces[:count]
    require(
        all(
            r["outcome"]
            in {"contradiction", "survives_row_propagation", "complete_cover_candidate"}
            for r in completed
        ),
        "completed trace statuses",
    )
    require(
        dict(Counter(r["outcome"] for r in completed)) == cursor["outcomes"], "outcome accounting"
    )
    require(sum(cursor["outcomes"].values()) == count, "completed accounting")
    require(
        sum(len(r["trace"]) for r in traces) == cursor["total_forcing_steps"], "step accounting"
    )
    require(sum(r["row_visits"] for r in traces) == cursor["row_visits"], "row visit accounting")
    interrupted = cursor["interrupted_case"]
    if interrupted is None:
        require(len(traces) == count, "no extra committed trace")
    else:
        require(len(traces) == count + 1, "one interrupted committed trace")
        require(traces[count]["outcome"] == "incomplete_wall_budget", "interrupted status")
        require(interrupted["survivor_index"] == count, "interrupted index stays uncompleted")
        require(
            interrupted["pair_ordinal"] == traces[count]["pair_ordinal"], "interrupted identity"
        )
        require(interrupted["trace_prefix_saved"] is True, "interrupted saved flag")
        require(interrupted["next_row"] == traces[count]["final_evidence"]["next_row"], "next row")
        require(interrupted["pass"] == traces[count]["final_evidence"]["pass"], "interrupted pass")
    surviving = [r for r in completed if r["outcome"] == "survives_row_propagation"]
    require(len(surviving) == len(records["survivor"]), "survivor accounting")
    for saved, original in zip(records["survivor"], surviving):
        require(all(original[k] == v for k, v in saved.items()), "survivor binding")
    expected_candidates = [
        r["verified_cover"] for r in completed if r["outcome"] == "complete_cover_candidate"
    ]
    require(
        cursor["verified_full_cover_candidates"] == expected_candidates,
        "verified candidate accounting",
    )
    return cursor, tails


def worker_control(runner, scenario):
    survivors = [
        {"pair_ordinal": 100 + i, "partial_id": 10 + i, "profile_id": 20 + i} for i in range(3)
    ]
    outcomes = ["contradiction", "survives_row_propagation", "contradiction"]
    if scenario == "cooperative_interruption":
        outcomes[1] = "incomplete_wall_budget"
    if scenario in ("verified_candidate", "candidate_verifier_failure"):
        outcomes[0] = "complete_cover_candidate"
    producer = SimpleNamespace(
        load_inputs=Mock(return_value=(None, None, survivors, None)),
        propagate=Mock(side_effect=[record(s, o) for s, o in zip(survivors, outcomes)]),
        verify_cover_candidate=Mock(return_value={"witness": "synthetic", "sha256": "synthetic"}),
    )
    if scenario == "candidate_verifier_failure":
        producer.verify_cover_candidate.side_effect = MockCrash("verifier failure")
    times = None
    if scenario == "stop_before_first":
        times = [0, 44.5, 44.5]
    if scenario == "stop_before_second":
        times = [0, 0, 44.5, 44.5]
    with tempfile.TemporaryDirectory(prefix="independent-row-worker-") as directory:
        folder, raw = Path(directory), Path(directory) / "raw"
        raw.mkdir()
        save(folder / "manifest.json", {"synthetic": True})
        save(
            folder / "launch.json",
            {"supervisor_pid": os.getppid(), "manifest_sha256": digest(folder / "manifest.json")},
        )
        runner.atomic_dump(raw / "cursor.json", runner.initial_cursor())
        original_write, original_atomic = runner.write_member, runner.atomic_dump
        trace_calls = atomic_calls = 0

        def write(handle, value):
            nonlocal trace_calls
            trace = Path(handle.name).name == "traces.jsonl.gz"
            if trace:
                trace_calls += 1
            fault = trace_calls == 2 and (
                (trace and scenario in ("before_trace", "mid_trace", "after_trace"))
                or (not trace and scenario in ("before_survivor", "mid_survivor", "after_survivor"))
            )
            if fault:
                if scenario.startswith("before_"):
                    raise MockCrash(scenario)
                if scenario.startswith("mid_"):
                    compressed = gzip.compress((json.dumps(value) + "\n").encode(), mtime=0)
                    handle.write(compressed[: len(compressed) // 2])
                    handle.flush()
                    raise MockCrash(scenario)
                original_write(handle, value)
                raise MockCrash(scenario)
            return original_write(handle, value)

        def atomic(path, value):
            nonlocal atomic_calls
            atomic_calls += 1
            if atomic_calls == 2 and scenario == "before_cursor_replace":
                save(path.with_suffix(path.suffix + ".tmp"), value)
                raise MockCrash(scenario)
            original_atomic(path, value)
            if atomic_calls == 2 and scenario == "after_cursor_replace":
                raise MockCrash(scenario)

        clock = Mock(side_effect=times) if times is not None else Mock(return_value=0)
        crashed = False
        with (
            patch.object(runner, "HERE", folder),
            patch.object(runner, "RAW", raw),
            patch.object(runner, "COUNT", 3),
            patch.object(runner, "pins", return_value={"scope": "synthetic only"}),
            patch.object(runner, "frozen_propagator", return_value=producer),
            patch.object(runner, "relative", side_effect=str),
            patch.object(runner, "write_member", side_effect=write),
            patch.object(runner, "atomic_dump", side_effect=atomic),
            patch.object(runner.time, "monotonic", clock),
            patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no real child")),
            patch.object(runner.os, "killpg", side_effect=AssertionError("no real signal")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            try:
                runner.worker()
            except MockCrash:
                crashed = True
        cursor, tails = prefix_check(raw)
        fault_cases = {
            "before_trace",
            "mid_trace",
            "after_trace",
            "before_survivor",
            "mid_survivor",
            "after_survivor",
            "before_cursor_replace",
            "after_cursor_replace",
            "candidate_verifier_failure",
        }
        expected_count = 3
        if scenario in fault_cases or scenario in (
            "cooperative_interruption",
            "stop_before_second",
        ):
            expected_count = 1
        if scenario in ("stop_before_first", "candidate_verifier_failure"):
            expected_count = 0
        if scenario == "after_cursor_replace":
            expected_count = 2
        require(cursor["next_survivor_index"] == expected_count, "expected saved prefix")
        require(crashed == (scenario in fault_cases), "injected crash observed")
        require(
            (folder / "result.json").exists() is not crashed, "result only after terminal worker"
        )
        for call in producer.propagate.call_args_list:
            require(call.args[3] == 44.5, "exact cooperative row deadline")
        if not crashed:
            result = read(folder / "result.json")
            require(result["completed_cases"] == expected_count, "terminal cursor binding")
            require(result["complete"] == (expected_count == 3), "complete only for every case")
            require(result["wall_budget_seconds"] == 45, "total cooperative budget")
            require(result["wall_budget_respected"] is True, "synthetic timing")
        if scenario == "verified_candidate":
            require(producer.verify_cover_candidate.call_count == 1, "candidate verifier required")
        elif scenario != "candidate_verifier_failure":
            producer.verify_cover_candidate.assert_not_called()
        return {
            "scenario": scenario,
            "completed_prefix": expected_count,
            "crashed": crashed,
            "propagator_calls_mocked": producer.propagate.call_count,
            "ignored_tail_bytes": tails,
        }


def watchdog_controls(runner):
    results = []
    for name, waits, kill_errors, signals, watchdog, killed in (
        ("normal", [0], [], [], False, False),
        (
            "term",
            [subprocess.TimeoutExpired("synthetic", 50), -15],
            [],
            [signal.SIGTERM],
            True,
            False,
        ),
        (
            "kill",
            [
                subprocess.TimeoutExpired("synthetic", 50),
                subprocess.TimeoutExpired("synthetic", 5),
                -9,
            ],
            [],
            [signal.SIGTERM, signal.SIGKILL],
            True,
            True,
        ),
        (
            "term_exit_race",
            [subprocess.TimeoutExpired("synthetic", 50), 0],
            [ProcessLookupError()],
            [signal.SIGTERM],
            True,
            False,
        ),
        (
            "kill_exit_race",
            [
                subprocess.TimeoutExpired("synthetic", 50),
                subprocess.TimeoutExpired("synthetic", 5),
                0,
            ],
            [None, ProcessLookupError()],
            [signal.SIGTERM, signal.SIGKILL],
            True,
            True,
        ),
    ):
        process = Mock(pid=424242)
        process.wait.side_effect = waits
        with (
            patch.object(runner.subprocess, "Popen", return_value=process) as popen,
            patch.object(runner.os, "killpg", side_effect=kill_errors or None) as kill,
            patch.object(runner.time, "monotonic", side_effect=[0, 1]),
        ):
            result = runner.bounded_child(["synthetic-child"], io.BytesIO(), io.BytesIO())
        require(
            popen.call_count == 1 and popen.call_args.kwargs["start_new_session"] is True,
            "one isolated mocked child",
        )
        require([call.args[1] for call in kill.call_args_list] == signals, "exact signal path")
        require(
            all(call.args[0] == process.pid for call in kill.call_args_list), "child group only"
        )
        require(process.wait.call_args_list[0].kwargs == {"timeout": 50.0}, "external watchdog")
        if watchdog:
            require(process.wait.call_args_list[1].kwargs == {"timeout": 5.0}, "termination grace")
        require(
            result["watchdog_fired"] == watchdog and result["kill_required"] == killed,
            "watchdog flags",
        )
        require(result["returncode"] == waits[-1], "final child return code")
        results.append({"scenario": name, **result})
    return results


def wrapper_control(runner, status):
    with tempfile.TemporaryDirectory(prefix="independent-row-supervisor-") as directory:
        folder, raw = Path(directory), Path(directory) / "raw"
        save(folder / "manifest.json", {"synthetic": True})

        def child(command, stdout, stderr):
            require(command[-1] == "worker", "single worker command")
            stdout.write(b"synthetic stdout\n")
            stderr.write(b"")
            if status == "complete":
                save(folder / "result.json", {"synthetic": True})
            return {
                "returncode": 0 if status == "complete" else -9,
                "watchdog_fired": status != "complete",
                "kill_required": status != "complete",
            }

        with (
            patch.object(runner, "HERE", folder),
            patch.object(runner, "RAW", raw),
            patch.object(runner, "pins", return_value={}),
            patch.object(runner, "bounded_child", side_effect=child) as bounded,
            patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no real process")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            runner.run()
            require(bounded.call_count == 1, "one wrapper child")
            try:
                runner.run()
            except AssertionError:
                pass
            else:
                raise AssertionError("wrapper repeated a launch")
            require(bounded.call_count == 1, "no retry after terminal or killed child")
        result = read(folder / "execution.json")
        require(result["result_present"] == (status == "complete"), "terminal presence recorded")
        require(result["retry_or_automatic_resume"] is False, "no automatic resume")
        require(result["cursor"] == runner.initial_cursor(), "supervisor preserves cursor")
        require(result["cursor_file_sha256"] == digest(raw / "cursor.json"), "cursor receipt hash")
        require(result["stdout_sha256"] == digest(raw / "stdout.log"), "stdout receipt hash")
        require(result["stderr_sha256"] == digest(raw / "stderr.log"), "stderr receipt hash")
        return {"scenario": status, "mocked_children": bounded.call_count, "retry_rejected": True}


def main():
    for path, expected in (
        (PRODUCER / "run.py", RUNNER_SHA),
        (PRODUCER / "manifest.json", MANIFEST_SHA),
        (PRODUCER / "files.json", FILES_SHA),
        (BENCHMARK / "run.py", PROPAGATOR_SHA),
        (BENCHMARK_AUDIT, AUDIT_SHA),
    ):
        require(digest(path) == expected, "frozen top-level pin")
    manifest = read(PRODUCER / "manifest.json")
    for path, expected in manifest["dependencies"].items():
        require(digest(ROOT / path) == expected, "manifest dependency: " + path)
    audit = read(BENCHMARK_AUDIT)
    require(audit["passed"] is True and audit["cases"] == 1000, "independent benchmark audit")
    require(audit["force_steps_replayed"] == 79165, "audited force steps")
    require(
        audit["outcomes"] == {"contradiction": 893, "survives_row_propagation": 107},
        "audited outcomes",
    )
    require(
        audit["benchmark_sha256"] == digest(BENCHMARK / "benchmark.json"),
        "benchmark result binding",
    )
    require(
        audit["manifest_sha256"] == digest(BENCHMARK / "manifest.json"),
        "benchmark manifest binding",
    )
    require(manifest["source_sha256"] == RUNNER_SHA, "runner manifest binding")
    require(manifest["benchmark_source_sha256"] == PROPAGATOR_SHA, "unchanged propagator binding")
    for key, expected in {
        "case_count": 10228,
        "wall_budget_seconds": 45.0,
        "stop_starting_new_cases_at_seconds": 44.5,
        "row_deadline_seconds": 44.5,
        "process_watchdog_seconds": 50.0,
        "termination_grace_seconds": 5.0,
        "remaining_domain_per_case": 3003,
        "exact_rows_per_case": 456,
        "cardinality_demand": 44,
        "full_passes_maximum": 1,
        "optimizer_calls": 0,
        "failed_literal_probing": False,
        "retry_or_automatic_resume": False,
    }.items():
        require(manifest[key] == expected, "exact scope and budget: " + key)
    runner = load_runner()
    require(runner.pins() == manifest, "producer read-only pin guard")
    scenarios = (
        "normal",
        "cooperative_interruption",
        "stop_before_first",
        "stop_before_second",
        "verified_candidate",
        "candidate_verifier_failure",
        "before_trace",
        "mid_trace",
        "after_trace",
        "before_survivor",
        "mid_survivor",
        "after_survivor",
        "before_cursor_replace",
        "after_cursor_replace",
    )
    workers = [worker_control(runner, scenario) for scenario in scenarios]
    watchdogs = watchdog_controls(runner)
    wrappers = [wrapper_control(runner, status) for status in ("complete", "killed")]
    review = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "runner_sha256": RUNNER_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "producer_files_sha256": FILES_SHA,
        "benchmark_source_sha256": PROPAGATOR_SHA,
        "independent_benchmark_audit_sha256": AUDIT_SHA,
        "dependency_pins_checked": len(manifest["dependencies"]),
        "worker_controls": workers,
        "watchdog_controls": watchdogs,
        "wrapper_controls": wrappers,
        "actual_propagation_calls": 0,
        "actual_processes": 0,
        "actual_signals": 0,
        "optimizer_calls": 0,
        "durability_scope": "Atomic cursor and flushed gzip prefixes for process interruption; "
        "not a power-loss or storage-failure guarantee.",
        "arithmetic_scope": "Frozen benchmark propagator independently checked on all saved "
        "1000 benchmark cases; full runtime traces need separate replay.",
        "scope": manifest["scope"],
    }
    save(HERE / "review.json", review)
    save(
        HERE / "gate.json",
        {
            "decision": "GO",
            "runner_sha256": RUNNER_SHA,
            "manifest_sha256": MANIFEST_SHA,
            "independent_review_sha256": digest(HERE / "review.json"),
            "independent_benchmark_audit_sha256": AUDIT_SHA,
            "maximum_launches": 1,
            "case_count": 10228,
            "cooperative_seconds": 45,
            "stop_new_and_row_deadline_seconds": 44.5,
            "watchdog_seconds": 50,
            "grace_seconds": 5,
            "retry_or_resume_authorized": False,
            "optimizer_calls_authorized": 0,
            "scope": manifest["scope"],
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "mocked_controls": 21,
                "review_sha256": digest(HERE / "review.json"),
                "gate_sha256": digest(HERE / "gate.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
