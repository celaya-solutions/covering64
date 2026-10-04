# Document:    Bounded Deterministic Weak-Pair Descent Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      548e0ee8e1055817e7cc83cf100350e0d5a4fbe5cffd72b2833e0df213fcaf6c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze a wrapper and existing binaries; no build, search, or solver launch."""

import importlib.util
import json
import platform
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-d28-deterministic-descent-20261004"
BASE = HERE.parent / "weak-pair-d28-relabel-novelty/representative.txt"
BASE_SHA = "c6d132069270ead505488fa863a12a0f16a82e289c989a1c4d5961b13826e06f"
PINS = {
    "weak-pair-swap-scan/manifest.json": (
        "71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764"
    ),
    "weak-pair-two-swap-scan-v2/manifest.json": (
        "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287"
    ),
    "weak-pair-d28-relabel-novelty/manifest.json": (
        "d691cb2a5405e2fb8796455a6cf4d336e70aca000f362b536181c57ab1603f36"
    ),
    "weak-pair-swap-scan-runtime-independent/postcheck.json": (
        "a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c"
    ),
    "weak-pair-two-swap-scan-v2-runtime-independent/postcheck.json": (
        "c2922a53aae7a51154b2006f457d88df886ab115fa6b88993920d04c62eb8d41"
    ),
}


def main():
    spec = importlib.util.spec_from_file_location("descent_runner", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    sha, require, dump = runner.sha, runner.require, runner.dump
    require(not RAW.exists() and not (HERE / "manifest.json").exists(), "preserve preparation")
    inputs = {str((HERE.parent / path).relative_to(ROOT)): digest for path, digest in PINS.items()}
    for path, digest in inputs.items():
        require(sha(ROOT / path) == digest, f"pinned input changed: {path}")
    old = {
        kind: json.loads((HERE.parent / folder / "manifest.json").read_text())
        for kind, folder in (("one", "weak-pair-swap-scan"), ("two", "weak-pair-two-swap-scan-v2"))
    }
    require(old["one"]["core_rows"] == old["two"]["core_rows"], "core rows differ")
    cores = old["one"]["core_rows"]
    for prior in old.values():
        inputs.update(prior["source_files"] | prior["input_files"])
        inputs[prior["binary_path"]] = prior["binary_sha256"]
    audit = json.loads((HERE.parent / "weak-pair-d28-relabel-novelty/manifest.json").read_text())
    inputs.update(audit["files"])
    inputs[str(BASE.relative_to(ROOT))] = BASE_SHA
    for path, digest in inputs.items():
        require(sha(ROOT / path) == digest, f"input changed: {path}")
    recorders = {
        kind: runner.load_recorder(HERE.parent / folder / "run.py")
        for kind, folder in (("one", "weak-pair-swap-scan"), ("two", "weak-pair-two-swap-scan-v2"))
    }
    blocks = recorders["one"].STANDALONE.parse_witness(BASE.read_text())
    ids = sorted(recorders["one"].RANK[tuple(sorted(block))] for block in blocks)
    initial = runner.verify_family(ids, recorders["one"], cores)
    require(
        initial == runner.verify_family(ids, recorders["two"], cores), "recorder profiles differ"
    )
    require(initial["sha256"] == BASE_SHA and runner.rank(initial) == (12, 28), "baseline changed")
    controls = json.loads((HERE / "controls.json").read_text())
    require(controls["passed"] and controls["search_launches"] == 0, "wrapper controls failed")
    require(controls["runner_sha256"] == sha(HERE / "run.py"), "controls bind wrong runner")
    RAW.mkdir(parents=True)
    shells = {}
    for kind, prior in old.items():
        binary = RAW / f"{kind}-swap"
        shutil.copy2(ROOT / prior["binary_path"], binary)
        require(sha(binary) == prior["binary_sha256"], "binary copy changed")
        recorder_path = Path(recorders[kind].__file__).resolve()
        shells[kind] = {
            "binary_path": str(binary.relative_to(ROOT)),
            "binary_sha256": sha(binary),
            "original_binary_path": prior["binary_path"],
            "recorder_path": str(recorder_path.relative_to(ROOT)),
            "recorder_sha256": sha(recorder_path),
        }
    sources = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (HERE / "prepare.py", HERE / "run.py", HERE / "controls.py")
    }
    for relative, digest in (inputs | sources).items():
        path = ROOT / relative
        if path.suffix in (".py", ".cpp", ".hpp"):
            target = RAW / "frozen-sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            require(sha(target) == digest, "source snapshot changed")
    shutil.copyfile(BASE, HERE / "center-00.txt")
    dump(HERE / "center-00-verification.json", initial)
    preparation = {
        "passed": True,
        "search_launches": 0,
        "solver_launches": 0,
        "builds": 0,
        "initial_sha256": BASE_SHA,
        "initial_rank": [12, 28],
        "same_core_rows": True,
        "unchanged_binary_hashes": {kind: s["binary_sha256"] for kind, s in shells.items()},
        "coverage": "Existing generic exact-distance-one and exact-distance-two shell "
        "proofs apply to each new 64-block center. Pair-floor pruning is recomputed "
        "from that center; fixed named weak rows/core caps are unchanged.",
        "adoption": "Run both shells from the same center. Noncover adoption or local closure "
        "requires both complete. Rank by (holes,D2max), then the full sorted family "
        "ID tuple. Every adopted center is freshly dual verified and weak/core legal.",
    }
    dump(HERE / "preparation.json", preparation)
    manifest = {
        "document": "Bounded Deterministic Weak-Pair Descent Manifest",
        "version": "v1.0.0",
        "date": "2026-10-04",
        "status": "PREPARED_NOT_RUN",
        "search_launches": 0,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": platform.python_version(),
        "initial": initial,
        "core_rows": cores,
        "shells": shells,
        "max_rounds": 4,
        "max_shell_launches": 8,
        "budget": {
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "budget_transfer": False,
            "relaunch": False,
            "seed": None,
        },
        "selection": "Strict lexicographic (holes,D2max), then lexicographically least full "
        "sorted 64-element block-ID tuple among all tied best families from both shells.",
        "stop_policy": "Stop on any incomplete/invalid terminal, no strict improvement after "
        "both completed shells, a dual-verified cover, or four rounds. Observed "
        "covers may stop early without center adoption or round-optimum claims. "
        "An incomplete shell preserves incomplete status and observed witnesses.",
        "sources": sources,
        "input_files": inputs,
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(RAW.rglob("*"))
            if path.is_file()
        },
        "files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(HERE.iterdir())
            if path.is_file()
        },
        "scope": "Deterministic descent through at most four selected centers under fixed weak "
        "pair/single/quadruple rows and four named core caps. Complete shell claims "
        "apply only to the exact round center and filters; no unrestricted existence, "
        "global lower-bound, or radius-four model claim.",
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "search_launches": 0,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "runner_sha256": sha(HERE / "run.py"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
