# Document:    Guarded Full Circulant Link Support Launch
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8eaf457651264c50fe4b1a01cb2f4fa63475c9ac6e1ee3b5428e17f0c3db774e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One guarded finite-screen launch with an external fifty-second watchdog."""

import argparse
import json
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FULL = ROOT / "experiments/2026-10-04/circulant-chosen-link-support-full"
EXPECTED_MANIFEST = "2c12c4372ef388026d7a6238b7789f72ad8dcaf74ba471035cb2dcdf86dc4439"


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def launch(gate_path):
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] is True and gate["launch_permitted"] is True
    assert gate["manifest_sha256"] == sha(FULL / "manifest.json") == EXPECTED_MANIFEST
    manifest = json.loads((FULL / "manifest.json").read_text())
    assert sha(FULL / "run.py") == manifest["source_sha256"]
    for path, digest in manifest["dependencies"].items():
        assert sha(ROOT / path) == digest, path
    assert sha(HERE / "catalog-audit.json") == (
        "e832913ef7d0ead42fdcb9c75538654e6dedfdb81091dd44519fa900cfbfe158"
    )
    command = [sys.executable, str(FULL / "run.py"), "run"]
    receipt = {
        "manifest_sha256": EXPECTED_MANIFEST,
        "gate_sha256": sha(gate_path),
        "source_sha256": sha(Path(__file__)),
        "cooperative_processing_seconds": 45,
        "external_watchdog_seconds": 50,
        "termination_grace_seconds": 5,
        "command": command,
        "started_unix": time.time(),
        "retry": False,
    }
    with (HERE / "full-launch.json").open("x") as output:
        json.dump(receipt, output, indent=2, sort_keys=True)
        output.write("\n")
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    watchdog = terminated = killed = False
    try:
        stdout, stderr = process.communicate(timeout=50)
    except subprocess.TimeoutExpired:
        watchdog = terminated = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            killed = True
            process.kill()
            stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    (HERE / "full-stdout.log").write_text(stdout)
    (HERE / "full-stderr.log").write_text(stderr)
    result = receipt | {
        "child_process_elapsed_seconds": elapsed,
        "elapsed_includes_child_hashing_and_outputs": True,
        "returncode": process.returncode,
        "watchdog": watchdog,
        "terminated": terminated,
        "killed": killed,
        "stdout_sha256": sha(HERE / "full-stdout.log"),
        "stderr_sha256": sha(HERE / "full-stderr.log"),
        "child_result_sha256": sha(FULL / "result.json")
        if (FULL / "result.json").is_file()
        else None,
    }
    with (HERE / "full-runtime.json").open("x") as output:
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(result, sort_keys=True))
    if process.returncode or watchdog:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    launch(parser.parse_args().gate)
