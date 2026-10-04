# Document:    Independent Weak-Pair Swap Scan Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6c654bfdd969de8de53ee426f9351e03b8c47a143c37b04e20186ddb4fccaef2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite controls and read-only source bindings; never starts the scan driver."""

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import compare
import oracle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-swap-scan"
RAW = ROOT / "experiments/scratch/weak-pair-swap-scan-independent-20261004"
MANIFEST_SHA = "71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764"
SNAPSHOT_SHA = "514393dbcf2f2a3ea92d55b82b4a65a27840cf28e2d3c5d2f43451ba6c38f352"
KERNEL_SHA = "d374d813225b03d8ac9085255f9c0548e14a31a611bdc7ec5abeb0cce2040fd3"
CORES_SHA = "054c89d9fed5fdc8e3b511c6452ae3fb14df4b40e64c993772401a264f30e92d"
require = oracle.require


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def family_text(ids):
    return "".join(" ".join(map(str, oracle.SUBSETS[5][i])) + "\n" for i in sorted(ids))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def recorder_controls(direct, runner, cores):
    old, new = direct["bases"]["old_h12"], direct["bases"]["cp_final"]
    outgoing, incoming = 3145, 3752
    original = set(old["ids"])
    ins = [i for i in range(4368) if i not in original]
    ordinal = sorted(original).index(outgoing) * 4304 + ins.index(incoming) + 1
    before = old["metrics"] | {"cardinality": 64}
    after = new["metrics"] | {"cardinality": 64}
    initial = {"ids": old["ids"], "metrics": before}
    candidate = {"outgoing": outgoing, "incoming": incoming, "metrics": after}
    events = [
        {
            "event": "start",
            "budget_seconds": 120,
            "total": 275456,
            "control_limit": ordinal,
            "baseline": before,
        },
        candidate | {"event": "improvement", "serial": 1, "evaluated": ordinal, "seconds": 0.1},
        {
            "event": "final",
            "complete": False,
            "reason": "control_limit",
            "total": 275456,
            "evaluated": ordinal,
            "legal": 1,
            "strictly_improving_neighbors": 1,
            "strict_improvement_records": 1,
            "best_ties": 1,
            "best_rank": [12, 32],
            "seconds": 0.2,
        },
    ]
    prefix = RAW / "synthetic-recorder-control"

    def validate(rows, ties, limit=ordinal):
        Path(str(prefix) + "-ties.json").write_text(json.dumps(ties) + "\n")
        return runner.validate(
            prefix,
            "\n".join(map(json.dumps, rows)),
            1,
            "",
            121.0,
            initial,
            cores,
            control_limit=limit,
        )

    positive = validate(events, [candidate])
    expected_hash = hashlib.sha256(family_text(new["ids"]).encode()).hexdigest()
    require(
        positive["passed"] and positive["best_ties"][0]["sha256"] == expected_hash,
        "positive saved tie not the actual known improving family",
    )
    damaged = []
    for name in (
        "incomplete_marked_complete",
        "early_timeout",
        "numeric_complete",
        "floating_counter",
        "negative_seconds",
        "wrong_ordinal",
        "wrong_metrics",
        "duplicate_tie",
        "invalid_outgoing",
    ):
        rows, ties = copy.deepcopy(events), [copy.deepcopy(candidate)]
        limit = ordinal
        if name in ("incomplete_marked_complete", "early_timeout"):
            rows[0]["control_limit"] = None
            limit = None
            rows[-1]["reason"] = (
                "complete" if name == "incomplete_marked_complete" else "time_limit"
            )
            rows[-1]["seconds"] = 120.0 if name == "incomplete_marked_complete" else 119.0
        elif name == "numeric_complete":
            rows[-1]["complete"] = 0
        elif name == "floating_counter":
            rows[-1]["evaluated"] = float(ordinal)
        elif name == "negative_seconds":
            rows[-1]["seconds"] = -1
        elif name == "wrong_ordinal":
            rows[1]["evaluated"] -= 1
        elif name == "wrong_metrics":
            rows[1]["metrics"]["holes"] = ties[0]["metrics"]["holes"] = 11
        elif name == "duplicate_tie":
            ties.append(copy.deepcopy(candidate))
            rows[-1]["best_ties"] = rows[-1]["strictly_improving_neighbors"] = 2
        else:
            rows[1]["outgoing"] = ties[0]["outgoing"] = -1
        try:
            validate(rows, ties, limit)
        except (AssertionError, ValueError, KeyError):
            damaged.append(name)
        else:
            raise ValueError(f"damaged recorder control accepted: {name}")
    validate(events, [candidate])
    return {
        "positive_known_swap": [outgoing, incoming],
        "true_ordinal": ordinal,
        "verified_tie_sha256": expected_hash,
        "damaged_controls_rejected": damaged,
        "scope": "Synthetic log fixtures with real recounted witness; no prefix executed.",
    }


def main():
    output = HERE / "gate.json"
    require(not output.exists(), "preserve prior gate")
    require(sha(PRODUCER / "manifest.json") == MANIFEST_SHA, "manifest changed")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    bindings = []
    for group in ("source_files", "input_files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"binding changed: {relative}")
            bindings.append({"path": relative, "sha256": digest, "group": group})
    require(sha(PRODUCER / "kernel.hpp") == KERNEL_SHA, "reused kernel changed")
    require(sha(PRODUCER / "cores.hpp") == CORES_SHA, "reused core rows changed")
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
    require(
        manifest["total_neighbors"] == 275456
        and manifest["selected_blocks"] == 64
        and manifest["incoming_blocks"] == 4304
        and manifest["universe_blocks"] == 4368,
        "neighborhood dimensions",
    )
    require(manifest["full_enumeration_launched"] is False, "producer launched before gate")
    require(sha(RAW / "oracle-snapshots.json") == SNAPSHOT_SHA, "direct oracle changed")
    direct = json.loads((RAW / "oracle-snapshots.json").read_text())
    cases = json.loads((HERE / "cases.json").read_text())
    require(sha(HERE / "oracle.py") == direct["oracle_sha256"], "oracle source changed")
    require(sha(HERE / "oracle_controls.py") == direct["source_sha256"], "control source changed")
    require(sha(HERE / "cases.json") == direct["cases_sha256"], "control cases changed")
    require(direct["core_rows"] == manifest["core_rows"], "core set mismatch")
    require(manifest["initial"]["ids"] == direct["bases"]["cp_final"]["ids"], "wrong scan base")
    require(
        sha(ROOT / manifest["initial"]["path"])
        == manifest["initial"]["sha256"]
        == cases["cp_final"]["sha256"],
        "wrong initial source bytes",
    )
    require(
        manifest["initial"]["metrics"]
        == direct["bases"]["cp_final"]["metrics"] | {"cardinality": 64},
        "initial metrics",
    )
    require(sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"], "binary changed")
    require(sha(Path(manifest["compiler_path"])) == manifest["compiler_sha256"], "compiler changed")
    compiler_version = subprocess.check_output([manifest["compiler_path"], "--version"], text=True)
    require(compiler_version == manifest["compiler_version"], "compiler version changed")
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
    require(not (RAW / "control-final").exists(), "preserve final control binary")
    build = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (RAW / "build-final.stdout").write_text(build.stdout)
    (RAW / "build-final.stderr").write_text(build.stderr)
    require(build.returncode == 0 and not build.stderr, "control build failed")
    executions = []
    for base in ("old_h12", "cp_final"):
        control_command = [
            str(RAW / "control-final"),
            str(ROOT / cases[base]["path"]),
            str(RAW / f"{base}-cases.txt"),
        ]
        run = subprocess.run(control_command, capture_output=True, text=True, timeout=30)
        (RAW / f"{base}-final.stdout.jsonl").write_text(run.stdout)
        (RAW / f"{base}-final.stderr.txt").write_text(run.stderr)
        require(run.returncode == 0 and not run.stderr, "final finite control failed")
        executions.append({"command": control_command, "returncode": run.returncode})
    compared = compare.compare("final")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    standalone = load_module("independent_swap_standalone", ROOT / "scripts/check_cover.py")
    verified = []
    for index, row in enumerate(list(direct["bases"].values()) + direct["snapshots"]):
        ids = row["ids"]
        blocks = [oracle.SUBSETS[5][i] for i in ids]
        package = verify_cover(blocks, 16, 5, 3)
        separate = standalone.verify_cover(blocks, 16, 5, 3, expected_blocks=64)
        holes = [
            list(oracle.SUBSETS[3][i]) for i, count in enumerate(row["counts"]["3"]) if count == 0
        ]
        require(
            sorted(map(list, package["uncovered"])) == holes == separate["uncovered"],
            "independent verifier holes differ",
        )
        require(package["valid"] == separate["valid"] == (not holes), "false covering verdict")
        witness = RAW / f"control-family-{index:02d}.txt"
        witness.write_text(family_text(ids))
        require(
            sha(witness) == package["canonical_sha256"] == separate["canonical_sha256"],
            "candidate canonical hash differs",
        )
        verified.append(
            {
                "path": str(witness.relative_to(ROOT)),
                "sha256": sha(witness),
                "holes": len(holes),
                "package_valid": package["valid"],
                "standalone_valid": separate["valid"],
            }
        )
    runner = load_module("independent_swap_recorder", PRODUCER / "run.py")
    recorder = recorder_controls(direct, runner, manifest["core_rows"])
    rows = [oracle.SUBSETS[5][i] for i in direct["bases"]["cp_final"]["ids"]]
    invalid = {
        "duplicate": rows[:-1] + [rows[0]],
        "truncated_family": rows[:-1],
        "wrong_label": [(0, 2, 3, 4, 5)] + rows[1:],
        "wrong_block_size": [rows[0][:-1]] + rows[1:],
        "repeated_point": [(1, 1, 3, 4, 5)] + rows[1:],
    }
    empty_cases = RAW / "empty-cases.txt"
    empty_cases.write_text("")
    refusals = []
    for name, malformed in invalid.items():
        source = RAW / f"reject-{name}.txt"
        source.write_text("".join(" ".join(map(str, row)) + "\n" for row in malformed))
        run = subprocess.run(
            [str(RAW / "control-final"), str(source), str(empty_cases)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        require(run.returncode == 3 and bool(run.stderr), "damaged input accepted")
        refusals.append(
            {
                "name": name,
                "returncode": run.returncode,
                "stderr": run.stderr.strip(),
                "source_sha256": sha(source),
            }
        )
    require(sha(PRODUCER / "manifest.json") == MANIFEST_SHA, "producer changed during gate")
    receipt = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": sha(Path(__file__)),
        "optimizer_launches": 0,
        "launch_authority": "root only",
        "budget": manifest["budget"],
        "artifact_bindings": bindings,
        "reused_kernel_sha256": KERNEL_SHA,
        "reused_cores_sha256": CORES_SHA,
        "control_comparison": compared,
        "direct_count_delta_checks": direct["dependency_checks"],
        "proof_sha256": sha(HERE / "DEPENDENCY.md"),
        "proof_separate_review": "exact-search agent: dependency and unique-neighbor proofs sound",
        "build": {
            "command": command,
            "returncode": build.returncode,
            "compiler_sha256": manifest["compiler_sha256"],
            "compiler_version": compiler_version,
            "binary_sha256": sha(RAW / "control-final"),
        },
        "control_runs": executions,
        "verified_control_families": verified,
        "recorder_controls": recorder,
        "damaged_input_controls": refusals,
        "independent_sources": {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir()) if p.is_file()
        },
        "scope": "One fixed-base64-by4304 neighborhood; no global theorem; timeout is incomplete.",
        "saving": "Strict rank improvements plus every final best tie strictly below baseline.",
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "GO",
                "gate_sha256": sha(output),
                "manifest_sha256": MANIFEST_SHA,
                "fixed_swaps": compared["trials"],
            }
        )
    )


if __name__ == "__main__":
    main()
