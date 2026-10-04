# Document:    Strong Compact Count Model Independent Outcome Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b03ef5d961cd284c8fa293112874f3683ea09a88043784309bd854e99aa97043
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check native response and every saved/final vector without construction calls."""

import hashlib
import importlib.util
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TARGET = ROOT / "experiments/2026-10-04/compact-pair-two-counts"
RAW = ROOT / "experiments/scratch/compact-pair-two-counts-run-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    gate = json.loads((HERE / "gate.json").read_text())
    producer = json.loads((TARGET / "result.json").read_text())
    manifest = json.loads((TARGET / "manifest.json").read_text())
    assert gate["passed"] and gate["optimizer_calls"] == 0
    assert sha(HERE / "check.py") == gate["checker_sha256"]
    assert sha(HERE / "gate.py") == gate["launch_checker_sha256"]
    assert sha(TARGET / "manifest.json") == gate["manifest_sha256"]
    assert sha(TARGET / "execute.py") == gate["runner_source_sha256"]
    assert producer["optimization_calls"] == 1 and not producer["global_lower_bound_claim"]
    assert producer["gate_sha256"] == sha(HERE / "gate.json")
    assert producer["manifest_sha256"] == gate["manifest_sha256"]
    assert producer["model_sha256"] == gate["model_sha256"]
    assert producer["parameters_sha256"] == gate["parameters_sha256"]
    assert producer["budget"] == {"cases": 1, "seconds": 120, "workers": 4, "seed": 2026104301}
    for relative, checksum in manifest["input_files"].items():
        assert sha(ROOT / relative) == checksum
    for record in producer["raw_files"].values():
        assert sha(ROOT / record["path"]) == record["sha256"]
    for name, original in [
        ("execute.py", TARGET / "execute.py"),
        ("prepare.py", TARGET / "prepare.py"),
        ("manifest.json", TARGET / "manifest.json"),
        ("gate.json", HERE / "gate.json"),
        ("model.pbtxt", ROOT / manifest["model_path"]),
        ("parameters.pbtxt", ROOT / manifest["parameters_path"]),
    ]:
        assert sha(RAW / name) == sha(original)
    assert sha(RAW / "used-parameters.pbtxt") == gate["parameters_sha256"]
    model = text_format.Parse((RAW / "model.pbtxt").read_text(), cp_model_pb2.CpModelProto())
    response = text_format.Parse(
        (RAW / "response.pbtxt").read_text(), cp_model_pb2.CpSolverResponse()
    )
    status = cp_model_pb2.CpSolverStatus.Name(response.status)
    assert status == producer["status"] and status in {
        "UNKNOWN",
        "FEASIBLE",
        "OPTIMAL",
        "INFEASIBLE",
    }
    assert abs(response.wall_time - producer["reported_seconds"]) < 1e-6
    assert abs(response.best_objective_bound - producer["objective_bound"]) < 1e-6
    assert producer["seconds"] >= response.wall_time - 0.1
    assert producer["guidance_kind"] == "block-only infeasible guidance"
    assert not producer["guidance_is_complete"] and not producer["guidance_has_feasible_extension"]
    encoding = load_module("independent_count_encoding", HERE / "check.py")
    family_source = ROOT / "experiments/2026-10-04/native-core-cap-escape-independent/check.py"
    assert sha(family_source) == "23f4921f3619fcc0de60cf6b614b6916449c85018ffacdcf2b4c43fa309e20b0"
    family_audit = load_module("independent_family_audit", family_source)
    records = producer["records"]
    final = producer["final"]
    if status in {"FEASIBLE", "OPTIMAL"}:
        assert final is not None and len(response.solution) == 5608
    else:
        assert final is None and not response.solution and not records
    if records:
        assert producer["first_feasible_callback_seconds"] == records[0]["callback_seconds"]
        logged = [
            json.loads(line) for line in (RAW / "callback-records.jsonl").read_text().splitlines()
        ]
        assert logged == records
    else:
        assert producer["first_feasible_callback_seconds"] is None
        assert not (RAW / "callback-records.jsonl").exists()
    audited, seen, paths = [], set(), set()
    previous_objective = None
    for record in records + ([final] if final else []):
        is_final = record is final
        path, vector_path = ROOT / record["path"], ROOT / record["values_path"]
        assert sha(path) == record["sha256"] and sha(vector_path) == record["values_sha256"]
        values = json.loads(vector_path.read_text())
        assert len(values) == 5608 and all(type(value) is int for value in values)
        assert encoding.failures(model, values) == {"domain_indices": [], "constraint_indices": []}
        if is_final:
            assert values == list(response.solution)
        report = family_audit.check_family(path, manifest["core_rows"])
        ids = [i for i in range(4368) if values[i]]
        actual_ids = sorted(family_audit.RANK[block] for block in family_audit.family(path))
        assert ids == actual_ids == record["ids"]
        assert report["holes"] == record["holes"] == sum(values[5048:5608])
        assert report["core_overlaps"] == record["core_overlaps"]
        assert not report["forbidden_partitions"] and record["global_five_heavy_clear"]
        objective = 65 * report["holes"] + report["core_overlaps"][0]
        assert objective == record["composite_objective"]
        if is_final:
            assert abs(objective - response.objective_value) < 1e-6
            assert record["ties_callback_best"] == (
                objective == producer["best_composite_objective"]
            )
            assert record["matches_saved_callback_ids"] == (tuple(ids) in seen)
        else:
            kind = (
                "improvement"
                if previous_objective is None or objective < previous_objective
                else "callback_tie"
            )
            assert previous_objective is None or objective <= previous_objective
            assert record["kind"] == kind and tuple(ids) not in seen
            previous_objective = objective
            seen.add(tuple(ids))
        assert path not in paths
        paths.add(path)
        report.update(
            label=record["label"],
            vector_sha256=sha(vector_path),
            objective=objective,
            complete_model_assignment_passed=True,
            final=is_final,
        )
        audited.append(report)
    assert paths == set((TARGET / "full-4368").glob("*.txt"))
    assert producer["best_composite_objective"] == previous_objective
    zero_found = any(row["holes"] == 0 for row in audited)
    assert producer["covering_witness"] == zero_found
    assert bool(producer["verified_zero_candidates"]) == zero_found
    native_log = (RAW / "solver.log").read_text()
    result = {
        "passed": True,
        "postcheck_sha256": sha(Path(__file__)),
        "gate_sha256": sha(HERE / "gate.json"),
        "producer_result_sha256": sha(TARGET / "result.json"),
        "construction_calls_in_audit": 0,
        "producer_optimizer_calls": 1,
        "status": status,
        "reported_seconds": response.wall_time,
        "objective_bound": response.best_objective_bound,
        "callback_records": len(records),
        "native_response_values": len(response.solution),
        "saved_or_final_records": len(audited),
        "distinct_families": len({row["canonical_sha256"] for row in audited}),
        "best_holes": min((row["holes"] for row in audited), default=None),
        "cover_found": zero_found,
        "global_lower_bound_claim": False,
        "native_hint_messages": producer["native_hint_messages"],
        "native_search_start_seconds": producer["native_search_start_seconds"],
        "first_feasible_callback_seconds": producer["first_feasible_callback_seconds"],
        "solver_log_bytes": len(native_log.encode()),
        "families": audited,
        "scope": "Exact saved/final model assignments and both covering verifiers. "
        "No solver call in this audit; UNKNOWN and timeouts remain inconclusive.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "families"}))


if __name__ == "__main__":
    main()
