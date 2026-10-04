# Document:    H6 Two-Point Star Repair Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1fbf8391cf5ebd007873795b3fabf833ca1decb26981a598de1027573a2629dc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or execute one explicitly local H6 star pilot after an independent gate."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-two-point-star-repair-20261004"
OLD = HERE.parent / "two-point-star-repair-v2/run.py"
OLD_SHA = "708b31333b659e864f9ee4ab37c7ae9909833b13f7c64a229b4f6fbc6b2abdc7"
BASE = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
BASE_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
REVISION = "d2bfd843889e8b6f549881c7493fae196383b170"
PIVOT = (6, 10)
SEED = 2026106001

assert hashlib.sha256(OLD.read_bytes()).hexdigest() == OLD_SHA
SPEC = importlib.util.spec_from_file_location("h6_reused_star_v2", OLD)
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)
BLOCKS, TRIPLES, RANK = old.BLOCKS, old.TRIPLES, old.RANK
PAIRS = list(itertools.combinations(range(1, 17), 2))
sha, dump, family, dual = old.sha, old.dump, old.family, old.dual
read_model, check_vector, Collector = old.read_model, old.check_vector, old.Collector


def build(ids):
    """Reuse the old encoding, tightening only its final hole cap from 12 to 6."""
    model = old.build(ids, PIVOT)
    row = model.proto.constraints[len(model.proto.constraints) - 1]
    assert row.has_linear() and list(row.linear.domain) == [-(2**63), 12]
    assert list(row.linear.vars) == list(range(4368, 4928))
    assert list(row.linear.coeffs) == [1] * 560
    row.linear.domain[1] = 6
    assert not model.validate()
    return model


def violations(model, values):
    """Report every violated domain and active linear row for a complete vector."""
    assert len(values) == len(model.proto.variables)
    assert all(type(value) is int for value in values)
    errors = []
    for index, (value, variable) in enumerate(zip(values, model.proto.variables)):
        domain = list(variable.domain)
        if not any(a <= value <= b for a, b in zip(domain[::2], domain[1::2])):
            errors.append({"kind": "domain", "index": index, "value": value, "domain": domain})
    for index, row in enumerate(model.proto.constraints):
        active = all(values[e] if e >= 0 else not values[-e - 1] for e in row.enforcement_literal)
        if not active:
            continue
        assert row.has_linear()
        amount = sum(values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs))
        domain = list(row.linear.domain)
        if not any(a <= amount <= b for a, b in zip(domain[::2], domain[1::2])):
            record = {"kind": "linear", "row": index, "amount": amount, "domain": domain}
            if 1121 <= index <= 1240:
                record["pair"] = list(PAIRS[index - 1121])
            errors.append(record)
    return errors


def parameters():
    params = cp_model.CpSolver().parameters
    params.max_time_in_seconds = 120
    params.num_search_workers = 4
    params.random_seed = SEED
    params.log_search_progress = True
    return params


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert revision == REVISION and sha(BASE) == BASE_SHA
    blocks = [tuple(map(int, line.split())) for line in BASE.read_text().splitlines()]
    ids = sorted(RANK[b] for b in blocks)
    assert blocks == sorted(set(blocks)) and len(ids) == 64
    checks = dual(BASE)
    assert len(checks[0]["uncovered"]) == 6
    model = build(ids)
    chosen = set(ids)
    counts = {t: sum(set(t) <= set(BLOCKS[i]) for i in ids) for t in TRIPLES}
    values = [int(i in chosen) for i in range(4368)]
    values += [int(counts[t] == 0) for t in TRIPLES]
    bad = violations(model, values)
    expected_pairs = [(4, 6), (5, 6), (10, 12)]
    assert bad == [
        {
            "kind": "linear",
            "row": 1121 + PAIRS.index(pair),
            "amount": 4,
            "domain": [5, 2**63 - 1],
            "pair": list(pair),
        }
        for pair in expected_pairs
    ]
    hint = dict(zip(model.proto.solution_hint.vars, model.proto.solution_hint.values))
    assert len(hint) == 4928 and [hint[i] for i in range(4928)] == values
    RAW.mkdir(parents=True)
    model_path = RAW / "model.pbtxt"
    model_path.write_text(str(model.proto))
    parameter_path = RAW / "parameters.pbtxt"
    parameter_path.write_text(str(parameters()))
    dump(RAW / "initial-vector.json", {"values": values})
    dump(
        HERE / "initial-hint-audit.json",
        {
            "feasible": False,
            "complete": True,
            "violations": bad,
            "hole_count": 6,
            "blocks": 64,
            "baseline_verifiers": checks,
            "statement": "The complete initial hint is infeasible on exactly three pair rows.",
        },
    )
    dependencies = [
        OLD,
        BASE,
        ROOT / "uv.lock",
        ROOT / "scripts/check_cover.py",
        ROOT / "src/covering64/core.py",
        ROOT / "src/covering64/cli.py",
        HERE.parent / "two-point-star-repair-v2-runtime-independent/postcheck.json",
        HERE.parent / "h6-anchored-pair-repair/check.py",
        HERE.parent / "h6-anchored-pair-repair/profile.json",
    ]
    prepared = [
        model_path,
        parameter_path,
        RAW / "initial-vector.json",
        HERE / "initial-hint-audit.json",
        HERE / "README.md",
        HERE / "controls.py",
    ]
    dump(
        HERE / "manifest.json",
        {
            "source_revision": revision,
            "source_sha256": sha(__file__),
            "ortools_version": ortools.__version__,
            "python_version": platform.python_version(),
            "dependencies": {str(p.relative_to(ROOT)): sha(p) for p in dependencies},
            "prepared_files": {str(p.relative_to(ROOT)): sha(p) for p in prepared},
            "model": str(model_path.relative_to(ROOT)),
            "model_sha256": sha(model_path),
            "parameters": str(parameter_path.relative_to(ROOT)),
            "parameters_sha256": sha(parameter_path),
            "pivot": list(PIVOT),
            "variables": 4928,
            "rows": 1242,
            "fixed_blocks": 2002,
            "fixed_selected": 30,
            "free_blocks": 2366,
            "free_selected": 34,
            "seed": SEED,
            "seconds": 120,
            "workers": 4,
            "watchdog": 140,
            "grace": 5,
            "max_calls": 1,
            "initial_hint_feasible": False,
            "search_launches_during_preparation": 0,
            "scope": "One fixed {6,10} star neighborhood: retain every outside-star membership; "
            "exact64, exact hole flags, pair floor5, H<=6, minimize H. No D2/D3/D4, core or "
            "degree-profile restrictions. One call, no retries or budget transfers. The initial "
            "hint is infeasible. No unrestricted, global nonexistence or novelty claim.",
        },
    )


def preflight(gate_path):
    gate = json.loads(gate_path.read_text())
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert gate["decision"] == "GO" and gate["passed"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["source_sha256"] == sha(__file__)
    assert manifest["source_revision"] == REVISION
    assert manifest["ortools_version"] == ortools.__version__
    assert manifest["python_version"] == platform.python_version()
    for group in ("dependencies", "prepared_files"):
        for name, expected in manifest[group].items():
            assert sha(ROOT / name) == expected, name
    assert (
        manifest["seed"],
        manifest["seconds"],
        manifest["workers"],
        manifest["watchdog"],
        manifest["grace"],
        manifest["max_calls"],
    ) == (SEED, 120, 4, 140, 5, 1)
    return manifest


def child(gate_path):
    manifest = preflight(gate_path)
    output = RAW / "run-1"
    launch = json.loads((output / "launch.json").read_text())
    assert launch["gate_sha256"] == sha(gate_path)
    assert launch["manifest_sha256"] == sha(HERE / "manifest.json")
    with (output / "child-started.json").open("x") as handle:
        json.dump({"one_call": True, "gate_sha256": sha(gate_path)}, handle)
    model = read_model(ROOT / manifest["model"])
    solver = cp_model.CpSolver()
    assert solver.parameters.parse_text_format((ROOT / manifest["parameters"]).read_text())
    assert str(solver.parameters) == str(parameters())
    (output / "parameters.pbtxt").write_text(str(solver.parameters))
    collector = Collector(model, output)
    status = solver.solve(model, collector)
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        dump(output / "final-vector.json", {"values": list(solver.response_proto.solution)})
    (output / "response.pbtxt").write_text(str(solver.response_proto))
    dump(
        output / "outcome.json",
        {
            "status": solver.status_name(status),
            "wall_seconds": solver.wall_time,
            "callbacks": collector.count,
            "objective": solver.objective_value,
            "bound": solver.best_objective_bound,
        },
    )


def execute(gate_path):
    manifest = preflight(gate_path)
    assert not (HERE / "result.json").exists() and not (RAW / "run-1").exists()
    output = RAW / "run-1"
    output.mkdir()
    dump(
        output / "launch.json",
        {"gate_sha256": sha(gate_path), "manifest_sha256": sha(HERE / "manifest.json")},
    )
    command = [sys.executable, str(Path(__file__).resolve()), "--child", str(gate_path.resolve())]
    started = time.monotonic()
    timeout = False
    with (output / "stdout.log").open("w") as out, (output / "stderr.log").open("w") as err:
        process = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err)
        try:
            process.wait(timeout=manifest["watchdog"])
        except subprocess.TimeoutExpired:
            timeout = True
            process.terminate()
            try:
                process.wait(timeout=manifest["grace"])
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    model = read_model(ROOT / manifest["model"])
    saved = []
    vectors = sorted(output.glob("callback-*.json"))
    if (output / "final-vector.json").exists():
        vectors.append(output / "final-vector.json")
    for vector_path in vectors:
        values = json.loads(vector_path.read_text())["values"]
        check_vector(model, values)
        ids = [i for i, value in enumerate(values[:4368]) if value]
        witness = output / (vector_path.stem + ".txt")
        witness.write_text(family(ids))
        checks = dual(witness)
        holes = len(checks[0]["uncovered"])
        assert holes == sum(values[4368:])
        saved.append(
            {
                "vector": str(vector_path.relative_to(ROOT)),
                "witness": str(witness.relative_to(ROOT)),
                "holes": holes,
                "sha256": sha(witness),
                "verifiers": checks,
            }
        )
        if holes == 0:
            (HERE / "cover.txt").write_text(witness.read_text())
    outcome_path = output / "outcome.json"
    outcome = json.loads(outcome_path.read_text()) if outcome_path.exists() else None
    result = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "command": command,
        "returncode": process.returncode,
        "watchdog_fired": timeout,
        "elapsed_seconds": time.monotonic() - started,
        "outcome": outcome,
        "saved": saved,
        "cover_found": any(v["holes"] == 0 for v in saved),
        "relaunch": False,
        "calls": 1,
        "scope": manifest["scope"],
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*")) if p.is_file()
        },
    }
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "cover_found": result["cover_found"],
                "calls": 1,
                "result_sha256": sha(HERE / "result.json"),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--child", type=Path, metavar="GATE")
    group.add_argument("--execute", type=Path, metavar="GATE")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child(args.child)
    else:
        execute(args.execute)
