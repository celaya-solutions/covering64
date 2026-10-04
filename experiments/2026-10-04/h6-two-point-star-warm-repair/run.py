# Document:    H6 Two Point Star Warm Repair Adapter
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e4f60af4699df14ece27ea83f6c42e0184876ce431bd9885c94a43fe96fa447c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Prepare a feasible H9 hint; reuse the pinned one-call runner without rewriting it."""

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/h6-two-point-star-warm-repair-20261004"
BASE_RUNNER = HERE.parent / "h6-two-point-star-repair/run.py"
BASE_RUNNER_SHA = "b177c7986a8c35b03013f3bd8da18102151794a52d564c938033cf2a1e2943fd"
BASE_RAW = ROOT / "experiments/scratch/h6-two-point-star-repair-20261004"
BASE_MODEL_SHA = "32f04e29da51daa7983f2f64b75b966fe5779eae0e830df1ef5af5d4434d0814"
START = HERE.parent / "h6-anchored-pair-repair/candidate-02.txt"
START_SHA = "a579aa1176b5ab073db53208f3e2055df01b848fd82db94866ff870835428f05"
REVISION = "614ab2a22f503efc5df9a3b3d2fa821e2f12f63d"
SEED = 2026106002
PIVOT = (6, 10)

assert hashlib.sha256(BASE_RUNNER.read_bytes()).hexdigest() == BASE_RUNNER_SHA
SPEC = importlib.util.spec_from_file_location("frozen_h6_star_runner", BASE_RUNNER)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

# The inherited functions resolve these globals in their original module.
# Point execution and preflight at this adapter while retaining function bodies.
runner.HERE = HERE
runner.RAW = RAW
runner.BASE = START
runner.BASE_SHA = START_SHA
runner.SEED = SEED
runner.REVISION = REVISION
runner.__file__ = str(Path(__file__).resolve())
sha, dump = runner.sha, runner.dump
BLOCKS, TRIPLES = runner.BLOCKS, runner.TRIPLES


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert revision == REVISION and sha(START) == START_SHA
    assert sha(BASE_RAW / "model.pbtxt") == BASE_MODEL_SHA
    blocks = tuple(tuple(map(int, row.split())) for row in START.read_text().splitlines())
    assert len(blocks) == len(set(blocks)) == 64 and list(blocks) == sorted(blocks)
    chosen = {runner.RANK[block] for block in blocks}
    base_model = runner.read_model(BASE_RAW / "model.pbtxt")
    model = cp_model.CpModel()
    model.proto.copy_from(base_model.proto)
    assert len(model.proto.variables) == 4928 and len(model.proto.constraints) == 1242
    final_row = model.proto.constraints[1241]
    assert list(final_row.linear.vars) == list(range(4368, 4928))
    assert list(final_row.linear.coeffs) == [1] * 560
    assert list(final_row.linear.domain) == [-(2**63), 6]
    final_row.linear.domain[1] = 9
    values = [int(i in chosen) for i in range(4368)]
    values += [int(not any(set(t) <= set(b) for b in blocks)) for t in TRIPLES]
    assert sum(values[:4368]) == 64 and sum(values[4368:]) == 9
    assert list(model.proto.solution_hint.vars) == [*range(4368, 4928), *range(4368)]
    for position, variable in enumerate(model.proto.solution_hint.vars):
        model.proto.solution_hint.values[position] = values[variable]
    assert not model.validate() and runner.violations(model, values) == []
    runner.check_vector(model, values)
    checks = runner.dual(START)
    assert len(checks[0]["uncovered"]) == 9 and checks[0]["valid"] is False
    outside = [i for i, block in enumerate(BLOCKS) if not set(PIVOT).intersection(block)]
    old_values = json.loads((BASE_RAW / "initial-vector.json").read_text())["values"]
    assert len(outside) == 2002 and sum(values[i] for i in outside) == 30
    assert all(values[i] == old_values[i] for i in outside)
    changed = [i for i in range(4368) if values[i] != old_values[i]]
    assert len(changed) == 4 and all(set(PIVOT).intersection(BLOCKS[i]) for i in changed)
    restored = cp_model.CpModel()
    restored.proto.copy_from(model.proto)
    restored.proto.constraints[1241].linear.domain[1] = 6
    restored.proto.solution_hint.copy_from(base_model.proto.solution_hint)
    assert str(restored.proto) == str(base_model.proto)
    parameters = runner.parameters()
    original_parameters = type(parameters)()
    assert original_parameters.parse_text_format((BASE_RAW / "parameters.pbtxt").read_text())
    restored_parameters = type(parameters)()
    restored_parameters.copy_from(parameters)
    restored_parameters.random_seed = 2026106001
    assert str(restored_parameters) == str(original_parameters)

    RAW.mkdir(parents=True)
    model_path = RAW / "model.pbtxt"
    model_path.write_text(str(model.proto))
    parameters_path = RAW / "parameters.pbtxt"
    parameters_path.write_text(str(parameters))
    dump(RAW / "initial-vector.json", {"values": values})
    dump(
        HERE / "initial-hint-audit.json",
        {
            "complete": True,
            "feasible": True,
            "blocks": 64,
            "hole_count": 9,
            "violations": [],
            "baseline_verifiers": checks,
            "initial_sha256": START_SHA,
            "statement": "The full H9 hint satisfies every domain and row of the new model.",
            "weak_pair_qualification_claim": False,
        },
    )
    dump(
        HERE / "outside-membership-proof.json",
        {
            "passed": True,
            "pivot": list(PIVOT),
            "outside_memberships": 2002,
            "outside_selected": 30,
            "free_memberships": 2366,
            "free_selected": 34,
            "outside_memberships_unchanged": True,
            "changed_global_ids": changed,
            "changed_blocks": [BLOCKS[i] for i in changed],
            "every_changed_block_touches_pivot": True,
            "old_initial_vector_sha256": sha(BASE_RAW / "initial-vector.json"),
            "new_initial_vector_sha256": sha(RAW / "initial-vector.json"),
        },
    )
    dump(
        HERE / "model-delta.json",
        {
            "passed": True,
            "base_model_sha256": BASE_MODEL_SHA,
            "model_sha256": sha(model_path),
            "changed_constraint_indices": [1241],
            "old_hole_cap": 6,
            "new_hole_cap": 9,
            "changed_hint_positions": [
                i
                for i, (a, b) in enumerate(
                    zip(base_model.proto.solution_hint.values, model.proto.solution_hint.values)
                )
                if a != b
            ],
            "hint_variable_order_unchanged": True,
            "all_other_proto_content_unchanged": True,
            "restoring_hole_cap_and_hint_recovers_base_proto_exactly": True,
            "parameter_delta_only_random_seed": [2026106001, SEED],
            "base_parameters_sha256": sha(BASE_RAW / "parameters.pbtxt"),
            "parameters_sha256": sha(parameters_path),
        },
    )
    dependencies = [
        BASE_RUNNER,
        BASE_RAW / "model.pbtxt",
        BASE_RAW / "parameters.pbtxt",
        BASE_RAW / "initial-vector.json",
        START,
        HERE.parent / "two-point-star-repair-v2/run.py",
        HERE.parent / "h6-two-point-star-repair/manifest.json",
        HERE.parent / "h6-two-point-star-repair-independent/gate.json",
        HERE.parent / "h6-two-point-star-repair-independent/checks.json",
        HERE.parent / "h6-two-point-star-repair-runtime-independent/postcheck.json",
        HERE.parent / "h6-anchored-pair-repair/profile.json",
        HERE.parent / "h6-anchored-pair-repair-independent/review.json",
        ROOT / "uv.lock",
        ROOT / "scripts/check_cover.py",
        ROOT / "src/covering64/core.py",
        ROOT / "src/covering64/cli.py",
    ]
    prepared = [
        model_path,
        parameters_path,
        RAW / "initial-vector.json",
        HERE / "initial-hint-audit.json",
        HERE / "outside-membership-proof.json",
        HERE / "model-delta.json",
        HERE / "README.md",
        HERE / "controls.py",
    ]
    dump(
        HERE / "manifest.json",
        {
            "source_revision": revision,
            "source_sha256": sha(__file__),
            "base_runner_path": str(BASE_RUNNER.relative_to(ROOT)),
            "base_runner_sha256": BASE_RUNNER_SHA,
            "runner_strategy": "Pinned runner functions reused unchanged with adapter globals.",
            "ortools_version": ortools.__version__,
            "python_version": platform.python_version(),
            "dependencies": {str(p.relative_to(ROOT)): sha(p) for p in dependencies},
            "prepared_files": {str(p.relative_to(ROOT)): sha(p) for p in prepared},
            "model": str(model_path.relative_to(ROOT)),
            "model_sha256": sha(model_path),
            "parameters": str(parameters_path.relative_to(ROOT)),
            "parameters_sha256": sha(parameters_path),
            "pivot": list(PIVOT),
            "variables": 4928,
            "rows": 1242,
            "fixed_blocks": 2002,
            "fixed_selected": 30,
            "free_blocks": 2366,
            "free_selected": 34,
            "initial_sha256": START_SHA,
            "initial_hint_feasible": True,
            "hole_ceiling": 9,
            "seed": SEED,
            "seconds": 120,
            "workers": 4,
            "watchdog": 140,
            "grace": 5,
            "max_calls": 1,
            "search_launches_during_preparation": 0,
            "scope": (
                "Same fixed {6,10} outside memberships as the prior star model; exact64, "
                "exact hole flags, pair floor5, H<=9, minimize H. Only model deltas are "
                "the hole ceiling6 to9 and full feasible H9 hint. No D2/D3/D4, core or "
                "degree restrictions. One call; no retry, extension or budget transfer."
            ),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "initial_hint_feasible": True,
                "optimizer_launches": 0,
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
        runner.child(args.child)
    else:
        runner.execute(args.execute)
