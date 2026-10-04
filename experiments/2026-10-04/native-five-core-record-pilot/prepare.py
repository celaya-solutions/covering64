# Document:    Five Core Record Pilot Preparation and Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      564597c54db7b8d99460baa0e989d703ba9d7cd2c0034298fb25fe685efb6da3
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
PROOF = HERE.with_name("h11-d25-common-core-cap")
INVENTORY = HERE.with_name("h11-common-core-saved-inventory-independent") / "inventory.json"
START_PATH = (
    "experiments/2026-10-04/weak-pair-neutral-queue-runtime-independent/family-f621e945358cc9e5.txt"
)
START_SHA = "f621e945358cc9e51c53995ee9a4a6161a0124778984fa410a87227984a28a7a"
STARTS = [
    (2026105601, START_PATH, START_SHA, 11),
    (
        2026105602,
        "experiments/2026-10-04/native-variable-partial-start/seed-2026104802/search-record-5-admissible64.txt",
        "439d5153ba2f2063c8dedb20ce71f9381dfecdca087e4fa9f9f0dd3808f4d22f",
        11,
    ),
]
REUSED["scan.hpp"] = "65d59df903e5da7a646a3764f469905ec6705e958d680d9c98eb17445734d560"


def freeze_header(path):
    lines = path.read_text().splitlines(keepends=True)
    digest = hashlib.sha256("".join(lines[9:]).encode()).hexdigest()
    lines[5] = re.sub(r"SHA256:      .*", "SHA256:      " + digest, lines[5])
    path.write_text("".join(lines))


def main():
    assert not (HERE / "manifest.json").exists(), "already frozen"
    assert INVENTORY.exists(), "wait for independent saved-family inventory"
    assert sha(INVENTORY) == "720e1856a16aaf32b3fbf456a37e644d626a849aa0ae5e3bd7b989bd6680cece"
    assert json.loads(INVENTORY.read_text())["passed"] is True
    assert (
        sha(PROOF / "certificate.json")
        == "1006dc7a15b515c075311da4ef8f074d92da60d10ed9fe3b12db23c77dc687ad"
    )
    assert (
        sha(PROOF / "core-62.txt")
        == "c2190a6c9fdc0e0f5cc56c991b79c109925e1c3f7ea375ec353535c717415b72"
    )
    RAW.mkdir(parents=True, exist_ok=True)
    for name, digest in REUSED.items():
        origin_path = (
            HERE.with_name("weak-pair-two-swap-scan-v2") / name
            if name == "scan.hpp"
            else OLD / name
        )
        assert sha(HERE / name) == sha(origin_path) == digest
    for path in HERE.iterdir():
        if path.suffix in (".hpp", ".cpp", ".py") and path.name not in REUSED:
            freeze_header(path)
    origin = OLD / "manifest.json"
    old_manifest = json.loads(origin.read_text())
    cores = old_manifest["core_rows"] + [
        json.loads((PROOF / "certificate.json").read_text())["core_ids"]
    ]
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
        assert row["cap_admissible"] == row["weak_qualified"] == (seed == 2026105602)
        assert row["metrics"]["core_overlaps"][4] == (62 if seed == 2026105601 else 0)
        row["seed"] = seed
        initials.append(row)
    compiler = Path("/usr/bin/clang++")
    builds = []
    sanitizer = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
    for source, name, flags in [
        ("search.cpp", "search", ["-O3", "-DNDEBUG"]),
        ("control.cpp", "control-zero", [*sanitizer, "-DVC_CONTROL_STEPS=0"]),
        ("control.cpp", "control-eight", sanitizer),
        ("qualification_control.cpp", "qualification", sanitizer),
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
            str(BUDGET["seeds"][0]),
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
    qualification_prefix = RAW / "qualification"
    qualification_command = [
        str(RAW / "qualification"),
        str(ROOT / START_PATH),
        str(qualification_prefix),
    ]
    qualified = subprocess.run(
        qualification_command, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30
    )
    (RAW / "qualification.stdout.jsonl").write_text(qualified.stdout)
    (RAW / "qualification.stderr.txt").write_text(qualified.stderr)
    assert qualified.returncode == 0 and qualified.stderr == ""
    qualification_rows = []
    for event in map(json.loads, qualified.stdout.splitlines()):
        path = Path(str(qualification_prefix) + "-" + event["case"] + ".txt")
        actual = checked(path, cores)
        assert actual["metrics"]["cardinality"] == event["cardinality"]
        assert actual["metrics"]["holes"] == event["holes"]
        assert actual["metrics"]["core_overlaps"] == event["overlaps"]
        assert actual["cap_admissible"] == event["cap_admissible"]
        if actual["weak_metrics"] is not None:
            assert all(
                actual["weak_metrics"][key] == event[key]
                for key in ("minimum_pair_count", "D3", "D4")
            )
        qualification_rows.append({"event": event, "checked": actual})
    assert len(qualification_rows) == 6
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "controls": controls,
            "qualification_rows": qualification_rows,
            "separate_weak_bucket_hole_ceiling": 11,
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
        INVENTORY,
        *[p for p in PROOF.iterdir() if p.is_file()],
        HERE.with_name("native-variable-partial-start") / "manifest.json",
        HERE.with_name("native-variable-partial-start") / "search.cpp",
        HERE.with_name("native-variable-partial-start") / "run.py",
        HERE.with_name("weak-pair-swap-scan") / "run.py",
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
        "core_thresholds": [55, 55, 55, 55, 56],
        "new_core_witness_path": str((PROOF / "core-62.txt").relative_to(ROOT)),
        "new_core_witness_sha256": sha(PROOF / "core-62.txt"),
        "new_core_certificate_sha256": sha(PROOF / "certificate.json"),
        "inventory_sha256": sha(INVENTORY),
        "named_image_only": True,
        "all_relabel_novelty_claim": False,
        "weak_record_hole_ceiling": 11,
        "weak_record_ranking": ["holes", "D2max"],
        "D2sum_role": "reported metadata only",
        "historical_qualified_rank": [11, 27],
        "historical_qualified_sha256": STARTS[1][2],
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
        "source_algorithm",
        "upstream_revision",
    ]:
        manifest[key] = old_manifest[key]
    manifest["records"] = [
        "best_complete",
        "best_raw_exact64",
        "best_five_core_admissible_exact64",
        "best_weak_qualified_exact64_among_H_at_most_11",
        "actual_final",
    ]
    manifest["core_policy"] = (
        "Exact64 record classification only; five thresholds55,55,55,55,56; all live states allowed"
    )
    manifest["weak_record_policy"] = (
        "Separate bucket ranked(H,D2max); pairfloor5,D3=D4=0,fivecaps,H<=11; no live/RNG change"
    )
    manifest["input_files"][str((HERE / "README.md").relative_to(ROOT))] = sha(HERE / "README.md")
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
