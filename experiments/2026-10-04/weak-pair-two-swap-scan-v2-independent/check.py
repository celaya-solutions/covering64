# Document:    Independent Two-Swap Scan V2 Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e001bf67ce4c83069c6c286ef705ebd432de7e13b109ca9422240fc5594e2fc5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Gate finite controls and frozen bindings; contains no scan-driver launch."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import compare
import recorder_controls

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-two-swap-scan-v2"
ORIGINAL = HERE.parent / "weak-pair-two-swap-scan"
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-v2-independent-20261004"
MANIFEST = "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287"
EXPECTATIONS = "ba6db6936a457ed17720224a197814553dc38eda5b1c13ac937580605f1eb0f4"
EMPTY = "cbba2ec63c436fd580773fe5ac50e23f3556cc799554e3426ef3882416a40fee"
PRIOR_GATE = "3f6247263cb75a0258357e2e356158388fad434e8b89bb6c9210f9871adc889c"
BASE = "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    output = HERE / "gate.json"
    require(not output.exists(), "preserve gate")
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    bindings = []
    for group in ("source_files", "input_files", "raw_files"):
        for path, digest in manifest[group].items():
            require(sha(ROOT / path) == digest, f"binding changed: {path}")
            bindings.append({"path": path, "sha256": digest, "group": group})
    prior_path = HERE.parent / "weak-pair-swap-scan-independent/gate.json"
    require(sha(prior_path) == PRIOR_GATE, "prior one-swap kernel gate changed")
    prior = json.loads(prior_path.read_text())
    for name in ("scan.hpp", "kernel.hpp", "cores.hpp"):
        source = HERE.parent / "weak-pair-swap-scan" / name
        require(sha(PRODUCER / name) == sha(source), "reused one-swap header changed")
        require(
            any(
                row["path"] == str(source.relative_to(ROOT)) and row["sha256"] == sha(source)
                for row in prior["artifact_bindings"]
            ),
            "header not bound by prior gate",
        )
    for name in ("two_scan.hpp", "scan.hpp", "kernel.hpp", "cores.hpp", "search.cpp"):
        require(sha(PRODUCER / name) == sha(ORIGINAL / name), "v2 native source changed")
    require(
        manifest["budget"]
        == {
            "passes": 1,
            "seconds": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "seed": None,
            "relaunch": False,
            "enumerate_complete_ties": True,
            "budget_reallocation": False,
        },
        "budget changed",
    )
    require(manifest["full_enumeration_launched"] is False, "producer launched before gate")
    require(
        sha(ROOT / manifest["initial"]["path"]) == manifest["initial"]["sha256"] == BASE,
        "wrong initial family",
    )
    require(sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"], "binary changed")
    require(sha(RAW / "control-expectations.json") == EXPECTATIONS, "control expectations changed")
    require(sha(RAW / "empty-support.json") == EMPTY, "empty support expectation changed")
    direct = json.loads((RAW / "control-expectations.json").read_text())
    extra = json.loads((RAW / "empty-support.json").read_text())
    old_controls = HERE.parent / "weak-pair-two-swap-scan-independent"
    require(sha(old_controls / "prepare_controls.py") == direct["source_sha256"], "fixture source")
    require(
        sha(old_controls / "empty_support_control.py") == extra["source_sha256"], "empty source"
    )
    oracle_path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    require(sha(oracle_path) == direct["oracle_sha256"] == extra["oracle_sha256"], "oracle changed")
    require(
        manifest["initial"]["ids"] == direct["base_ids"]
        and manifest["initial"]["metrics"] == direct["baseline"]["metrics"] | {"cardinality": 64},
        "initial direct recount mismatch",
    )
    require(manifest["core_rows"] == direct["core_rows"], "core rows changed")
    require(sha(Path(manifest["compiler_path"])) == manifest["compiler_sha256"], "compiler changed")
    version = subprocess.check_output([manifest["compiler_path"], "--version"], text=True)
    require(version == manifest["compiler_version"], "compiler version changed")
    command = [
        manifest["compiler_path"],
        "-std=c++20",
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        "-Wall",
        "-Wextra",
        "-pedantic",
        str(HERE / "control.cpp"),
        "-o",
        str(RAW / "control-final"),
    ]
    require(not (RAW / "control-final").exists(), "preserve final binary")
    build = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (RAW / "build.stdout").write_text(build.stdout)
    (RAW / "build.stderr").write_text(build.stderr)
    require(build.returncode == 0 and not build.stderr, "control compile failure")
    execution = [
        str(RAW / "control-final"),
        str(ROOT / manifest["initial"]["path"]),
        str(RAW / "cases.txt"),
    ]
    run = subprocess.run(execution, capture_output=True, text=True, timeout=30)
    (RAW / "final.stdout.jsonl").write_text(run.stdout)
    (RAW / "final.stderr.txt").write_text(run.stderr)
    require(run.returncode == 0 and not run.stderr, "finite native controls failed")
    comparison = compare.compare("final")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    oracle = load("gate_independent_oracle", oracle_path)
    standalone = load("gate_standalone_checker", ROOT / "scripts/check_cover.py")
    families = (
        [{"ids": direct["base_ids"], **direct["baseline"]}]
        + [row["partial"] for row in direct["fixtures"] + extra["fixtures"]]
        + comparison.pop("full_states")
    )
    verified = []
    for index, row in enumerate(families):
        blocks = [oracle.SUBSETS[5][i] for i in row["ids"]]
        counts = row["counts"].get(3, row["counts"].get("3"))
        holes = [list(oracle.SUBSETS[3][i]) for i, count in enumerate(counts) if count == 0]
        package = verify_cover(blocks, 16, 5, 3)
        separate = standalone.verify_cover(blocks, 16, 5, 3, expected_blocks=len(blocks))
        require(
            sorted(map(list, package["uncovered"])) == holes == separate["uncovered"],
            "dual verifier hole disagreement",
        )
        require(package["valid"] == separate["valid"] == (not holes), "covering label")
        witness = RAW / f"control-family-{index:02d}.txt"
        witness.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
        require(
            sha(witness) == package["canonical_sha256"] == separate["canonical_sha256"],
            "canonical family mismatch",
        )
        verified.append(
            {
                "path": str(witness.relative_to(ROOT)),
                "sha256": sha(witness),
                "cardinality": len(blocks),
                "holes": len(holes),
                "package_valid": package["valid"],
                "standalone_valid": separate["valid"],
            }
        )
    recorder = recorder_controls.control(
        load("frozen_recorder", PRODUCER / "run.py"), manifest["core_rows"]
    )
    rows = [oracle.SUBSETS[5][i] for i in direct["base_ids"]]
    malformed = {
        "duplicate": rows[:-1] + [rows[0]],
        "truncated_family": rows[:-1],
        "bad_label": [(0, 2, 3, 4, 5)] + rows[1:],
        "wrong_size": [rows[0][:-1]] + rows[1:],
        "repeated_point": [(1, 1, 3, 4, 5)] + rows[1:],
    }
    empty_file = RAW / "empty-cases.txt"
    empty_file.write_text("")
    rejected = []
    for name, content in malformed.items():
        source = RAW / f"reject-{name}.txt"
        source.write_text("".join(" ".join(map(str, b)) + "\n" for b in content))
        damaged = subprocess.run(
            [str(RAW / "control-final"), str(source), str(empty_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        require(damaged.returncode == 3 and bool(damaged.stderr), "damaged family accepted")
        rejected.append(
            {
                "name": name,
                "returncode": damaged.returncode,
                "stderr": damaged.stderr.strip(),
                "sha256": sha(source),
            }
        )
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed during audit")
    proof = HERE.parent / "weak-pair-swap-scan-runtime-independent/LOCAL-REPAIR.md"
    receipt = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "source_sha256": sha(Path(__file__)),
        "optimizer_launches": 0,
        "launch_authority": "root only",
        "budget": manifest["budget"],
        "artifact_bindings": bindings,
        "reused_gate_sha256": PRIOR_GATE,
        "control_comparison": comparison,
        "verified_control_families": verified,
        "recorder_controls": recorder,
        "damaged_inputs": rejected,
        "proof_path": str(proof.relative_to(ROOT)),
        "proof_sha256": sha(proof),
        "proof_separate_review": (
            "Exact-search agent confirmed pair-floor equivalence "
            "and unique exact-distance-two coverage."
        ),
        "neighborhood": {
            "outer_cases": 8676864,
            "shell_total": 18668272896,
            "base_sha256": BASE,
            "includes_distances_zero_or_one": False,
        },
        "build": {
            "command": command,
            "returncode": build.returncode,
            "compiler_sha256": manifest["compiler_sha256"],
            "compiler_version": version,
            "binary_sha256": sha(RAW / "control-final"),
        },
        "control_run": {"command": execution, "returncode": run.returncode},
        "independent_sources": {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir()) if p.is_file()
        },
        "scope": (
            "One fixed exact-distance-two shell with declared legal filters. "
            "Timeout is incomplete; no global theorem."
        ),
        "saving": (
            "Only strict best improvements and all final best ties strictly below baseline; "
            "empty improvement set is valid."
        ),
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(output),
                "manifest_sha256": MANIFEST,
                "verified_control_families": len(verified),
            }
        )
    )


if __name__ == "__main__":
    main()
