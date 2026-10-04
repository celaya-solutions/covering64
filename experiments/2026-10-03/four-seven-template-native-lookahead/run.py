# Document:    Bounded Anchor-Pair Lookahead Native Pilot
# Version:     v1.2.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3360401c4db35ad30a8d32476039fc8567239781763534328fb871d32b245873
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Run two frozen native pilots, one single-threaded process."""

import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-lookahead-v1.2.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case):
    name = case["name"]
    folder = RAW / "pilots"
    prefix = folder / name
    command = [
        str(RAW / "search"),
        str(ROOT / case["catalog_path"]),
        str(ROOT / case["seed_path"]),
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
    zero_checks = []
    if process.returncode == 0:
        for label, prefix_args in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", [sys.executable, "scripts/check_cover.py"]),
        ]:
            checked = subprocess.run(
                prefix_args + [str(folder / f"{name}-best.txt"), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            (folder / f"{name}-cover-{label}.json").write_text(checked.stdout)
            (folder / f"{name}-cover-{label}.stderr").write_text(checked.stderr)
            if checked.returncode != 0 or not json.loads(checked.stdout)["valid"]:
                raise RuntimeError("native zero-hole witness failed exact cover verification")
            zero_checks.append({"checker": label, "exit": checked.returncode})
    result = {
        "name": name,
        "zero_cover_checks": zero_checks,
        "command": command,
        "seed": case["seed"],
        "requested_seconds": case["seconds"],
        "elapsed_seconds": time.time() - began,
        "started_unix": began,
        "exit": process.returncode,
        "native_result": last,
        "best_sha256": sha(folder / f"{name}-best.txt"),
        "raw_best_sha256": sha(folder / f"{name}-raw-best.txt"),
        "score_best_sha256": sha(folder / f"{name}-score-best.txt"),
        "log_sha256": sha(folder / f"{name}.log"),
    }
    print(json.dumps({"event": "completed", **result}), flush=True)
    return result


def main():
    metadata = json.loads((HERE / "environment.json").read_text())
    if (
        sha(ROOT / "scripts/four_seven_template_lookahead_heuristic.cpp")
        != metadata["source_sha256"]
    ):
        raise RuntimeError("native source changed after review")
    if sha(RAW / "search") != metadata["binaries"]["search"]:
        raise RuntimeError("native binary changed after review")
    if sha(HERE / "seeds.json") != metadata["seeds_sha256"]:
        raise RuntimeError("seed manifest changed after review")
    if sha(Path(__file__)) != metadata["source_snapshots"]["run.py"]:
        raise RuntimeError("runner source changed after review")
    cases = [
        c for c in json.loads((HERE / "seeds.json").read_text())["cases"] if c["name"] == "cycle"
    ]
    if len(cases) != 1 or cases[0]["seconds"] != 300 or cases[0]["workers"] != 1:
        raise RuntimeError("pilot budget or worker count changed")
    for case in cases:
        if sha(ROOT / case["seed_path"]) != case["seed_sha256"]:
            raise RuntimeError("seed changed after review")
        if sha(ROOT / case["catalog_path"]) != case["catalog_sha256"]:
            raise RuntimeError("exported catalog changed after review")
        if sha(ROOT / case["source_catalog_path"]) != case["source_catalog_sha256"]:
            raise RuntimeError("audited source catalog changed after review")
    folder = RAW / "pilots"
    folder.mkdir(exist_ok=False)
    (RAW / "run.py").write_bytes(Path(__file__).read_bytes())
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        for result in pool.map(run, cases):
            results.append(result)
            (folder / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
