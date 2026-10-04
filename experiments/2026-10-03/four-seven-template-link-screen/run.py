# Document:    Bounded Fixed-Link Screen with Complete Surviving Template Hulls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ab81569639466747c7fcfd86f0c2398c2f9e99addabdf39a60f357232448e1be
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools
from ortools.linear_solver import linear_solver_pb2, pywraplp

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTIFACTS = REPO / "experiments/2026-10-03"
UTILITIES_SHA256 = "c6b67b22660707c701ae038db497e81fded3c647e9f1978873b5e27da573afcf"
MANIFEST_SHA256 = "21c243c87f44aebe780d8a48e330684d5fcaefbc2a587fa236516d64d8cfc38a"
BASE_ROWS = 4550
FIXED_COUNT = 7


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compressed(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def save_compressed(path, value):
    path.write_bytes(
        gzip.compress((json.dumps(value, separators=(",", ":")) + "\n").encode(), mtime=0)
    )


def utilities():
    path = HERE / "whole-hull-utilities.py"
    if not path.exists():
        path = ARTIFACTS / "four-seven-template-hull/run_lp.py"
    require(digest(path) == UTILITIES_SHA256, "frozen whole-hull utilities changed")
    specification = importlib.util.spec_from_file_location("frozen_whole_hull_utilities", path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module, path


class ReusableHull:
    """Only seven fixed rows change; the complete original prefix is hashed each time."""

    def __init__(self, payload, phase_one=False):
        self.width = payload["width"]
        self.phase_one = phase_one
        self.solver = pywraplp.Solver.CreateSolver("GLOP")
        require(self.solver is not None, "GLOP unavailable")
        self.variables = [self.solver.NumVar(0, 1, f"x{i}") for i in range(self.width)]
        self.constraints = []
        for index, (ids, coefficients, lower, upper) in enumerate(payload["rows"]):
            row = self.solver.RowConstraint(
                lower if lower is not None else -self.solver.infinity(),
                upper if upper is not None else self.solver.infinity(),
                f"row_{index}",
            )
            for column, coefficient in zip(ids, coefficients, strict=True):
                row.SetCoefficient(self.variables[column], coefficient)
            self.constraints.append(row)
        require(len(self.constraints) == BASE_ROWS, "wrong original constraint count")
        self.fixed_rows = []
        self.slacks = []
        for i in range(FIXED_COUNT):
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

    def export(self):
        proto = linear_solver_pb2.MPModelProto()
        self.solver.ExportModelToProto(proto)
        return proto

    def _clear_row(self, index):
        row = self.fixed_rows[index]
        row.Clear()
        row.SetBounds(0, 0)
        if self.phase_one:
            lower, upper = self.slacks[index]
            row.SetCoefficient(lower, 1)
            row.SetCoefficient(upper, -1)

    def audit(self, fixed_ids):
        proto = self.export()
        require(len(proto.constraint) == BASE_ROWS + FIXED_COUNT, "unexpected constraint count")
        require(
            len(proto.variable) == self.width + (14 if self.phase_one else 0),
            "unexpected variable count",
        )
        suffix = proto.constraint[BASE_ROWS:]
        summaries = []
        for i, row in enumerate(suffix):
            expected = []
            if self.phase_one:
                expected.extend(((self.width + 2 * i, 1), (self.width + 2 * i + 1, -1)))
            if fixed_ids is not None:
                expected.append((fixed_ids[i], 1))
            actual = sorted(zip(row.var_index, row.coefficient, strict=True))
            require(actual == sorted(expected), "stale or damaged fixed-row coefficient")
            value = 1 if fixed_ids is not None else 0
            require(row.lower_bound == row.upper_bound == value, "stale or damaged fixed-row bound")
            require(row.name == f"fixed_block_{i}", "fixed-row name mismatch")
            summaries.append(
                dict(row_index=BASE_ROWS + i, coefficients=actual, lower=value, upper=value)
            )
        del proto.constraint[BASE_ROWS:]
        require(
            hashlib.sha256(proto.SerializeToString(deterministic=True)).hexdigest()
            == self.prefix_sha256,
            "original variables, objective or constraints changed",
        )
        return dict(
            prefix_sha256=self.prefix_sha256,
            active_fixed_ids=fixed_ids,
            phase_one=self.phase_one,
            fixed_rows=summaries,
        )

    def fix(self, ids):
        require(self.active is None, "must reset before fixing another representative")
        require(
            len(ids) == FIXED_COUNT
            and len(set(ids)) == FIXED_COUNT
            and all(type(i) is int and 0 <= i < 4368 for i in ids),
            "seven distinct block IDs required",
        )
        self.audit(None)
        for i, block in enumerate(ids):
            self._clear_row(i)
            self.fixed_rows[i].SetCoefficient(self.variables[block], 1)
            self.fixed_rows[i].SetBounds(1, 1)
        self.active = list(ids)
        return self.audit(self.active)

    def reset(self):
        for i in range(FIXED_COUNT):
            self._clear_row(i)
        self.active = None
        return self.audit(None)

    def solve(self, seconds, log_path):
        require(self.active is not None, "representative must be fixed before solving")
        require(math.isfinite(seconds) and seconds > 0, "positive finite solver budget")
        self.audit(self.active)
        self.solver.SetTimeLimit(max(1, math.floor(seconds * 1000)))
        saved = [os.dup(1), os.dup(2)]
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            with log_path.open("w") as log:
                os.dup2(log.fileno(), 1)
                os.dup2(log.fileno(), 2)
                self.solver.EnableOutput()
                start = time.monotonic()
                status = self.solver.Solve()
                seconds_used = time.monotonic() - start
        finally:
            for fd, original in zip((1, 2), saved, strict=True):
                os.dup2(original, fd)
                os.close(original)
        state = self.audit(self.active)
        names = {
            self.solver.OPTIMAL: "OPTIMAL",
            self.solver.FEASIBLE: "FEASIBLE",
            self.solver.INFEASIBLE: "INFEASIBLE",
            self.solver.UNBOUNDED: "UNBOUNDED",
            self.solver.ABNORMAL: "ABNORMAL",
            self.solver.NOT_SOLVED: "NOT_SOLVED",
        }
        record = dict(
            status=int(status),
            status_name=names.get(status, "UNKNOWN_STATUS"),
            solve_seconds=seconds_used,
            allocated_seconds=seconds,
            phase_one=self.phase_one,
            model_audit=state,
            log_sha256=digest(log_path),
        )
        primal, dual = None, None
        if status in (self.solver.OPTIMAL, self.solver.FEASIBLE):
            record["objective"] = self.solver.Objective().Value()
            if self.phase_one:
                dual = [row.dual_value() for row in [*self.constraints, *self.fixed_rows]]
                require(all(math.isfinite(value) for value in dual), "nonfinite dual")
            else:
                primal = [variable.solution_value() for variable in self.variables]
                require(all(math.isfinite(value) for value in primal), "nonfinite primal")
        return record, primal, dual


def load_inputs(input_directory, representatives_path, audit_path):
    manifest_path = input_directory / "manifest.json"
    require(digest(manifest_path) == MANIFEST_SHA256, "original-100 hull manifest required")
    manifest = json.loads(manifest_path.read_text())
    audit = json.loads(audit_path.read_text())
    require(
        audit.get("valid") is True and audit.get("manifest_sha256") == MANIFEST_SHA256,
        "matrix audit required",
    )
    selected = json.loads(representatives_path.read_text())
    source_reps_path = ARTIFACTS / "four-seven-link-orbits/result.json"
    source_reps = json.loads(source_reps_path.read_text())
    require(
        digest(source_reps_path) == manifest["inputs"][str(source_reps_path.relative_to(REPO))],
        "original representative manifest hash",
    )
    full_reps = {r["id"]: r for case in source_reps["cases"] for r in case["representatives"]}
    first_audit_path = ARTIFACTS / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"
    blossom_audit_path = ARTIFACTS / "four-seven-blossom-independent/blossom-screen-audit.json"
    require(
        digest(first_audit_path) == manifest["inputs"][str(first_audit_path.relative_to(REPO))],
        "original certificate audit manifest hash",
    )
    first = json.loads(first_audit_path.read_text())
    blossom = json.loads(blossom_audit_path.read_text())
    require(
        first["complete_selected_coverage"] is True
        and first["records"] == 258
        and first["excluded"] == 100,
        "original full first-link audit required",
    )
    require(
        blossom["complete_selected_coverage"] is True
        and blossom["records"] == 158
        and blossom["excluded"] == 2,
        "complete blossom audit required",
    )
    require(
        digest(blossom_audit_path) == selected["selection"]["independent_audit_sha256"],
        "selection audit hash",
    )
    excluded = set()
    for report in (first, blossom):
        for record in report["checks"]:
            if record["proves_infeasible"]:
                require(Fraction(*record["gap"]) > 0, "nonpositive exclusion gap")
                excluded.add(record["id"])
    require(len(excluded) == 102, "prior exclusion count")
    actual = [r["id"] for c in selected["cases"] for r in c["representatives"]]
    require(
        len(actual) == len(set(actual)) == 156 and set(actual) == set(full_reps) - excluded,
        "complete surviving first-link selection required",
    )
    blocks = list(combinations(range(1, 17), 5))
    block_ids = {block: i for i, block in enumerate(blocks)}
    prepared = {}
    for case in selected["cases"]:
        name = case["case"]
        record = next(r for r in manifest["cases"] if r["case"] == name)
        matrix_path = input_directory / name / "extended-rows.json.gz"
        require(digest(matrix_path) == record["extended_rows_sha256"], "matrix hash")
        payload = compressed(matrix_path)
        representatives = []
        for representative in case["representatives"]:
            require(representative == full_reps[representative["id"]], "representative changed")
            require(representative["id"].startswith(name + "-"), "representative case")
            ids = [block_ids[(1, 2, 3, *edge)] for edge in representative["edges"]]
            require(len(ids) == len(set(ids)) == FIXED_COUNT, "bad fixed blocks")
            representatives.append(dict(**representative, fixed_ids=ids))
        prepared[name] = dict(
            record=record, payload=payload, matrix_path=matrix_path, representatives=representatives
        )
    return (
        manifest,
        prepared,
        dict(
            original_audit_sha256=digest(first_audit_path),
            blossom_audit_sha256=digest(blossom_audit_path),
            selected_sha256=digest(representatives_path),
            matrix_audit_sha256=digest(audit_path),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=REPO / "experiments/scratch/four-seven-template-hull-20261003"
    )
    parser.add_argument(
        "--representatives",
        type=Path,
        default=ARTIFACTS / "four-seven-blossom-screen/remaining-representatives.json",
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=ARTIFACTS / "four-seven-template-hull/independent-audit.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=("cycle", "matching", "both"), default="both")
    parser.add_argument("--seconds", type=float, default=15.0)
    args = parser.parse_args()
    require(
        math.isfinite(args.seconds) and 0 < args.seconds <= 15, "solver budget must be in (0,15]"
    )
    require(not args.output.exists(), "output directory must be new")
    helpers, utility_path = utilities()
    manifest, prepared, input_hashes = load_inputs(args.input, args.representatives, args.audit)
    for case in prepared.values():
        helpers.validate_rows(case["payload"]["rows"], case["payload"]["width"])
    args.output.mkdir(parents=True)
    (args.output / "run.py").write_bytes(Path(__file__).read_bytes())
    (args.output / "whole-hull-utilities.py").write_bytes(utility_path.read_bytes())
    (args.output / "representatives.json").write_bytes(args.representatives.read_bytes())
    (args.output / "prototype-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name in ("check_cover.py",):
        (args.output / name).write_bytes((REPO / "scripts" / name).read_bytes())
    (args.output / "core.py").write_bytes(
        Path(helpers.verify_cover.__code__.co_filename).read_bytes()
    )
    metadata = dict(
        source_sha256=digest(Path(__file__)),
        utilities_sha256=UTILITIES_SHA256,
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        ortools_version=ortools.__version__,
        manifest_sha256=MANIFEST_SHA256,
        input_hashes=input_hashes,
        seconds_per_representative=args.seconds,
        command=sys.argv,
        selected_case=args.case,
        verifier_sha256={n: digest(args.output / n) for n in ("core.py", "check_cover.py")},
        cases={},
        scope="Original-100 surviving template hull plus exactly seven fixed block equalities. "
        "156 representatives omit the 102 independently excluded first-link types. "
        "Positive generated certificates require independent replay before exclusion claims.",
    )
    results = []
    for name, case in prepared.items():
        if args.case not in ("both", name):
            continue
        directory = args.output / name
        directory.mkdir()
        (directory / "extended-rows.json.gz").write_bytes(case["matrix_path"].read_bytes())
        model = ReusableHull(case["payload"])
        (directory / "feasibility-base.pb.gz").write_bytes(
            gzip.compress(model.prefix_bytes, mtime=0)
        )
        metadata["cases"][name] = dict(
            width=model.width,
            base_rows=BASE_ROWS,
            fixed_rows=FIXED_COUNT,
            representatives=len(case["representatives"]),
            matrix_sha256=digest(case["matrix_path"]),
            feasibility_base_sha256=model.prefix_sha256,
        )
        (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        phase_model = None
        for representative in case["representatives"]:
            identifier = representative["id"]
            target = directory / identifier
            target.mkdir()
            fixed_ids = representative["fixed_ids"]
            fixed_rows = [[[i], [1], 1, 1] for i in fixed_ids]
            rows = [*case["payload"]["rows"], *fixed_rows]
            (target / "fixed-rows.json").write_text(
                json.dumps(
                    dict(
                        id=identifier,
                        case=name,
                        width=model.width,
                        base_matrix_sha256=digest(case["matrix_path"]),
                        rows=fixed_rows,
                    ),
                    indent=2,
                )
                + "\n"
            )
            before = model.fix(fixed_ids)
            try:
                feasibility, primal, _ = model.solve(
                    args.seconds, target / "feasibility-solver.log"
                )
            finally:
                reset = model.reset()
            result = dict(
                id=identifier,
                case=name,
                fixed_ids=fixed_ids,
                checked_rows=len(rows),
                checked_columns=model.width,
                feasibility_lp=feasibility,
                fixed_state_audit=before,
                reset_audit=reset,
                certificate_pending_replay=False,
                independently_excluded=False,
            )
            if primal is not None:
                result["primal_metrics"] = helpers.primal_metrics(primal, rows)
                sparse = dict(
                    width=model.width,
                    values=[[i, value] for i, value in enumerate(primal) if value != 0],
                    zero_default=True,
                    fixed_ids=fixed_ids,
                    base_matrix_sha256=digest(case["matrix_path"]),
                )
                save_compressed(target / "sparse-primal.json.gz", sparse)
                result["sparse_primal_sha256"] = digest(target / "sparse-primal.json.gz")
                result["integral_blocks"] = helpers.check_integral_blocks(
                    primal, target, args.output / "check_cover.py"
                )
            elif feasibility["status"] == pywraplp.Solver.INFEASIBLE:
                remaining = max(0, args.seconds - feasibility["solve_seconds"])
                if remaining >= 0.001:
                    if phase_model is None:
                        phase_model = ReusableHull(case["payload"], phase_one=True)
                        (directory / "phase-one-base.pb.gz").write_bytes(
                            gzip.compress(phase_model.prefix_bytes, mtime=0)
                        )
                        metadata["cases"][name]["phase_one_base_sha256"] = phase_model.prefix_sha256
                        (args.output / "metadata.json").write_text(
                            json.dumps(metadata, indent=2) + "\n"
                        )
                    phase_model.fix(fixed_ids)
                    try:
                        phase, _, dual = phase_model.solve(
                            remaining, target / "phase-one-solver.log"
                        )
                    finally:
                        phase_reset = phase_model.reset()
                    result["phase_one_lp"] = phase
                    result["phase_one_reset_audit"] = phase_reset
                    if dual is not None:
                        save_compressed(target / "phase-one-dual.json.gz", dict(weights=dual))
                        result["certificate_attempts"] = []
                        for denominator in (1_000_000, 1_000_000_000):
                            certificate = helpers.integer_certificate(
                                rows, model.width, dual, denominator
                            )
                            certificate_path = target / f"certificate-{denominator}.json"
                            certificate_path.write_text(json.dumps(certificate, indent=2) + "\n")
                            result["certificate_attempts"].append(
                                dict(
                                    file=certificate_path.name,
                                    sha256=digest(certificate_path),
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
            save_compressed(args.output / "results.json.gz", results)
            print(
                json.dumps(
                    dict(
                        id=identifier,
                        status=feasibility["status_name"],
                        pending_certificate=result["certificate_pending_replay"],
                        solve_seconds=result["solve_seconds_total"],
                    )
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
