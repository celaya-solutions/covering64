# Document:    Single Unrestricted Repair from the Five-Hole LP-Guided Seed
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      16f4c0574e35a053886827f7cb2400dc84d974a4d5e422dd6c1b296985c854fd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/five-hole-unrestricted-repair-2026104061"
BASE = ROOT / "experiments/2026-10-03/filter-fan-repair"
BINARY = ROOT / "experiments/scratch/filter-fan-repair-v1.0.0-final-20261003/search"
SEED = HERE.parent / "lp-guided-best-lp/seed.txt"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    gate = json.loads((BASE / "root-audit.json").read_text())
    preflight = json.loads((BASE / "preflight.json").read_text())
    assert gate["passed"] and preflight["passed"]
    assert sha(BASE / "search.cpp") == gate["source_sha256"]
    assert sha(BINARY) == gate["binary_sha256"]
    for path, expected in preflight["hashes"].items():
        assert sha(ROOT / path) == expected
    assert sha(SEED) == "8b9a64761c9547e15a82c9435e8a6837ffa05d34c12ae420533550ea2f1d6fc4"
    RAW.mkdir(parents=True)
    inputs = RAW / "inputs"
    inputs.mkdir()
    for path in [
        BASE / "search.cpp",
        BASE / "root-audit.json",
        BASE / "preflight.json",
        BASE / "check_traces.py",
        BINARY,
        SEED,
        Path(__file__),
    ]:
        shutil.copy2(path, inputs / path.name)
    command = [
        str(inputs / "search"),
        str(inputs / "seed.txt"),
        "2026104061",
        "60",
        "beam",
        str(RAW / "repair"),
        "12",
        "6",
        "12",
    ]
    manifest = {
        "version": "v1.0.0",
        "seed": 2026104061,
        "seconds": 60,
        "workers": 1,
        "mode": "beam",
        "width": 12,
        "fan": 6,
        "depth": 12,
        "blocks_available": 4368,
        "mutable_slots": 64,
        "fixed_heavy_blocks": 0,
        "incidence_restrictions": False,
        "source_sha256": sha(BASE / "search.cpp"),
        "binary_sha256": sha(BINARY),
        "seed_sha256": sha(SEED),
        "gate_sha256": sha(BASE / "root-audit.json"),
        "preflight_sha256": sha(BASE / "preflight.json"),
        "trace_checker_sha256": sha(BASE / "check_traces.py"),
        "runner_sha256": sha(Path(__file__)),
        "command": command,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "One bounded unrestricted construction attempt. No nonexistence claim.",
    }
    save(HERE / "manifest.json", manifest)
    started, forced = time.monotonic(), False
    with (RAW / "stdout.jsonl").open("w") as stdout, (RAW / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        print(json.dumps({"started": True, "pid": process.pid, "seconds": 60}), flush=True)
        try:
            code = process.wait(timeout=80)
        except subprocess.TimeoutExpired:
            forced = True
            process.terminate()
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait(timeout=5)
    events = [json.loads(line) for line in (RAW / "stdout.jsonl").read_text().splitlines()]
    result = {
        "exit": code,
        "forced_termination": forced,
        "wrapper_seconds": time.monotonic() - started,
        "manifest_sha256": sha(HERE / "manifest.json"),
        "stdout_sha256": sha(RAW / "stdout.jsonl"),
        "stderr_sha256": sha(RAW / "stderr.log"),
        "traces_sha256": sha(RAW / "repair-traces.jsonl"),
        "final": events[-1],
        "scope": manifest["scope"],
    }
    save(HERE / "result.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
