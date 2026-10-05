# Document:    Global Circulant Pair Profile Orbit Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bc40ae061ef210c9d0e5ff2790de39896218995c31d2609d3ad3d4da916a06b2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One full-block model for all 52 excess-profile representatives; root launch only."""

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
RAW = ROOT / "experiments/scratch/circulant-all-profile-global-pilot-20261004"
ENUMERATION = HERE.parent / "circulant-all-excess-profiles"
INDEPENDENT = HERE.parent / "circulant-all-excess-independent"
GEOMETRY_SHA = "c1c9e6d640141238e03e2a37fb37155c1ee8f67868dd59fca8844fd93ec0a1a9"
ORBITS_SHA = "d0aab8d3de76e07c23a71adb10d10b36e403275fd236f52522f38e0efac480d6"
SEED = 2026106501
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
sys.path.insert(0, str(ROOT / "src"))
from covering64.core import verify_cover  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def inputs():
    assert sha(ENUMERATION / "geometry.json") == GEOMETRY_SHA
    assert sha(INDEPENDENT / "orbits.json") == ORBITS_SHA
    geometry = json.loads((ENUMERATION / "geometry.json").read_text())
    orbits = json.loads((INDEPENDENT / "orbits.json").read_text())
    representatives = [entry["representative_mask"] for entry in orbits]
    assert len(representatives) == 52 and representatives == sorted(set(representatives))
    assert len(geometry["forced"]) == 32 and len(geometry["choices"]) == 48
    table = [
        {"representative_mask": mask, "center_bits": [(mask >> i) & 1 for i in range(48)]}
        for mask in representatives
    ]
    return geometry, table


def build():
    geometry, table = inputs()
    forced = {tuple(sorted((p, q, centers[0]))) for p, q, centers in geometry["forced"]}
    conditional = {}
    for index, (p, q, centers) in enumerate(geometry["choices"]):
        for bit, center in enumerate(centers):
            triple = tuple(sorted((p, q, center)))
            assert triple not in forced and triple not in conditional
            conditional[triple] = (index, 1 if bit == 0 else -1, 2 if bit == 0 else 1)
    assert len(forced) == 32 and len(conditional) == 96
    model = cp_model.CpModel()
    blocks = [model.new_bool_var(f"block_{i}") for i in range(4368)]
    choices = [model.new_bool_var(f"center_choice_{i}") for i in range(48)]
    model.add(sum(blocks) == 64)
    for triple in TRIPLES:
        carriers = [i for i, block in enumerate(BLOCKS) if all(p in block for p in triple)]
        assert len(carriers) == 78
        row = sum(blocks[i] for i in carriers)
        if triple in conditional:
            index, coefficient, demand = conditional[triple]
            model.add(row + coefficient * choices[index] == demand)
        else:
            model.add(row == (2 if triple in forced else 1))
    model.add_allowed_assignments(choices, [entry["center_bits"] for entry in table])
    assert not model.validate()
    assert len(model.proto.variables) == 4416 and len(model.proto.constraints) == 562
    return model, blocks, choices, table


def parameters():
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = SEED
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 4
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    return solver


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    model, _, _, table = build()
    RAW.mkdir(parents=True)
    (RAW / "model.pbtxt").write_text(str(model.proto))
    (RAW / "parameters.pbtxt").write_text(str(parameters().parameters))
    dump(HERE / "allowed-profile-table.json", table)
    paths = [
        Path(__file__),
        HERE / "seed-check.json",
        HERE / "allowed-profile-table.json",
        RAW / "model.pbtxt",
        RAW / "parameters.pbtxt",
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
    ]
    paths.extend(ENUMERATION / name for name in ("enumerate.py", "geometry.json", "profiles.json"))
    paths.extend(
        INDEPENDENT / name
        for name in ("check.py", "audit.json", "orbits.json", "automorphisms.json", "README.md")
    )
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "python": platform.python_version(),
            "ortools": ortools.__version__,
            "pins": {str(path.relative_to(ROOT)): sha(path) for path in paths},
            "scope": (
                "Named circulant pair profile; complete reduction by excess-profile symmetry."
            ),
            "graph_steps_mod16": [1, 3, 8, 13, 15],
            "excess_profiles": 1300,
            "graph_automorphisms": 32,
            "excess_profile_representatives": 52,
            "cover_orbits_classified": False,
            "block_variables": 4368,
            "choice_variables": 48,
            "variables": 4416,
            "binary_variables": 4416,
            "fixed_variables": 0,
            "rows": 562,
            "cardinality_rows": 1,
            "triple_rows": 560,
            "table_rows": 1,
            "allowed_table_vectors": 52,
            "table_columns": 48,
            "forced_demand_two_triples": 32,
            "conditional_triples": 96,
            "fixed_demand_one_triples": 432,
            "fixed_links": None,
            "fixed_neighborhoods": None,
            "fixed_blocks": None,
            "cover_invariance_constraints": None,
            "hint": None,
            "objective": None,
            "seed": SEED,
            "native_seconds": 300,
            "workers": 4,
            "watchdog_seconds": 310,
            "termination_grace_seconds": 5,
            "calls": 1,
            "relaunch": False,
            "retries": False,
            "budget_transfer": False,
        },
    )
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "optimizer_calls": 0,
                "pins": len(paths),
            }
        )
    )


def child():
    assert not (RAW / "child-result.json").exists()
    model, block_variables, choice_variables, table = build()
    assert str(model.proto) == (RAW / "model.pbtxt").read_text()
    assert table == json.loads((HERE / "allowed-profile-table.json").read_text())
    solver = parameters()
    assert str(solver.parameters) == (RAW / "parameters.pbtxt").read_text()
    with (RAW / "solver.log").open("x") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        start = time.monotonic()
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status),
        "native_seconds": solver.wall_time,
        "solve_elapsed_seconds": time.monotonic() - start,
        "complete64": False,
        "independent_infeasibility_proof": False,
    }
    (RAW / "response.pbtxt").write_text(str(solver.response_proto))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = [int(solver.value(v)) for v in block_variables]
        center_bits = [int(solver.value(v)) for v in choice_variables]
        mask = sum(bit << i for i, bit in enumerate(center_bits))
        assert center_bits in [entry["center_bits"] for entry in table]
        dump(
            RAW / "vector.json",
            {"block_values": values, "center_bits": center_bits, "representative_mask": mask},
        )
        blocks = [block for block, selected in zip(BLOCKS, values, strict=True) if selected]
        witness = HERE / "witness.txt"
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
        geometry, _ = inputs()
        excess = {tuple(sorted((p, q, centers[0]))) for p, q, centers in geometry["forced"]}
        excess |= {
            tuple(sorted((p, q, centers[center_bits[i]])))
            for i, (p, q, centers) in enumerate(geometry["choices"])
        }
        triple_counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
        result["exact_profile_matches"] = all(
            triple_counts[t] == 1 + int(t in excess) for t in TRIPLES
        )
        pairs = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
        edges = {tuple(e) for e in geometry["edges"]}
        result["pair_profile_matches"] = all(
            pairs[pair] == (6 if pair in edges else 5)
            for pair in itertools.combinations(range(1, 17), 2)
        )
        assert len(blocks) == 64 and result["package"]["valid"] and standalone.returncode == 0
        assert result["exact_profile_matches"] is True and result["pair_profile_matches"] is True
        result.update(
            {"complete64": True, "representative_mask": mask, "witness_sha256": sha(witness)}
        )
    dump(RAW / "child-result.json", result)


def execute(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] is True and gate["launch_permitted"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    for relative, digest in manifest["pins"].items():
        assert sha(ROOT / relative) == digest, relative
    assert manifest["ortools"] == ortools.__version__
    assert not (HERE / "launch.json").exists() and not (HERE / "result.json").exists()
    assert not (RAW / "child-result.json").exists()
    command = [sys.executable, str(Path(__file__)), "--child"]
    with (HERE / "launch.json").open("x") as out:
        json.dump(
            {
                "manifest_sha256": sha(manifest_path),
                "gate_sha256": sha(gate_path),
                "command": command,
                "started_unix": time.time(),
            },
            out,
            indent=2,
        )
    start = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    watchdog = terminated = killed = False
    try:
        stdout, stderr = process.communicate(timeout=310)
    except subprocess.TimeoutExpired:
        watchdog = terminated = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            killed = True
            process.kill()
            stdout, stderr = process.communicate()
    (RAW / "stdout.log").write_text(stdout)
    (RAW / "stderr.log").write_text(stderr)
    result = {
        "manifest_sha256": sha(manifest_path),
        "gate_sha256": sha(gate_path),
        "elapsed_seconds": time.monotonic() - start,
        "returncode": process.returncode,
        "watchdog": watchdog,
        "terminated": terminated,
        "killed": killed,
        "child": json.loads((RAW / "child-result.json").read_text())
        if (RAW / "child-result.json").exists()
        else None,
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path) for path in RAW.iterdir() if path.is_file()
        },
    }
    dump(HERE / "result.json", result)
    print(json.dumps({key: result[key] for key in ("returncode", "watchdog", "child")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--child", action="store_true")
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child()
    else:
        assert args.gate is not None
        execute(args.gate)
