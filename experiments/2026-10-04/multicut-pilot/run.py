# Document:    Single Fourteen-Cut Guided Cycle Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      61e15b9557f5fdb81dd1bd42f3488a2922a859f170b61a39cfcb9d31bfa49eec
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = HERE.parent / "multicut-native-final"
RAW = ROOT / "experiments/scratch/multicut-pilot-v1.0.0"
NATIVE = ROOT / "experiments/scratch/multicut-native-v1.4.1/search"
SOURCE = ROOT / "scripts/four_seven_template_multicut_final_heuristic.cpp"
CUT = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
SEED = ROOT / "experiments/2026-10-03/cut-pilot-heavy-completion/seed.txt"
GATE = HERE.parent / "multicut-native-root/audit-v1.4.1.json"
RUNTIME_GATE = HERE.parent / "multicut-independent/audit-v1.4.1.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists(), "single fresh pilot required"
    gate = json.loads(GATE.read_text())
    audit = json.loads((PREVIOUS / "audit.json").read_text())
    runtime_gate = json.loads(RUNTIME_GATE.read_text())
    assert gate["passed"] and audit["passed"] and runtime_gate["passed"]
    assert sha(SOURCE) == gate["source_sha256"] == audit["source_sha256"]
    assert sha(NATIVE) == audit["binaries"]["search"]
    assert sha(SOURCE) == runtime_gate["source_sha256"]
    assert sha(NATIVE) == runtime_gate["binary_sha256"]
    assert sha(CUT) == audit["cut_sha256"]
    assert sha(PREVIOUS / "audit.py") == audit["checker_sha256"]
    assert sha(SEED) == "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93"
    config = next(
        c
        for c in json.loads(
            (
                ROOT / "experiments/2026-10-03/four-seven-template-native-lookahead/seeds.json"
            ).read_text()
        )["cases"]
        if c["name"] == "cycle"
    )
    catalog = ROOT / config["catalog_path"]
    assert sha(catalog) == config["catalog_sha256"]
    RAW.mkdir(parents=True)
    inputs = RAW / "inputs"
    inputs.mkdir()
    for src, name in [
        (NATIVE, "search"),
        (SOURCE, SOURCE.name),
        (SEED, "seed.txt"),
        (catalog, "catalog.txt"),
        (CUT, "cut.json"),
        (GATE, "root-gate.json"),
        (RUNTIME_GATE, "runtime-gate.json"),
        (PREVIOUS / "audit.json", "native-audit.json"),
        (PREVIOUS / "build.json", "build.json"),
        (PREVIOUS / "audit.py", "native-audit.py"),
        (Path(__file__), "run.py"),
    ]:
        shutil.copy2(src, inputs / name)
        assert sha(inputs / name) == sha(src)
    command = [
        str(inputs / "search"),
        str(inputs / "catalog.txt"),
        str(inputs / "seed.txt"),
        "2026104051",
        "180",
        str(RAW / "cycle"),
        "--cut-guide",
        "--cut-weight",
        "10",
    ]
    manifest = {
        "version": "v1.0.0",
        "native_version": "v1.4.1",
        "seed": 2026104051,
        "native_seconds": 180,
        "hard_wait_seconds": 210,
        "processes": 1,
        "workers": 1,
        "command": command,
        "runner_sha256": sha(Path(__file__)),
        "source_sha256": sha(SOURCE),
        "binary_sha256": sha(NATIVE),
        "seed_sha256": sha(SEED),
        "catalog_sha256": sha(catalog),
        "cut_sha256": sha(CUT),
        "gate_sha256": sha(GATE),
        "runtime_gate_sha256": sha(RUNTIME_GATE),
        "cut_weight": 10,
        "native_audit_sha256": sha(PREVIOUS / "audit.json"),
        "build_metadata_sha256": sha(PREVIOUS / "build.json"),
        "source_seed": str(SEED.relative_to(ROOT)),
        "source_catalog": str(catalog.relative_to(ROOT)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "One authorized constructive cycle pilot with fourteen-cut guide; "
        "no exclusion or global covering claim.",
    }
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    before = time.monotonic()
    forced = False
    with (RAW / "stdout.jsonl").open("w") as stdout, (RAW / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        print(
            json.dumps({"started": True, "pid": process.pid, "seed": 2026104051, "seconds": 180}),
            flush=True,
        )
        try:
            code = process.wait(timeout=210)
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
        "wrapper_seconds": time.monotonic() - before,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "stdout_sha256": sha(RAW / "stdout.jsonl"),
        "stderr_sha256": sha(RAW / "stderr.log"),
        "native_finished": next((e for e in reversed(events) if e["event"] == "finished"), None),
        "scope": manifest["scope"],
    }
    save(HERE / "result.json", result)
    save(RAW / "result.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
