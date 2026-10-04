# Document:    Bounded GLOP Screen of the Complete Surviving Link Hull
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cc7edb1fd1d58278cb0eafe2695d84b2f4d6d0937fe3e9520187bed644a85f68
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import gzip
import hashlib
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
from ortools.linear_solver import pywraplp

from covering64.core import verify_cover, write_blocks

EPSILON = 1e-7
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


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


def validate_rows(rows, width):
    require(type(width) is int and width >= 4768, "wrong variable width")
    require(len(rows) == 4550, "expected complete original-base template hull")
    for ids, coefficients, lower, upper in rows:
        require(len(ids) == len(coefficients) and len(ids) == len(set(ids)), "malformed row")
        require(all(type(i) is int and 0 <= i < width for i in ids), "column index out of range")
        require(all(type(c) is int for c in coefficients), "noninteger coefficient")
        require(all(b is None or type(b) is int for b in (lower, upper)), "noninteger bound")
        require(lower is None or upper is None or lower <= upper, "inverted row bounds")


def solve_stage(rows, width, seconds, directory, phase_one=False):
    stage = "phase-one" if phase_one else "feasibility"
    start = time.monotonic()
    solver = pywraplp.Solver.CreateSolver("GLOP")
    require(solver is not None, "GLOP unavailable")
    variables = [solver.NumVar(0, 1, f"x{i}") for i in range(width)]
    constraints = []
    for index, (ids, coefficients, lower, upper) in enumerate(rows):
        row = solver.RowConstraint(
            lower if lower is not None else -solver.infinity(),
            upper if upper is not None else solver.infinity(),
            f"row_{index}",
        )
        for column, coefficient in zip(ids, coefficients, strict=True):
            row.SetCoefficient(variables[column], coefficient)
        if phase_one and index >= 4270:
            for side, bound, sign in (("lower", lower, 1), ("upper", upper, -1)):
                if bound is not None:
                    slack = solver.NumVar(0, solver.infinity(), f"slack_{side}_{index}")
                    row.SetCoefficient(slack, sign)
                    solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    construction_seconds = time.monotonic() - start
    solver.SetTimeLimit(max(1, math.floor(seconds * 1000)))
    log_path = directory / f"{stage}-solver.log"
    saved = [os.dup(1), os.dup(2)]
    try:
        sys.stdout.flush()
        sys.stderr.flush()
        with log_path.open("w") as log:
            os.dup2(log.fileno(), 1)
            os.dup2(log.fileno(), 2)
            solver.EnableOutput()
            start_solve = time.monotonic()
            status = solver.Solve()
            solve_seconds = time.monotonic() - start_solve
    finally:
        for fd, original in zip((1, 2), saved, strict=True):
            os.dup2(original, fd)
            os.close(original)
    names = {
        solver.OPTIMAL: "OPTIMAL",
        solver.FEASIBLE: "FEASIBLE",
        solver.INFEASIBLE: "INFEASIBLE",
        solver.UNBOUNDED: "UNBOUNDED",
        solver.ABNORMAL: "ABNORMAL",
        solver.NOT_SOLVED: "NOT_SOLVED",
    }
    result = dict(
        status=int(status),
        status_name=names.get(status, "UNKNOWN_STATUS"),
        stage=stage,
        construction_seconds=construction_seconds,
        solve_seconds=solve_seconds,
        allocated_solver_seconds=seconds,
        solver_version=solver.SolverVersion(),
        log_sha256=digest(log_path),
        original_columns=width,
        original_rows=len(rows),
    )
    primal = None
    dual = None
    if status in (solver.OPTIMAL, solver.FEASIBLE):
        result["objective"] = solver.Objective().Value()
        if phase_one:
            dual = [row.dual_value() for row in constraints]
            require(all(math.isfinite(v) for v in dual), "nonfinite phase-one dual")
        else:
            primal = [variable.solution_value() for variable in variables]
            require(all(math.isfinite(v) for v in primal), "nonfinite primal")
    return result, primal, dual


def primal_metrics(values, rows):
    domain = max(max(-value, value - 1, 0) for value in values)
    residual = 0.0
    for ids, coefficients, lower, upper in rows:
        total = math.fsum(values[i] * c for i, c in zip(ids, coefficients, strict=True))
        residual = max(
            residual, 0 if lower is None else lower - total, 0 if upper is None else total - upper
        )
    clipped = [max(0, min(1, value)) for value in values[:4368]]
    return dict(
        max_domain_violation=domain,
        max_row_violation=residual,
        numerically_valid=domain <= EPSILON and residual <= EPSILON,
        block_sum=math.fsum(values[:4368]),
        double_sum=math.fsum(values[4368:4768]),
        fractional_block_count=sum(EPSILON < v < 1 - EPSILON for v in clipped),
        fractional_block_mass=math.fsum(min(v, 1 - v) for v in clipped),
        positive_template_weights=sum(v > EPSILON for v in values[4768:]),
    )


def integer_certificate(rows, width, dual, denominator):
    require(len(dual) == len(rows), "dual row count")
    weights = [round(value * denominator) for value in dual]
    column_sums = [0] * width
    rhs = 0
    for (ids, coefficients, lower, upper), weight in zip(rows, weights, strict=True):
        if not weight:
            continue
        bound = lower if weight > 0 else upper
        require(bound is not None, "dual weight selects infinite bound")
        rhs += weight * bound
        for column, coefficient in zip(ids, coefficients, strict=True):
            column_sums[column] += weight * coefficient
    box_max = sum(max(0, total) for total in column_sums)
    gap = Fraction(rhs - box_max, denominator)
    return dict(
        denominator=denominator,
        weights=[[i, w] for i, w in enumerate(weights) if w],
        rhs_numerator=rhs,
        box_max_numerator=box_max,
        gap=[gap.numerator, gap.denominator],
        checked_columns=width,
        checked_rows=len(rows),
        proves_infeasible=gap > 0,
        box_bounds=[0, 1],
    )


def check_integral_blocks(values, directory, standalone):
    block_values = values[:4368]
    distance = max(min(abs(v), abs(v - 1)) for v in block_values)
    selected = [i for i, value in enumerate(block_values) if value >= 0.5]
    report = dict(
        max_integrality_distance=distance,
        near_integral=distance <= EPSILON,
        selected_block_count=len(selected),
        candidate_checked=False,
    )
    if distance > EPSILON or len(selected) != 64:
        return report
    blocks = list(combinations(range(1, 17), 5))
    candidate = [blocks[i] for i in selected]
    path = directory / "integral-block-candidate.txt"
    write_blocks(path, candidate)
    package = verify_cover(candidate)
    process = subprocess.run(
        [sys.executable, str(standalone), str(path), "--expected-blocks", "64"],
        capture_output=True,
        text=True,
    )
    require(process.returncode in (0, 1), "standalone candidate checker crashed")
    separate = json.loads(process.stdout)
    require(
        package["canonical_sha256"] == separate["canonical_sha256"]
        and [list(triple) for triple in package["uncovered"]] == separate["uncovered"]
        and package["valid"] == separate["valid"],
        "cover checker disagreement",
    )
    checks = dict(package=package, standalone=separate)
    (directory / "integral-block-checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    report.update(
        candidate_checked=True,
        valid_cover=package["valid"],
        uncovered_count=len(package["uncovered"]),
        candidate_sha256=digest(path),
        checks_sha256=digest(directory / "integral-block-checks.json"),
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=REPO / "experiments/scratch/four-seven-template-hull-20261003"
    )
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=("cycle", "matching", "both"), default="both")
    parser.add_argument("--seconds", type=float, default=60.0)
    args = parser.parse_args()
    require(
        math.isfinite(args.seconds) and args.seconds > 0, "positive finite solver budget required"
    )
    require(not args.output.exists(), "output directory must be new")
    manifest_path = args.input / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    audit = json.loads(args.audit.read_text())
    require(
        audit.get("valid") is True and audit.get("manifest_sha256") == digest(manifest_path),
        "successful independent audit of this exact manifest required",
    )
    selected = [r for r in manifest["cases"] if args.case == "both" or r["case"] == args.case]
    require(len(selected) == (2 if args.case == "both" else 1), "case not in manifest")
    payloads = {}
    for record in selected:
        path = args.input / record["case"] / "extended-rows.json.gz"
        require(digest(path) == record["extended_rows_sha256"], "frozen matrix hash mismatch")
        payload = compressed(path)
        require(payload["width"] == record["total_variables"], "matrix width mismatch")
        require(
            payload["variable_bounds"]
            == "Every variable has bounds [0,1]; all are continuous in this LP.",
            "unexpected variable domains",
        )
        validate_rows(payload["rows"], payload["width"])
        payloads[record["case"]] = payload
    args.output.mkdir(parents=True)
    (args.output / "run_lp.py").write_bytes(Path(__file__).read_bytes())
    (args.output / "prototype-manifest.json").write_bytes(manifest_path.read_bytes())
    (args.output / "independent-audit.json").write_bytes(args.audit.read_bytes())
    verifier_sources = {}
    for name, source in (
        ("check_cover.py", REPO / "scripts/check_cover.py"),
        ("core.py", Path(verify_cover.__code__.co_filename)),
    ):
        (args.output / name).write_bytes(source.read_bytes())
        verifier_sources[name] = digest(source)
    metadata = dict(
        source_sha256=digest(Path(__file__)),
        manifest_sha256=digest(manifest_path),
        audit_sha256=digest(args.audit),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        ortools_version=ortools.__version__,
        solver="GLOP",
        epsilon=EPSILON,
        command=sys.argv,
        solver_seconds_per_case=args.seconds,
        budget_scope="Sum of Solve wall times for feasibility and optional phase one; "
        "construction recorded separately.",
        verifier_sources=verifier_sources,
        matrix_hashes={r["case"]: r["extended_rows_sha256"] for r in selected},
        scope="Regular four-sevenfold branch with complete surviving-link catalogs. "
        "Numerical feasibility is not a cover. Status alone is not an exact exclusion.",
    )
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    results = []
    for record in selected:
        case = record["case"]
        directory = args.output / case
        directory.mkdir()
        payload = payloads[case]
        rows, width = payload["rows"], payload["width"]
        feasibility, primal, _ = solve_stage(rows, width, args.seconds, directory)
        result = dict(case=case, feasibility=feasibility, proves_infeasible=False)
        if primal is not None:
            save_compressed(
                directory / "primal.json.gz",
                dict(
                    case=case,
                    width=width,
                    values=primal,
                    matrix_sha256=record["extended_rows_sha256"],
                ),
            )
            result["primal_metrics"] = primal_metrics(primal, rows)
            result["primal_sha256"] = digest(directory / "primal.json.gz")
            result["integral_blocks"] = check_integral_blocks(
                primal, directory, args.output / "check_cover.py"
            )
        elif feasibility["status"] == pywraplp.Solver.INFEASIBLE:
            remaining = max(0, args.seconds - feasibility["solve_seconds"])
            if remaining >= 0.001:
                phase, _, dual = solve_stage(rows, width, remaining, directory, phase_one=True)
                result["phase_one"] = phase
                if dual is not None:
                    save_compressed(directory / "phase-one-dual.json.gz", dict(weights=dual))
                    result["phase_one_dual_sha256"] = digest(directory / "phase-one-dual.json.gz")
                    result["certificate_attempts"] = []
                    for denominator in (1_000_000, 1_000_000_000):
                        certificate = integer_certificate(rows, width, dual, denominator)
                        path = directory / f"certificate-{denominator}.json"
                        path.write_text(json.dumps(certificate, indent=2) + "\n")
                        result["certificate_attempts"].append(
                            dict(
                                file=path.name,
                                sha256=digest(path),
                                gap=certificate["gap"],
                                proves_infeasible=certificate["proves_infeasible"],
                            )
                        )
                        if certificate["proves_infeasible"]:
                            result["proves_infeasible"] = True
                            break
        result["solve_seconds_total"] = feasibility["solve_seconds"] + result.get(
            "phase_one", {}
        ).get("solve_seconds", 0)
        (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
