# Document:    Independent Radius Four Feasibility Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      877322504c72965af3c30fd5461e72f182855a2ccfcf316429cc94194cbe7dd9
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
SOURCE = HERE.parent / "radius-four-feasibility-repair-v2"
MANIFEST_SHA = "dd8ade21144046f04b2a9e03737e6a93382a95681e4f17c652c0aa4780be772c"
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
    assert len(model.proto.constraints) in (14405, 14407)
    assert active == len(model.proto.constraints) - 560
    assert not model.has_objective() and not model.proto.has_solution_hint()
    return {
        "variables_checked": len(values),
        "rows_checked": len(model.proto.constraints),
        "enforced_rows_checked": active,
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


def actual_check(values, cores, baseline_ids):
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
        "cardinality": len(ids),
        "baseline_overlap": len(set(ids) & set(baseline_ids)),
        "replacement_distance": 64 - len(set(ids) & set(baseline_ids)),
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
    review_path = HERE.parent / "radius-four-runner-review/review.json"
    assert sha(review_path) == "d8b5f7a70760acca9b7f683ad47764e26594090f3ecc66108d4571c0ae09de90"
    review = read(review_path)
    assert review["passed"] is True and review["decision"] == "RUNNER_GO"
    for path, digest in review["files"].items():
        assert sha(ROOT / path) == digest
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "manifest.json") == MANIFEST_SHA
    for kind in ("sources", "input_files", "files", "raw_files"):
        for path, digest in manifest[kind].items():
            assert sha(ROOT / path) == digest, path
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text())
    assert not model.validate() and not model.has_objective()
    assert not model.proto.has_solution_hint()
    assert len(model.proto.variables) == 5728 and len(model.proto.constraints) == 14407
    parameters = sat_parameters_pb2.SatParameters()
    text_format.Parse((ROOT / manifest["parameters_path"]).read_text(), parameters)
    assert parameters == sat_parameters_pb2.SatParameters(
        max_time_in_seconds=300,
        num_search_workers=4,
        random_seed=2026105201,
        log_search_progress=True,
        log_to_stdout=False,
    )
    baseline = read((ROOT / manifest["model_path"]).with_name("baseline-vector.json"))
    assert baseline["is_solution_hint"] is False
    return manifest, model, baseline


def preflight():
    manifest, model, baseline = load()
    values = baseline["values"]
    actual = actual_check(values, manifest["core_rows"], manifest["baseline_ids"])
    assert actual["actual_metrics"]["holes"] == 12
    assert actual["actual_metrics"]["D2max"] == actual["actual_metrics"]["D2sum"] == 29
    assert actual["actual_metrics"]["replacement_distance"] == 0
    assert actual["canonical_values"] == values
    try:
        vector_check(model, values)
    except AssertionError:
        baseline_rejected = True
    else:
        raise AssertionError("12-hole baseline accepted by local11-hole model")
    prefix_proto = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), prefix_proto)
    del prefix_proto.constraints[14405:]
    prefix = cp_model.CpModel()
    assert prefix.proto.parse_text_format(text_format.MessageToString(prefix_proto))
    before = str(prefix.proto)
    checked = vector_check(prefix, values)
    assert str(prefix.proto) == before
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
        damaged = values.copy()
        change(damaged)
        try:
            vector_check(prefix, damaged)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError(f"damaged vector accepted: {label}")
    slack = values.copy()
    slack[5608] += 1
    assert vector_check(prefix, slack) == checked
    assert (
        actual_check(slack, manifest["core_rows"], manifest["baseline_ids"])["auxiliary_slack"] == 1
    )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "baseline_rejected_by_local_hole_bound": baseline_rejected,
        "prefix_vector_check": checked,
        "damaged_controls_rejected": rejected,
        "valid_auxiliary_slack_accepted": True,
        "no_objective_or_hint_created": str(prefix.proto) == before,
    }
    dump(HERE / "preflight.json", report)
    print(json.dumps({"passed": True, "preflight_sha256": sha(HERE / "preflight.json")}))


def postcheck():
    manifest, model, _ = load()
    result = read(SOURCE / "result.json")
    assert result["manifest_sha256"] == MANIFEST_SHA
    raw = ROOT / result["raw_directory"]
    launch = read(raw / "launch.json")
    gate_path = Path(launch["command"][launch["command"].index("--gate") + 1])
    gate = read(gate_path)
    pre = read(SOURCE / "runner-preflight.json")
    assert sha(gate_path) == result["gate_sha256"] == pre["gate_sha256"] == launch["gate_sha256"]
    assert sha(gate_path) == "3150b8caae0c68e7ca47d18b3c5642494ebf31d31e11bec6ee721995a7a3df6e"
    assert gate["passed"] is True and gate["decision"] == "GO"
    assert gate["manifest_sha256"] == MANIFEST_SHA
    for kind in ("model", "parameters"):
        assert gate[f"{kind}_sha256"] == manifest[f"{kind}_sha256"]
    assert gate["runner_sha256"] == sha(SOURCE / "execute.py")
    for path, digest in result["raw_files"].items():
        assert sha(ROOT / path) == digest, path
    assert result["single_child_launches"] == result["optimizer_call_upper_bound"] == 1
    assert result["relaunch"] is False and result["budget_transfer"] is False
    watchdog = result["watchdog"]
    assert watchdog["deadline_seconds"] == 330 and watchdog["grace_seconds"] == 5
    assert watchdog["relaunch"] is False
    assert result["objective"] is None
    child = result["child_result"]
    response_path = raw / "response.pbtxt"
    response = None
    if response_path.exists():
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse(response_path.read_text(), response)
    if child is not None:
        assert child == read(raw / "child-result.json")
        assert child["optimizer_calls"] == result["optimizer_calls"] == 1
        assert child["manifest_sha256"] == MANIFEST_SHA
        assert child["runner_sha256"] == sha(SOURCE / "execute.py")
        assert child["model_sha256"] == manifest["model_sha256"]
        assert child["parameters_sha256"] == manifest["parameters_sha256"]
        assert child["gate_sha256"] == result["gate_sha256"]
        assert response is not None
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == child["status"]
        assert response.wall_time == child["solver_wall_seconds"]
        assert 0 <= response.wall_time < 305
        assert abs(child["elapsed_seconds"] - response.wall_time) < 30
        assert child["objective"] is None and child["saved_states"] == result["saved_states"]
    if watchdog["fired"]:
        assert result["status"] == "WATCHDOG_TIMEOUT" and watchdog["terminate_sent"]
    elif result["returncode"] != 0 or child is None:
        assert result["status"] == "ERROR"
    else:
        assert result["status"] == child["status"]
    events = []
    path = raw / "callbacks.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            events.append(json.loads(line))
    assert [event["number"] for event in events] == list(range(1, len(events) + 1))
    if child is not None:
        assert len(events) == child["callbacks"]
        assert child["first_feasible_seconds"] == (events[0]["elapsed_seconds"] if events else None)
    verified, saved = {}, []
    first_cover = None
    for summary in result["saved_states"]:
        label = summary["label"]
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
        assert checked == vector["vector_check"]
        actual = actual_check(values, manifest["core_rows"], manifest["baseline_ids"])
        assert actual["canonical_values"] == vector["canonical_values"]
        assert vector_check(model, actual["canonical_values"]) == vector["canonical_vector_check"]
        assert actual["actual_metrics"] == summary["actual_metrics"]
        assert actual["pair_details"] == receipt["pair_details"]
        assert sum(values[5608:]) == summary["solver_deficit_sum"]
        profile = profile_check(actual["triple_counts"], receipt["global_profile"])
        metrics = actual["actual_metrics"]
        assert metrics["holes"] <= 11 and metrics["replacement_distance"] <= 4
        cover = metrics["holes"] == 0
        assert summary["cover_found"] is cover and summary["feasible_partial"] is (not cover)
        assert summary["feasibility_target_met"] is True
        witness = ROOT / summary["witness_path"]
        assert witness.read_text() == "".join(
            " ".join(map(str, b)) + "\n" for b in actual["blocks"]
        )
        if summary["witness_sha256"] not in verified:
            verified[summary["witness_sha256"]] = dual_verify(witness, metrics["holes"], label)
        for name in ("package", "standalone"):
            assert receipt["verification"][name]["valid"] is cover
            assert receipt["verification"][name]["blocks"] == 64
            assert len(receipt["verification"][name]["uncovered"]) == metrics["holes"]
        if label == "final":
            assert response is not None and values == list(response.solution)
        else:
            number = int(label.removeprefix("callback-"))
            event = events[number - 1]
            assert event["actual_metrics"] == metrics and event["cover_found"] is cover
            assert event["feasible_partial"] is (not cover)
            assert event["elapsed_seconds"] == summary["elapsed_seconds"]
            assert first_cover is None
            if cover:
                first_cover = label
        saved.append(
            {
                "label": label,
                "actual_metrics": metrics,
                "vector_check": checked,
                "auxiliary_slack": actual["auxiliary_slack"],
                "profile_maximum": profile,
                "witness_sha256": summary["witness_sha256"],
                "vector_sha256": summary["vector_sha256"],
                "verifiers": verified[summary["witness_sha256"]],
            }
        )
    if child is not None:
        receipt_paths = {str(path.relative_to(ROOT)) for path in raw.glob("*-receipt.json")}
        assert receipt_paths == {row["receipt_path"] for row in result["saved_states"]}
        assert child["stopped_on_actual_cover"] is (first_cover is not None)
        assert len(saved) == len(events) + int(bool(response.solution))
        if response.solution:
            assert response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL)
            assert saved[-1]["label"] == "final"
        else:
            assert response.status in (
                cp_model_pb2.UNKNOWN,
                cp_model_pb2.INFEASIBLE,
                cp_model_pb2.MODEL_INVALID,
            )
            assert not saved and not events
    cover_found = any(row["actual_metrics"]["holes"] == 0 for row in saved)
    partial_found = any(row["actual_metrics"]["holes"] > 0 for row in saved)
    assert (
        result["cover_found"] is cover_found and result["feasible_partial_found"] is partial_found
    )
    assert result["feasibility_target_met"] is bool(saved)
    if child is not None:
        assert (
            child["cover_found"] is cover_found and child["feasible_partial_found"] is partial_found
        )
        assert child["feasibility_target_met"] is bool(saved)
    log = (raw / "solver.log").read_text()
    assert log.count("Starting CP-SAT solver") == 1
    if child is not None:
        assert log.count("CpSolverResponse summary:") == 1
    arrays = (
        {}
        if response is None
        else {field.name: len(getattr(response, field.name))
        for field in response.DESCRIPTOR.fields
        if field.is_repeated}
    )
    report = {
        "passed": True,
        "optimizer_calls_by_audit": 0,
        "checker_sha256": sha(__file__),
        "reference_checker_sha256": (
            "58d71a04451553ec33ee2fe252278b31ce04dfeb8cab77cb7fa814ade671641e"
        ),
        "manifest_sha256": MANIFEST_SHA,
        "result_sha256": sha(SOURCE / "result.json"),
        "gate_sha256": result["gate_sha256"],
        "status": result["status"],
        "native_status": None
        if response is None
        else cp_model_pb2.CpSolverStatus.Name(response.status),
        "native_repeated_field_lengths": arrays,
        "callbacks": len(events),
        "saved_vectors": len(saved),
        "unique_families": len(verified),
        "dual_verifier_calls": 2 * len(verified),
        "saved_states": saved,
        "first_actual_cover_callback": first_cover,
        "cover_found": cover_found,
        "feasible_partial_found": partial_found,
        "configured_budget_seconds": 300,
        "configured_workers": 4,
        "configured_seed": 2026105201,
        "watchdog": watchdog,
        "solver_wall_seconds": None if response is None else response.wall_time,
        "all_available_vectors_domains_rows_and_metrics_recounted": True,
        "no_objective_or_hint": not model.has_objective() and not model.proto.has_solution_hint(),
        "scope": "Only saved states from the bounded radius-four feasibility model. "
        "No solver called by audit. UNKNOWN/timeouts are inconclusive; no global theorem follows.",
    }
    dump(HERE / "postcheck.json", report)
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "status": result["status"],
                "saved_vectors": len(saved),
                "cover_found": cover_found,
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
