# Document:    Gated Soft Strong-Pair H12 Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      57c74759cdaa7b23c9a61fe8389d28d37040910aef0d374ab3ec8ad469f3f5c3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One explicitly gated run, saving every callback and final vector without filtering."""

import argparse
import importlib.util
import json
import time
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "experiments/scratch/soft-pair-h12-start-run-20261004"


def load_preparer():
    spec = importlib.util.spec_from_file_location("soft_model_preparer", HERE / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    prep = load_preparer()
    helper = prep.helper_module()
    require = helper.require
    require(not RUN.exists() and not (HERE / "result.json").exists(), "run already exists")
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(prep.sha(args.gate) == args.gate_sha256, "gate hash mismatch")
    gate = json.loads(args.gate.read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required")
    expected = {
        "manifest_sha256": prep.sha(manifest_path),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "hint_sha256": manifest["hint_sha256"],
        "runner_sha256": prep.sha(__file__),
    }
    for key, value in expected.items():
        require(gate.get(key) == value, f"gate binding mismatch: {key}")
    for relative, digest in (manifest["sources"] | manifest["input_files"]).items():
        require(prep.sha(ROOT / relative) == digest, f"source changed: {relative}")
    for kind in ("model", "parameters", "hint"):
        require(
            prep.sha(ROOT / manifest[f"{kind}_path"]) == manifest[f"{kind}_sha256"],
            f"frozen {kind} changed",
        )
    require(helper.load_sources() == manifest["core_rows"], "core rows changed")
    model = cp_model.CpModel()
    require(
        model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text()), "model parse"
    )
    require(not model.validate(), "model validation failed")
    hint = json.loads((ROOT / manifest["hint_path"]).read_text())
    vector_check = prep.check_vector(model, hint["values"])
    require(vector_check == manifest["hint_vector_check"], "hint vector changed")
    require(list(model.proto.solution_hint.vars) == list(range(5728)), "hint index coverage")
    require(list(model.proto.solution_hint.values) == hint["values"], "hint values differ")
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / manifest["parameters_path"]).read_text()),
        "parameter parse",
    )
    variables = [model.get_int_var_from_proto_index(i) for i in range(5728)]
    RUN.mkdir(parents=True)
    prep.dump(
        HERE / "runner-preflight.json",
        {
            "passed": True,
            "optimizer_calls_before_run": 0,
            "gate_path": str(args.gate.resolve()),
            "gate_sha256": args.gate_sha256,
            **expected,
            "hint_vector_check": vector_check,
        },
    )
    started = time.monotonic()
    events = []
    saved = []
    first_feasible = None
    stopped_on_actual_d2zero = False

    def save(values, objective, bound, label, elapsed):
        ids = [i for i, value in enumerate(values[:4368]) if value == 1]
        checked = prep.check_vector(model, values)
        actual = prep.recount(ids, manifest["core_rows"])
        metrics = actual["metrics"]
        require(values[:5608] == actual["values"][:5608], "exact auxiliary recount mismatch")
        require(
            all(a >= b for a, b in zip(values[5608:], actual["values"][5608:], strict=True)),
            "solver deficits below actual deficits",
        )
        require(
            checked["objective"] == objective == 561 * sum(values[5608:]) + metrics["holes"],
            "solver objective disagreement",
        )
        verification = helper.dual_verify(actual["blocks"], metrics["holes"])
        profile = helper.global_profile(actual["triple_counts"])
        qualified = metrics["D2max"] == 0 and metrics["D3"] == metrics["D4"] == 0
        qualified &= metrics["minimum_pair_count"] >= 5 and max(metrics["core_overlaps"]) <= 55
        qualified &= profile["maximum"] <= 26
        witness = RUN / f"{label}.txt"
        witness.write_text("".join(" ".join(map(str, block)) + "\n" for block in actual["blocks"]))
        vector = RUN / f"{label}-vector.json"
        prep.dump(
            vector,
            {"values": values, "canonical_values": actual["values"], "vector_check": checked},
        )
        record = {
            "label": label,
            "elapsed_seconds": elapsed,
            "solver_objective": objective,
            "best_objective_bound": bound,
            "solver_deficit_sum": sum(values[5608:]),
            "actual_metrics": metrics,
            "qualified_D2zero_hint": qualified,
            "covering_witness": metrics["holes"] == 0,
            "global_profile": profile,
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": prep.sha(witness),
            "vector_path": str(vector.relative_to(ROOT)),
            "vector_sha256": prep.sha(vector),
            "verification": verification,
            "pair_details": actual["pair_details"],
        }
        receipt = RUN / f"{label}-receipt.json"
        prep.dump(receipt, record)
        summary = {
            key: record[key]
            for key in (
                "label",
                "elapsed_seconds",
                "solver_objective",
                "best_objective_bound",
                "solver_deficit_sum",
                "actual_metrics",
                "qualified_D2zero_hint",
                "covering_witness",
                "witness_path",
                "witness_sha256",
                "vector_path",
                "vector_sha256",
            )
        }
        summary.update(
            {"receipt_path": str(receipt.relative_to(ROOT)), "receipt_sha256": prep.sha(receipt)}
        )
        saved.append(summary)
        return qualified

    class SaveEvery(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            nonlocal first_feasible, stopped_on_actual_d2zero
            elapsed = time.monotonic() - started
            if first_feasible is None:
                first_feasible = elapsed
            number = len(events) + 1
            values = [self.value(variable) for variable in variables]
            objective, bound = self.objective_value, self.best_objective_bound
            qualified = save(values, objective, bound, f"callback-{number:04d}", elapsed)
            event = {
                "number": number,
                "elapsed_seconds": elapsed,
                "solver_objective": objective,
                "actual": saved[-1]["actual_metrics"],
                "qualified_D2zero_hint": qualified,
            }
            events.append(event)
            with (RUN / "callbacks.jsonl").open("a") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
            if qualified:
                stopped_on_actual_d2zero = True
                self.stop_search()

    callback = SaveEvery()
    log_path = RUN / "solver.log"
    with log_path.open("x") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.solve(model, callback)
    elapsed = time.monotonic() - started
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = [solver.value(variable) for variable in variables]
        save(values, solver.objective_value, solver.best_objective_bound, "final", elapsed)
    (RUN / "response.pbtxt").write_text(str(solver.response_proto))
    (RUN / "response-stats.txt").write_text(solver.response_stats() + "\n")
    result = {
        "status": solver.status_name(status),
        "optimizer_calls": 1,
        "elapsed_seconds": elapsed,
        "solver_wall_seconds": solver.wall_time,
        "first_feasible_seconds": first_feasible,
        "callbacks": len(events),
        "saved_states": saved,
        "stopped_on_actual_D2zero": stopped_on_actual_d2zero,
        "objective_bound": solver.best_objective_bound,
        "manifest_sha256": prep.sha(manifest_path),
        "gate_sha256": args.gate_sha256,
        "source_sha256": prep.sha(__file__),
        "raw_directory": str(RUN.relative_to(ROOT)),
        "raw_files": {
            str(path.relative_to(ROOT)): prep.sha(path)
            for path in sorted(RUN.iterdir())
            if path.is_file()
        },
        "scope": "Constructive soft-pair search; UNKNOWN is inconclusive; no global proof.",
    }
    prep.dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "callbacks": len(events),
                "actual_D2zero": stopped_on_actual_d2zero,
                "result_sha256": prep.sha(HERE / "result.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
