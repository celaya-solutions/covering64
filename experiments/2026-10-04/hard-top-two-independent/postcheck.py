# Document:    Independent Hard Top-Two Runtime Vector Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7af39816517819f366aa9706ae7fe64d9d4800fa27e50b5f18bfad22862144c8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
import itertools
import json
import subprocess
from collections import Counter

from check import (
    HERE,
    MANIFEST_SHA,
    ROOT,
    SETS,
    SOURCE,
    canonical_hint,
    expected_rows,
    model_check,
    read,
    sha,
    vector_failures,
)
from google.protobuf import text_format
from ortools.sat import cp_model_pb2


def dual_verify(path, holes, label):
    receipts = []
    for name, prefix in (
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
    ):
        process = subprocess.run(
            prefix + [str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert process.returncode == int(holes != 0) and not process.stderr
        payload = json.loads(process.stdout)
        assert payload["blocks"] == 64 and payload["valid"] == (holes == 0)
        assert len(payload["uncovered"]) == holes
        output = HERE / f"{label}-{name}.json"
        output.write_text(process.stdout)
        receipts.append(
            {
                "path": str(output.relative_to(ROOT)),
                "sha256": sha(output),
                "canonical_sha256": payload["canonical_sha256"],
            }
        )
    assert receipts[0]["canonical_sha256"] == receipts[1]["canonical_sha256"]
    return receipts


def actual_check(values, cores, diagnostic, profile_check):
    canonical, actual = canonical_hint(values[:4368], cores)
    assert values[:5608] == canonical[:5608]
    assert actual["D2max"] == actual["D2sum"] == 0 and not actual["bad_budgets"]
    blocks = [SETS[5][i] for i, value in enumerate(values[:4368]) if value]
    triples = Counter(t for block in blocks for t in itertools.combinations(block, 3))
    quads = Counter(q for block in blocks for q in itertools.combinations(block, 4))
    pairs = dict(zip(SETS[2], values[4368:4488], strict=True))
    details = []
    d3 = d4 = 0
    for pair in SETS[2]:
        positions = [(x, triples[tuple(sorted((*pair, x)))]) for x in range(1, 17) if x not in pair]
        z = sorted((value for _, value in positions), reverse=True)[1]
        ys = [max(0, value - z) for _, value in positions]
        deficits = [
            max(0, 12 - 3 * pairs[pair] + a + b)
            for (_, a), (_, b) in itertools.combinations(positions, 2)
        ]
        d3 += sum(max(0, 13 - 3 * pairs[pair] + count) for _, count in positions)
        d4 += sum(
            max(0, 12 - 3 * pairs[pair] + 2 * quads[tuple(sorted((*pair, a, b)))])
            for (a, _), (b, _) in itertools.combinations(positions, 2)
        )
        details.append(
            {
                "pair": list(pair),
                "positions": [list(pos) for pos in positions],
                "z": z,
                "y": ys,
                "D2max": max(deficits),
                "D2sum": sum(deficits),
            }
        )
    assert d3 == d4 == 0 and min(pairs.values()) >= 5 and max(actual["core_overlaps"]) <= 55
    for key in ("holes", "D2max", "D2sum", "core_overlaps"):
        assert diagnostic[key] == actual[key]
    assert diagnostic["D3"] == d3 and diagnostic["D4"] == d4
    assert diagnostic["minimum_pair_count"] == min(pairs.values())
    assert diagnostic["rows_checked"] == 3605 and not diagnostic["row_failures"]
    assert diagnostic["domains_pass"] and diagnostic["qualified"]
    assert diagnostic["covering_witness"] == (actual["holes"] == 0)
    maximum = profile_check(triples, diagnostic["global_profile"])
    assert maximum <= 26
    return canonical, actual, blocks, details, maximum


def main():
    gate, model_gate = read(HERE / "gate.json"), read(HERE / "model-gate.json")
    manifest, runner = read(SOURCE / "manifest.json"), read(SOURCE / "runner-manifest.json")
    result, preflight = read(SOURCE / "result.json"), read(SOURCE / "runner-preflight.json")
    assert gate["passed"] and gate["decision"] == "GO" and model_gate["passed"]
    assert gate["model_gate_sha256"] == sha(HERE / "model-gate.json")
    assert model_gate["checker_sha256"] == sha(HERE / "check.py")
    assert gate["checker_sha256"] == sha(HERE / "runner_gate.py")
    assert result["manifest_sha256"] == MANIFEST_SHA == sha(SOURCE / "manifest.json")
    assert result["gate_sha256"] == preflight["gate_sha256"] == sha(HERE / "gate.json")
    assert (
        result["runner_manifest_sha256"]
        == gate["runner_manifest_sha256"]
        == sha(SOURCE / "runner-manifest.json")
    )
    assert result["source_sha256"] == gate["runner_sha256"] == sha(SOURCE / "execute.py")
    for relative, digest in (manifest["sources"] | runner["sources"]).items():
        assert sha(ROOT / relative) == digest
    for kind in ("model", "parameters", "guidance"):
        assert gate[f"{kind}_sha256"] == sha(ROOT / manifest[f"{kind}_path"])
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse((ROOT / manifest["model_path"]).read_text(), proto)
    guidance = read(ROOT / manifest["guidance_path"])
    model_check(proto, expected_rows(manifest["core_rows"]), guidance["values"])
    assert result["optimizer_calls"] == 1
    for path, digest in result["raw_files"].items():
        assert sha(ROOT / path) == digest
    raw = ROOT / result["raw_directory"]
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((raw / "response.pbtxt").read_text(), response)
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert response.wall_time == result["solver_wall_seconds"] and 0 <= response.wall_time < 125
    assert abs(result["elapsed_seconds"] - response.wall_time) < 2
    assert response.best_objective_bound == result["objective_bound"]
    shared = HERE.parent / "soft-pair-two-postcheck/check.py"
    shared_manifest = read(HERE.parent / "soft-pair-two-postcheck/manifest.json")
    assert sha(shared) == shared_manifest["files"][str(shared.relative_to(ROOT))]
    spec = importlib.util.spec_from_file_location("independent_profile_basis", shared)
    basis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(basis)
    events_path = raw / "callbacks.jsonl"
    events = (
        [json.loads(line) for line in events_path.read_text().splitlines()]
        if events_path.exists()
        else []
    )
    assert len(events) == result["callbacks"]
    assert [row["number"] for row in events] == list(range(1, len(events) + 1))
    verified, saved = {}, []
    previous_objective, first_cover = float("inf"), None
    for index, summary in enumerate(result["saved_states"]):
        label = summary["label"]
        assert label == f"callback-{index + 1:04d}" or (label == "final" and index == len(events))
        for kind in ("witness", "vector", "receipt"):
            assert sha(ROOT / summary[f"{kind}_path"]) == summary[f"{kind}_sha256"]
        receipt = read(ROOT / summary["receipt_path"])
        assert all(
            receipt[key] == value
            for key, value in summary.items()
            if key not in ("receipt_path", "receipt_sha256")
        )
        vector = read(ROOT / summary["vector_path"])
        values = vector["values"]
        assert not vector_failures(proto, values)
        objective = sum(values[5048:5608])
        assert summary["solver_objective"] == objective
        assert vector["vector_check"] == {
            "variables_checked": 7408,
            "rows_checked": 3605,
            "enforced_rows_checked": 3045,
            "objective": objective,
        }
        canonical, actual, blocks, details, maximum = actual_check(
            values, manifest["core_rows"], summary["actual_metrics"], basis.profile_check
        )
        assert canonical == vector["canonical_values"] and not vector_failures(proto, canonical)
        assert receipt["pair_details"] == details
        assert actual["holes"] == objective
        assert summary["qualified_D2zero_hint"] and summary["covering_witness"] == (objective == 0)
        witness = ROOT / summary["witness_path"]
        assert witness.read_text() == "".join(" ".join(map(str, block)) + "\n" for block in blocks)
        if summary["witness_sha256"] not in verified:
            verified[summary["witness_sha256"]] = dual_verify(witness, objective, label)
        if label != "final":
            event = events[index]
            assert event["actual_metrics"] == summary["actual_metrics"]
            assert event["solver_objective"] == objective <= previous_objective
            assert event["covering_witness"] == (objective == 0)
            assert first_cover is None, "callback after cover stop request"
            previous_objective = objective
            if objective == 0:
                first_cover = label
        else:
            assert values == list(response.solution) and objective == response.objective_value
        saved.append(
            {
                "label": label,
                "holes": objective,
                "D2max": 0,
                "core_overlaps": actual["core_overlaps"],
                "profile_maximum": maximum,
                "noncanonical_auxiliary_values": sum(
                    a != b for a, b in zip(values[5608:], canonical[5608:], strict=True)
                ),
                "witness_sha256": summary["witness_sha256"],
                "vector_sha256": summary["vector_sha256"],
                "verifiers": verified[summary["witness_sha256"]],
            }
        )
    assert result["stopped_on_actual_cover"] == (first_cover is not None)
    assert len(result["saved_states"]) == len(events) + int(bool(response.solution))
    if response.solution:
        assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
        assert result["saved_states"][-1]["label"] == "final"
        assert 0 <= response.best_objective_bound <= response.objective_value
    else:
        assert response.status in (cp_model_pb2.UNKNOWN, cp_model_pb2.INFEASIBLE)
        assert not saved and not events
    assert result["first_feasible_seconds"] == (events[0]["elapsed_seconds"] if events else None)
    log = (raw / "solver.log").read_text()
    assert log.count("Starting CP-SAT solver") == log.count("CpSolverResponse summary:") == 1
    report = {
        "passed": True,
        "optimizer_calls_by_audit": 0,
        "checker_sha256": sha(__file__),
        "profile_checker_sha256": sha(shared),
        "manifest_sha256": MANIFEST_SHA,
        "gate_sha256": sha(HERE / "gate.json"),
        "result_sha256": sha(SOURCE / "result.json"),
        "status": result["status"],
        "callbacks": len(events),
        "saved_vectors": len(saved),
        "unique_families": len(verified),
        "dual_verifier_calls": 2 * len(verified),
        "first_actual_cover_callback": first_cover,
        "saved_states": saved,
        "elapsed_seconds": result["elapsed_seconds"],
        "solver_wall_seconds": response.wall_time,
        "objective_bound": response.best_objective_bound,
        "scope": "Full serialized-model recheck and runtime audit. Legitimate noncanonical "
        "z/y values are checked by inequalities and retained, not forced to canonical values. "
        "Only holes0 with both verifiers is a cover. UNKNOWN/timeouts are inconclusive and "
        "CP-SAT INFEASIBLE is not an independently checked theorem. No optimizer called.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "status": result["status"],
                "callbacks": len(events),
                "saved_vectors": len(saved),
            }
        )
    )


if __name__ == "__main__":
    main()
