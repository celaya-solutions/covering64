# Document:    Eight Unfixed Circulant Exact Profile Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      418c2cf6677e18437bcc2651d1630e382683b43c0e1f9cd334319858a44568d2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare eight full block models; the root alone may launch an approved batch."""

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARITHMETIC = HERE.parent / "circulant-pair-graph-screen"
RAW = ROOT / "experiments/scratch/circulant-exact-profile-pilot-20261004"
PROFILE_SHA = "dec757aef695e80546c0408a5ebe116cb4666e9472e1e3b429d07bef2990a908"
SEEDS = list(range(2026106401, 2026106409))
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
sys.path.insert(0, str(ROOT / "src"))
from covering64.core import verify_cover  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def profile(index):
    assert type(index) is int and 0 <= index < 8
    path = ARITHMETIC / "profiles.json"
    assert sha(path) == PROFILE_SHA
    data = json.loads(path.read_text())[index]
    excess = {tuple(t) for t in data["excess_triples"]}
    assert len(excess) == 80 and excess <= set(TRIPLES)
    return data, excess


def build(index):
    _, excess = profile(index)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{i}") for i in range(len(BLOCKS))]
    model.add(sum(variables) == 64)
    for triple in TRIPLES:
        carriers = [i for i, block in enumerate(BLOCKS) if all(p in block for p in triple)]
        assert len(carriers) == 78
        model.add(sum(variables[i] for i in carriers) == 1 + int(triple in excess))
    assert not model.validate()
    assert len(model.proto.variables) == 4368 and len(model.proto.constraints) == 561
    return model, variables


def parameters(index):
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = SEEDS[index]
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 1
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    return solver


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    RAW.mkdir(parents=True)
    cases = []
    for index in range(8):
        data, _ = profile(index)
        case = RAW / f"case-{index + 1:02d}"
        case.mkdir()
        model, _ = build(index)
        (case / "model.pbtxt").write_text(str(model.proto))
        (case / "parameters.pbtxt").write_text(str(parameters(index).parameters))
        cases.append(
            {
                "index": index,
                "name": case.name,
                "seed": SEEDS[index],
                "center_offsets": data["center_offsets"],
                "point_link_core_type": data["point_links"][0]["type"],
                "model_sha256": sha(case / "model.pbtxt"),
                "parameters_sha256": sha(case / "parameters.pbtxt"),
            }
        )
    paths = [
        Path(__file__),
        HERE / "seed-check.json",
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
    ]
    paths.extend(
        ARITHMETIC / name
        for name in (
            "build.py",
            "summary.json",
            "profiles.json",
            "geometry.json",
            "screen.json",
            "rejected-orbit-choices.json",
            "README.md",
        )
    )
    paths.extend(
        RAW / case["name"] / name for case in cases for name in ("model.pbtxt", "parameters.pbtxt")
    )
    manifest = {
        "scope": "Eight exact profiles for the non-Clebsch circulant pair graph; conditional only.",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "ortools": ortools.__version__,
        "cases": cases,
        "pins": {str(p.relative_to(ROOT)): sha(p) for p in paths},
        "variables": 4368,
        "binary_variables": 4368,
        "fixed_variables": 0,
        "rows": 561,
        "cardinality": 64,
        "triple_rows": 560,
        "triple_demand_one": 480,
        "triple_demand_two": 80,
        "hint": None,
        "objective": None,
        "fixed_links": None,
        "fixed_neighborhoods": None,
        "cover_symmetry_constraints": None,
        "calls": 8,
        "sequential": True,
        "workers_per_call": 1,
        "native_seconds_per_call": 30,
        "native_seconds_total_cap": 240,
        "watchdog_seconds_per_call": 35,
        "termination_grace_seconds_per_call": 5,
        "relaunch": False,
        "retries": False,
        "budget_transfer": False,
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "models_prepared": 8,
                "optimizer_calls": 0,
                "pins": len(paths),
            }
        )
    )


def child(index):
    assert type(index) is int and 0 <= index < 8
    case = RAW / f"case-{index + 1:02d}"
    assert not (case / "child-result.json").exists()
    model, variables = build(index)
    assert str(model.proto) == (case / "model.pbtxt").read_text()
    solver = parameters(index)
    assert str(solver.parameters) == (case / "parameters.pbtxt").read_text()
    with (case / "solver.log").open("x") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        start = time.monotonic()
        status = solver.solve(model)
    result = {
        "index": index,
        "seed": SEEDS[index],
        "status": solver.status_name(status),
        "native_seconds": solver.wall_time,
        "solve_elapsed_seconds": time.monotonic() - start,
        "complete64": False,
        "independent_infeasibility_proof": False,
    }
    (case / "response.pbtxt").write_text(str(solver.response_proto))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = [int(solver.value(v)) for v in variables]
        dump(case / "vector.json", values)
        blocks = [block for block, selected in zip(BLOCKS, values, strict=True) if selected]
        witness = HERE / f"witness-{index + 1:02d}.txt"
        assert not witness.exists()
        witness.write_text("".join(" ".join(map(str, block)) + "\n" for block in blocks))
        result["package"] = verify_cover(blocks)
        standalone = subprocess.run(
            [
                sys.executable,
                "-I",
                str(ROOT / "scripts/check_cover.py"),
                str(witness),
                "--expected-blocks",
                "64",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        result["standalone"] = json.loads(standalone.stdout)
        result["standalone_returncode"] = standalone.returncode
        _, excess = profile(index)
        triple_counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
        result["exact_profile_matches"] = all(
            triple_counts[t] == 1 + int(t in excess) for t in TRIPLES
        )
        assert len(blocks) == 64 and result["package"]["valid"] and standalone.returncode == 0
        assert result["exact_profile_matches"] is True
        result["complete64"] = True
        result["witness_sha256"] = sha(witness)
    dump(case / "child-result.json", result)


def execute(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] is True and gate["launch_permitted"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    for relative, digest in manifest["pins"].items():
        assert sha(ROOT / relative) == digest, relative
    assert manifest["ortools"] == ortools.__version__ and len(manifest["cases"]) == 8
    assert not (HERE / "launch.json").exists() and not (HERE / "result.json").exists()
    assert all(
        not (RAW / case["name"] / "child-result.json").exists() for case in manifest["cases"]
    )
    with (HERE / "launch.json").open("x") as out:
        json.dump(
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "started_unix": time.time(),
                "seeds": SEEDS,
                "sequential": True,
            },
            out,
            indent=2,
        )
    start = time.monotonic()
    runs = []
    for index in range(8):
        case = RAW / f"case-{index + 1:02d}"
        command = [sys.executable, str(Path(__file__)), "--child", "--profile", str(index)]
        case_start = time.monotonic()
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        watchdog = terminated = killed = False
        try:
            stdout, stderr = process.communicate(timeout=35)
        except subprocess.TimeoutExpired:
            watchdog = terminated = True
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                killed = True
                process.kill()
                stdout, stderr = process.communicate()
        (case / "stdout.log").write_text(stdout)
        (case / "stderr.log").write_text(stderr)
        child_path = case / "child-result.json"
        result = {
            "index": index,
            "seed": SEEDS[index],
            "command": command,
            "elapsed_seconds": time.monotonic() - case_start,
            "returncode": process.returncode,
            "watchdog": watchdog,
            "terminated": terminated,
            "killed": killed,
            "child": json.loads(child_path.read_text()) if child_path.exists() else None,
            "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in case.iterdir() if p.is_file()},
        }
        runs.append(result)
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "elapsed_seconds": time.monotonic() - start,
                "planned_calls": 8,
                "finished_calls": len(runs),
                "runs": runs,
            },
        )
        print(
            json.dumps(
                {
                    "index": index,
                    "returncode": process.returncode,
                    "watchdog": watchdog,
                    "child": result["child"],
                }
            ),
            flush=True,
        )
        if process.returncode != 0 or watchdog or result["child"] is None:
            break
        if result["child"]["status"] == "MODEL_INVALID":
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--child", action="store_true")
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--profile", type=int)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child(args.profile)
    else:
        assert args.gate is not None
        execute(args.gate)
