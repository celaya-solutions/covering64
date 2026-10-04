# Document:    H6 Strict-Hole Radius-Three Launch and Validation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c357a1f4188d06b51847c0ef2a1acc7dcd92b007c8199c5bb41063ff104bc7ec
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
RAW = ROOT / "experiments/scratch/h6-strict-hole-radius3-pilot-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


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
    base = module(ROOT / manifest["verifier_path"], "strict_hole_checked")
    classifier = module(ROOT / manifest["classifier_path"], "strict_hole_classifier")
    cores, sixth = manifest["core_rows"], manifest["sixth_cap"]
    initial = base.checked(ROOT / manifest["input_path"], cores)
    assert initial["metrics"]["cardinality"] == 64 and initial["metrics"]["holes"] == 6
    native.mkdir()
    command = [
        str(ROOT / manifest["binary_path"]),
        str(ROOT / manifest["input_path"]),
        "6",
        "5",
        str(native),
        "59",
        "64",
    ]
    started = time.monotonic()
    watchdog = False
    try:
        process = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False, timeout=60
        )
        stdout, stderr, returncode = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as error:
        watchdog = True
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
        returncode = None
    elapsed = time.monotonic() - started
    (RAW / "stdout.json").write_text(stdout)
    (RAW / "stderr.txt").write_text(stderr)
    # Persist the launch receipt before validation, including failed or killed runs.
    receipt = {
        "manifest_sha256": sha(manifest_path),
        "gate_path": str(args.gate.resolve()),
        "gate_sha256": sha(args.gate),
        "command": command,
        "elapsed_seconds": elapsed,
        "watchdog": watchdog,
        "returncode": returncode,
        "stdout_sha256": sha(RAW / "stdout.json"),
        "stderr_sha256": sha(RAW / "stderr.txt"),
        "validation_passed": False,
        "complete_radius3": False,
    }
    dump(HERE / "launch.json", receipt)
    assert not stderr, "native error; raw artifacts retained"
    assert returncode == 0 or watchdog, "native failed; raw artifacts retained"
    summary = json.loads(stdout) if returncode == 0 else None
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
        assert checked["metrics"]["holes"] == int(row["holes"]) <= 5
        classified.append({"distance": distance, "dropped": dropped, "added": added, **result})
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
            "complete_radius3": complete,
            "native_summary": summary,
            "candidate_count": len(classified),
            "unledgered_raw_candidate_files": len(native_files) - len(rows),
            "initial": classifier.classify_saved(initial, sixth),
            "candidates": classified,
            "complete_at_most64": any(row["complete_at_most64"] for row in classified),
            "scope": "All candidates with at most5 holes at exact replacement distances1,2,3 "
            "from the pinned raw H6 family, only if complete_radius3 is true. "
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
                    "complete_radius3",
                    "candidate_count",
                    "complete_at_most64",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
