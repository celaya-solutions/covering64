# Document:    H6 Neutral Radius-Three Launch and Validation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a4be1989cffc926a92cf030306ae5e0e4611f4e937d2cf12e78e70689087843b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Root-only launch after a matching independent gate; never run during preparation."""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-neutral-radius3-pilot-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def execute_bounded(command, seconds=35, grace=5):
    started = time.monotonic()
    watchdog = terminated = killed = False
    process = subprocess.Popen(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        stdout, stderr = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        watchdog = terminated = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=grace)
        except subprocess.TimeoutExpired:
            killed = True
            process.kill()
            stdout, stderr = process.communicate()
    return {
        "stdout": stdout,
        "stderr": stderr,
        "returncode": process.returncode,
        "watchdog": watchdog,
        "terminated": terminated,
        "killed": killed,
        "elapsed_seconds": time.monotonic() - started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(args.gate.read_text())
    assert gate["passed"] is True and gate["launch_permitted"] is True
    assert gate["manifest_sha256"] == sha(manifest_path), "gate is for different manifest"
    for relative, digest in manifest["pins"].items():
        assert sha(ROOT / relative) == digest, f"changed pin: {relative}"
    result_path = HERE / "result.json"
    native = RAW / "native"
    assert not result_path.exists() and not native.exists(), "no relaunch"
    base = module(ROOT / manifest["verifier_path"], "neutral_checked")
    classifier = module(ROOT / manifest["classifier_path"], "neutral_classifier")
    cores, sixth = manifest["core_rows"], manifest["sixth_cap"]
    initial = base.checked(ROOT / manifest["input_path"], cores)
    assert initial["metrics"]["cardinality"] == 64 and initial["metrics"]["holes"] == 6
    native.mkdir()
    command = [
        str(ROOT / manifest["binary_path"]),
        str(ROOT / manifest["input_path"]),
        "6",
        "6",
        str(native),
        "30",
        "64",
    ]
    execution = execute_bounded(command)
    stdout, stderr = execution["stdout"], execution["stderr"]
    returncode, watchdog = execution["returncode"], execution["watchdog"]
    (RAW / "stdout.json").write_text(stdout)
    (RAW / "stderr.txt").write_text(stderr)
    # Persist the launch receipt before validation, including failed or killed runs.
    receipt = {
        "manifest_sha256": sha(manifest_path),
        "gate_path": str(args.gate.resolve()),
        "gate_sha256": sha(args.gate),
        "command": command,
        "elapsed_seconds": execution["elapsed_seconds"],
        "watchdog": watchdog,
        "watchdog_terminated": execution["terminated"],
        "watchdog_killed": execution["killed"],
        "returncode": returncode,
        "stdout_sha256": sha(RAW / "stdout.json"),
        "stderr_sha256": sha(RAW / "stderr.txt"),
        "validation_passed": False,
        "complete_neutral_radius3": False,
    }
    dump(HERE / "launch.json", receipt)
    assert not stderr, "native error; raw artifacts retained"
    assert returncode == 0 or watchdog, "native failed; raw artifacts retained"
    summary = json.loads(stdout) if returncode == 0 and not watchdog else None
    rows = list(csv.DictReader((native / "candidates.tsv").open(), delimiter="\t"))
    assert [int(row["candidate"]) for row in rows] == list(range(1, len(rows) + 1))
    saved = HERE / "candidates"
    saved.mkdir()
    classified = []
    original = set(initial["ids"])
    for row in rows:
        number = int(row["candidate"])
        source = native / f"candidate-{number}.txt"
        target = saved / source.name
        shutil.copyfile(source, target)
        checked = base.checked(target, cores)
        result = classifier.classify_saved(checked, sixth)
        distance = int(row["distance"])
        dropped = [int(x) for x in row["drop_ids"].split(",")]
        added = [int(x) for x in row["add_ids"].split(",")]
        family = set(checked["ids"])
        assert 1 <= distance <= 3 and len(family) == 64
        assert sorted(original - family) == dropped and sorted(family - original) == added
        assert len(dropped) == len(added) == distance
        assert checked["metrics"]["holes"] == int(row["holes"]) <= 6
        weak = checked["weak_metrics"]
        endpoint_weak = weak["minimum_pair_count"] >= 5 and weak["D3"] == weak["D4"] == 0
        classified.append(
            {
                "distance": distance,
                "dropped": dropped,
                "added": added,
                **result,
                "package": checked["package"],
                "standalone": checked["standalone"],
                "endpoint_weak_qualified": endpoint_weak,
            }
        )
    # A killed process may leave an unledgered partial file: preserve it as raw,
    # explicitly count it, and never treat a killed run as complete.
    native_files = list(native.glob("candidate-*.txt"))
    assert watchdog or len(native_files) == len(rows)
    assert len({tuple(row["ids"]) for row in classified}) == len(classified)
    complete = False
    if summary is not None:
        assert summary["status"] in ("complete", "timeout")
        assert summary["candidates"] == len(rows)
        assert len(summary["shells"]) == 3
        for distance, shell in enumerate(summary["shells"], 1):
            assert shell["distance"] == distance
            expected = math.comb(64, distance)
            assert 0 <= shell["deletions"] <= expected
            assert shell["candidates"] == sum(r["distance"] == distance for r in classified)
            if shell["complete"]:
                assert shell["deletions"] == expected
        complete = summary["status"] == "complete"
        assert complete == all(shell["complete"] for shell in summary["shells"])
    receipt.update(
        {
            "validation_passed": True,
            "complete_neutral_radius3": complete,
            "native_summary": summary,
            "candidate_count": len(classified),
            "unledgered_raw_candidate_files": len(native_files) - len(rows),
            "initial": classifier.classify_saved(initial, sixth),
            "candidates": classified,
            "complete_at_most64": any(row["complete_at_most64"] for row in classified),
            "weak_endpoint_count": sum(row["endpoint_weak_qualified"] for row in classified),
            "weak_six_cap_count": sum(row["weak_six_cap_qualified"] for row in classified),
            "scope": "All candidates with at most6 holes at exact replacement distances1,2,3 "
            "from the pinned raw H6 family, only if complete_neutral_radius3 is true. "
            "Pair/weak/six-cap metrics are postclassification only. No global conclusion.",
        }
    )
    dump(result_path, receipt)
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "validation_passed",
                    "complete_neutral_radius3",
                    "candidate_count",
                    "weak_endpoint_count",
                    "complete_at_most64",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
