# Document:    Bounded Lazy Heavy Master Continuation
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/2026-10-03"
RAW = ROOT / "experiments/scratch/lazy-heavy-master-continuation-20261004"
ANCHORS = [tuple(range(a, a + 3)) for a in (1, 5, 9, 13)]
BUNDLE = OLD / "cut-survivor-lp-screen/cut-bundle.json"
ORACLE = OLD / "lookahead-cut-independent/check.py"
LP = OLD / "cut-survivor-lp-screen/lp_core.py"
SEED = 2026104061
MAX_STEPS = 100
WALL_SECONDS = 90
CASE_RESERVE_SECONDS = 27
MASTER_SECONDS = 5
PREVIOUS = HERE.parent / "lazy-heavy-master"
PREVIOUS_GATE = HERE.parent / "lazy-heavy-master-independent/postcheck.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    assert not path.exists(), f"Preserve completed evidence: {path}"
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_master(heavy, global_ids, cuts):
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"block_{i}") for i in global_ids]
    model.add(sum(xs) == 28)
    # One anchor triple and two outside points per heavy block. Each of the
    # other twelve points appears once; that anchor's hub appears twice.
    for anchor in ANCHORS:
        for p in range(1, 17):
            if p in anchor:
                continue
            target = 2 if p == max(anchor) + 1 else 1
            ids = [i for i, b in enumerate(heavy) if set(anchor + (p,)) <= set(b)]
            model.add(sum(xs[i] for i in ids) == target)
    for triple in itertools.combinations(range(1, 17), 3):
        if triple in ANCHORS:
            continue
        ids = [i for i, b in enumerate(heavy) if set(triple) <= set(b)]
        if ids:
            model.add(sum(xs[i] for i in ids) <= 2)
    for cut in cuts:
        model.add(sum(c * x for c, x in zip(cut["coefficients"], xs, strict=True))
                  >= cut["rhs"])
    return model, xs


def load_cuts(bundle):
    previous_gate_bytes = PREVIOUS_GATE.read_bytes()
    previous_gate = json.loads(previous_gate_bytes)
    assert previous_gate["passed"] and previous_gate["checked_new_cuts"] == 10
    assert previous_gate["total_checked_cuts"] == 24
    cuts = list(bundle["cuts"])
    assert len(cuts) == 14
    for step in range(10):
        path = PREVIOUS / f"learned-cut-{step:02}.json"
        captured = path.read_bytes()
        assert sha(captured) == previous_gate["receipts"][str(path.relative_to(ROOT))]
        cuts.append(json.loads(captured))
    return cuts, sha(previous_gate_bytes)


def prepare():
    assert not RAW.exists(), "Preserve completed raw evidence"
    RAW.mkdir(parents=True)
    bundle_bytes = BUNDLE.read_bytes()
    bundle = json.loads(bundle_bytes)
    gate_path = HERE.parent / "cut-bundle-independent/audit.json"
    gate_bytes = gate_path.read_bytes()
    gate = json.loads(gate_bytes)
    assert gate["passed"] and gate["bundle_sha256"] == sha(bundle_bytes)
    assert sha(ORACLE.read_bytes()) == (
        "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    )
    assert sha(LP.read_bytes()) == (
        "35d379455244f2511b00d6fb8dff01de69c1c6a0ca2869c3c73c7e03ce5220d1"
    )
    oracle = load_module("incidence_oracle", ORACLE)
    blocks, ordinary, heavy, _, rows = oracle.rebuild()
    assert bundle["heavy_blocks"] == [list(b) for b in heavy]
    assert bundle["heavy_global_ids"] == [blocks.index(b) for b in heavy]
    cuts, previous_gate_sha256 = load_cuts(bundle)
    model, _ = build_master(heavy, bundle["heavy_global_ids"], cuts)
    proto_bytes = str(model.proto).encode()
    (RAW / "master.pbtxt").write_bytes(proto_bytes)
    (RAW / "run-frozen.py").write_bytes(Path(__file__).read_bytes())
    manifest = {"source_sha256": sha(Path(__file__).read_bytes()),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "bundle_sha256": sha(bundle_bytes), "cut_gate_sha256": sha(gate_bytes),
                "oracle_sha256": sha(ORACLE.read_bytes()), "lp_sha256": sha(LP.read_bytes()),
                "master_sha256": sha(proto_bytes), "variables": len(model.proto.variables),
                "constraints": len(model.proto.constraints), "ortools": ortools.__version__,
                "seed": SEED, "iterations": MAX_STEPS, "master_seconds_each": MASTER_SECONDS,
                "wall_seconds": WALL_SECONDS, "case_reserve_seconds": CASE_RESERVE_SECONDS,
                "initial_cuts": len(cuts), "previous_gate_sha256": previous_gate_sha256,
                "python": sys.version,
                "lp_seconds_each_phase": 10, "workers": 1,
                "ordinary_columns": len(ordinary), "completion_rows": len(rows),
                "scope": "Regular four-sevenfold candidate generation, all six hub graphs."}
    save(HERE / "manifest.json", manifest)
    print(json.dumps(manifest))


def run():
    manifest = json.loads((HERE / "manifest.json").read_bytes())
    assert manifest["source_sha256"] == sha(Path(__file__).read_bytes())
    assert manifest["bundle_sha256"] == sha(BUNDLE.read_bytes())
    assert manifest["oracle_sha256"] == sha(ORACLE.read_bytes())
    assert manifest["lp_sha256"] == sha(LP.read_bytes())
    assert not (HERE / "results.json").exists()
    oracle = load_module("incidence_oracle", ORACLE)
    lp = load_module("completion_lp", LP)
    _, ordinary, heavy, _, rows = oracle.rebuild()
    bundle = json.loads(BUNDLE.read_bytes())
    cuts, previous_gate_sha256 = load_cuts(bundle)
    assert previous_gate_sha256 == manifest["previous_gate_sha256"]
    assert len(cuts) == manifest["initial_cuts"] == 24
    results = []
    started = time.monotonic()
    stop_reason = "iteration_limit"
    for step in range(MAX_STEPS):
        remaining = WALL_SECONDS - (time.monotonic() - started)
        if remaining < CASE_RESERVE_SECONDS:
            stop_reason = "wall_budget_reserve"
            break
        case_started = time.monotonic()
        directory = RAW / f"step-{step:02}"
        directory.mkdir()
        model, variables = build_master(heavy, bundle["heavy_global_ids"], cuts)
        proto_bytes = str(model.proto).encode()
        (directory / "master.pbtxt").write_bytes(proto_bytes)
        if step == 0:
            assert sha(proto_bytes) == manifest["master_sha256"]
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = MASTER_SECONDS
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = SEED + step
        solver.parameters.randomize_search = True
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        logs = []
        solver.log_callback = logs.append
        status = solver.solve(model)
        (directory / "solver.log").write_text("".join(logs))
        (directory / "response.pbtxt").write_text(str(solver.response_proto))
        (directory / "parameters.pbtxt").write_text(str(solver.parameters))
        record = {"step": step, "master_status": solver.status_name(status),
                  "master_seconds": solver.wall_time, "master_sha256": sha(proto_bytes),
                  "cut_count": len(cuts), "seed": SEED + step,
                  "remaining_at_case_start": remaining}
        results.append(record)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            record["stop"] = "No heavy candidate; status is not a checked exclusion."
            stop_reason = "master_without_candidate"
            record["case_seconds"] = time.monotonic() - case_started
            break
        fixed = {i for i, x in enumerate(variables) if solver.value(x)}
        assert len(fixed) == 28
        record["heavy_indices"] = sorted(fixed)
        (directory / "heavy.txt").write_text("".join(
            " ".join(map(str, heavy[i])) + "\n" for i in sorted(fixed)))
        shifted = []
        for ordinary_ids, heavy_ids, lower, upper in rows:
            shift = len(fixed.intersection(heavy_ids))
            shifted.append((ordinary_ids, [1] * len(ordinary_ids), lower - shift,
                            upper if upper == lp.INF else upper - shift))
        save(directory / "completion-rows.json", shifted)
        feasibility, values, _ = lp.solve(shifted)
        record["lp"] = [feasibility]
        if values is not None:
            primal = None
            for limit in (1000, 10000, 1000000):
                primal = lp.exact_primal(shifted, values, limit)
                if primal:
                    break
            save(directory / "numerical-primal.json", values)
            if primal:
                save(directory / "exact-primal.json", primal)
                record["stop"] = "Exact fractional completion; integer cover still required."
            else:
                record["stop"] = "Numerical feasibility without exact rational witness."
            stop_reason = "exact_fractional_completion" if primal else "unresolved_primal"
            record["case_seconds"] = time.monotonic() - case_started
            break
        elastic, _, numerical_dual = lp.solve(shifted, elastic=True)
        record["lp"].append(elastic)
        if numerical_dual is None:
            record["stop"] = "No separable numerical dual; inconclusive."
            stop_reason = "unresolved_dual"
            record["case_seconds"] = time.monotonic() - case_started
            break
        save(directory / "numerical-dual.json", numerical_dual)
        dual = None
        for denominator in (1000, 10000, 1000000):
            candidate = lp.exact_dual(shifted, numerical_dual, denominator)
            if candidate["proves_infeasible"]:
                dual = candidate
                break
        if dual is None:
            record["stop"] = "No exact signed-dual contradiction; inconclusive."
            stop_reason = "unresolved_exact_dual"
            record["case_seconds"] = time.monotonic() - case_started
            break
        ordinary_sum, coefficients, constant = [0] * len(ordinary), [0] * len(heavy), 0
        for row, weight in dual["weights"]:
            oi, hi, lower, upper = rows[row]
            bound = lower if weight > 0 else upper
            assert abs(bound) < 2**60
            constant += weight * bound
            for i in oi:
                ordinary_sum[i] += weight
            for i in hi:
                coefficients[i] += weight
        box = sum(max(0, c) for c in ordinary_sum)
        lhs = sum(coefficients[i] for i in fixed)
        assert box == dual["box_max_numerator"]
        assert constant - lhs == dual["rhs_numerator"]
        cut = {"coefficients": coefficients, "rhs": constant - box,
               "constant": constant, "ordinary_box_max": box,
               "ordinary_coefficients": ordinary_sum, "source_lhs": lhs,
               "denominator": dual["denominator"], "dual": dual}
        assert lhs < cut["rhs"]
        save(directory / "learned-cut.json", cut)
        cuts.append(cut)
        record["gap"] = dual["gap"]
        record["cut_sha256"] = sha((directory / "learned-cut.json").read_bytes())
        record["case_seconds"] = time.monotonic() - case_started
        print(json.dumps(record), flush=True)
    report = {"version": "v1.1.0", "manifest_sha256": sha((HERE / "manifest.json").read_bytes()),
              "seconds": time.monotonic() - started, "steps": results,
              "initial_cuts": 24, "new_cuts": len(cuts) - 24,
              "stop_reason": stop_reason, "wall_target_seconds": WALL_SECONDS,
              "scope": "Regular family candidate generator only; no covering witness claimed."}
    completed = [r for r in results if "gap" in r]
    def trend(group):
        if not group:
            return None
        gaps = [r["gap"][0] / r["gap"][1] for r in group]
        return {"cases": len(group), "gap_min": min(gaps), "gap_mean": sum(gaps) / len(gaps),
                "gap_max": max(gaps),
                "master_seconds_mean": sum(r["master_seconds"] for r in group) / len(group),
                "case_seconds_mean": sum(r["case_seconds"] for r in group) / len(group)}
    report["trend"] = {"first_ten": trend(completed[:10]),
                       "last_ten": trend(completed[-10:]), "all": trend(completed)}
    save(HERE / "results.json", report)
    index = {str(path.relative_to(ROOT)): sha(path.read_bytes())
             for path in sorted(RAW.rglob("*")) if path.is_file()}
    save(HERE / "hash-index.json", {"files": index,
                                   "results_sha256": sha((HERE / "results.json").read_bytes())})
    print(json.dumps(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run"))
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else run)()
