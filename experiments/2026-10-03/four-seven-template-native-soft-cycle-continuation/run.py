# Document:    Verified Twelve-Hole Cycle Continuation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a81bf6ed290d200b2dfb0ba043ea763c3220ab4b2a685b47ae0b496e18e9e673
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Run one frozen 600-second cycle continuation and reuse the frozen auditors."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / "four-seven-template-native-soft"
RAW = ROOT / "experiments/scratch/four-seven-template-native-soft-cycle-continuation-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    frozen = json.loads((HERE / "inputs.json").read_text())
    for path, expected in frozen["files"].items():
        if sha(ROOT / path) != expected:
            raise ValueError("frozen input changed: " + path)
    case = json.loads((HERE / "seeds.json").read_text())["cases"][0]
    if (case["name"], case["seconds"], case["seed"], case["workers"]) != (
        "cycle",
        600,
        2026103972,
        1,
    ):
        raise ValueError("continuation budget or identity changed")
    sys.path.insert(0, str(BASE))
    import audit
    import diagnose

    audit.RAW = RAW
    seed = audit.inspect(ROOT / case["seed_path"], case)
    if (seed["holes"], seed["score"]) != (12, 92):
        raise ValueError("wrong initial state")
    save(HERE / "seed-audit.json", seed)
    folder = RAW / "pilots"
    command = [
        str(ROOT / frozen["binary_path"]),
        str(ROOT / case["catalog_path"]),
        str(ROOT / case["seed_path"]),
        str(case["seed"]),
        str(case["seconds"]),
        str(folder / "cycle"),
    ]
    began = time.time()
    print(json.dumps({"event": "launch", "command": command}), flush=True)
    with (folder / "cycle.log").open("w") as log, (folder / "cycle.err").open("w") as err:
        process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=err, check=False)
    events = [json.loads(line) for line in (folder / "cycle.log").read_text().splitlines()]
    last = events[-1]
    if last["event"] != "finished" or process.returncode != int(last["best_holes"] != 0):
        raise ValueError("continuation did not finish normally")
    if (folder / "cycle.err").stat().st_size:
        raise ValueError("unexpected native diagnostics")
    if process.returncode == 0:
        witness = audit.inspect(folder / "cycle-best.txt", case)
        if witness["holes"]:
            raise ValueError("native zero did not pass both independent covering checks")
        save(HERE / "zero-cover-checks.json", witness)
    result = {
        "name": "cycle",
        "command": command,
        "started_unix": began,
        "elapsed_seconds": time.time() - began,
        "requested_seconds": 600,
        "seed": 2026103972,
        "workers": 1,
        "exit": process.returncode,
        "native_result": last,
        "log_sha256": sha(folder / "cycle.log"),
        "raw_best_sha256": sha(folder / "cycle-raw-best.txt"),
        "score_best_sha256": sha(folder / "cycle-score-best.txt"),
    }
    save(HERE / "results.json", result)
    save(RAW / "results.json", result)
    print(json.dumps({"event": "native_complete", **result}), flush=True)
    report = audit.audit(folder)
    save(HERE / "pilot-audit.json", report)
    diagnose.HERE = HERE
    diagnose.RAW = RAW
    diagnose.main()
    print(
        json.dumps(
            {
                "event": "audited",
                "snapshots": report["snapshot_count"],
                "operations": report["operation_count"],
                "covers": report["covers"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
