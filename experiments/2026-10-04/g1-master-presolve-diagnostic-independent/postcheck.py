# Document:    Independent Fixed-g1 Presolve Diagnostic Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check two identical-model diagnostics, registry gates and any admitted LPs."""

import importlib.util
import json

from check import DAY, HERE, ROOT, SOURCE, parameters, read, sha
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

RAW = ROOT / "experiments/scratch/g1-master-presolve-diagnostic-20261004"
spec = importlib.util.spec_from_file_location(
    "independent_presolve_g1", DAY / "g1-link-descent-independent/independent.py"
)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def encoded(proto):
    return proto.SerializeToString(deterministic=True)


def main():
    assert not (HERE / "postcheck.json").exists()
    gate = read(HERE / "audit.json")
    manifest = read(SOURCE / "manifest.json")
    result = read(SOURCE / "result.json")
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "audit.json")
    assert result["source_sha256"] == gate["source_sha256"] == sha(SOURCE / "run.py")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert result["budgets"] == manifest["budgets"]
    assert result["graph_index"] == 1 and result["family_sha256"] == manifest["family_sha256"]
    assert not result["exact_fractional_feasibility"], "Exact primal requires separate replay"
    for relative, expected in result["raw_sha256"].items():
        assert sha(RAW / relative) == expected
    assert result["cases"] == read(RAW / "cases.json")
    assert len(result["cases"]) == result["master_calls"] <= 2
    original = (ROOT / manifest["model_path"]).read_bytes()
    model = text_format.Parse(original.decode(), cp_model_pb2.CpModelProto())
    blocks, _, _, heavy, rows = ind.basis()
    gids = [blocks.index(block) for block in heavy]
    assert gids == manifest["heavy_global_ids"]
    checked, evaluated, improvements = [], {}, []
    lp_calls, total_solver = 0, 0.0
    best, best_ids = manifest["baseline_elastic_objective"], manifest["baseline_heavy_global_ids"]
    assert result["initial_objective"] == best
    for case, record in zip(manifest["cases"], result["cases"]):
        assert record["name"] == case["name"]
        folder = RAW / case["name"]
        assert (folder / "master.pbtxt").read_bytes() == original
        assert sha(folder / "master.pbtxt") == record["model_sha256"] == gate["model_sha256"]
        params = text_format.Parse((folder / "parameters.pbtxt").read_text(),
                                  sat_parameters_pb2.SatParameters())
        assert encoded(params) == encoded(parameters(case["cp_model_presolve"]))
        assert record["cp_model_presolve"] is case["cp_model_presolve"]
        assert sha(folder / "parameters.pbtxt") == record["parameters_sha256"]
        assert record["parameters_sha256"] == case["parameters_sha256"]
        assert sha(folder / "response.pbtxt") == record["response_sha256"]
        assert sha(folder / "solver.log") == record["log_sha256"]
        response = text_format.Parse((folder / "response.pbtxt").read_text(),
                                     cp_model_pb2.CpSolverResponse())
        status = cp_model_pb2.CpSolverStatus.Name(response.status)
        assert status == record["master_status"]
        assert abs(response.wall_time - record["master_reported_seconds"]) < 1e-6
        total_solver += record["master_seconds"]
        summary = {
            "name": case["name"], "status": status, "branches": response.num_branches,
            "conflicts": response.num_conflicts, "lp_iterations": response.num_lp_iterations,
            "master_seconds": record["master_seconds"], "lp_called": record["lp_called"],
        }
        if status not in ("OPTIMAL", "FEASIBLE"):
            assert not record["lp_called"] and "heavy_global_ids" not in record
            checked.append(summary)
            continue
        ids = record["heavy_global_ids"]
        assert len(ids) == len(set(ids)) == 28 and ids == sorted(ids)
        chosen = tuple(blocks[i] for i in ids)
        positions = {gids.index(i) for i in ids}
        assert list(response.solution) == [int(i in positions) for i in range(276)]
        for row in model.constraints:
            value = sum(c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
                        if i in positions)
            assert row.linear.domain[0] <= value <= row.linear.domain[1]
        distance = 28 - len(set(ids) & set(manifest["baseline_heavy_global_ids"]))
        assert distance == response.objective_value == record["distance_replacements"]
        assert ind.digest(chosen) == record["heavy_sha256"]
        assert sha(folder / "registry.json") == record["registry_sha256"]
        receipt = read(folder / "registry.json")
        reasons = ind.validate_receipt(chosen, receipt)
        assert reasons == record["rejected_links"]
        assert record["registry_accepted"] == (not reasons)
        summary.update(distance=distance, registry_accepted=not reasons)
        if reasons:
            assert not record["lp_called"] and "lp" not in record
            checked.append(summary)
            continue
        shifted = ind.shifted(rows, heavy, chosen)
        assert ind.digest(shifted) == record["shifted_rows_sha256"]
        key = tuple(ids)
        if key in evaluated:
            previous = evaluated[key]
            assert not record["lp_called"] and record["lp_reused"]
            assert record["reused_case"] == previous["name"]
            assert record["reused_lp_record_sha256"] == ind.digest(previous)
            assert record["lp"] == previous["lp"]
        else:
            assert record["lp_called"]
            assert json.loads(json.dumps(shifted)) == read(folder / "completion-rows.json")
            lp_calls += 1
            numerical = record["lp"]
            total_solver += numerical["seconds"]
            assert numerical["time_limit_seconds"] == 1
            if "vector_path" in record:
                residual = ind.check_vector({**record, **numerical})
                summary["residual_recounted"] = residual
                if numerical["status"] == "OPTIMAL" and numerical["objective"] < best - 1e-7:
                    best, best_ids = numerical["objective"], ids
                    improvements.append({
                        "status": "OPTIMAL", "objective": best, "rank": len(checked),
                        "heavy_global_ids": ids, "heavy_sha256": record["heavy_sha256"]
                    })
            else:
                assert numerical["status"] not in ("OPTIMAL", "FEASIBLE")
            evaluated[key] = record
        checked.append(summary)
    assert lp_calls == result["fresh_completion_lps"] <= len(evaluated) <= 2
    assert abs(total_solver - result["solver_seconds"]) < 1e-6
    assert best == result["best_objective"] and best_ids == result["best_heavy_global_ids"]
    assert improvements == result["improvements"]
    assert result["complete_diagnostic"] == (len(result["cases"]) == 2)
    assert result["stop_reason"] == (
        "numerical_zero" if result["numerical_zero"] else "two_parameter_cases_completed"
    )
    assert not result["covering_witness"] and not result["global_lower_bound_claim"]
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
        "gate_sha256": sha(HERE / "audit.json"), "result_sha256": sha(SOURCE / "result.json"),
        "model_sha256": gate["model_sha256"], "cases": checked, "fresh_lps": lp_calls,
        "solver_seconds": total_solver, "wall_seconds": result["wall_seconds"],
        "best_objective": best, "scope": "Two bounded parameter diagnostics on the same "
        "fixed-g1 model. UNKNOWN and timeouts are inconclusive; no global bound.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
