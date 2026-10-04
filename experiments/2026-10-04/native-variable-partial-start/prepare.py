# Document:    Partial Start Pilot Preparation and Focused Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      dbcb85517cadad772013c2b109dab2c9b817d921b1d74a42f6181ccfeca4b35c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build the changed driver and bounded controls; never launch timed optimization."""

import hashlib
import json
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from run import BUDGET, HERE, RAW, ROOT, checked, dump, sha, validate

OLD = HERE.with_name("native-variable-cardinality")
REUSED = {
    "kernel.hpp": "d374d813225b03d8ac9085255f9c0548e14a31a611bdc7ec5abeb0cce2040fd3",
    "cores.hpp": "054c89d9fed5fdc8e3b511c6452ae3fb14df4b40e64c993772401a264f30e92d",
}
STARTS = [
    (
        2026104801,
        "experiments/2026-10-04/native-core-cap-escape-v2/seed-2026104201/search-final-best.txt",
        "15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46",
        9,
    ),
    (
        2026104802,
        "experiments/2026-10-04/native-variable-cardinality/seed-2026104702/"
        "search-final-admissible64.txt",
        "330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00",
        12,
    ),
]


def freeze_header(path):
    lines = path.read_text().splitlines(keepends=True)
    digest = hashlib.sha256("".join(lines[9:]).encode()).hexdigest()
    lines[5] = re.sub(r"SHA256:      .*", "SHA256:      " + digest, lines[5])
    path.write_text("".join(lines))


def main():
    assert not (HERE / "manifest.json").exists(), "already frozen"
    RAW.mkdir(parents=True, exist_ok=True)
    for name, digest in REUSED.items():
        assert sha(HERE / name) == sha(OLD / name) == digest
    for path in HERE.iterdir():
        if path.suffix in (".hpp", ".cpp", ".py") and path.name not in REUSED:
            freeze_header(path)
    origin = OLD / "manifest.json"
    old_manifest = json.loads(origin.read_text())
    cores = old_manifest["core_rows"]
    incumbent = ROOT / "data/baselines/belic-1997.txt"
    assert sha(incumbent) == "89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f"
    incumbent_check = checked(incumbent, cores)
    assert incumbent_check["metrics"]["cardinality"] == 65
    assert incumbent_check["metrics"]["holes"] == 0
    initials = []
    for seed, relative, digest, holes in STARTS:
        assert sha(ROOT / relative) == digest
        row = checked(ROOT / relative, cores)
        assert row["metrics"]["cardinality"] == 64 and row["metrics"]["holes"] == holes
        assert row["cap_admissible"]
        row["seed"] = seed
        initials.append(row)
    compiler = Path("/usr/bin/clang++")
    builds = []
    sanitizer = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
    for source, name, flags in [
        ("search.cpp", "search", ["-O3", "-DNDEBUG"]),
        ("control.cpp", "control-zero", [*sanitizer, "-DVC_CONTROL_STEPS=0"]),
        ("control.cpp", "control-eight", sanitizer),
    ]:
        command = [
            str(compiler),
            "-std=c++20",
            *flags,
            "-Wall",
            "-Wextra",
            "-pedantic",
            str(HERE / source),
            "-o",
            str(RAW / name),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        (RAW / f"build-{name}.stdout").write_text(result.stdout)
        (RAW / f"build-{name}.stderr").write_text(result.stderr)
        assert result.returncode == 0 and not result.stderr, result.stderr
        builds.append(
            {"command": command, "returncode": result.returncode, "binary_sha256": sha(RAW / name)}
        )
    controls = []
    for initial in initials:
        for step_limit, binary_name in [(0, "control-zero"), (8, "control-eight")]:
            directory = RAW / f"control-{initial['seed']}-{step_limit}"
            directory.mkdir()
            command = [
                str(RAW / binary_name),
                str(incumbent),
                str(ROOT / initial["path"]),
                str(initial["seed"]),
                "300",
                str(directory / "search"),
            ]
            started = time.monotonic()
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30
            )
            elapsed = time.monotonic() - started
            (directory / "stdout.jsonl").write_text(result.stdout)
            (directory / "stderr.txt").write_text(result.stderr)
            receipt = validate(
                directory,
                result.stdout,
                result.returncode,
                result.stderr,
                elapsed,
                cores,
                initial["seed"],
                initial,
                step_limit,
            )
            assert not receipt["success"], "real cover found in controls; stop and review"
            assert receipt["final"]["iterations"] == step_limit
            if step_limit == 8:
                assert receipt["final"]["fallbacks"] == 4
                assert receipt["final"]["min_cardinality"] == 62
            receipt.update(
                {
                    "command": command,
                    "elapsed_seconds": elapsed,
                    "step_limit": step_limit,
                    "seed": initial["seed"],
                }
            )
            controls.append(receipt)
    rejection_controls = []
    for name, complete_path, partial_path in [
        ("partial_as_incumbent", ROOT / initials[0]["path"], ROOT / initials[0]["path"]),
        ("complete_as_partial", incumbent, incumbent),
    ]:
        command = [
            str(RAW / "control-zero"),
            str(complete_path),
            str(partial_path),
            "2026104801",
            "300",
            str(RAW / f"invalid-{name}"),
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30
        )
        assert result.returncode == 3 and result.stdout == ""
        rejection_controls.append(
            {"command": command, "returncode": result.returncode, "stderr": result.stderr}
        )
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "controls": controls,
            "input_role_rejections": rejection_controls,
            "sanitizers": ["address", "undefined"],
            "production_driver_exercised": True,
            "step_limits": [0, 8],
            "timed_optimization_launched": False,
            "reused_kernel_hashes": REUSED,
        },
    )
    reused_gate = HERE.with_name("native-variable-cardinality-independent") / "gate.json"
    sources = [p for p in HERE.iterdir() if p.suffix in (".hpp", ".cpp", ".py")]
    input_paths = [
        incumbent,
        origin,
        reused_gate,
        HERE / "controls.json",
        ROOT / "uv.lock",
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
        OLD / "PARTIAL_START_PROPOSAL.md",
        OLD / "OUTCOME.md",
        OLD / "result.json",
        HERE.with_name("native-core-cap-escape-independent") / "relabel-screen.json",
        HERE.with_name("native-variable-cardinality-relabel-screen") / "screen.json",
        HERE.with_name("native-partial-start-profiles") / "diagnostic.json",
        ROOT / "experiments/2026-10-04/post-d2-literature/README.md",
        ROOT / "experiments/2026-10-04/post-d2-literature/sources.json",
        *[ROOT / row["path"] for row in initials],
    ]
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "budget": BUDGET,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_files": {str(p.relative_to(ROOT)): sha(p) for p in sources},
        "input_files": {str(p.relative_to(ROOT)): sha(p) for p in input_paths},
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.rglob("*") if p.is_file()},
        "core_rows": cores,
        "incumbent_path": str(incumbent.relative_to(ROOT)),
        "initial_complete": incumbent_check,
        "initial_partials": initials,
        "binary_path": str((RAW / "search").relative_to(ROOT)),
        "binary_sha256": sha(RAW / "search"),
        "compiler_path": str(compiler),
        "compiler_sha256": sha(compiler),
        "compiler_version": subprocess.check_output([str(compiler), "--version"], text=True),
        "python_version": sys.version,
        "platform": platform.platform(),
        "builds": builds,
        "controls_sha256": sha(HERE / "controls.json"),
        "reused_kernel_hashes": REUSED,
        "reused_kernel_gate_path": str(reused_gate.relative_to(ROOT)),
        "reused_kernel_gate_sha256": sha(reused_gate),
        "reused_kernel_manifest_sha256": sha(origin),
        "initialization": {
            "incumbent_cardinality": 65,
            "live_cardinality": 64,
            "weights": 1,
            "configuration_flags": True,
            "last_flip_timestamps": 0,
            "step": 0,
            "initial_record_mutations": 0,
            "expected_initial_fallback_steps": 4,
            "scores": "recomputed from the new initial family and unit weights; no old weights",
        },
        "core_policy": "diagnostic records only; no cap restrictions on any live state",
        "no_other_search_policy_changes": True,
        "timed_optimization_launched": False,
    }
    for key in [
        "all_blocks",
        "triples",
        "labels",
        "block_order",
        "cost",
        "ranking",
        "tabu_tenure",
        "novelty_residue_threshold",
        "no_eligible_fallback",
        "decay",
        "trajectory_incumbent65",
        "records",
        "source_algorithm",
        "upstream_revision",
    ]:
        manifest[key] = old_manifest[key]
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "controls_sha256": sha(HERE / "controls.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
