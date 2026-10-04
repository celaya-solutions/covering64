# Document:    Independent Radius Four Runner Review
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1ca19104d48ab008948a9fc6386b2d454a10e91f62b436ce130c563045838e51
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Static runner inspection only; never imports or invokes a solver."""

import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.with_name("radius-four-feasibility-repair-v2")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    path = PRODUCER / "execute.py"
    source = path.read_text()
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    attr_calls = lambda name: [  # noqa: E731
        node for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr == name
    ]
    solves = attr_calls("solve")
    assert len(solves) == 1
    assert isinstance(solves[0].func.value, ast.Name) and solves[0].func.value.id == "solver"
    assert not any(
        isinstance(node, (ast.For, ast.While)) and solves[0] in list(ast.walk(node))
        for node in ast.walk(tree)
    )
    launches = attr_calls("Popen")
    assert len(launches) == 1
    assert not any(
        isinstance(node, (ast.For, ast.While)) and launches[0] in list(ast.walk(node))
        for node in ast.walk(tree)
    )
    stops = attr_calls("stop_search")
    assert len(stops) == 1
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "cover"
        and stops[0] in list(ast.walk(node))
        for node in ast.walk(tree)
    )
    expected_fragments = [
        "len(model.proto.variables) == 5728 and len(model.proto.constraints) == 14407",
        "variables = [model.get_int_var_from_proto_index(i) for i in range(5728)]",
        "checked = prep.check_vector(model, values)",
        'canonical_check = prep.check_vector(model, actual["values"])',
        'values[:5608] == actual["values"][:5608]',
        'all(a >= b for a, b in zip(values[5608:], actual["values"][5608:], strict=True))',
        'metrics["holes"] <= 11 and metrics["replacement_distance"] <= 4',
        'verification = helper.dual_verify(actual["blocks"], metrics["holes"])',
        'cover = metrics["holes"] == 0',
        'all(verification[k]["valid"] is cover for k in ("package", "standalone"))',
        '"values": values',
        '"canonical_values": actual["values"]',
        '"verification": verification',
        '"vector_sha256": prep.sha(vector)',
        '"witness_sha256": prep.sha(witness)',
        '"receipt_sha256": prep.sha(receipt)',
        '"feasible_partial": not cover',
        "if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):",
        'save([solver.value(v) for v in variables], "final", elapsed)',
        '(RUN / "response.pbtxt").write_text(str(solver.response_proto))',
        "process.wait(timeout=330)",
        "process.wait(timeout=5)",
        "process.terminate()",
        "process.kill()",
        "except (OSError, json.JSONDecodeError) as error:",
        'child_terminal_error = f"{type(error).__name__}: {error}"',
        'terminal = "WATCHDOG_TIMEOUT"',
        'terminal = "ERROR"',
        '"optimizer_call_upper_bound": 1',
        '"relaunch": False',
        '"budget_transfer": False',
        '"objective": None',
    ]
    for fragment in expected_fragments:
        assert fragment in source, fragment
    checks = {
        "single_solve_call_outside_loops": True,
        "single_child_launch_outside_loops": True,
        "watchdog_330_grace_5_no_retry": True,
        "sole_explicit_stop_guarded_by_actual_cover": True,
        "all_5728_callback_and_final_values_saved": True,
        "raw_and_canonical_vector_checks_preserved": True,
        "actual_recount_and_dual_verifier_before_cover_classification": True,
        "partial_and_cover_flags_separate": True,
        "response_proto_and_stats_saved_on_normal_return": True,
        "malformed_terminal_file_recovery_present": True,
        "local_scope_and_no_global_proof_claim": True,
    }
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "check_type": "AST assertions and direct source review; not a solver execution",
        "runner_path": str(path.relative_to(ROOT)),
        "runner_sha256": sha(path),
        "checker_sha256": sha(Path(__file__)),
        "checks": checks,
        "scope_limit": (
            "Runner only; model/parameter proof and post-run vector audit belong to root."
        ),
        "resolved_issue": "V1 could fail to write a terminal result after a watchdog interrupted "
        "child-result.json; v2 catches unreadable/malformed child terminal files and recovers "
        "complete receipts before reporting WATCHDOG_TIMEOUT or ERROR.",
    }
    output = HERE / "source-review.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "runner_sha256": sha(path), "review_sha256": sha(output)}))


if __name__ == "__main__":
    main()
