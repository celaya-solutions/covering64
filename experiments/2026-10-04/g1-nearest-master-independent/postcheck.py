# Document:    Independent Fixed-g1 Nearest Master Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay every master, registry transport, completion row and exact separating plane."""

import importlib.util
import json

from check import DAY, HERE, PLAN, ROOT, SOURCE, ind, master, read, validate_nogood
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

RAW = ROOT / "experiments/scratch/g1-nearest-master-20261004"
spec = importlib.util.spec_from_file_location(
    "independent_nearest_g1_cut", DAY / "g1-whole-link-certificates-independent/check.py"
)
exact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exact)


def encoded(proto):
    return proto.SerializeToString(deterministic=True)


def main():
    assert not (HERE / "postcheck.json").exists()
    gate, manifest = read(HERE / "audit.json"), read(SOURCE / "manifest.json")
    result = read(SOURCE / "result.json")
    assert gate["passed"] and result["gate_sha256"] == ind.sha(HERE / "audit.json")
    assert result["source_sha256"] == gate["source_sha256"] == ind.sha(SOURCE / "run.py")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == ind.sha(SOURCE / "manifest.json")
    assert result["budget"] == manifest["budget"]
    assert not result["exact_fractional_feasibility"], "Exact primal requires separate replay"
    for relative, expected in result["raw_sha256"].items():
        assert ind.sha(RAW / relative) == expected
    blocks, anchors, ordinary, heavy, rows = ind.basis()
    gids = [blocks.index(block) for block in heavy]
    family_sha = manifest["family_sha256"]
    assert result["family_sha256"] == family_sha and result["graph_index"] == 1
    broad = read(PLAN / "broad-cuts-reference.json")["cuts"]
    certificate = read(DAY / "g1-whole-link-certificates-independent/audit.json")
    conditional = read(ROOT / certificate["bundle_path"])["cuts"]
    nogoods = read(ROOT / manifest["nogoods_path"])
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    initial = manifest["baseline_elastic_objective"]
    best, best_ids = initial, manifest["baseline_heavy_global_ids"]
    assert result["initial_objective"] == initial == 7.52051548546158
    assert len(result["records"]) <= 150 and result["admitted_lps"] <= 50
    assert result["solver_seconds"] <= 120 and result["wall_seconds"] <= 160
    checked, seen, improvements = [], set(), []
    cumulative, admitted, rejected, cut_count = 0.0, 0, 0, 0
    for step, record in enumerate(result["records"]):
        folder = RAW / f"step-{step:03d}"
        assert record["step"] == step
        actual = text_format.Parse((folder / "master.pbtxt").read_text(),
                                  cp_model_pb2.CpModelProto())
        expected = master(heavy, anchors, gids, broad + conditional, nogoods,
                          manifest["baseline_heavy_global_ids"])
        assert encoded(actual) == encoded(expected)
        assert ind.sha(folder / "master.pbtxt") == record["master_sha256"]
        assert record["broad_cut_count"] == len(broad) == 353
        assert record["g1_cut_count"] == len(conditional)
        assert record["registry_nogood_count"] == len(nogoods)
        params = text_format.Parse((folder / "parameters.pbtxt").read_text(),
                                  sat_parameters_pb2.SatParameters())
        expected_params = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=2, num_search_workers=1, random_seed=2026104070 + step,
            randomize_search=True, log_search_progress=True, log_to_stdout=False
        )
        assert encoded(params) == encoded(expected_params)
        response = text_format.Parse((folder / "response.pbtxt").read_text(),
                                     cp_model_pb2.CpSolverResponse())
        status = cp_model_pb2.CpSolverStatus.Name(response.status)
        assert status == record["master_status"]
        cumulative += record["master_seconds"]
        if status not in ("OPTIMAL", "FEASIBLE"):
            assert step == len(result["records"]) - 1
            assert result["stop_reason"] == "inconclusive_master_without_candidate"
            assert not record["lp_called"]
            checked.append({"step": step, "master_status": status, "lp_called": False})
            continue
        ids = record["heavy_global_ids"]
        assert len(ids) == len(set(ids)) == 28 and ids == sorted(ids)
        assert tuple(ids) not in seen
        seen.add(tuple(ids))
        positions = {gids.index(i) for i in ids}
        assert list(response.solution) == [int(i in positions) for i in range(276)]
        for row in actual.constraints:
            value = sum(c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
                        if i in positions)
            assert row.linear.domain[0] <= value <= row.linear.domain[1]
        distance = 28 - len(set(ids) & set(manifest["baseline_heavy_global_ids"]))
        assert distance == response.objective_value == record["distance_replacements"]
        chosen = tuple(blocks[i] for i in ids)
        assert ind.digest(chosen) == record["heavy_sha256"]
        receipt = read(ROOT / record["registry_path"])
        assert ind.sha(ROOT / record["registry_path"]) == record["registry_sha256"]
        reasons = ind.validate_receipt(chosen, receipt)
        assert record["registry_accepted"] == (not reasons)
        if reasons:
            rejected += 1
            assert not record["lp_called"]
            new = read(folder / "new-registry-nogoods.json")
            assert len(new) == len(reasons) == record["new_registry_nogoods"]
            assert ind.sha(folder / "new-registry-nogoods.json") == record[
                "new_registry_nogoods_sha256"
            ]
            assert {n["anchor_group_zero_based"] for n in new} == {
                reason["anchor_group_zero_based"] for reason in reasons
            }
            for nogood in new:
                validate_nogood(nogood, blocks, anchors, gids)
                assert all(nogood["heavy_global_ids"] != old["heavy_global_ids"] for old in nogoods)
                assert set(nogood["heavy_global_ids"]) <= set(ids)
                nogoods.append(nogood)
            checked.append({"step": step, "registry_rejected": True, "new_nogoods": len(new)})
            continue
        if not record["lp_called"]:
            assert step == len(result["records"]) - 1
            assert result["stop_reason"] == "budget_before_admitted_lp"
            continue
        admitted += 1
        numerical = record["lp"]
        cumulative += numerical["seconds"]
        shifted = ind.shifted(rows, heavy, chosen)
        assert ind.digest(shifted) == record["shifted_rows_sha256"]
        assert json.loads(json.dumps(shifted)) == read(folder / "completion-rows.json")
        if "vector_path" not in record:
            assert numerical["status"] not in ("OPTIMAL", "FEASIBLE")
            assert step == len(result["records"]) - 1
            assert result["stop_reason"] == "inconclusive_lp_without_solution"
            continue
        combined = {**record, **numerical}
        residual = ind.check_vector(combined)
        if numerical["status"] == "OPTIMAL" and numerical["objective"] < best - 1e-7:
            best, best_ids = numerical["objective"], ids
            improvements.append({
                "status": "OPTIMAL", "objective": best, "rank": step,
                "heavy_global_ids": ids, "heavy_sha256": record["heavy_sha256"]
            })
        if "learned_cut_path" not in record:
            assert step == len(result["records"]) - 1
            assert result["stop_reason"] in (
                "unresolved_numerical_feasibility", "unresolved_exact_conditional_dual"
            )
            continue
        cut = read(ROOT / record["learned_cut_path"])
        assert ind.sha(ROOT / record["learned_cut_path"]) == record["learned_cut_sha256"]
        assert cut["source_heavy_global_ids"] == ids
        assert cut["source_heavy_sha256"] == record["heavy_sha256"]
        assert cut["source_shifted_rows_sha256"] == record["shifted_rows_sha256"]
        normalized = {**cut, "maximum_signed_row_weight": max(
            abs(weight) for _, weight in cut["dual"]["weights"]
        )}
        gap = exact.verify_cut(normalized, rows, support_o, support_h, gids, family_sha)
        assert record["exact_gap"] == [gap.numerator, gap.denominator]
        conditional.append(cut)
        cut_count += 1
        checked.append({"step": step, "residual_recounted": residual,
                        "exact_gap": record["exact_gap"], "distance": distance})
    assert result["master_proposals"] == len(result["records"])
    assert result["registry_rejected_proposals"] == rejected
    assert result["admitted_lps"] == admitted
    assert result["new_conditional_cuts"] == cut_count
    assert result["final_conditional_cuts"] == len(conditional) == 1000 + cut_count
    assert result["new_registry_nogoods"] == len(nogoods) - 19
    assert read(RAW / "final-registry-nogoods.json") == nogoods
    assert abs(cumulative - result["solver_seconds"]) < 1e-6
    assert result["best_objective"] == best and result["best_heavy_global_ids"] == best_ids
    assert result["improvements"] == improvements
    assert not result["covering_witness"] and not result["global_lower_bound_claim"]
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": ind.sha(__file__),
        "gate_sha256": ind.sha(HERE / "audit.json"),
        "result_sha256": ind.sha(SOURCE / "result.json"),
        "master_proposals": len(result["records"]), "registry_rejected": rejected,
        "admitted_lps": admitted, "new_exact_g1_cuts": cut_count,
        "new_registry_nogoods": len(nogoods) - 19,
        "solver_seconds": cumulative, "wall_seconds": result["wall_seconds"],
        "initial_objective": initial, "best_objective": best,
        "stop_reason": result["stop_reason"], "results": checked,
        "scope": "Bounded fixed-g1 campaign readback. Exact planes exclude their source "
        "patterns; numerical objectives and master timeouts do not prove global bounds.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
