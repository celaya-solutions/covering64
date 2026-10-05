# Document:    Preparation Controls for Full Circulant Row Propagation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fb3642e37894757827f8d115acef2619ff9a868d56681057891c9395dd7993a0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Mock watchdog and cursor controls; no real case propagation or child process."""

from __future__ import annotations

import contextlib
import gzip
import importlib.util
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("full_row_runner_controls", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def watchdog_controls():
    cases = [
        ([0], False, False, [50.0], []),
        ([7], False, False, [50.0], []),
        (
            [subprocess.TimeoutExpired("mock", 50), -15],
            True,
            False,
            [50.0, 5.0],
            [runner.signal.SIGTERM],
        ),
        (
            [subprocess.TimeoutExpired("mock", 50), subprocess.TimeoutExpired("mock", 5), -9],
            True,
            True,
            [50.0, 5.0, None],
            [runner.signal.SIGTERM, runner.signal.SIGKILL],
        ),
    ]
    for waits, watchdog, kill, deadlines, signals in cases:
        child = Mock(pid=314159)
        child.wait.side_effect = waits
        with (
            patch.object(runner.subprocess, "Popen", return_value=child) as launch,
            patch.object(runner, "terminate_group") as terminate,
        ):
            result = runner.bounded_child(["mock-child"], None, None)
        assert result["watchdog_fired"] is watchdog
        assert result["kill_required"] is kill
        assert [call.kwargs.get("timeout") for call in child.wait.call_args_list] == deadlines
        assert [call.args[1] for call in terminate.call_args_list] == signals
        assert launch.call_count == 1
        assert launch.call_args.kwargs["start_new_session"] is True
    with patch.object(runner.os, "killpg", side_effect=ProcessLookupError) as send:
        runner.terminate_group(Mock(pid=314159), runner.signal.SIGTERM)
    assert send.call_count == 1
    return 5


def compressed_prefix_controls():
    records = [{"case": 0, "trace": [1, 2]}, {"case": 1, "trace": [3]}]
    handle = io.BytesIO()
    offsets = [runner.write_member(handle, record) for record in records]
    assert offsets[0] < offsets[1]
    assert [json.loads(line) for line in gzip.decompress(handle.getvalue()).splitlines()] == records
    # The committed prefix remains independently decodable even if a tail is damaged.
    raw_with_tail = handle.getvalue() + gzip.compress(b"uncommitted\n", mtime=0)[:11]
    prefix = raw_with_tail[: offsets[-1]]
    assert [json.loads(line) for line in gzip.decompress(prefix).splitlines()] == records
    failed = False
    try:
        gzip.decompress(raw_with_tail)
    except (EOFError, OSError):
        failed = True
    assert failed
    return 3


def synthetic_record(original, outcome):
    return {
        **original,
        "outcome": outcome,
        "trace": [{"row": 0, "value": 0, "global_ids": [1365]}],
        "row_visits": 1,
        "selected_count": 0,
        "removed_count": 1,
        "selected_mask_sha256": "synthetic-selected",
        "removed_mask_sha256": "synthetic-removed",
        "final_evidence": {"next_row": 1, "pass": 1},
    }


def worker_cursor_control(interrupt):
    survivors = [
        {"pair_ordinal": value + 100, "partial_id": value, "profile_id": value}
        for value in range(3)
    ]
    outcomes = ["contradiction", "survives_row_propagation", "contradiction"]
    if interrupt:
        outcomes[1] = "incomplete_wall_budget"
    producer = SimpleNamespace(
        load_inputs=Mock(return_value=(None, None, survivors, None)),
        propagate=Mock(
            side_effect=[
                synthetic_record(original, outcome)
                for original, outcome in zip(survivors, outcomes)
            ]
        ),
        verify_cover_candidate=Mock(side_effect=AssertionError("unexpected synthetic candidate")),
    )
    with tempfile.TemporaryDirectory(prefix="circulant-row-controls-") as directory:
        folder = Path(directory)
        raw = folder / "raw"
        raw.mkdir()
        runner.dump(folder / "manifest.json", {"synthetic": True})
        runner.dump(
            folder / "launch.json",
            {
                "supervisor_pid": os.getppid(),
                "manifest_sha256": runner.sha(folder / "manifest.json"),
            },
        )
        runner.atomic_dump(raw / "cursor.json", runner.initial_cursor())
        with (
            patch.object(runner, "HERE", folder),
            patch.object(runner, "RAW", raw),
            patch.object(runner, "COUNT", 3),
            patch.object(runner, "pins", return_value={"scope": "synthetic control"}),
            patch.object(runner, "frozen_propagator", return_value=producer),
            patch.object(runner, "relative", side_effect=str),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            runner.worker()
        result = json.loads((folder / "result.json").read_text())
        cursor = json.loads((raw / "cursor.json").read_text())
        proof_bytes = (raw / "traces.jsonl.gz").read_bytes()
        survivor_bytes = (raw / "survivors.jsonl.gz").read_bytes()
        assert cursor["trace_committed_bytes"] == len(proof_bytes)
        assert cursor["survivor_committed_bytes"] == len(survivor_bytes)
        proofs = [json.loads(line) for line in gzip.decompress(proof_bytes).splitlines()]
        remaining = [json.loads(line) for line in gzip.decompress(survivor_bytes).splitlines()]
        completed = 1 if interrupt else 3
        assert result["completed_cases"] == completed
        assert cursor["completed_prefix"] == [0, completed]
        assert cursor["next_survivor_index"] == completed
        assert result["complete"] is not interrupt
        assert cursor["trace_records"] == len(proofs) == producer.propagate.call_count
        assert cursor["survivor_records"] == len(remaining) == (0 if interrupt else 1)
        assert sum(cursor["outcomes"].values()) == completed
        if interrupt:
            assert cursor["interrupted_case"]["survivor_index"] == 1
            assert cursor["interrupted_case"]["next_row"] == 1
            assert cursor["interrupted_case"]["trace_prefix_saved"] is True
            assert proofs[-1]["outcome"] == "incomplete_wall_budget"
        else:
            assert cursor["interrupted_case"] is None
            assert remaining[0]["pair_ordinal"] == 101
        producer.verify_cover_candidate.assert_not_called()
    return 1


if __name__ == "__main__":
    controls = watchdog_controls() + compressed_prefix_controls()
    controls += worker_cursor_control(False) + worker_cursor_control(True)
    print(
        json.dumps(
            {
                "passed_controls": controls,
                "real_child_processes": 0,
                "real_process_signals": 0,
                "real_propagation_calls": 0,
                "optimizer_calls": 0,
            },
            indent=2,
        )
    )
