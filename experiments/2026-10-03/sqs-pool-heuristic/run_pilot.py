# Document:    Gated Native SQS Pool Heuristic Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b0d7ab27ae6ac98949d73e33dcc136df1b3efe5eff952a9d310e9eb3b42d6aa8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run exactly the prepared native pilot after a separate independent gate."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/sqs-pool-heuristic-20261003"
PILOT = RAW / "pilot-2026104021"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def verify_candidate(path, pool):
    blocks = list(read_blocks(path))
    assert len(blocks) == len(set(blocks)) == 64 and all(block in pool for block in blocks)
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(path), "--expected-blocks", "64"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode in (0, 1)
    standalone = json.loads(process.stdout)
    assert package["canonical_sha256"] == standalone["canonical_sha256"]
    assert [list(triple) for triple in package["uncovered"]] == standalone["uncovered"]
    assert package["valid"] == standalone["valid"] == (len(package["uncovered"]) == 0)
    assert process.returncode == (0 if package["valid"] else 1)
    save(PILOT / (path.stem + "-package.json"), package)
    save(PILOT / (path.stem + "-standalone.json"), standalone)
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "blocks": 64,
        "holes": len(package["uncovered"]),
        "cover": package["valid"],
        "both_verifiers_agree": True,
        "canonical_sha256": package["canonical_sha256"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(args.gate.read_text())
    assert gate["passed"] is True and gate["manifest_sha256"] == sha(manifest_path)
    assert gate["source_sha256"] == sha(args.gate.parent / "check.py")
    for recorded in (manifest["artifacts"], gate["verified_inputs"]):
        for relative, expected in recorded.items():
            path = (ROOT / relative).resolve()
            assert path.is_relative_to(ROOT) and sha(path) == expected
    for prefix in ("source", "binary", "pool", "pool_json", "initial"):
        assert sha(ROOT / manifest[f"{prefix}_path"]) == manifest[f"{prefix}_sha256"]
    assert manifest["proposed_pilot"] == {
        "seed": 2026104021,
        "seconds": 60,
        "processes": 1,
        "status": "not_run",
    }
    assert manifest["optimization_runs"] == 0 and manifest["global_lower_bound_claim"] is False
    assert not PILOT.exists() and not (HERE / "pilot-result.json").exists()
    PILOT.mkdir()
    (PILOT / "run_pilot.py").write_bytes(Path(__file__).read_bytes())
    (PILOT / "independent-gate.json").write_bytes(args.gate.read_bytes())
    command = [
        str(ROOT / manifest["binary_path"]),
        "run",
        str(ROOT / manifest["pool_path"]),
        str(ROOT / manifest["initial_path"]),
        "2026104021",
        "60",
        str(PILOT / "native"),
    ]
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runner_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(manifest_path),
        "gate_sha256": sha(args.gate),
        "source_sha256": manifest["source_sha256"],
        "binary_sha256": manifest["binary_sha256"],
        "pool_sha256": manifest["pool_sha256"],
        "initial_sha256": manifest["initial_sha256"],
        "initial_holes": manifest["initial_holes"],
        "python_version": platform.python_version(),
        "seed": 2026104021,
        "requested_seconds": 60,
        "processes": 1,
        "argv": command,
    }
    save(PILOT / "start.json", start)
    process = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90
    )
    save(
        PILOT / "process.json",
        {"returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr},
    )
    assert process.returncode == 0, process.stderr
    native = json.loads((PILOT / "native/result.json").read_text())
    assert native["seed"] == 2026104021 and native["budget_seconds"] == 60
    assert native["global_lower_bound_claim"] is False
    assert native["proposals"] == native["accepted"] + native["rejected"] + native["selected_skips"]
    pool = set(read_blocks(ROOT / manifest["pool_path"]))
    candidates = [
        verify_candidate(path, pool) for path in sorted((PILOT / "native").glob("best-*.txt"))
    ]
    for candidate in candidates:
        assert Path(candidate["path"]).stem == f"best-{candidate['holes']}"
    final = verify_candidate(PILOT / "native/final64.txt", pool)
    assert final["holes"] == native["final_holes"]
    assert min(candidate["holes"] for candidate in candidates) == native["best_holes"]
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "native": native,
        "candidates": candidates,
        "final": final,
        "cover_found": native["best_holes"] == 0,
        "scope": manifest["scope"],
        "global_lower_bound_claim": False,
        "artifact_sha256": {
            str(path.relative_to(PILOT)): sha(path)
            for path in sorted(PILOT.rglob("*"))
            if path.is_file()
        },
    }
    save(HERE / "pilot-result.json", result)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("artifact_sha256", "candidates")
            }
        )
    )


if __name__ == "__main__":
    main()
