# Document:    External Watchdog for the Full Affine Support Pass
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4751b19c935bcf1097e50d17aa8af1e960b9dc17ae323a4631155d5a01b624d9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Root launch only, after a frozen independent GO; no retries or resumption."""

import json
import os
import signal
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATE = HERE.parent / "affine-expanded-full-independent/gate.json"
RAW = ROOT / "experiments/scratch/affine-expanded-full-support-v1.0.0"
LOGS = ROOT / "experiments/scratch/affine-expanded-full-launch-v1.0.0"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    require(len(sys.argv) == 2 and sys.argv[1] == "root-authorized-run", "explicit root launch")
    require(
        not LOGS.exists()
        and not RAW.exists()
        and not (HERE / "result.json").exists()
        and not (HERE / "launch-result.json").exists(),
        "no retry or resume",
    )
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(GATE.read_text())
    require(gate["decision"] == "GO", "independent GO required")
    require(gate["manifest_sha256"] == sha(HERE / "manifest.json"), "manifest gate pin")
    require(
        gate["source_sha256"] == manifest["source_sha256"] == sha(HERE / "run.py"),
        "runner source pin",
    )
    require(
        gate["launcher_sha256"] == manifest["launcher_sha256"] == sha(__file__),
        "launcher source pin",
    )
    require(
        manifest["external_watchdog_seconds"] == 660.0
        and manifest["termination_grace_seconds"] == 5.0,
        "watchdog budget",
    )
    LOGS.mkdir(parents=True)
    env = dict(os.environ)
    env["AFFINE_FULL_STARTED_MONOTONIC"] = str(started)
    timed_out, forced_kill = False, False
    with (LOGS / "stdout.log").open("wb") as stdout, (LOGS / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(
            [sys.executable, str(HERE / "run.py"), "run"],
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            process.wait(timeout=max(0.001, 660.0 - (time.monotonic() - started)))
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass  # The child exited after the timeout; still reap it and save the receipt.
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                forced_kill = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # The same exit race can occur at the end of the grace period.
                process.wait()
    cursor = None
    if (RAW / "cursor.json").exists():
        cursor = json.loads((RAW / "cursor.json").read_text())
    result = {
        "returncode": process.returncode,
        "external_timeout": timed_out,
        "forced_kill_after_grace": forced_kill,
        "elapsed_seconds": time.monotonic() - started,
        "within_650_seconds_including_child_receipt": time.monotonic() - started < 650.0,
        "committed_cursor": cursor,
        "source_sha256": sha(HERE / "run.py"),
        "launcher_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(GATE),
        "logs": {str(p.relative_to(ROOT)): sha(p) for p in sorted(LOGS.iterdir())},
        "automatic_retry": False,
        "automatic_resume": False,
    }
    (HERE / "launch-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "committed_cursor"}, sort_keys=True))
    return process.returncode


if __name__ == "__main__":
    sys.exit(main())
