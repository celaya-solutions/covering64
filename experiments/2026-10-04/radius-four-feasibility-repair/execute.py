# Document:    Gated Radius-Four Feasibility Repair Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bf66d5bf0f609a01f01744e8f2124c9c9e013693bde11face46023bc8017b9a8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One independently gated feasibility call under an outer watchdog."""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "experiments/scratch/radius-four-feasibility-repair-run-20261004"


def load_preparer():
    spec = importlib.util.spec_from_file_location("radius_four_preparer", HERE / "prepare.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def preflight(args, prep):
    require = prep.require
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(prep.sha(args.gate) == args.gate_sha256, "gate hash mismatch")
    gate = json.loads(args.gate.read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required")
    expected = {
        "manifest_sha256": prep.sha(manifest_path),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "runner_sha256": prep.sha(__file__),
    }
    for key, value in expected.items():
        require(gate.get(key) == value, f"gate binding mismatch: {key}")
    for group in ("sources", "input_files", "files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(prep.sha(ROOT / relative) == digest, f"frozen file changed: {relative}")
    require(prep.helper_module().load_sources() == manifest["core_rows"], "core rows changed")
    model = cp_model.CpModel()
    require(
        model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text()), "model parse"
    )
    require(not model.validate(), "model validation failed")
    require(not list(model.proto.solution_hint.vars), "unexpected hint variables")
    require(not list(model.proto.solution_hint.values), "unexpected hint values")
    require(not model.has_objective(), "unexpected objective")
    require(
        len(model.proto.variables) == 5728 and len(model.proto.constraints) == 14407,
        "model size changed",
    )
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / manifest["parameters_path"]).read_text()),
        "parameter parse",
    )
    return manifest, expected, model, solver


def inner(args, prep, manifest, expected, model, solver):
    require = prep.require
    launch = json.loads((RUN / "launch.json").read_text())
    require(launch["parent_pid"] == os.getppid(), "inner launch must be watchdog child")
    require(launch["gate_sha256"] == args.gate_sha256, "inner gate mismatch")
    require(launch["manifest_sha256"] == expected["manifest_sha256"], "inner manifest mismatch")
    require(not (RUN / "inner-started.json").exists(), "inner already started")
    prep.dump(RUN / "inner-started.json", {"pid": os.getpid(), "optimizer_calls_before_run": 0})
    helper = prep.helper_module()
    variables = [model.get_int_var_from_proto_index(i) for i in range(5728)]
    started = time.monotonic()
    saved, events = [], []
    first_feasible = None
    stopped_on_actual_cover = False

    def save(values, label, elapsed):
        checked = prep.check_vector(model, values)
        ids = [i for i, value in enumerate(values[:4368]) if value == 1]
        actual = prep.recount(ids, manifest["core_rows"], manifest["baseline_ids"])
        metrics = actual["metrics"]
        require(values[:5608] == actual["values"][:5608], "exact auxiliaries disagree")
        require(
            all(a >= b for a, b in zip(values[5608:], actual["values"][5608:], strict=True)),
            "solver deficits below actual deficits",
        )
        require(metrics["holes"] <= 11 and metrics["replacement_distance"] <= 4, "local bounds")
        canonical_check = prep.check_vector(model, actual["values"])
        verification = helper.dual_verify(actual["blocks"], metrics["holes"])
        cover = metrics["holes"] == 0
        require(
            all(verification[k]["valid"] is cover for k in ("package", "standalone")),
            "dual cover classification",
        )
        witness = RUN / f"{label}.txt"
        with witness.open("x") as handle:
            handle.write("".join(" ".join(map(str, b)) + "\n" for b in actual["blocks"]))
        vector = RUN / f"{label}-vector.json"
        prep.dump(
            vector,
            {
                "values": values,
                "canonical_values": actual["values"],
                "vector_check": checked,
                "canonical_vector_check": canonical_check,
            },
        )
        record = {
            "label": label,
            "elapsed_seconds": elapsed,
            "actual_metrics": metrics,
            "solver_deficit_sum": sum(values[5608:]),
            "cover_found": cover,
            "feasible_partial": not cover,
            "feasibility_target_met": True,
            "global_profile": helper.global_profile(actual["triple_counts"]),
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
            key: value
            for key, value in record.items()
            if key not in ("verification", "pair_details", "global_profile")
        }
        summary.update(
            {"receipt_path": str(receipt.relative_to(ROOT)), "receipt_sha256": prep.sha(receipt)}
        )
        saved.append(summary)
        return cover

    class SaveEvery(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            nonlocal first_feasible, stopped_on_actual_cover
            elapsed = time.monotonic() - started
            if first_feasible is None:
                first_feasible = elapsed
            number = len(events) + 1
            cover = save([self.value(v) for v in variables], f"callback-{number:04d}", elapsed)
            event = {
                "number": number,
                "elapsed_seconds": elapsed,
                "actual_metrics": saved[-1]["actual_metrics"],
                "cover_found": cover,
                "feasible_partial": not cover,
            }
            events.append(event)
            with (RUN / "callbacks.jsonl").open("a") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
            if cover:
                stopped_on_actual_cover = True
                self.stop_search()

    callback = SaveEvery()
    with (RUN / "solver.log").open("x") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.solve(model, callback)
    elapsed = time.monotonic() - started
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        save([solver.value(v) for v in variables], "final", elapsed)
    (RUN / "response.pbtxt").write_text(str(solver.response_proto))
    (RUN / "response-stats.txt").write_text(solver.response_stats() + "\n")
    prep.dump(
        RUN / "child-result.json",
        {
            "status": solver.status_name(status),
            "optimizer_calls": 1,
            "elapsed_seconds": elapsed,
            "solver_wall_seconds": solver.wall_time,
            "first_feasible_seconds": first_feasible,
            "callbacks": len(events),
            "saved_states": saved,
            "cover_found": any(row["cover_found"] for row in saved),
            "feasible_partial_found": any(row["feasible_partial"] for row in saved),
            "feasibility_target_met": bool(saved),
            "stopped_on_actual_cover": stopped_on_actual_cover,
            **expected,
            "gate_sha256": args.gate_sha256,
            "objective": None,
            "scope": manifest["scope"],
        },
    )


def outer(args, prep, manifest, expected):
    require = prep.require
    require(not RUN.exists() and not (HERE / "result.json").exists(), "run already exists")
    RUN.mkdir(parents=True)
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--gate",
        str(args.gate.resolve()),
        "--gate-sha256",
        args.gate_sha256,
        "--execute",
        "--inner",
    ]
    prep.dump(
        RUN / "launch.json",
        {
            "parent_pid": os.getpid(),
            "command": command,
            "gate_sha256": args.gate_sha256,
            **expected,
        },
    )
    prep.dump(
        HERE / "runner-preflight.json",
        {
            "passed": True,
            "optimizer_calls_before_run": 0,
            "gate_sha256": args.gate_sha256,
            **expected,
        },
    )
    watchdog = {
        "deadline_seconds": 330,
        "grace_seconds": 5,
        "fired": False,
        "terminate_sent": False,
        "kill_sent": False,
        "relaunch": False,
    }
    started = time.monotonic()
    with (RUN / "stdout.txt").open("x") as stdout, (RUN / "stderr.txt").open("x") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        try:
            process.wait(timeout=330)
        except subprocess.TimeoutExpired:
            watchdog["fired"] = watchdog["terminate_sent"] = True
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                watchdog["kill_sent"] = True
                process.kill()
                process.wait()
    child_path = RUN / "child-result.json"
    child = json.loads(child_path.read_text()) if child_path.exists() else None
    saved = [] if child is None else child["saved_states"]
    if child is None:
        for path in sorted(RUN.glob("*-receipt.json")):
            try:
                row = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            saved.append(
                {
                    key: value
                    for key, value in row.items()
                    if key not in ("verification", "pair_details", "global_profile")
                }
                | {"receipt_path": str(path.relative_to(ROOT)), "receipt_sha256": prep.sha(path)}
            )
    terminal = child["status"] if child is not None else "ERROR"
    if watchdog["fired"]:
        terminal = "WATCHDOG_TIMEOUT"
    elif process.returncode != 0:
        terminal = "ERROR"
    result = {
        "status": terminal,
        "child_result": child,
        "watchdog": watchdog,
        "returncode": process.returncode,
        "outer_elapsed_seconds": time.monotonic() - started,
        "single_child_launches": 1,
        "relaunch": False,
        "budget_transfer": False,
        "optimizer_calls": 1 if child is not None else None,
        "optimizer_call_upper_bound": 1,
        "saved_states": saved,
        "cover_found": any(row["cover_found"] for row in saved),
        "feasible_partial_found": any(row["feasible_partial"] for row in saved),
        "feasibility_target_met": bool(saved),
        "objective": None,
        "manifest_sha256": expected["manifest_sha256"],
        "gate_sha256": args.gate_sha256,
        "raw_directory": str(RUN.relative_to(ROOT)),
        "raw_files": {
            str(path.relative_to(ROOT)): prep.sha(path)
            for path in sorted(RUN.iterdir())
            if path.is_file()
        },
        "scope": manifest["scope"],
    }
    prep.dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "status": terminal,
                "cover_found": result["cover_found"],
                "feasible_partial_found": result["feasible_partial_found"],
                "result_sha256": prep.sha(HERE / "result.json"),
            },
            sort_keys=True,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--inner", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    prep = load_preparer()
    manifest, expected, model, solver = preflight(args, prep)
    if args.inner:
        inner(args, prep, manifest, expected, model, solver)
    else:
        outer(args, prep, manifest, expected)


if __name__ == "__main__":
    main()
