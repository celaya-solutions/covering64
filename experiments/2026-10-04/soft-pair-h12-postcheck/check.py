# Document:    Independent H12 Soft Pair Vector and Outcome Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      05cfcd57ea85ba8faf338acaf02d80a6b68d2b5417ab058bb84811c40f8890e9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import argparse
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "soft-pair-h12-start"
MANIFEST_SHA = "3fbd306aeff1494adc4c76311d4d9cf23ce14216f2d9ab81a9e8bc0d8204fe46"
SETS = {n: list(itertools.combinations(range(1, 17), n)) for n in (2, 3, 4, 5)}
RANK = {block: i for i, block in enumerate(SETS[5])}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def vector_check(model, values):
    assert len(values) == len(model.proto.variables) == 5728
    for variable, value in zip(model.proto.variables, values, strict=True):
        domain = list(variable.domain)
        assert type(value) is int and len(domain) % 2 == 0
        assert any(
            low <= value <= high for low, high in zip(domain[::2], domain[1::2], strict=True)
        )
    active = 0
    for row in model.proto.constraints:
        assert row.has_linear()
        if not all(
            values[lit] == 1 if lit >= 0 else values[-lit - 1] == 0
            for lit in row.enforcement_literal
        ):
            continue
        active += 1
        lhs = sum(
            coefficient * values[index]
            for index, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
        )
        domain = list(row.linear.domain)
        assert any(low <= lhs <= high for low, high in zip(domain[::2], domain[1::2], strict=True))
    objective = model.proto.objective
    value = objective.scaling_factor * (
        objective.offset
        + sum(
            coefficient * values[index]
            for index, coefficient in zip(objective.vars, objective.coeffs, strict=True)
        )
    )
    assert active == 13845 and len(model.proto.constraints) == 14405
    assert value == 561 * sum(values[5608:]) + sum(values[5048:5608])
    return {
        "variables_checked": len(values),
        "rows_checked": len(model.proto.constraints),
        "enforced_rows_checked": active,
        "objective": value,
    }


def profile_check(counts, supplied=None):
    heavy = [
        (sum(1 << (x - 1) for x in triple), 5 + int(count >= 7), triple)
        for triple, count in sorted(counts.items())
        if count >= 6
    ]
    dp = {0: 0}
    for mask, weight, _ in heavy:
        additions = {}
        for used, value in dp.items():
            if used & mask == 0:
                combined = used | mask
                additions[combined] = max(additions.get(combined, 0), value + weight)
        for used, value in additions.items():
            dp[used] = max(dp.get(used, 0), value)
    maximum = max(dp.values())
    if supplied is not None:
        witness = [tuple(triple) for triple in supplied["positive_weight_disjoint_triples"]]
        assert all(len(triple) == 3 and counts[triple] >= 6 for triple in witness)
        assert len(set().union(*map(set, witness))) == 3 * len(witness) if witness else True
        assert sum(5 + int(counts[triple] >= 7) for triple in witness) == maximum
        assert supplied["maximum"] == maximum and supplied["bound"] == 26
    return maximum


def actual_check(values, cores):
    ids = [i for i, value in enumerate(values[:4368]) if value]
    assert len(ids) == 64 and all(values[i] == 1 for i in ids)
    blocks = [SETS[5][i] for i in ids]
    counts = {
        n: Counter(q for block in blocks for q in itertools.combinations(block, n))
        for n in (2, 3, 4)
    }
    pairs = [counts[2][pair] for pair in SETS[2]]
    triples = [counts[3][triple] for triple in SETS[3]]
    holes = [int(count == 0) for count in triples]
    deficits, details = [], []
    d2sum = d3 = d4 = 0
    for pair in SETS[2]:
        p = counts[2][pair]
        positions = [
            (x, counts[3][tuple(sorted((*pair, x)))]) for x in range(1, 17) if x not in pair
        ]
        assert sum(count for _, count in positions) == 3 * p
        rows = [
            max(0, 12 - 3 * p + ca + cb)
            for (_, ca), (_, cb) in itertools.combinations(positions, 2)
        ]
        maximum = max(rows)
        deficits.append(maximum)
        d2sum += sum(rows)
        d3 += sum(max(0, 13 - 3 * p + count) for _, count in positions)
        d4 += sum(
            max(0, 12 - 3 * p + 2 * counts[4][tuple(sorted((*pair, a, b)))])
            for (a, _), (b, _) in itertools.combinations(positions, 2)
        )
        details.append(
            {
                "pair": list(pair),
                "positions": [list(pos) for pos in positions],
                "deficit": maximum,
                "D2sum": sum(rows),
            }
        )
    canonical = values[:4368] + pairs + triples + holes + deficits
    assert values[:5608] == canonical[:5608]
    assert all(solver >= actual for solver, actual in zip(values[5608:], deficits, strict=True))
    overlaps = [len(set(ids) & set(core)) for core in cores]
    assert max(overlaps) <= 55 and min(pairs) >= 5 and d3 == 0
    metrics = {
        "holes": sum(holes),
        "D2max": sum(deficits),
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "minimum_pair_count": min(pairs),
        "core_overlaps": overlaps,
        "canonical_objective": 561 * sum(deficits) + sum(holes),
    }
    return {
        "blocks": blocks,
        "canonical_values": canonical,
        "actual_metrics": metrics,
        "pair_details": details,
        "triple_counts": counts[3],
        "auxiliary_slack": sum(values[5608:]) - sum(deficits),
    }


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


def load():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "manifest.json") == MANIFEST_SHA
    for path, digest in (manifest["sources"] | manifest["input_files"]).items():
        assert sha(ROOT / path) == digest
    for path, digest in manifest["frozen_proofs"].items():
        assert sha(HERE.parent / path) == digest
    for kind in ("model", "parameters", "hint"):
        assert sha(ROOT / manifest[f"{kind}_path"]) == manifest[f"{kind}_sha256"]
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text())
    assert not model.validate()
    parameters = sat_parameters_pb2.SatParameters()
    text_format.Parse((ROOT / manifest["parameters_path"]).read_text(), parameters)
    assert parameters == sat_parameters_pb2.SatParameters(
        max_time_in_seconds=300,
        num_search_workers=4,
        random_seed=2026104901,
        log_search_progress=True,
        log_to_stdout=False,
    )
    hint = read(ROOT / manifest["hint_path"])
    assert list(model.proto.solution_hint.vars) == list(range(5728))
    assert list(model.proto.solution_hint.values) == hint["values"]
    assert vector_check(model, hint["values"]) == manifest["hint_vector_check"]
    actual = actual_check(hint["values"], manifest["core_rows"])
    assert actual["auxiliary_slack"] == 0 and actual["actual_metrics"] == manifest["hint_metrics"]
    assert actual["canonical_values"] == hint["values"]
    assert profile_check(actual["triple_counts"], hint["global_profile"]) <= 26
    return manifest, model, hint


def preflight():
    manifest, model, hint = load()
    rejected = []
    for label, change in (
        ("short_vector", lambda x: x.pop()),
        ("noninteger", lambda x: x.__setitem__(0, bool(x[0]))),
        ("block_domain", lambda x: x.__setitem__(0, 2)),
        ("count_identity", lambda x: x.__setitem__(4368, x[4368] + 1)),
        ("hole_channel", lambda x: x.__setitem__(5048, 1 - x[5048])),
        ("deficit_domain", lambda x: x.__setitem__(5608, -1)),
        (
            "understated_deficit",
            lambda x: x.__setitem__(next(i for i in range(5608, 5728) if x[i] > 0), 0),
        ),
        ("cardinality", lambda x: x.__setitem__(next(i for i in range(4368) if x[i] == 0), 1)),
    ):
        damaged = hint["values"].copy()
        change(damaged)
        try:
            vector_check(model, damaged)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError(f"damaged control accepted: {label}")
    slack = hint["values"].copy()
    slack[5608] += 1
    checked = vector_check(model, slack)
    actual = actual_check(slack, manifest["core_rows"])
    assert checked["objective"] == 19086 + 561 and actual["auxiliary_slack"] == 1
    assert actual["actual_metrics"] == manifest["hint_metrics"]
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "damaged_controls_rejected": rejected,
        "complete_hint_values": 5728,
        "hint_objective": 19086,
        "valid_positive_auxiliary_slack_accepted": True,
        "scope": "Independent vector checker control and runner semantic review; root owns "
        "the serialized model gate and sole launch. No Solve called.",
    }
    dump(HERE / "preflight.json", report)
    print(
        json.dumps(
            {"passed": True, "preflight_sha256": sha(HERE / "preflight.json"), "optimizer_calls": 0}
        )
    )


def postcheck():
    manifest, model, _ = load()
    result = read(SOURCE / "result.json")
    assert result["manifest_sha256"] == MANIFEST_SHA and result["optimizer_calls"] == 1
    assert result["source_sha256"] == sha(SOURCE / "execute.py")
    pre = read(SOURCE / "runner-preflight.json")
    gate = read(pre["gate_path"])
    assert sha(pre["gate_path"]) == result["gate_sha256"] == pre["gate_sha256"]
    assert result["gate_sha256"] == (
        "be4b5b900e1de8238d70c4a7d88c17dcefa2c9d30b8d73655bbb25ca12820990"
    )
    assert gate["passed"] and gate["decision"] == "GO"
    assert gate["manifest_sha256"] == MANIFEST_SHA
    for kind in ("model", "parameters", "hint"):
        assert gate[f"{kind}_sha256"] == manifest[f"{kind}_sha256"]
    assert gate["runner_sha256"] == sha(SOURCE / "execute.py")
    for path, digest in result["raw_files"].items():
        assert sha(ROOT / path) == digest
    raw = ROOT / result["raw_directory"]
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((raw / "response.pbtxt").read_text(), response)
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert response.best_objective_bound == result["objective_bound"]
    assert response.wall_time == result["solver_wall_seconds"]
    assert abs(result["elapsed_seconds"] - response.wall_time) < 2
    assert 0 <= response.wall_time < 305
    callbacks_path = raw / "callbacks.jsonl"
    events = (
        [json.loads(line) for line in callbacks_path.read_text().splitlines()]
        if callbacks_path.exists()
        else []
    )
    assert [event["number"] for event in events] == list(range(1, len(events) + 1))
    assert len(events) == result["callbacks"]
    saved = []
    first_zero = None
    previous_objective = float("inf")
    verified = {}
    for index, summary in enumerate(result["saved_states"]):
        label = summary["label"]
        if label != "final":
            assert label == f"callback-{index + 1:04d}"
        else:
            assert index == len(result["saved_states"]) - 1
        for kind in ("receipt", "witness", "vector"):
            assert sha(ROOT / summary[f"{kind}_path"]) == summary[f"{kind}_sha256"]
        receipt = read(ROOT / summary["receipt_path"])
        assert all(
            receipt[key] == value
            for key, value in summary.items()
            if key not in ("receipt_path", "receipt_sha256")
        )
        vector = read(ROOT / summary["vector_path"])
        values = vector["values"]
        checked = vector_check(model, values)
        assert (
            checked == vector["vector_check"]
            and checked["objective"] == summary["solver_objective"]
        )
        actual = actual_check(values, manifest["core_rows"])
        assert actual["canonical_values"] == vector["canonical_values"]
        assert actual["actual_metrics"] == summary["actual_metrics"]
        assert actual["pair_details"] == receipt["pair_details"]
        assert sum(values[5608:]) == summary["solver_deficit_sum"]
        assert summary["solver_objective"] >= actual["actual_metrics"]["canonical_objective"]
        profile = profile_check(actual["triple_counts"], receipt["global_profile"])
        holes, d2 = actual["actual_metrics"]["holes"], actual["actual_metrics"]["D2max"]
        qualified = d2 == 0
        if qualified:
            assert actual["actual_metrics"]["D3"] == actual["actual_metrics"]["D4"] == 0
            assert profile <= 26
        assert summary["qualified_D2zero_hint"] == qualified
        assert summary["covering_witness"] == (holes == 0)
        witness = ROOT / summary["witness_path"]
        expected_text = "".join(" ".join(map(str, block)) + "\n" for block in actual["blocks"])
        assert witness.read_text() == expected_text
        if summary["witness_sha256"] not in verified:
            verified[summary["witness_sha256"]] = dual_verify(witness, holes, label)
        if label != "final":
            event = events[index]
            assert event["actual"] == actual["actual_metrics"]
            assert event["solver_objective"] == summary["solver_objective"] <= previous_objective
            previous_objective = summary["solver_objective"]
            assert event["qualified_D2zero_hint"] == qualified
            assert first_zero is None, "callback received after first zero stop request"
            if qualified:
                first_zero = label
        else:
            assert values == list(response.solution)
            assert summary["solver_objective"] == response.objective_value
        saved.append(
            {
                "label": label,
                "actual_metrics": actual["actual_metrics"],
                "solver_objective": checked["objective"],
                "auxiliary_slack": actual["auxiliary_slack"],
                "profile_maximum": profile,
                "witness_sha256": summary["witness_sha256"],
                "vector_sha256": summary["vector_sha256"],
                "verifiers": verified[summary["witness_sha256"]],
            }
        )
    assert result["stopped_on_actual_D2zero"] == (first_zero is not None)
    assert len(result["saved_states"]) == len(events) + int(bool(response.solution))
    if response.solution:
        assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
        assert result["saved_states"][-1]["label"] == "final"
        assert 0 <= response.best_objective_bound <= response.objective_value
    else:
        assert response.status == cp_model_pb2.UNKNOWN and not saved and not events
    if events:
        assert result["first_feasible_seconds"] == events[0]["elapsed_seconds"]
    else:
        assert result["first_feasible_seconds"] is None
    log = (raw / "solver.log").read_text()
    assert log.count("Starting CP-SAT solver") == log.count("CpSolverResponse summary:") == 1
    report = {
        "passed": True,
        "optimizer_calls_by_audit": 0,
        "reference_checker_sha256": (
            "e9827db7e6f4197f087babfb259650c4993dcf5b0048f7e750f7a4d2b1c1f619"
        ),
        "all_vector_domains_rows_recounted": True,
        "solver_auxiliary_slack_distinguished_from_actual_deficits": True,
        "configured_budget_seconds": 300,
        "configured_workers": 4,
        "configured_seed": 2026104901,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "result_sha256": sha(SOURCE / "result.json"),
        "gate_sha256": result["gate_sha256"],
        "status": result["status"],
        "callbacks": len(events),
        "saved_vectors": len(saved),
        "unique_families": len(verified),
        "dual_verifier_calls": 2 * len(verified),
        "first_actual_zero_callback": first_zero,
        "saved_states": saved,
        "elapsed_seconds": result["elapsed_seconds"],
        "solver_wall_seconds": response.wall_time,
        "objective_bound": response.best_objective_bound,
        "scope": "Every saved full vector, domain, enforced row and actual metric is checked. "
        "Solver auxiliary deficits may have slack; actual zero is independently determined. "
        "No optimizer was called. No global lower-bound or infeasibility proof follows.",
    }
    dump(HERE / "postcheck.json", report)
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "status": result["status"],
                "saved_vectors": len(saved),
                "first_actual_zero_callback": first_zero,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--postcheck", action="store_true")
    arguments = parser.parse_args()
    if arguments.postcheck:
        postcheck()
    else:
        preflight()
