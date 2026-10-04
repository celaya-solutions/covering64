# Document:    Neutral Queue Preparation and Build
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f3fb63d4ad2cf74213b30bc7bc6d035a169d81e7cdbfe81f0068e96711d47729
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Build observer variants and run a synthetic recorder unit; never launch native search."""

import importlib.util
import json
import platform
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-neutral-queue-20261004"
PINS = {
    "weak-pair-d28-deterministic-descent/manifest.json": (
        "c985387e9429ca012c001dc03a105b702c8c231b55d005515e478c267cd5c17c"
    ),
    "weak-pair-d28-deterministic-descent/result.json": (
        "bb0d1335d340935346a3d7733dde2e0115979202abe873f7bc8c28d5adfbd790"
    ),
    "weak-pair-d28-deterministic-descent-runtime-independent/postcheck.json": (
        "13e39d802c2e7433d3f983e027e07c53edc866364f9fe8cc8088a3f92a937765"
    ),
    "weak-pair-swap-scan/manifest.json": (
        "71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764"
    ),
    "weak-pair-two-swap-scan-v2/manifest.json": (
        "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287"
    ),
}
INITIAL_SHA = "f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d"


def main():
    spec = importlib.util.spec_from_file_location("neutral_prepare_runner", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    base = runner.base_module()
    sha, require, dump = base.sha, base.require, base.dump
    require(not RAW.exists() and not (HERE / "manifest.json").exists(), "preserve preparation")
    inputs = {str((HERE.parent / p).relative_to(ROOT)): h for p, h in PINS.items()}
    for p, h in inputs.items():
        require(sha(ROOT / p) == h, f"pinned input changed: {p}")
    campaign = HERE.parent / "weak-pair-d28-deterministic-descent"
    prior = json.loads((campaign / "manifest.json").read_text())
    result = json.loads((campaign / "result.json").read_text())
    post = json.loads(
        (
            HERE.parent / "weak-pair-d28-deterministic-descent-runtime-independent/postcheck.json"
        ).read_text()
    )
    require(
        post["passed"] and post["local_closure"] and post["final_rank"] == [12, 26], "descent audit"
    )
    require(
        post["producer_result_sha256"] == sha(campaign / "result.json"), "descent audit binding"
    )
    require(
        post["final_center_sha256"] == result["final_center"]["sha256"] == INITIAL_SHA,
        "endpoint changed",
    )
    inputs.update(prior["input_files"] | prior["sources"] | prior["files"] | result["raw_files"])
    old = {
        kind: json.loads((HERE.parent / folder / "manifest.json").read_text())
        for kind, folder in (("one", "weak-pair-swap-scan"), ("two", "weak-pair-two-swap-scan-v2"))
    }
    require(
        old["one"]["core_rows"] == old["two"]["core_rows"] == prior["core_rows"],
        "core rows changed",
    )
    for source in old.values():
        inputs.update(source["source_files"] | source["input_files"])
    reused = {}
    for name in ("kernel.hpp", "cores.hpp", "scan.hpp", "two_scan.hpp"):
        original = HERE.parent / "weak-pair-two-swap-scan-v2" / name
        require(sha(HERE / name) == sha(original), f"evaluation kernel changed: {name}")
        reused[name] = sha(original)
    for p, h in inputs.items():
        require(sha(ROOT / p) == h, f"input changed: {p}")
    adapter = runner.load(HERE / "adapter.py", "neutral_prepare_adapter")
    recorders = {kind: adapter.Recorder(kind) for kind in ("one", "two")}
    initial = base.verify_family(
        result["final_center"]["ids"], recorders["one"], prior["core_rows"]
    )
    require(
        initial == base.verify_family(initial["ids"], recorders["two"], prior["core_rows"]),
        "profile disagreement",
    )
    require(initial["sha256"] == INITIAL_SHA and runner.rank(initial) == (12, 26), "initial rank")
    require(
        initial["verification"]["package"]["pair_multiplicities"] == {"5": 80, "6": 40},
        "pair histogram",
    )
    visited = {row["center_sha256"]: row["center_metrics"] for row in result["rounds"]}
    visited.update(
        {source["initial"]["sha256"]: source["initial"]["metrics"] for source in old.values()}
    )
    require(
        all((m["holes"], m["D2max"]) >= (12, 26) for m in visited.values()),
        "historical better center",
    )
    controls = json.loads((HERE / "controls.json").read_text())
    require(
        controls["passed"] and controls["native_search_launches"] == 0, "Python controls failed"
    )
    require(
        controls["runner_sha256"] == sha(HERE / "run.py")
        and controls["adapter_sha256"] == sha(HERE / "adapter.py"),
        "Python controls source binding",
    )
    RAW.mkdir(parents=True)
    compiler = Path("/usr/bin/clang++")
    compiler_version = subprocess.check_output([str(compiler), "--version"], text=True)
    builds = []
    shells = {}
    for name, source, flags in (
        ("one", "one_search.cpp", ["-O3", "-DNDEBUG"]),
        ("two", "two_search.cpp", ["-O3", "-DNDEBUG"]),
        (
            "neutral-unit",
            "neutral_control.cpp",
            ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"],
        ),
    ):
        binary = RAW / name
        command = [
            str(compiler),
            "-std=c++20",
            *flags,
            "-Wall",
            "-Wextra",
            "-pedantic",
            str(HERE / source),
            "-o",
            str(binary),
        ]
        built = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        (RAW / f"build-{name}.stdout").write_text(built.stdout)
        (RAW / f"build-{name}.stderr").write_text(built.stderr)
        require(built.returncode == 0, f"compile failed: {name}")
        builds.append(
            {"command": command, "returncode": built.returncode, "binary_sha256": sha(binary)}
        )
        if name in ("one", "two"):
            shells[name] = {
                "binary_path": str(binary.relative_to(ROOT)),
                "binary_sha256": sha(binary),
                "recorder_path": str((HERE / "adapter.py").relative_to(ROOT)),
                "recorder_sha256": sha(HERE / "adapter.py"),
                "original_recorder_path": str(adapter.ORIGINALS[name].relative_to(ROOT)),
                "original_recorder_sha256": sha(adapter.ORIGINALS[name]),
            }
    unit = subprocess.run(
        [str(RAW / "neutral-unit"), str(RAW / "unit-sample")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    (RAW / "unit.stdout.json").write_text(unit.stdout)
    (RAW / "unit.stderr.txt").write_text(unit.stderr)
    require(
        unit.returncode == 0 and not unit.stderr and json.loads(unit.stdout)["passed"],
        "recorder unit failed",
    )
    sample = json.loads((RAW / "unit-sample-neutral.json").read_text())
    meta = json.loads((RAW / "unit-sample-neutral-meta.json").read_text())
    require(
        meta
        == {
            "neutral_seen": 100,
            "retained": 64,
            "cap": 64,
            "capped": True,
            "complete": True,
            "rank": [12, 26],
        },
        "synthetic native cap control",
    )
    require([r["neutral_index"] for r in sample] == list(range(64, 0, -1)), "sort after retention")
    require(
        [r["ids"][-1] for r in sample] == list(range(936, 1000)), "first64 not global smallest64"
    )
    dump(
        HERE / "native-controls.json",
        {
            "passed": True,
            "search_launches": 0,
            "native_search_launches": 0,
            "recorder_unit_calls": 1,
            "sanitizers": "address,undefined",
            "synthetic_seen": 100,
            "retained": 64,
            "global_smallest_claim": False,
            "unit_binary_sha256": sha(RAW / "neutral-unit"),
        },
    )
    (HERE / "seed.txt").write_text(recorders["one"].family_text(initial["ids"]))
    require(sha(HERE / "seed.txt") == INITIAL_SHA, "seed preservation")
    dump(HERE / "seed-verification.json", initial)
    sources = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted(HERE.iterdir())
        if p.suffix in (".py", ".cpp", ".hpp")
    }
    for relative, digest in (inputs | sources).items():
        p = ROOT / relative
        if p.suffix in (".py", ".cpp", ".hpp"):
            target = RAW / "frozen-sources" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            require(sha(target) == digest, "source snapshot")
    manifest = {
        "document": "Bounded Strict-First Neutral Queue Manifest",
        "version": "v1.0.0",
        "date": "2026-10-04",
        "status": "PREPARED_NOT_RUN",
        "search_launches": 0,
        "native_search_launches": 0,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": platform.python_version(),
        "compiler_path": str(compiler),
        "compiler_sha256": sha(compiler),
        "compiler_version": compiler_version,
        "builds": builds,
        "initial": initial,
        "core_rows": prior["core_rows"],
        "initial_pair_histogram": {"5": 80, "6": 40},
        "historical_visited_hashes": sorted(visited),
        "historical_visited_metrics": visited,
        "seed_revisit_exception": INITIAL_SHA,
        "reused_evaluation_headers": reused,
        "shells": shells,
        "neutral_cap_per_shell": 64,
        "neutral_sampling": "First64 legal equal-to-baseline-rank families in unchanged traversal, "
        "then sorted by full IDs. Not globally smallest64; cap does not stop scanning.",
        "budget": {
            "max_centers": 16,
            "max_shell_launches": 32,
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "relaunch": False,
            "budget_transfer": False,
            "seed": None,
        },
        "queue_policy": "Both shells use the same center. Prefer best strict improvement "
        "with lex full-family-ID tie choice; clear worse-rank frontier. Otherwise "
        "enqueue sampled equal-rank families, deduplicate all historical/current "
        "visited hashes, and take lex least full IDs. Initial neutral collector is "
        "the sole historical revisit and counts as center1. Stop on incomplete, "
        "cover, empty sampled frontier, or16 centers; no automatic restart.",
        "scope": "Strict-improvement accounting and exact one/two-swap shells retain the frozen "
        "proofs and weak/core filters. Neutral outputs are a capped traversal sample. "
        "Sample exhaustion is not plateau exhaustion or a global nonexistence claim. "
        "Any actual cover requires both independent verifiers.",
        "input_files": inputs,
        "sources": sources,
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*")) if p.is_file()
        },
        "files": {str(p.relative_to(ROOT)): sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "native_search_launches": 0,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "runner_sha256": sha(HERE / "run.py"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
