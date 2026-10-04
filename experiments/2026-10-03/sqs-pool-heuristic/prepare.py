# Document:    Prepare and Freeze a Strict SQS Pool Heuristic
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cc6890a853fe30b195ef708b56830af4cb8879e3db9e031497199769bbd40b42
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Compile and generate finite audit evidence without launching optimization."""

import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/sqs-pool-heuristic-20261003"
POOL = ROOT / "experiments/scratch/new-construction-web-20261003/union-pool.json"
POOL_HASH = "b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6"
SOURCE = ROOT / "scripts/sqs_pool_heuristic.cpp"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_blocks(path, rows):
    path.write_text("".join(" ".join(map(str, block)) + "\n" for block in rows))


def main():
    assert not (HERE / "manifest.json").exists(), "preserve frozen preparation"
    assert not RAW.exists(), "preserve raw preparation artifacts"
    assert sha(POOL) == POOL_HASH
    payload = json.loads(POOL.read_text())
    universe = list(itertools.combinations(range(1, 17), 5))
    pool = [tuple(row["block"]) for row in payload["pool"]]
    assert len(pool) == len(set(pool)) == 1744 and pool == sorted(pool)
    for i, row in enumerate(payload["pool"]):
        assert row["local_id"] == i and universe[row["global_id"]] == pool[i]
    RAW.mkdir()
    pool_text = RAW / "allowed-pool.txt"
    write_blocks(pool_text, pool)
    (RAW / SOURCE.name).write_bytes(SOURCE.read_bytes())
    (RAW / "prepare.py").write_bytes(Path(__file__).read_bytes())
    compiler = shutil.which("c++")
    assert compiler
    compiler_version = subprocess.check_output([compiler, "--version"], text=True)
    (RAW / "compiler-version.txt").write_text(compiler_version)
    binary = RAW / "sqs_pool_heuristic"
    command = [
        compiler,
        "-std=c++17",
        "-O3",
        "-Wall",
        "-Wextra",
        "-Werror",
        str(SOURCE),
        "-o",
        str(binary),
    ]
    compiled = subprocess.run(command, text=True, capture_output=True, check=False)
    save(
        RAW / "compile.json",
        {
            "argv": command,
            "returncode": compiled.returncode,
            "stdout": compiled.stdout,
            "stderr": compiled.stderr,
        },
    )
    assert compiled.returncode == 0, compiled.stderr
    prepared = subprocess.run(
        [str(binary), "prepare", str(pool_text), str(RAW / "preparation")],
        text=True,
        capture_output=True,
        check=False,
    )
    save(
        RAW / "prepare-process.json",
        {"returncode": prepared.returncode, "stdout": prepared.stdout, "stderr": prepared.stderr},
    )
    assert prepared.returncode == 0, prepared.stderr
    initial_path = RAW / "preparation/initial64.txt"
    initial = list(read_blocks(initial_path))
    package = verify_cover(initial)
    standalone_process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(initial_path), "--expected-blocks", "64"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert standalone_process.returncode in (0, 1)
    standalone = json.loads(standalone_process.stdout)
    assert package["blocks"] == standalone["blocks"] == len(set(initial)) == 64
    assert package["canonical_sha256"] == standalone["canonical_sha256"]
    assert [list(triple) for triple in package["uncovered"]] == standalone["uncovered"]
    assert package["valid"] == standalone["valid"] == (not package["uncovered"])
    assert all(block in set(pool) for block in initial)
    save(RAW / "initial-package.json", package)
    save(RAW / "initial-standalone.json", standalone)
    preparation = json.loads((RAW / "preparation/preparation.json").read_text())
    assert preparation["optimization_runs"] == 0
    assert preparation["initial_holes"] == len(package["uncovered"])
    controls = RAW / "malformed-controls"
    controls.mkdir()
    initial_lines = initial_path.read_text().splitlines()
    pool_lines = pool_text.read_text().splitlines()
    absent = next(block for block in universe if block not in set(pool))
    outside = sorted([*initial[:-1], absent])
    cases = [
        ("start-too-few", "start", initial_lines[:-1]),
        ("start-duplicate", "start", [*initial_lines[:-1], initial_lines[0]]),
        ("start-outside-pool", "start", [" ".join(map(str, block)) for block in outside]),
        ("start-bad-token", "start", ["1 2 3 4 5x", *initial_lines[1:]]),
        ("start-zero-label", "start", ["0 2 3 4 5", *initial_lines[1:]]),
        ("start-label17", "start", ["1 2 3 4 17", *initial_lines[1:]]),
        ("start-repeated-point", "start", ["1 2 3 4 4", *initial_lines[1:]]),
        ("start-four-points", "start", ["1 2 3 4", *initial_lines[1:]]),
        ("start-reversed-points", "start", ["5 4 3 2 1", *initial_lines[1:]]),
        ("pool-too-few", "pool", pool_lines[:-1]),
        ("pool-duplicate", "pool", [*pool_lines[:-1], pool_lines[0]]),
        ("pool-bad-token", "pool", ["1 2 3 4 5x", *pool_lines[1:]]),
        ("pool-unordered", "pool", [pool_lines[1], pool_lines[0], *pool_lines[2:]]),
    ]
    rejected = []
    for name, kind, lines in cases:
        path = controls / f"{name}.txt"
        path.write_text("\n".join(lines) + "\n")
        process = subprocess.run(
            [
                str(binary),
                "validate",
                str(path if kind == "pool" else pool_text),
                str(path if kind == "start" else initial_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert process.returncode == 2, f"damaged control accepted: {name}"
        rejected.append({"name": name, "returncode": process.returncode, "stderr": process.stderr})
    valid = subprocess.run(
        [str(binary), "validate", str(pool_text), str(initial_path)],
        text=True,
        capture_output=True,
        check=True,
    )
    save(RAW / "input-controls.json", {"valid": json.loads(valid.stdout), "rejected": rejected})
    artifacts = {
        str(path.relative_to(ROOT)): sha(path) for path in sorted(RAW.rglob("*")) if path.is_file()
    }
    for path in (SOURCE, POOL, HERE / "prepare.py", HERE / "run_pilot.py", HERE / "check_pilot.py"):
        artifacts[str(path.relative_to(ROOT))] = sha(path)
    manifest = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_path": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha(SOURCE),
        "binary_path": str(binary.relative_to(ROOT)),
        "binary_sha256": sha(binary),
        "compiler": compiler,
        "compiler_version": compiler_version,
        "pool_json_path": str(POOL.relative_to(ROOT)),
        "pool_json_sha256": POOL_HASH,
        "pool_path": str(pool_text.relative_to(ROOT)),
        "pool_sha256": sha(pool_text),
        "initial_path": str(initial_path.relative_to(ROOT)),
        "initial_sha256": sha(initial_path),
        "initial_holes": preparation["initial_holes"],
        "initial_delta_rows": 107520,
        "move_controls": 96,
        "damaged_inputs_rejected": len(rejected),
        "artifacts": artifacts,
        "optimization_runs": 0,
        "proposed_pilot": {"seed": 2026104021, "seconds": 60, "processes": 1, "status": "not_run"},
        "scope": "Hole minimization among exactly 64 distinct members of the frozen 1744-block "
        "two-SQS extension pool. No point-degree, fixed-core, orbit, or symmetry restrictions. "
        "Positive holes are not a cover or a lower-bound proof.",
        "global_lower_bound_claim": False,
    }
    save(HERE / "manifest.json", manifest)
    print(json.dumps({key: value for key, value in manifest.items() if key != "artifacts"}))


if __name__ == "__main__":
    main()
