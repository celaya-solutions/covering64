# Document:    Non-Solver Controls for Novel Point Link Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4387890027296cba35c5c1883f126e11e14f1b9930358d6834b80e4bc1c07146
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reject old and malformed local witnesses; mock all watchdog outcomes."""

import importlib.util
import json
import signal
import subprocess
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock, call, patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("novel_link_runner", HERE / "run.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def main():
    rejected = []
    for number in range(1, 5):
        data = json.loads((HERE / f"case-{number}-data.json").read_text())
        old = [RUNNER.QUADS[index] for index in data["old_image_quad_ids"][0]]
        cases = {
            "old-image": old,
            "duplicate": sorted([old[0], *old[:-1]]),
            "short": old[:-1],
            "bad-label": sorted([tuple([0, *old[0][1:]]), *old[1:]]),
            "boolean-label": sorted([tuple([False, *old[0][1:]]), *old[1:]]),
        }
        for name, blocks in cases.items():
            try:
                RUNNER.verify_new(blocks, data, HERE / "must-not-be-created")
            except (AssertionError, ValueError, TypeError) as exc:
                rejected.append(
                    {"case": number, "control": name, "rejected": True, "reason": str(exc)}
                )
            else:
                raise AssertionError(f"invalid local witness accepted: {number}/{name}")
    assert not (HERE / "must-not-be-created").exists()
    watchdog = RUNNER.module(RUNNER.BASE, "frozen_watchdog_controls")
    paths = [
        ("normal", [0], [call(timeout=35.0)], [], False, False),
        (
            "term",
            [subprocess.TimeoutExpired("mock", 35), -15],
            [call(timeout=35.0), call(timeout=5.0)],
            [call(123456, signal.SIGTERM)],
            True,
            False,
        ),
        (
            "kill",
            [subprocess.TimeoutExpired("mock", 35), subprocess.TimeoutExpired("mock", 5), -9],
            [call(timeout=35.0), call(timeout=5.0), call()],
            [call(123456, signal.SIGTERM), call(123456, signal.SIGKILL)],
            True,
            True,
        ),
        (
            "term-race",
            [subprocess.TimeoutExpired("mock", 35), 0],
            [call(timeout=35.0), call(timeout=5.0)],
            [call(123456, signal.SIGTERM)],
            True,
            False,
        ),
    ]
    mocked = []
    for name, answers, waits, signals, timed_out, killed in paths:
        process = Mock()
        process.pid = 123456
        process.wait.side_effect = answers
        stdout, stderr = object(), object()
        with (
            patch.object(watchdog.subprocess, "Popen", return_value=process) as popen,
            patch.object(watchdog.os, "killpg") as killpg,
        ):
            if name == "term-race":
                killpg.side_effect = ProcessLookupError
            result = watchdog.bounded_child(["mock"], stdout, stderr)
        assert process.wait.call_args_list == waits and killpg.call_args_list == signals
        popen.assert_called_once_with(
            ["mock"], cwd=RUNNER.ROOT, stdout=stdout, stderr=stderr, start_new_session=True
        )
        assert result["watchdog_fired"] is timed_out and result["kill_required"] is killed
        assert result["returncode"] == answers[-1]
        mocked.append(
            {
                "name": name,
                "passed": True,
                "timeouts": [entry.kwargs.get("timeout") for entry in waits],
                "signals": [int(entry.args[1]) for entry in signals],
            }
        )
    receipt = {
        "passed": True,
        "runner_sha256": sha256((HERE / "run.py").read_bytes()).hexdigest(),
        "watchdog_source_sha256": sha256(RUNNER.BASE.read_bytes()).hexdigest(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "rejected_witness_controls": rejected,
        "mocked_watchdog_controls": mocked,
        "optimizer_calls": 0,
        "real_processes_launched": 0,
        "real_signals_sent": 0,
    }
    (HERE / "controls.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "witness_controls": len(rejected),
                "mocked_watchdog_controls": len(mocked),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
