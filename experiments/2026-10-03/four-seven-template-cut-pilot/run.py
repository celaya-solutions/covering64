# Document:    Single Heavy-Cut Guided Cycle Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ddc506ef6c6dddba909d1de48ec5589c03ef1323d3d79a8cc81fa06647f0875a
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
PREVIOUS = HERE.parent / "four-seven-template-cut"
RAW = ROOT / "experiments/scratch/four-seven-template-cut-pilot-v1.0.0"
NATIVE = ROOT / "experiments/scratch/four-seven-template-cut-v1.3.0/search"
SOURCE = ROOT / "scripts/four_seven_template_cut_heuristic.cpp"
CUT = HERE.parent / "lookahead-parametric-cut/cut.json"
SEED = HERE.parent / "four-seven-template-native-lookahead/performance-cycle-best.txt"
GATE = PREVIOUS / "root-read-only.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists(), "single fresh pilot required"
    gate = json.loads(GATE.read_text())
    audit = json.loads((PREVIOUS / "audit.json").read_text())
    assert gate["passed"] and audit["passed"]
    assert sha(SOURCE) == gate["source_sha256"] == audit["source_sha256"]
    assert sha(NATIVE) == gate["binary_sha256"] == audit["binaries"]["search"]
    assert sha(CUT) == audit["cut_sha256"]
    assert sha(PREVIOUS / "audit.py") == audit["checker_sha256"]
    assert sha(SEED) == "8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3"
    config = next(
        c
        for c in json.loads(
            (HERE.parent / "four-seven-template-native-lookahead/seeds.json").read_text()
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
        "2026104722",
        "300",
        str(RAW / "cycle"),
        "--cut-guide",
    ]
    manifest = {
        "version": "v1.0.0",
        "native_version": "v1.3.0",
        "seed": 2026104722,
        "native_seconds": 300,
        "hard_wait_seconds": 330,
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
        "native_audit_sha256": sha(PREVIOUS / "audit.json"),
        "build_metadata_sha256": sha(PREVIOUS / "build.json"),
        "source_seed": str(SEED.relative_to(ROOT)),
        "source_catalog": str(catalog.relative_to(ROOT)),
        "source_revision": sha(SOURCE),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "One authorized constructive cycle pilot with one labeled cut guide; "
        "no exclusion or global covering claim.",
    }
    save(HERE / "manifest.json", manifest)
    save(RAW / "manifest.json", manifest)
    before = time.monotonic()
    forced = False
    with (RAW / "stdout.jsonl").open("w") as stdout, (RAW / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        print(
            json.dumps({"started": True, "pid": process.pid, "seed": 2026104722, "seconds": 300}),
            flush=True,
        )
        try:
            code = process.wait(timeout=330)
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
