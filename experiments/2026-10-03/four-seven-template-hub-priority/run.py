# Document:    Frozen Template Hull Plus Hub-Count Priority Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      06d1f9968af37f68dc46f2dd42044e9e7514493b1d4bebded822f8b24ec180e1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Screen the one unexcluded hub case of each of 23 priority first-link types."""

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from itertools import combinations
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTIFACTS = REPO / "experiments/2026-10-03"
PREVIOUS_SHA256 = "c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e"
PLAN_SHA256 = "9653d367494c23fe4018990aa7ad142b1ccf9d0a495b634049f395a31912772c"
HULL_ROWS = 4550
BASE_ROWS = 4552
HUBS = frozenset((4, 8, 12, 16))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_module():
    path = HERE / "previous-runner.py"
    if not path.exists():
        path = ARTIFACTS / "four-seven-template-link-screen/run.py"
    require(digest(path) == PREVIOUS_SHA256, "previous runner hash")
    spec = importlib.util.spec_from_file_location("frozen_template_link_screen", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


PREVIOUS, PREVIOUS_PATH = previous_module()


def hub_rows(m4, z):
    require(type(m4) is type(z) is int and m4 in (0, 1) and z in (0, 1, 2), "hub case")
    counts = [len(set(block) & HUBS) for block in combinations(range(1, 17), 5)]
    four = [i for i, count in enumerate(counts) if count == 4]
    triple = [(i, math.comb(count, 3)) for i, count in enumerate(counts) if count >= 3]
    return [
        [four, [1] * len(four), m4, m4],
        [[i for i, _ in triple], [v for _, v in triple], 4 + z, 4 + z],
    ]


class CombinedHull(PREVIOUS.ReusableHull):
    """Reuse the frozen solver/reset methods, with two immutable hub rows."""

    def __init__(self, payload, m4, z, phase_one=False):
        require(len(payload["rows"]) == HULL_ROWS, "exact frozen hull row count")
        self.width = payload["width"]
        self.phase_one = phase_one
        self.hub_case = [m4, z]
        self.hub_equalities = hub_rows(m4, z)
        self.rows = [*payload["rows"], *self.hub_equalities]
        self.solver = pywraplp.Solver.CreateSolver("GLOP")
        require(self.solver is not None, "GLOP unavailable")
        self.variables = [self.solver.NumVar(0, 1, f"x{i}") for i in range(self.width)]
        self.constraints = []
        for index, (ids, coefficients, lower, upper) in enumerate(self.rows):
            row = self.solver.RowConstraint(
                lower if lower is not None else -self.solver.infinity(),
                upper if upper is not None else self.solver.infinity(),
                f"row_{index}",
            )
            for column, coefficient in zip(ids, coefficients, strict=True):
                row.SetCoefficient(self.variables[column], coefficient)
            self.constraints.append(row)
        self.fixed_rows, self.slacks = [], []
        for i in range(7):
            row = self.solver.RowConstraint(0, 0, f"fixed_block_{i}")
            if phase_one:
                lower = self.solver.NumVar(0, self.solver.infinity(), f"fixed_slack_lower_{i}")
                upper = self.solver.NumVar(0, self.solver.infinity(), f"fixed_slack_upper_{i}")
                self.solver.Objective().SetCoefficient(lower, 1)
                self.solver.Objective().SetCoefficient(upper, 1)
                self.slacks.append((lower, upper))
            self.fixed_rows.append(row)
            self._clear_row(i)
        self.solver.Objective().SetMinimization()
        self.active = None
        exported = self.export()
        del exported.constraint[BASE_ROWS:]
        self.prefix_bytes = exported.SerializeToString(deterministic=True)
        self.prefix_sha256 = hashlib.sha256(self.prefix_bytes).hexdigest()
        self.audit(None)

    def audit(self, fixed_ids):
        proto = self.export()
        require(len(proto.constraint) == 4559, "exact combined constraint count")
        require(len(proto.variable) == self.width + (14 if self.phase_one else 0), "variable count")
        summaries = []
        for i, row in enumerate(proto.constraint[BASE_ROWS:]):
            expected = []
            if self.phase_one:
                expected.extend(((self.width + 2 * i, 1), (self.width + 2 * i + 1, -1)))
            if fixed_ids is not None:
                expected.append((fixed_ids[i], 1))
            actual = sorted(zip(row.var_index, row.coefficient, strict=True))
            require(actual == sorted(expected), "fixed-row coefficients")
            value = 1 if fixed_ids is not None else 0
            require(row.lower_bound == row.upper_bound == value, "fixed-row bounds")
            require(row.name == f"fixed_block_{i}", "fixed-row name")
            summaries.append(
                dict(row_index=BASE_ROWS + i, coefficients=actual, lower=value, upper=value)
            )
        del proto.constraint[BASE_ROWS:]
        require(
            hashlib.sha256(proto.SerializeToString(deterministic=True)).hexdigest()
            == self.prefix_sha256,
            "frozen hull, hub rows, variables or objective changed",
        )
        return dict(
            prefix_sha256=self.prefix_sha256,
            hub_case=self.hub_case,
            active_fixed_ids=fixed_ids,
            phase_one=self.phase_one,
            fixed_rows=summaries,
        )


def prepare():
    plan_path = ARTIFACTS / "four-seven-template-hub-priority/priority-plan.json"
    require(digest(plan_path) == PLAN_SHA256, "frozen priority plan")
    plan = json.loads(plan_path.read_text())
    for path_key, hash_key in (
        ("source_hub_audit", "source_hub_audit_sha256"),
        ("source_template_summary", "source_template_summary_sha256"),
        ("hub_partition_audit", "hub_partition_audit_sha256"),
    ):
        require(digest(REPO / plan[path_key]) == plan[hash_key], f"changed {path_key}")
    hub_audit = json.loads((REPO / plan["source_hub_audit"]).read_text())
    summary = json.loads((REPO / plan["source_template_summary"]).read_text())
    require(hub_audit["passed"] and summary["complete"], "source audits")
    all_cases = {tuple(c) for c in hub_audit["checked_hub_cases"]}
    for name, checksum in plan["prior_child_audit_sha256"].items():
        require(
            digest(ARTIFACTS / "four-seven-hub-count-screen" / f"{name}-audit.json") == checksum,
            "prior conditional audit changed",
        )
    expected = []
    for identifier in summary["open_ids"]:
        excluded = hub_audit["case_exclusions_by_id"][identifier]
        if len(excluded) == 5:
            remaining = sorted(all_cases - {tuple(c) for c in excluded})
            expected.append(
                dict(
                    id=identifier,
                    case=identifier.split("-")[0],
                    hub_case=list(remaining[0]),
                    previously_excluded_hub_cases=excluded,
                )
            )
    require(plan["priority"] == expected and len(expected) == 23, "exact priority selection")
    manifest, cases, input_hashes = PREVIOUS.load_inputs(
        REPO / "experiments/scratch/four-seven-template-hull-20261003",
        ARTIFACTS / "four-seven-blossom-screen/remaining-representatives.json",
        ARTIFACTS / "four-seven-template-hull/independent-audit.json",
    )
    by_id = {r["id"]: r for case in cases.values() for r in case["representatives"]}
    prepared = [{**r, "fixed_ids": by_id[r["id"]]["fixed_ids"]} for r in expected]
    return plan, manifest, cases, input_hashes, prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    require(math.isfinite(args.seconds) and 0 < args.seconds <= 15, "solver budget")
    require(not args.output.exists(), "output directory must be new")
    preflight = json.loads(args.preflight.read_text())
    require(
        preflight["valid"] and preflight["runner_sha256"] == digest(Path(__file__)),
        "successful preflight of this frozen source required",
    )
    plan, manifest, cases, inputs, selected = prepare()
    helpers, utility_path = PREVIOUS.utilities()
    output = args.output
    output.mkdir(parents=True)
    for name, path in (
        ("run.py", Path(__file__)),
        ("previous-runner.py", PREVIOUS_PATH),
        ("whole-hull-utilities.py", utility_path),
        ("preflight.json", args.preflight),
        ("check_cover.py", REPO / "scripts/check_cover.py"),
        ("core.py", Path(helpers.verify_cover.__code__.co_filename)),
    ):
        (output / name).write_bytes(path.read_bytes())
    for name, value in (("priority-plan.json", plan), ("prototype-manifest.json", manifest)):
        (output / name).write_text(json.dumps(value, indent=2) + "\n")
    metadata = dict(
        runner_sha256=digest(Path(__file__)),
        previous_runner_sha256=PREVIOUS_SHA256,
        plan_sha256=PLAN_SHA256,
        preflight_sha256=digest(args.preflight),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        ortools_version=ortools_version,
        command=sys.argv,
        input_hashes=inputs,
        seconds_per_representative=args.seconds,
        models={},
    )
    models, results = {}, []
    for selected_case in selected:
        case, (m4, z), fixed = (
            selected_case["case"],
            selected_case["hub_case"],
            selected_case["fixed_ids"],
        )
        key = f"{case}-m4-{m4}-z-{z}"
        directory = output / key
        if key not in models:
            directory.mkdir()
            model = CombinedHull(cases[case]["payload"], m4, z)
            models[key] = [model, None]
            PREVIOUS.save_compressed(
                directory / "combined-base-rows.json.gz",
                dict(
                    width=model.width,
                    rows=model.rows,
                    variable_bounds="Every variable lies in [0,1].",
                ),
            )
            (directory / "feasibility-base.pb.gz").write_bytes(
                gzip.compress(model.prefix_bytes, mtime=0)
            )
            metadata["models"][key] = dict(
                width=model.width,
                original_rows=HULL_ROWS,
                hub_rows=model.hub_equalities,
                base_rows=BASE_ROWS,
                fixed_rows=7,
                original_matrix_sha256=digest(cases[case]["matrix_path"]),
                combined_matrix_sha256=digest(directory / "combined-base-rows.json.gz"),
                feasibility_prefix_sha256=model.prefix_sha256,
            )
        model, phase_model = models[key]
        target = directory / selected_case["id"]
        target.mkdir()
        fixed_rows = [[[i], [1], 1, 1] for i in fixed]
        full_rows = [*model.rows, *fixed_rows]
        (target / "fixed-rows.json").write_text(
            json.dumps(
                dict(
                    id=selected_case["id"],
                    case=case,
                    hub_case=[m4, z],
                    width=model.width,
                    combined_matrix_sha256=metadata["models"][key]["combined_matrix_sha256"],
                    rows=fixed_rows,
                ),
                indent=2,
            )
            + "\n"
        )
        before = model.fix(fixed)
        try:
            feasibility, primal, _ = model.solve(args.seconds, target / "feasibility-solver.log")
        finally:
            reset = model.reset()
        result = dict(
            **selected_case,
            checked_rows=4559,
            checked_columns=model.width,
            feasibility_lp=feasibility,
            fixed_state_audit=before,
            reset_audit=reset,
            certificate_pending_replay=False,
            independently_excluded=False,
        )
        if primal is not None:
            result["primal_metrics"] = helpers.primal_metrics(primal, full_rows)
            PREVIOUS.save_compressed(
                target / "sparse-primal.json.gz",
                dict(
                    width=model.width,
                    values=[[i, v] for i, v in enumerate(primal) if v != 0],
                    zero_default=True,
                    fixed_ids=fixed,
                    combined_matrix_sha256=metadata["models"][key]["combined_matrix_sha256"],
                ),
            )
            result["sparse_primal_sha256"] = digest(target / "sparse-primal.json.gz")
            result["integral_blocks"] = helpers.check_integral_blocks(
                primal, target, output / "check_cover.py"
            )
        elif feasibility["status"] == pywraplp.Solver.INFEASIBLE:
            remaining = max(0, args.seconds - feasibility["solve_seconds"])
            if remaining >= 0.001:
                if phase_model is None:
                    phase_model = CombinedHull(cases[case]["payload"], m4, z, phase_one=True)
                    models[key][1] = phase_model
                    (directory / "phase-one-base.pb.gz").write_bytes(
                        gzip.compress(phase_model.prefix_bytes, mtime=0)
                    )
                    metadata["models"][key]["phase_one_prefix_sha256"] = phase_model.prefix_sha256
                phase_model.fix(fixed)
                try:
                    phase, _, dual = phase_model.solve(remaining, target / "phase-one-solver.log")
                finally:
                    phase_reset = phase_model.reset()
                result["phase_one_lp"] = phase
                result["phase_one_reset_audit"] = phase_reset
                if dual is not None:
                    PREVIOUS.save_compressed(target / "phase-one-dual.json.gz", dict(weights=dual))
                    result["certificate_attempts"] = []
                    for denominator in (1_000_000, 1_000_000_000):
                        certificate = helpers.integer_certificate(
                            full_rows, model.width, dual, denominator
                        )
                        path = target / f"certificate-{denominator}.json"
                        path.write_text(json.dumps(certificate, indent=2) + "\n")
                        result["certificate_attempts"].append(
                            dict(
                                file=path.name,
                                sha256=digest(path),
                                gap=certificate["gap"],
                                exact_gap_positive=certificate["proves_infeasible"],
                            )
                        )
                        if certificate["proves_infeasible"]:
                            result["certificate_pending_replay"] = True
                            break
        result["solve_seconds_total"] = feasibility["solve_seconds"] + result.get(
            "phase_one_lp", {}
        ).get("solve_seconds", 0)
        (target / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        PREVIOUS.save_compressed(output / "results.json.gz", results)
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(
            json.dumps(
                dict(
                    id=result["id"],
                    hub_case=[m4, z],
                    status=feasibility["status_name"],
                    pending_certificate=result["certificate_pending_replay"],
                    solve_seconds=result["solve_seconds_total"],
                )
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
