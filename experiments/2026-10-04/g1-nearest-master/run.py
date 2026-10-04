# Document:    Registry-Filtered Fixed-g1 Nearest Heavy Master
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      272e414ce5373dfa14ba071dd736fd8155ad2c96ae89504daf2a33932de42172
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or run a bounded nearest-pattern master in the fixed-g1 branch."""

import argparse
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
PLAN = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
CERT = DAY / "g1-whole-link-certificates"
CERT_AUDIT = DAY / "g1-whole-link-certificates-independent/audit.json"
PREP = ROOT / "experiments/scratch/g1-nearest-master-preparation-20261004"
RAW = ROOT / "experiments/scratch/g1-nearest-master-20261004"
SEED = 2026104070


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


branch = load(DAY / "g1-link-descent/run.py", "nearest_g1_branch")
helpers = load(DAY / "nearest-heavy-master/run.py", "nearest_g1_helpers")
original = load(DAY / "lazy-heavy-master/run.py", "nearest_g1_original")
sha = branch.sha
data_hash = branch.data_hash


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def inputs():
    certificate = json.loads((CERT / "result.json").read_text())
    audit = json.loads(CERT_AUDIT.read_text())
    assert audit["passed"]
    bundle_path = ROOT / certificate["bundle_path"]
    assert sha(bundle_path) == certificate["bundle_sha256"]
    assert audit["bundle_sha256"] == certificate["bundle_sha256"]
    assert audit["graph_index"] == 1 and audit["replayed_graph_specific_planes"] == 1000
    assert audit["finite_whole_link_excluded"]
    conditional = json.loads(bundle_path.read_text())
    assert audit["family_sha256"] == conditional["family_sha256"]
    broad = json.loads((PLAN / "broad-cuts-reference.json").read_text())
    assert conditional["count"] == 1000 and conditional["graph_index"] == 1
    assert broad["count"] == 353
    assert all(cut["graph_index"] == 1 for cut in conditional["cuts"])
    for cut in broad["cuts"] + conditional["cuts"]:
        assert len(cut["coefficients"]) == 276
        assert abs(cut["rhs"]) + sum(abs(x) for x in cut["coefficients"]) < 2**60
    return broad["cuts"], conditional["cuts"], bundle_path, conditional


def link_nogood(group, global_ids, blocks, heavy_lookup, registry, source):
    anchor = set(range(4 * group + 1, 4 * group + 4))
    assert len(global_ids) == len(set(global_ids)) == 7
    selected = [blocks[i] for i in global_ids]
    assert all(anchor <= set(block) for block in selected)
    receipt = registry.link(group, [set(block) - anchor for block in selected])
    assert receipt["excluded"] and receipt["proof_sources"]
    return {
        "graph_index": 1,
        "anchor_group_zero_based": group,
        "heavy_global_ids": sorted(global_ids),
        "heavy_local_ids": sorted(heavy_lookup[i] for i in global_ids),
        "upper_bound": 6,
        "registry": receipt,
        "source": source,
    }


def build(heavy, heavy_global, cuts, nogoods, baseline_ids):
    model, variables = original.build_master(heavy, heavy_global, cuts)
    for nogood in nogoods:
        assert nogood["graph_index"] == 1 and len(nogood["heavy_local_ids"]) == 7
        model.add(sum(variables[i] for i in nogood["heavy_local_ids"]) <= 6)
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    model.minimize(28 - sum(variables[lookup[i]] for i in baseline_ids))
    return model, variables


def initial_nogoods(blocks, heavy_global, registry):
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    saved = json.loads((PLAN / "known-registry-nogoods.json").read_text())
    result = []
    for item in sorted(saved, key=lambda item: item["heavy_global_ids"]):
        nogood = link_nogood(
            item["anchor_group_zero_based"],
            item["heavy_global_ids"],
            blocks,
            lookup,
            registry,
            "saved_two_round_registry_rejection",
        )
        assert nogood["registry"]["representative"] == item["representative"]
        assert nogood["registry"]["proof_sources"] == item["proof_sources"]
        result.append(nogood)
    assert len(result) == len({tuple(item["heavy_global_ids"]) for item in result}) == 19
    return result


def prepare():
    assert not PREP.exists() and not (HERE / "manifest.json").exists()
    broad, conditional, bundle_path, bundle = inputs()
    blocks, ordinary, heavy, _, rows, changes = branch.basis()
    heavy_global = [blocks.index(block) for block in heavy]
    assert bundle["heavy_global_ids"] == heavy_global
    assert bundle["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    descent_path = DAY / "g1-link-descent/result.json"
    descent = json.loads(descent_path.read_text())
    baseline = descent["trajectory"][-1]
    assert baseline["objective"] == 7.52051548546158
    registry = branch.registry_module.Registry()
    assert registry.classify([blocks[i] for i in baseline["heavy_global_ids"]])["accepted"]
    nogoods = initial_nogoods(blocks, heavy_global, registry)
    model, _ = build(
        heavy, heavy_global, broad + conditional, nogoods, baseline["heavy_global_ids"]
    )
    assert len(model.proto.variables) == 276
    assert len(model.proto.constraints) == 605 + 353 + 1000 + 19 == 1977
    assert not model.validate()
    PREP.mkdir()
    master_path = PREP / "master.pbtxt"
    master_path.write_text(str(model.proto))
    dump(PREP / "initial-nogoods.json", nogoods)
    dump(PREP / "unconditional-g1-rows.json", rows)
    bound = json.loads((PLAN / "inputs.json").read_text())
    bound.update(json.loads((CERT / "result.json").read_text())["input_files"])
    paths = [
        Path(__file__),
        CERT / "result.json",
        CERT / "extract.py",
        CERT_AUDIT,
        bundle_path,
        PLAN / "broad-cuts-reference.json",
        PLAN / "known-registry-nogoods.json",
        DAY / "lazy-heavy-master/run.py",
        DAY / "nearest-heavy-master/run.py",
        DAY / "g1-link-descent/run.py",
        DAY / "g1-link-descent/registry.py",
        descent_path,
        DAY / "g1-link-descent-independent/postcheck.json",
        DAY / "g1-descent-best-independent/audit.json",
    ]
    paths += registry.input_paths()
    bound.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for relative, digest in bound.items():
        assert sha(ROOT / relative) == digest
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision_at_freeze": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_files": bound,
        "graph_index": 1,
        "hub_excesses": [0, 1, 1, 1, 1, 0],
        "hub_pair_targets": [5, 6, 6, 6, 6, 5],
        "family_sha256": bundle["family_sha256"],
        "six_row_changes": changes,
        "broad_cut_count": 353,
        "conditional_g1_cut_count": 1000,
        "initial_registry_nogoods": 19,
        "master_base_constraints": 605,
        "master_constraints": 1977,
        "master_path": str(master_path.relative_to(ROOT)),
        "master_sha256": sha(master_path),
        "nogoods_path": str((PREP / "initial-nogoods.json").relative_to(ROOT)),
        "nogoods_sha256": sha(PREP / "initial-nogoods.json"),
        "unconditional_rows_sha256": data_hash(rows),
        "heavy_global_ids": heavy_global,
        "ordinary_global_ids": [blocks.index(block) for block in ordinary],
        "baseline_heavy_global_ids": baseline["heavy_global_ids"],
        "baseline_elastic_objective": baseline["objective"],
        "baseline_record": baseline,
        "objective": (
            "Minimize replaced heavy blocks relative to the frozen g1 local minimum; "
            "no distance constraint or radius."
        ),
        "budget": {
            "admitted_lps": 50,
            "master_proposals": 150,
            "each_master_seconds": 2,
            "each_lp_seconds": 1,
            "combined_solver_seconds": 120,
            "wall_seconds": 160,
            "workers": 1,
            "seed": SEED,
        },
        "optimization_calls": 0,
        "scope": (
            "Only fixed hub graph g1. Registry nogoods and new exact cuts stay graph-scoped; "
            "no global lower-bound claim."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "master_sha256": sha(master_path),
                "master_constraints": 1977,
                "initial_nogoods": 19,
                "optimization_calls": 0,
            }
        )
    )


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == sha(__file__) == manifest["source_sha256"]
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not RAW.exists() and not (HERE / "result.json").exists()
    RAW.mkdir()
    for path in [Path(__file__), HERE / "manifest.json", gate_path]:
        (RAW / path.name).write_bytes(path.read_bytes())
    started = time.monotonic()
    broad, conditional, _, _ = inputs()
    blocks, ordinary, heavy, _, rows, _ = branch.basis()
    assert data_hash(rows) == manifest["unconditional_rows_sha256"]
    heavy_global = manifest["heavy_global_ids"]
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    registry = branch.registry_module.Registry()
    nogoods = initial_nogoods(blocks, heavy_global, registry)
    nogood_keys = {tuple(item["heavy_global_ids"]) for item in nogoods}
    exact = load(branch.generator.LP_CORE, "nearest_g1_exact")
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "budget": manifest["budget"],
        "graph_index": 1,
        "family_sha256": manifest["family_sha256"],
    }
    dump(RAW / "start.json", start)
    records = []
    improvements = []
    seen = set()
    lp_count = 0
    rejected = 0
    total_solver = 0.0
    best_objective = manifest["baseline_elastic_objective"]
    best_ids = manifest["baseline_heavy_global_ids"]
    numerical_zero = False
    exact_feasible = False
    stop_reason = "master_proposal_limit"
    for step in range(150):
        if lp_count >= 50:
            stop_reason = "admitted_lp_limit"
            break
        if total_solver >= 116.8 or time.monotonic() - started >= 153:
            stop_reason = "combined_solver_or_wall_budget"
            break
        folder = RAW / f"step-{step:03d}"
        folder.mkdir()
        model, variables = build(
            heavy, heavy_global, broad + conditional, nogoods, manifest["baseline_heavy_global_ids"]
        )
        model_path = folder / "master.pbtxt"
        model_path.write_text(str(model.proto))
        if step == 0:
            assert sha(model_path) == manifest["master_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 2
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = SEED + step
        solver.parameters.randomize_search = True
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        logs = []
        solver.log_callback = logs.append
        before = time.monotonic()
        status = solver.solve(model)
        seconds = time.monotonic() - before
        total_solver += seconds
        (folder / "master.log").write_text("".join(logs))
        (folder / "response.pbtxt").write_text(str(solver.response_proto))
        (folder / "parameters.pbtxt").write_text(str(solver.parameters))
        record = {
            "step": step,
            "master_status": solver.status_name(status),
            "master_seconds": seconds,
            "master_reported_seconds": solver.wall_time,
            "master_sha256": sha(model_path),
            "seed": SEED + step,
            "broad_cut_count": len(broad),
            "g1_cut_count": len(conditional),
            "registry_nogood_count": len(nogoods),
            "lp_called": False,
        }
        records.append(record)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            stop_reason = "inconclusive_master_without_candidate"
            dump(RAW / "steps.json", records)
            break
        positions = {i for i, variable in enumerate(variables) if solver.value(variable)}
        ids = [heavy_global[i] for i in sorted(positions)]
        assert len(ids) == 28 and tuple(ids) not in seen
        seen.add(tuple(ids))
        assert all(
            sum(cut["coefficients"][i] for i in positions) >= cut["rhs"]
            for cut in broad + conditional
        )
        assert all(sum(i in positions for i in item["heavy_local_ids"]) <= 6 for item in nogoods)
        distance = 28 - len(set(ids) & set(manifest["baseline_heavy_global_ids"]))
        assert solver.objective_value == distance
        fixed = [heavy[i] for i in sorted(positions)]
        receipt = registry.classify(fixed)
        dump(folder / "registry.json", receipt)
        record.update(
            heavy_global_ids=ids,
            heavy_sha256=data_hash(fixed),
            distance_replacements=distance,
            objective_bound=solver.best_objective_bound,
            registry_accepted=receipt["accepted"],
            registry_path=str((folder / "registry.json").relative_to(ROOT)),
            registry_sha256=sha(folder / "registry.json"),
        )
        new_nogoods = []
        for link in receipt["links"]:
            if not link["excluded"]:
                continue
            group = link["anchor_group_zero_based"]
            anchor = set(range(4 * group + 1, 4 * group + 4))
            link_ids = [i for i in ids if anchor <= set(blocks[i])]
            assert tuple(link_ids) not in nogood_keys
            nogood = link_nogood(group, link_ids, blocks, lookup, registry, f"master_step_{step}")
            assert data_hash(nogood["registry"]) == data_hash(link)
            nogoods.append(nogood)
            new_nogoods.append(nogood)
            nogood_keys.add(tuple(link_ids))
        if not receipt["accepted"]:
            assert new_nogoods
            rejected += 1
            dump(folder / "new-registry-nogoods.json", new_nogoods)
            record.update(
                new_registry_nogoods=len(new_nogoods),
                new_registry_nogoods_sha256=sha(folder / "new-registry-nogoods.json"),
            )
            dump(RAW / "steps.json", records)
            print(
                json.dumps(
                    {
                        "step": step,
                        "registry_rejected": True,
                        "new_nogoods": len(new_nogoods),
                        "admitted_lps": lp_count,
                        "solver_seconds": total_solver,
                    }
                ),
                flush=True,
            )
            continue
        assert not new_nogoods
        if total_solver >= 118.9 or time.monotonic() - started >= 156:
            stop_reason = "budget_before_admitted_lp"
            dump(RAW / "steps.json", records)
            break
        shifted = branch.generator.shifted_rows(rows, heavy, fixed)
        dump(folder / "completion-rows.json", shifted)
        numerical, values, dual = branch.sweep.solve(shifted)
        total_solver += numerical["seconds"]
        lp_count += 1
        record.update(lp_called=True, lp=numerical, shifted_rows_sha256=data_hash(shifted))
        if values is None:
            stop_reason = "inconclusive_lp_without_solution"
            dump(RAW / "steps.json", records)
            break
        dump(folder / "numerical-primal.json", values)
        dump(folder / "numerical-dual.json", dual)
        record.update(
            vector_path=str((folder / "numerical-primal.json").relative_to(ROOT)),
            vector_sha256=sha(folder / "numerical-primal.json"),
            dual_path=str((folder / "numerical-dual.json").relative_to(ROOT)),
            dual_sha256=sha(folder / "numerical-dual.json"),
        )
        if numerical["status"] == "OPTIMAL" and numerical["objective"] < best_objective - 1e-7:
            best_objective = numerical["objective"]
            best_ids = ids
            improvements.append(
                {
                    "status": "OPTIMAL",
                    "objective": best_objective,
                    "rank": step,
                    "heavy_global_ids": ids,
                    "heavy_sha256": record["heavy_sha256"],
                }
            )
        if numerical["recomputed_l1_residual"] <= 1e-7:
            numerical_zero = True
            stop_reason = "unresolved_numerical_feasibility"
            attempts = []
            for limit in (100, 10000, 1000000, 1000000000):
                primal = exact.exact_primal(shifted, values, limit)
                attempts.append({"denominator_limit": limit, "passed": primal is not None})
                if primal is not None:
                    primal.update(
                        graph_index=1,
                        family_sha256=manifest["family_sha256"],
                        heavy_global_ids=ids,
                        ordinary_global_ids=manifest["ordinary_global_ids"],
                        shifted_rows_sha256=record["shifted_rows_sha256"],
                    )
                    dump(HERE / "exact-primal.json", primal)
                    exact_feasible = True
                    stop_reason = "checked_exact_fractional_feasibility"
                    break
            dump(folder / "exact-primal-attempts.json", attempts)
            dump(RAW / "steps.json", records)
            break
        cut = helpers.derive_cut(exact, rows, shifted, dual, positions, len(ordinary), len(heavy))
        if cut is None:
            stop_reason = "unresolved_exact_conditional_dual"
            dump(RAW / "steps.json", records)
            break
        assert max(abs(weight) for _, weight in cut["dual"]["weights"]) <= cut["denominator"]
        cut.update(
            id=f"g1-nearest-step{step:03d}",
            graph_index=1,
            family_sha256=manifest["family_sha256"],
            source_heavy_global_ids=ids,
            source_heavy_sha256=record["heavy_sha256"],
            source_shifted_rows_sha256=record["shifted_rows_sha256"],
        )
        dump(folder / "learned-g1-cut.json", cut)
        conditional.append(cut)
        record.update(
            exact_gap=cut["dual"]["gap"],
            learned_cut_path=str((folder / "learned-g1-cut.json").relative_to(ROOT)),
            learned_cut_sha256=sha(folder / "learned-g1-cut.json"),
        )
        dump(RAW / "steps.json", records)
        print(
            json.dumps(
                {
                    "step": step,
                    "registry_rejected": False,
                    "admitted_lps": lp_count,
                    "elastic_objective": numerical.get("objective"),
                    "best_objective": best_objective,
                    "distance": distance,
                    "solver_seconds": total_solver,
                }
            ),
            flush=True,
        )
    wall_seconds = time.monotonic() - started
    assert lp_count <= 50 and len(records) <= 150 and total_solver <= 120 and wall_seconds <= 160
    dump(RAW / "final-registry-nogoods.json", nogoods)
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": manifest["baseline_elastic_objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": best_ids,
        "master_proposals": len(records),
        "registry_rejected_proposals": rejected,
        "admitted_lps": lp_count,
        "new_conditional_cuts": len(conditional) - 1000,
        "new_registry_nogoods": len(nogoods) - 19,
        "final_conditional_cuts": len(conditional),
        "broad_cuts": len(broad),
        "solver_seconds": total_solver,
        "wall_seconds": wall_seconds,
        "stop_reason": stop_reason,
        "numerical_zero": numerical_zero,
        "exact_fractional_feasibility": exact_feasible,
        "covering_witness": False,
        "global_lower_bound_claim": False,
        "records": records,
        "improvements": improvements,
    }
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.rglob("*")) if path.is_file()
    }
    dump(HERE / "result.json", result)
    dump(
        HERE / "stitch-input.json",
        {"initial_objective": manifest["baseline_elastic_objective"], "records": improvements},
    )
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("records", "improvements", "raw_sha256")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        assert args.gate is not None
        run(args.gate)
