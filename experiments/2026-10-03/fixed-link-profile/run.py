# Document:    Bounded Fixed Link Profile Native Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5049f6f71e3c58e61cc409af5c25d3f0ff3d3d28c620f26ef8ca1f765e049401
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Run four frozen native pilots, at most two single-threaded processes at a time."""

import concurrent.futures
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/fixed-link-profile-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case):
    name = case["name"]
    folder = RAW / "pilots"
    prefix = folder / name
    command = [
        str(RAW / "search"),
        str(ROOT / case["seed_path"]),
        str(case["anchor"]),
        str(case["high_point"]),
        str(case["seed"]),
        str(case["seconds"]),
        str(prefix),
    ]
    began = time.time()
    print(json.dumps({"event": "launch", "name": name, "command": command}), flush=True)
    with (folder / f"{name}.log").open("w") as log, (folder / f"{name}.err").open("w") as err:
        process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=err, check=False)
    events = [json.loads(line) for line in (folder / f"{name}.log").read_text().splitlines()]
    last = events[-1]
    if process.returncode not in [0, 1] or last["event"] != "finished":
        raise RuntimeError(f"pilot {name} did not finish normally")
    if process.returncode != int(last["best_holes"] != 0):
        raise RuntimeError("exit and best-hole count disagree")
    if (folder / f"{name}.err").stat().st_size:
        raise RuntimeError("unexpected native stderr")
    result = {
        "name": name,
        "command": command,
        "seed": case["seed"],
        "requested_seconds": case["seconds"],
        "elapsed_seconds": time.time() - began,
        "started_unix": began,
        "exit": process.returncode,
        "native_result": last,
        "best_sha256": sha(folder / f"{name}-best.txt"),
        "log_sha256": sha(folder / f"{name}.log"),
    }
    print(json.dumps({"event": "completed", **result}), flush=True)
    return result


def main():
    metadata = json.loads((HERE / "environment.json").read_text())
    if sha(ROOT / "scripts/fixed_link_profile_heuristic.cpp") != metadata["source_sha256"]:
        raise RuntimeError("native source changed after review")
    if sha(RAW / "search") != metadata["binaries"]["search"]:
        raise RuntimeError("native binary changed after review")
    cases = json.loads((HERE / "seeds.json").read_text())["cases"]
    for case in cases:
        if sha(ROOT / case["seed_path"]) != case["seed_sha256"]:
            raise RuntimeError("seed changed after review")
    folder = RAW / "pilots"
    folder.mkdir(exist_ok=False)
    (RAW / "run.py").write_bytes(Path(__file__).read_bytes())
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(run, cases):
            results.append(result)
            (folder / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
