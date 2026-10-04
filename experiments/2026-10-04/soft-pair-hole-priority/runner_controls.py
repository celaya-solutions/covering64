# Document:    Hole-Priority Runner Semantic Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c908a1c1b642c1711a8d01a2b21d8faf7e71b0dc821360904992f7fa60dc84ec
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import ast
import hashlib
import json
from pathlib import Path

from execute import classify_record

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "runner-semantics.json"
    assert not output.exists()
    base = {
        "holes": 0,
        "D2max": 0,
        "D2sum": 0,
        "D3": 0,
        "D4": 0,
        "minimum_pair_count": 5,
        "core_overlaps": [1, 1, 1, 2],
    }
    yes = {name: {"valid": True} for name in ("package", "standalone")}
    no = {name: {"valid": False} for name in ("package", "standalone")}
    assert classify_record(base, yes, {"maximum": 0}) == (True, False)
    partial = base | {"holes": 1}
    assert classify_record(partial, no, {"maximum": 0}) == (False, True)
    rejected_hints = []
    for field, value in (
        ("D2max", 1),
        ("D2sum", 1),
        ("D3", 1),
        ("D4", 1),
        ("minimum_pair_count", 4),
        ("core_overlaps", [56, 1, 1, 2]),
    ):
        assert classify_record(partial | {field: value}, no, {"maximum": 0}) == (False, False)
        rejected_hints.append(field)
    assert classify_record(partial, no, {"maximum": 27}) == (False, False)
    invalid_verdicts = [
        no,
        {"package": {"valid": True}, "standalone": {"valid": False}},
        {"package": {"valid": 1}, "standalone": {"valid": True}},
    ]
    for verdict in invalid_verdicts:
        try:
            classify_record(base, verdict, {"maximum": 0})
        except ValueError:
            pass
        else:
            raise AssertionError("inconsistent verdict accepted")
    novelty = HERE.parent / "soft-pair-h12-relabel-novelty"
    current = json.loads((novelty / "diagnostic.json").read_text())["producer_final"][
        "actual_metrics"
    ]
    actual_verdicts = {
        name: json.loads((novelty / f"final-{name}.json").read_text())
        for name in ("package", "standalone")
    }
    assert classify_record(current, actual_verdicts, {"maximum": 0}) == (False, False)
    tree = ast.parse((HERE / "execute.py").read_text())
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "stop_search"
    ]
    assert len(calls) == 1
    guards = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "covering"
        and calls[0] in list(ast.walk(node))
    ]
    assert len(guards) == 1
    assert 15361 > 120 * 128 == 15360
    assert 15361 * 12 + 32 == 184364
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "runner_sha256": sha(HERE / "execute.py"),
        "checker_sha256": sha(Path(__file__)),
        "synthetic_cover_classification": [True, False],
        "synthetic_positive_hole_zero_classification": [False, True],
        "nonqualifying_hint_controls": rejected_hints + ["global_profile"],
        "invalid_verdict_controls": len(invalid_verdicts),
        "actual_H12_D2_32_classification": [False, False],
        "sole_stop_call_guarded_by_covering": True,
        "hole_priority_bound": {"weight": 15361, "maximum_deficit_sum": 15360},
        "scope": "Pure classification/arithmetic/AST controls only. Synthetic positive cases "
        "are not actual covering families or zero-deficit witnesses; no solve is called.",
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "sha256": sha(output), "optimizer_calls": 0}))


if __name__ == "__main__":
    main()
