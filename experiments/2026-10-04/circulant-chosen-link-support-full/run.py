# Document:    Bounded Full Single Pass over Chosen Circulant Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      0ed9cec7dc3af985b1bf9f868a6e7692b6fe16592d83f85ede7edec1c7b5f0d1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Root launch only after review; reuse the frozen one-pass arithmetic unchanged."""

from __future__ import annotations

import gzip
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BENCHMARK = HERE.parent / "circulant-chosen-link-support-screen"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
RAW = ROOT / "experiments/scratch/circulant-chosen-link-support-full-v1.0.0"
TOTAL = 195296
SECONDS = 45.0


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def prepare():
    require(
        not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh full-pass preparation"
    )
    benchmark_manifest = json.loads((BENCHMARK / "manifest.json").read_text())
    benchmark = json.loads((BENCHMARK / "benchmark.json").read_text())
    require(
        benchmark["complete_benchmark"] and benchmark["completed_cases"] == 1000,
        "completed bounded benchmark",
    )
    require(benchmark_manifest["full_pair_count"] == TOTAL, "full workload")
    dependencies = {
        str((BENCHMARK / name).relative_to(ROOT)): sha(BENCHMARK / name)
        for name in ("run.py", "manifest.json", "benchmark.json", "files.json")
    }
    dependencies[str((CATALOG / "files.json").relative_to(ROOT))] = sha(CATALOG / "files.json")
    dependencies.update(benchmark_manifest["inputs"])
    dependencies[benchmark["proof_records"]] = benchmark["proof_records_sha256"]
    require(
        sha(BENCHMARK / "run.py") == benchmark_manifest["source_sha256"], "frozen arithmetic source"
    )
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(__file__),
            "dependencies": dependencies,
            "case_count": TOTAL,
            "first_pair_ordinal": 0,
            "last_pair_ordinal_inclusive": TOTAL - 1,
            "wall_budget_seconds": SECONDS,
            "stop_starting_new_cases_at_seconds": SECONDS - 0.5,
            "max_passes": 1,
            "iteration": False,
            "remaining_domain_per_case": 3003,
            "triple_rows_per_case": 455,
            "cardinality_demand": 44,
            "operation": "Unchanged frozen support and immediate forced-conflict checks only.",
            "cursor_on_cap": "next_pair_ordinal; completed prefix is exactly0..cursor-1",
            "retry_or_automatic_resume": False,
            "optimizer_calls": 0,
            "scope": benchmark_manifest["scope"],
            "benchmark_manifest_sha256": sha(BENCHMARK / "manifest.json"),
            "catalog_files_sha256": sha(CATALOG / "files.json"),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "full_pass_launched": False,
            }
        )
    )


def run():
    started = time.monotonic()
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "full runner source pin")
    require(
        manifest["case_count"] == TOTAL and manifest["wall_budget_seconds"] == SECONDS,
        "frozen workload and budget",
    )
    for path, expected in manifest["dependencies"].items():
        require(sha(ROOT / path) == expected, "frozen dependency")
    require(not (HERE / "result.json").exists() and not RAW.exists(), "fresh single pass")
    descriptor = os.open(HERE / "launch.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump({"manifest_sha256": sha(HERE / "manifest.json"), "max_passes": 1}, handle)
        handle.write("\n")
    spec = importlib.util.spec_from_file_location("frozen_one_pass", BENCHMARK / "run.py")
    arithmetic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arithmetic)
    data = arithmetic.load_frozen()
    require(data["boundaries"][-1] == TOTAL, "complete pair order")
    RAW.mkdir(parents=True)
    proof_path = RAW / "cases.jsonl.gz"
    survivor_path = RAW / "survivors.jsonl.gz"
    outcomes = Counter()
    operations = Counter()
    completed = 0
    with (
        proof_path.open("xb") as proof_raw,
        gzip.GzipFile(fileobj=proof_raw, mode="wb", mtime=0) as proof_gzip,
        io.TextIOWrapper(proof_gzip) as proof,
        survivor_path.open("xb") as survivor_raw,
        gzip.GzipFile(fileobj=survivor_raw, mode="wb", mtime=0) as survivor_gzip,
        io.TextIOWrapper(survivor_gzip) as survivors,
    ):
        for ordinal in range(TOTAL):
            if time.monotonic() - started >= SECONDS - 0.5:
                break
            record = arithmetic.screen(data, ordinal)
            require(record["pair_ordinal"] == completed, "complete ordered prefix")
            proof.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")
            if record["outcome"] == "survives_single_pass":
                survivors.write(
                    json.dumps(
                        {key: record[key] for key in ("pair_ordinal", "partial_id", "profile_id")},
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    + "\n"
                )
            outcomes[record["outcome"]] += 1
            operations.update(record["operation_counts"])
            completed += 1
    elapsed = time.monotonic() - started
    require(sum(outcomes.values()) == completed, "outcome accounting")
    result = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "source_sha256": sha(__file__),
        "completed_cases": completed,
        "requested_cases": TOTAL,
        "complete": completed == TOTAL,
        "stop_reason": "complete" if completed == TOTAL else "wall_budget",
        "next_pair_ordinal": completed,
        "completed_prefix": [0, completed],
        "completed_prefix_convention": "half-open ordinal interval",
        "outcomes": dict(outcomes),
        "operation_counts": dict(operations),
        "elapsed_seconds_including_load_and_output": elapsed,
        "wall_budget_seconds": SECONDS,
        "wall_budget_respected": elapsed <= SECONDS,
        "proof_records": str(proof_path.relative_to(ROOT)),
        "proof_records_sha256": sha(proof_path),
        "survivor_records": str(survivor_path.relative_to(ROOT)),
        "survivor_records_sha256": sha(survivor_path),
        "full_passes": 1,
        "iterative_propagation_launched": False,
        "optimizer_calls": 0,
        "survivor_meaning": "No contradiction in this single pass; no feasibility claim.",
        "scope": manifest["scope"],
    }
    dump(HERE / "result.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["run"]:
        run()
    else:
        raise SystemExit("Usage: run.py prepare|run")
