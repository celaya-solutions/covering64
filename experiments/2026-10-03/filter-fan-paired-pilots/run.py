# Document:    Approved Paired Filter-and-Fan Construction Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      61e38218f28d00c20f3f16397bc40e4f9b7b2de2d857ad61d293abbd0c0f8924
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run exactly six paired 30-second seeds, at most two single-thread searches."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOTYPE = HERE.parent / "filter-fan-repair"
RAW = ROOT / "experiments/scratch/filter-fan-paired-pilots-20261003"
SEED_PATH = ROOT / "experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt"
SOURCE_SHA = "2b674c341bc8e0e6214cb015dd60d573aa374d65a800bd765a6b27e2a5b7226e"
BINARY_SHA = "5ca6db3d7fcfe59004e907ad412817048be0b4d69a8ebd739decb2ca306e230d"
CHECKER_SHA = "3a4950dd339726d95c3ea763b211f2006c631305f082c7ab0b3671b53b21f00e"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def run_case(binary, seed, mode):
    directory = RAW / f"{seed}-{mode}"
    directory.mkdir()
    prefix = directory / "search"
    command = [str(binary), str(SEED_PATH), str(seed), "30", mode, str(prefix)]
    start = datetime.now(UTC).isoformat()
    began = time.monotonic()
    with (directory / "stdout.log").open("w") as stdout, (
        directory / "stderr.log"
    ).open("w") as stderr:
        result = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                timeout=40, check=False)
    elapsed = time.monotonic() - began
    require(result.returncode == 0, f"search failed: {seed}-{mode}")
    require(not (directory / "stderr.log").read_text(), "unexpected native diagnostics")
    events = [json.loads(line) for line in (directory / "stdout.log").read_text().splitlines()]
    final = events[-1]
    require(final["event"] == "final" and not final["interrupted"], "completed result")
    best = directory / "search-best.txt"
    package = verify_cover(read_blocks(best))
    standalone_run = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_cover.py"), str(best),
         "--v", "16", "--k", "5", "--t", "3"],
        cwd=ROOT, text=True, capture_output=True, check=False, timeout=15)
    independent = json.loads(standalone_run.stdout)
    require(standalone_run.returncode == (0 if package["valid"] else 1)
            and independent["valid"] == package["valid"]
            and independent["blocks"] == package["blocks"] == 64
            and independent["uncovered_count"] == len(package["uncovered"]) == final["best_deficit"]
            and {tuple(x) for x in independent["uncovered"]} == set(package["uncovered"]),
            "package and standalone disagreement")
    save(directory / "package.json", package)
    save(directory / "standalone.json", independent)
    record = dict(seed=seed, mode=mode, budget_seconds=30, single_thread=True,
                  command=command, started_utc=start, finished_utc=datetime.now(UTC).isoformat(),
                  process_wall_seconds=elapsed, native=final, events=events,
                  best_sha256=sha(best), canonical_sha256=package["canonical_sha256"],
                  valid_cover=package["valid"], missing_triples=package["uncovered"],
                  stdout_sha256=sha(directory / "stdout.log"),
                  trace_sha256=sha(directory / "search-traces.jsonl"),
                  trace_bytes=(directory / "search-traces.jsonl").stat().st_size,
                  best_double_verified=True)
    save(directory / "result.json", record)
    return record


def replay_case(record, checker):
    directory = RAW / f"{record['seed']}-{record['mode']}"
    traces = moves = degree_changes = 0
    began = time.monotonic()
    with (directory / "search-traces.jsonl").open() as stream:
        for line in stream:
            n, degrees = checker.inspect(json.loads(line))
            traces += 1
            moves += n
            degree_changes += degrees
    require(traces > 0, "empty trace archive")
    audit = dict(passed=True, all_saved_traces_replayed=True, traces=traces,
                 moves=moves, degree_changes=degree_changes,
                 seconds=time.monotonic() - began, trace_sha256=record["trace_sha256"],
                 checker_sha256=CHECKER_SHA)
    save(directory / "replay.json", audit)
    return audit


def main():
    require(not RAW.exists(), "new immutable campaign directory required")
    gate_path = PROTOTYPE / "root-audit.json"
    gate = json.loads(gate_path.read_text())
    require(gate["passed"] and gate["source_sha256"] == SOURCE_SHA and
            sha(PROTOTYPE / "search.cpp") == SOURCE_SHA, "root gate and source")
    frozen_binary = ROOT / "experiments/scratch/filter-fan-repair-v1.0.0-final-20261003/search"
    require(sha(frozen_binary) == BINARY_SHA == gate["binary_sha256"], "audited binary")
    checker_path = PROTOTYPE / "check_traces.py"
    require(sha(checker_path) == CHECKER_SHA, "frozen trace checker")
    package = verify_cover(read_blocks(SEED_PATH))
    require(package["canonical_sha256"] ==
            "d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf"
            and len(package["uncovered"]) == 3, "frozen unrestricted seed")
    RAW.mkdir(parents=True)
    for path in (Path(__file__), PROTOTYPE / "search.cpp", checker_path, gate_path, SEED_PATH,
                 ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        shutil.copyfile(path, RAW / path.name)
    binary = RAW / "search"
    shutil.copy2(frozen_binary, binary)
    metadata = dict(version="v1.0.0", started_utc=datetime.now(UTC).isoformat(),
                    seeds=list(range(2026100361, 2026100367)), modes=["beam", "greedy"],
                    seconds_per_run=30, maximum_concurrent_searches=2,
                    source_sha256=SOURCE_SHA, binary_sha256=BINARY_SHA,
                    root_audit_sha256=sha(gate_path), runner_sha256=sha(Path(__file__)),
                    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=ROOT, text=True).strip(),
                    policy_caveat="Greedy accepts its best component move including "
                                  "worsening ones; "
                                  "beam commits only a raw-improving prefix. This compares whole "
                                  "policies, not an isolated beam-width effect.")
    save(RAW / "metadata.json", metadata)
    results = []
    for seed in metadata["seeds"]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run_case, binary, seed, mode) for mode in metadata["modes"]]
            for future in as_completed(futures):
                record = future.result()
                results.append(record)
                save(RAW / "results.json", results)
                print(json.dumps(dict(event="run-finished", seed=record["seed"],
                                      mode=record["mode"],
                                      deficit=record["native"]["best_deficit"],
                                      proposals=record["native"]["proposals"],
                                      trace_bytes=record["trace_bytes"])), flush=True)
    spec = importlib.util.spec_from_file_location("frozen_trace_checker", checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    for record in sorted(results, key=lambda row: (row["seed"], row["mode"])):
        record["replay"] = replay_case(record, checker)
        save(RAW / f"{record['seed']}-{record['mode']}" / "result.json", record)
        save(RAW / "results.json", results)
        print(json.dumps(dict(event="replayed", seed=record["seed"], mode=record["mode"],
                              traces=record["replay"]["traces"], moves=record["replay"]["moves"])),
              flush=True)
    metadata["finished_utc"] = datetime.now(UTC).isoformat()
    metadata["results_sha256"] = sha(RAW / "results.json")
    save(RAW / "metadata.json", metadata)
    save(HERE / "results.json", results)
    save(HERE / "metadata.json", metadata)
    print(json.dumps(dict(event="complete", runs=len(results),
                          best_deficit=min(r["native"]["best_deficit"] for r in results))),
          flush=True)


if __name__ == "__main__":
    main()
