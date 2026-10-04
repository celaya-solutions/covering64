# Document:    Strong Compact Model Launch Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      96930313e8d5b784331b60bd85e4c4ad4fed6f2aa00a76011df980775dae3eb7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind the reviewed runner to the independently reconstructed frozen model."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / "experiments/2026-10-04/compact-pair-two-counts"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    model_gate_path = HERE / "model-gate.json"
    model_gate = json.loads(model_gate_path.read_text())
    manifest = json.loads((TARGET / "manifest.json").read_text())
    assert model_gate["passed"] and model_gate["optimizer_calls"] == 0
    assert sha(HERE / "check.py") == model_gate["checker_sha256"]
    assert sha(TARGET / "manifest.json") == model_gate["manifest_sha256"]
    assert sha(TARGET / "prepare.py") == model_gate["source_sha256"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    runner = TARGET / "execute.py"
    assert sha(runner) == "0445dff332c3e8b817c843ea3d82c56f1b95b85ec7918213af6dc14ab99e6803"
    calls = [
        node
        for node in ast.walk(ast.parse(runner.read_text()))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("solve", "Solve")
    ]
    assert len(calls) == 1
    spec = importlib.util.spec_from_file_location("reviewed_compact_runner", runner)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model, solver = module.load_frozen(manifest)
    assert len(model.proto.variables) == 5608 and len(model.proto.constraints) == 14404
    assert solver.parameters.max_time_in_seconds == 120
    assert solver.parameters.num_search_workers == 4 and solver.parameters.random_seed == 2026104301
    assert (
        not module.RAW.exists()
        and not module.OUTPUT.exists()
        and not (TARGET / "result.json").exists()
    )
    for relative in [
        "experiments/2026-10-04/global-five-heavy-dp-plan/check.py",
        "experiments/2026-10-04/global-five-heavy-dp-plan/result.json",
    ]:
        assert relative in manifest["input_files"]
    implication = ROOT / "experiments/2026-10-04/pair-cuts-imply-profile-independent/audit.json"
    assert sha(implication) == "2357a0cc1574912c0aab8f3dc9c7ded95a44be672aca32fd813bfb6f13594912"
    result = {
        **model_gate,
        "runner_source_sha256": sha(runner),
        "model_gate_sha256": sha(model_gate_path),
        "launch_checker_sha256": sha(Path(__file__)),
        "profile_implication_sha256": sha(implication),
        "runner_review": {
            "single_solve_call_site": True,
            "no_relaunch_guard": True,
            "serialized_model_and_parameters_roundtrip": True,
            "all_improvements_distinct_ties_and_final_saved": True,
            "complete5608_value_vectors_saved": True,
            "native_response_and_logs_saved": True,
            "global_profile_counter_bound_in_inputs": True,
            "infeasible_block_guidance_labeled": True,
            "all_saved_families_require_independent_postcheck": True,
        },
        "run_scope": "Exactly one120-second CP-SAT run, four workers, seed2026104301. "
        "No retries or budget extension. No optimizer was called by this gate.",
    }
    (HERE / "gate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "manifest_sha256": result["manifest_sha256"],
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
