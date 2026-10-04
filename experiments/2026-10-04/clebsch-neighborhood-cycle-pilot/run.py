# Document:    Clebsch Neighborhood and Cycle Construction Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6c05ca344cfd69accd3264a0b6f3a46b405f12b970a4e7cf484100d551233de7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""A conditional construction with 16 fixed neighbor blocks and 192 free cycles."""

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/clebsch-neighborhood-cycle-pilot-20261004"
sys.path.insert(0, str(ROOT / "src"))
from covering64.core import verify_cover  # noqa: E402

SEED = 2026106201
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def build():
    words = [x for x in range(32) if x.bit_count() % 2 == 0]
    edges = {
        p for p in itertools.combinations(range(1, 17), 2)
        if (words[p[0] - 1] ^ words[p[1] - 1]).bit_count() == 4
    }
    neighbors = {
        tuple(u for u in range(1, 17) if tuple(sorted((u, v))) in edges)
        for v in range(1, 17)
    }
    cycles = {
        b for b in BLOCKS
        if all(sum(tuple(sorted((u, v))) in edges for u in b if u != v) == 2 for v in b)
    }
    assert len(neighbors) == 16 and len(cycles) == 192 and not neighbors.intersection(cycles)
    kinds = [sum(p in edges for p in itertools.combinations(t, 2)) for t in TRIPLES]
    assert [kinds.count(k) for k in range(3)] == [160, 240, 160]
    model = cp_model.CpModel()
    variables = [
        model.new_int_var(int(b in neighbors), int(b in neighbors or b in cycles), f"block_{i}")
        for i, b in enumerate(BLOCKS)
    ]
    model.add(sum(variables) == 64)
    for triple, kind in zip(TRIPLES, kinds, strict=True):
        carriers = [i for i, b in enumerate(BLOCKS) if set(triple) <= set(b)]
        assert len(carriers) == 78
        row = sum(variables[i] for i in carriers)
        model.add_linear_constraint(row, 1, 2 if kind == 2 else 1)
    assert not model.validate()
    return model, variables, {
        "fixed_neighbor_ids": [i for i, b in enumerate(BLOCKS) if b in neighbors],
        "free_cycle_ids": [i for i, b in enumerate(BLOCKS) if b in cycles],
        "triple_kinds": kinds,
        "edges": sorted(edges),
    }


def parameters():
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.random_seed = SEED
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    return solver


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    model, _, geometry = build()
    RAW.mkdir(parents=True)
    (RAW / "model.pbtxt").write_text(str(model.proto))
    (RAW / "parameters.pbtxt").write_text(str(parameters().parameters))
    dump(HERE / "geometry.json", geometry)
    pins = {
        str(p.relative_to(ROOT)): sha(p)
        for p in [Path(__file__), HERE / "geometry.json", RAW / "model.pbtxt",
                  RAW / "parameters.pbtxt", ROOT / "src/covering64/core.py",
                  ROOT / "scripts/check_cover.py"]
    }
    dump(HERE / "manifest.json", {
        "scope": "Conditional 16-neighborhood Clebsch construction; not an unrestricted reduction.",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(), "ortools": ortools.__version__,
        "pins": pins, "variables": 4368, "rows": 561,
        "fixed_one": 16, "free_binary": 192, "fixed_zero": 4160,
        "seed": SEED, "native_seconds": 30, "workers": 1,
        "watchdog_seconds": 35, "termination_grace_seconds": 5,
        "calls": 1, "relaunch": False, "objective": None, "hint": None,
    })
    print(sha(HERE / "manifest.json"))


def child():
    model, variables, _ = build()
    assert str(model.proto) == (RAW / "model.pbtxt").read_text()
    solver = parameters()
    assert str(solver.parameters) == (RAW / "parameters.pbtxt").read_text()
    with (RAW / "solver.log").open("x") as log:
        solver.log_callback = lambda s: (log.write(s + "\n"), log.flush())
        start = time.monotonic()
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status), "native_wall_time": solver.wall_time,
        "elapsed_seconds": time.monotonic() - start,
        "independent_infeasibility_proof": False,
        "complete64": False,
    }
    (RAW / "response.pbtxt").write_text(str(solver.response_proto))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = [int(solver.value(v)) for v in variables]
        dump(RAW / "vector.json", values)
        blocks = [b for b, x in zip(BLOCKS, values, strict=True) if x]
        witness = HERE / "witness.txt"
        witness.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
        result["package"] = verify_cover(blocks)
        check = subprocess.run(
            [sys.executable, "-I", str(ROOT / "scripts/check_cover.py"), str(witness),
             "--expected-blocks", "64"], capture_output=True, text=True, check=False,
        )
        result["standalone"] = json.loads(check.stdout)
        result["standalone_returncode"] = check.returncode
        assert len(blocks) == 64 and result["package"]["valid"] and check.returncode == 0
        result["complete64"] = True
    dump(RAW / "child-result.json", result)


def execute(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] is True and gate["launch_permitted"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    for relative, digest in manifest["pins"].items():
        assert sha(ROOT / relative) == digest, relative
    assert ortools.__version__ == manifest["ortools"]
    marker = HERE / "launch.json"
    assert not marker.exists() and not (RAW / "child-result.json").exists()
    command = [sys.executable, str(Path(__file__)), "--child"]
    with marker.open("x") as out:
        json.dump({"manifest_sha256": sha(manifest_path), "gate_sha256": sha(gate_path),
                   "command": command, "started_unix": time.time()}, out, indent=2)
    start = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
    (RAW / "stdout.log").write_text(stdout)
    (RAW / "stderr.log").write_text(stderr)
    result = {
        "manifest_sha256": sha(manifest_path), "gate_sha256": sha(gate_path),
        "elapsed_seconds": time.monotonic() - start, "returncode": process.returncode,
        "watchdog": watchdog, "terminated": terminated, "killed": killed,
        "child": json.loads((RAW / "child-result.json").read_text())
        if (RAW / "child-result.json").exists() else None,
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()},
    }
    dump(HERE / "result.json", result)
    print(json.dumps({k: result[k] for k in ["returncode", "watchdog", "child"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--child", action="store_true")
    group.add_argument("--execute", action="store_true")
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child()
    else:
        assert args.gate is not None
        execute(args.gate)
