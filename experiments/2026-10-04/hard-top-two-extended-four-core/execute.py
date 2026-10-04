# Document:    Gated Hard Top-Two Extended Four-Core Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6795d87d369aef61a65bef2ee66088322c3004d3763aa89dac1709c9fbcf73ce
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One hash-gated run; save every reported vector and stop only on an actual cover."""

import argparse
import hashlib
import importlib.util
import json
import time
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "experiments/scratch/hard-top-two-extended-four-core-run-20261004"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def check_vector(model, values):
    require(len(values) == 7408 == len(model.proto.variables), "incomplete vector")
    for index, (variable, value) in enumerate(zip(model.proto.variables, values, strict=True)):
        domain = list(variable.domain)
        require(
            type(value) is int
            and any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"variable domain violation {index}",
        )
    enforced = 0
    for index, row in enumerate(model.proto.constraints):
        require(row.has_linear(), f"unexpected row type {index}")
        active = all(
            values[lit] == 1 if lit >= 0 else values[-lit - 1] == 0
            for lit in row.enforcement_literal
        )
        if not active:
            continue
        enforced += 1
        value = sum(
            coefficient * values[var]
            for var, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
        )
        domain = list(row.linear.domain)
        require(
            any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"linear row violation {index}",
        )
    objective = model.proto.objective
    value = objective.scaling_factor * (
        objective.offset
        + sum(
            coefficient * values[var]
            for var, coefficient in zip(objective.vars, objective.coeffs, strict=True)
        )
    )
    return {
        "variables_checked": len(values),
        "rows_checked": len(model.proto.constraints),
        "enforced_rows_checked": enforced,
        "objective": value,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    require(not RUN.exists() and not (HERE / "result.json").exists(), "run already exists")
    manifest_path, runner_path = HERE / "manifest.json", HERE / "runner-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    runner = json.loads(runner_path.read_text())
    require(sha(args.gate) == args.gate_sha256, "gate hash mismatch")
    gate = json.loads(args.gate.read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required")
    expected = {
        "manifest_sha256": sha(manifest_path),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "guidance_sha256": manifest["guidance_sha256"],
        "runner_sha256": sha(__file__),
        "runner_manifest_sha256": sha(runner_path),
    }
    for key, value in expected.items():
        require(gate.get(key) == value, f"gate binding mismatch: {key}")
    require(runner["manifest_sha256"] == sha(manifest_path), "runner model binding mismatch")
    for relative, digest in {**manifest["sources"], **runner["sources"]}.items():
        require(sha(ROOT / relative) == digest, f"source changed: {relative}")
    for kind in ("model", "parameters", "guidance"):
        require(
            sha(ROOT / manifest[f"{kind}_path"]) == manifest[f"{kind}_sha256"],
            f"frozen {kind} changed",
        )
    for relative, digest in manifest["proof_bindings"].items():
        require(sha(HERE.parent / relative) == digest, f"proof binding changed: {relative}")
    helper_path = HERE.parent / "pair-top-two-readonly-plan-v2/derive_hint.py"
    spec = importlib.util.spec_from_file_location("hard_top_two_helper", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(helper.load_sources() == manifest["core_rows"], "core support mismatch")
    model = cp_model.CpModel()
    require(
        model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text()),
        "model parse failed",
    )
    require(not model.validate(), "model validation failed")
    require(
        len(model.proto.variables) == 7408 and len(model.proto.constraints) == 3605, "model size"
    )
    guidance = json.loads((ROOT / manifest["guidance_path"]).read_text())
    require(
        list(model.proto.solution_hint.vars) == guidance["variable_indices"] == list(range(4368)),
        "guidance indices mismatch",
    )
    require(
        list(model.proto.solution_hint.values) == guidance["values"], "guidance values mismatch"
    )
    require(guidance["feasible_warm_start"] is False, "guidance misclassified")
    require(sha(ROOT / guidance["candidate_path"]) == guidance["candidate_sha256"], "H49 changed")
    solver = cp_model.CpSolver()
    require(
        solver.parameters.parse_text_format((ROOT / manifest["parameters_path"]).read_text()),
        "parameter parse failed",
    )
    require(
        solver.parameters.max_time_in_seconds == 120
        and solver.parameters.num_search_workers == 4
        and solver.parameters.random_seed == 2026104601,
        "budget or seed changed",
    )
    variables = [model.get_int_var_from_proto_index(index) for index in range(7408)]
    RUN.mkdir(parents=True)
    dump(
        HERE / "runner-preflight.json",
        {
            "passed": True,
            "optimizer_calls_before_run": 0,
            "gate_path": str(args.gate.resolve()),
            "gate_sha256": args.gate_sha256,
            **expected,
            "hint_entries": 4368,
            "hint_classification": "infeasible block-only H49 guidance",
        },
    )
    started = time.monotonic()
    events, saved = [], []
    first_feasible = None
    stopped_on_cover = False

    def save(values, objective, bound, label, elapsed):
        checked = check_vector(model, values)
        require(checked["objective"] == objective == sum(values[5048:5608]), "objective mismatch")
        ids = [index for index, value in enumerate(values[:4368]) if value == 1]
        require(len(ids) == 64, "candidate cardinality")
        witness = RUN / f"{label}.txt"
        witness.write_text(
            "".join(" ".join(map(str, helper.SETS[5][index])) + "\n" for index in ids)
        )
        diagnostic, canonical = helper.derive(witness)
        require(
            canonical is not None and diagnostic["qualified"], "independent recount rejected state"
        )
        require(values[:5608] == canonical["values"][:5608], "exact count/hole mismatch")
        require(
            diagnostic["holes"] == objective and diagnostic["D2max"] == 0, "actual metric mismatch"
        )
        diagnostic.pop("objective")
        is_cover = diagnostic["holes"] == 0
        require(
            canonical["verification"]["package"]["valid"] == is_cover
            and canonical["verification"]["standalone"]["valid"] == is_cover,
            "dual covering verifier mismatch",
        )
        vector = RUN / f"{label}-vector.json"
        dump(
            vector,
            {"values": values, "canonical_values": canonical["values"], "vector_check": checked},
        )
        record = {
            "label": label,
            "elapsed_seconds": elapsed,
            "solver_objective": objective,
            "best_objective_bound": bound,
            "actual_metrics": diagnostic,
            "qualified_D2zero_hint": True,
            "covering_witness": is_cover,
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": sha(witness),
            "vector_path": str(vector.relative_to(ROOT)),
            "vector_sha256": sha(vector),
            "verification": canonical["verification"],
            "pair_details": canonical["per_pair"],
        }
        receipt = RUN / f"{label}-receipt.json"
        dump(receipt, record)
        summary = {
            key: record[key]
            for key in (
                "label",
                "elapsed_seconds",
                "solver_objective",
                "best_objective_bound",
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
            {"receipt_path": str(receipt.relative_to(ROOT)), "receipt_sha256": sha(receipt)}
        )
        saved.append(summary)
        return is_cover

    class SaveEvery(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            nonlocal first_feasible, stopped_on_cover
            elapsed = time.monotonic() - started
            if first_feasible is None:
                first_feasible = elapsed
            number = len(events) + 1
            values = [self.value(variable) for variable in variables]
            objective, bound = self.objective_value, self.best_objective_bound
            is_cover = save(values, objective, bound, f"callback-{number:04d}", elapsed)
            event = {
                "number": number,
                "elapsed_seconds": elapsed,
                "solver_objective": objective,
                "actual_metrics": saved[-1]["actual_metrics"],
                "covering_witness": is_cover,
            }
            events.append(event)
            with (RUN / "callbacks.jsonl").open("a") as handle:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
            if is_cover:
                stopped_on_cover = True
                self.stop_search()

    with (RUN / "solver.log").open("x") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.solve(model, SaveEvery())
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
        "stopped_on_actual_cover": stopped_on_cover,
        "objective_bound": solver.best_objective_bound,
        "manifest_sha256": sha(manifest_path),
        "runner_manifest_sha256": sha(runner_path),
        "gate_sha256": args.gate_sha256,
        "source_sha256": sha(__file__),
        "raw_directory": str(RUN.relative_to(ROOT)),
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(RUN.iterdir())
            if path.is_file()
        },
        "guidance": "infeasible block-only H49; no feasible warm start",
        "scope": "Hard necessary-cut search; UNKNOWN inconclusive; no checked theorem.",
    }
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "callbacks": len(events),
                "actual_cover": stopped_on_cover,
                "result_sha256": sha(HERE / "result.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
