# Document:    Mocked Watchdog Controls for Conditional Link Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      19d802579e9ad4d2a6284138772b3ea542763f7e29c8f519a3b3c945ce5224c9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Test normal, TERM, and KILL branches without launching any subprocess."""

import importlib.util
import json
import signal
import subprocess
from hashlib import sha256
from pathlib import Path
from unittest.mock import Mock, call, patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("completion_runner", HERE / "run.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def main():
    results = {}
    cases = [
        ("normal", [0], [call(timeout=35.0)], [], False, False),
        (
            "term_after_watchdog",
            [subprocess.TimeoutExpired("mock", 35), -15],
            [call(timeout=35.0), call(timeout=5.0)],
            [call(123456, signal.SIGTERM)],
            True,
            False,
        ),
        (
            "kill_after_grace",
            [subprocess.TimeoutExpired("mock", 35), subprocess.TimeoutExpired("mock", 5), -9],
            [call(timeout=35.0), call(timeout=5.0), call()],
            [call(123456, signal.SIGTERM), call(123456, signal.SIGKILL)],
            True,
            True,
        ),
    ]
    for name, answers, waits, signals, watchdog, killed in cases:
        process = Mock()
        process.pid = 123456
        process.wait.side_effect = answers
        stdout, stderr = object(), object()
        with (
            patch.object(RUNNER.subprocess, "Popen", return_value=process) as popen,
            patch.object(RUNNER.os, "killpg") as killpg,
        ):
            result = RUNNER.bounded_child(["mock-command"], stdout, stderr)
        assert process.wait.call_args_list == waits
        assert killpg.call_args_list == signals
        popen.assert_called_once_with(
            ["mock-command"],
            cwd=RUNNER.ROOT,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        assert result["watchdog_fired"] is watchdog and result["kill_required"] is killed
        assert result["returncode"] == answers[-1]
        results[name] = {
            "passed": True,
            "wait_timeouts": [entry.kwargs.get("timeout") for entry in waits],
            "signals": [int(entry.args[1]) for entry in signals],
            "watchdog_fired": watchdog,
            "kill_required": killed,
        }
    output = {
        "passed": True,
        "runner_sha256": sha256((HERE / "run.py").read_bytes()).hexdigest(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "real_process_launches": 0,
        "real_signals_sent": 0,
        "optimizer_launches": 0,
        "cases": results,
    }
    (HERE / "controls.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "mock_cases": len(cases), "optimizer_launches": 0}))


if __name__ == "__main__":
    main()
