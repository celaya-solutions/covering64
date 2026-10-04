# Document:    Audited Sole-Degree-Nineteen LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ba1de091397a568d2b6542ec588f661bbdcd7e5cdc9aded5fe89baa5a8212732
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Sequential bounded LP screen of38 frozen independently audited raw models."""

import argparse
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp

from covering64.core import verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def exact_certificate(rows, width, dual, denominator):
    assert type(denominator) is int and denominator > 0
    weights = [int(round(value * denominator)) for value in dual]
    total = [0] * width
    rhs = 0
    for row_index, (weight, row) in enumerate(zip(weights, rows, strict=True)):
        indices, coefficients, lower, upper = row
        bound = lower if weight > 0 else upper
        if not weight:
            continue
        if bound is None:
            weights[row_index] = 0
            continue
        rhs += weight * bound
        for index, coefficient in zip(indices, coefficients, strict=True):
            total[index] += weight * coefficient
    support = sum(max(0, coefficient) for coefficient in total)
    gap = Fraction(rhs - support, denominator)
    return {"denominator": denominator,
            "weights": [[index, weight] for index, weight in enumerate(weights) if weight],
            "rhs_numerator": rhs, "box_max_numerator": support,
            "gap": [gap.numerator, gap.denominator], "proves_infeasible": rhs > support,
            "checked_rows": len(rows), "checked_columns": width}


def solve(rows, width, deadline, phase_one=False):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    assert solver is not None
    solver.SetNumThreads(1)
    xs = [solver.NumVar(0, 1, f"block_{index}") for index in range(width)]
    constraints = []
    for index, (indices, coefficients, lower, upper) in enumerate(rows):
        row = solver.Constraint(lower if lower is not None else -solver.infinity(),
                                upper if upper is not None else solver.infinity())
        for variable, coefficient in zip(indices, coefficients, strict=True):
            row.SetCoefficient(xs[variable], coefficient)
        if phase_one:
            for side, bound, coefficient in (("lo", lower, 1), ("hi", upper, -1)):
                if bound is not None:
                    slack = solver.NumVar(0, solver.infinity(), f"{side}_{index}")
                    row.SetCoefficient(slack, coefficient)
                    solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return {"status": "BUDGET_EXHAUSTED", "phase_one": phase_one}, None, None
    solver.SetTimeLimit(max(1, int(remaining * 1000)))
    solver.Objective().SetMinimization()
    started = time.monotonic()
    status = solver.Solve()
    labels = {pywraplp.Solver.OPTIMAL: "OPTIMAL", pywraplp.Solver.FEASIBLE: "FEASIBLE",
              pywraplp.Solver.INFEASIBLE: "INFEASIBLE", pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
              pywraplp.Solver.ABNORMAL: "ABNORMAL", pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED"}
    result = {"status": labels.get(status, str(status)), "phase_one": phase_one,
              "solver_seconds": time.monotonic() - started,
              "time_limit_milliseconds": max(1, int(remaining * 1000))}
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return result, None, None
    result["objective"] = solver.Objective().Value()
    return result, [variable.solution_value() for variable in xs], [
        constraint.dual_value() for constraint in constraints]


def primal_metrics(rows, values):
    assert all(math.isfinite(value) for value in values)
    domain = max(max(0, -value, value - 1) for value in values)
    row_error = 0.0
    for indices, coefficients, lower, upper in rows:
        value = math.fsum(coefficient * values[index]
                          for index, coefficient in zip(indices, coefficients, strict=True))
        row_error = max(row_error, max(0, lower - value) if lower is not None else 0,
                        max(0, value - upper) if upper is not None else 0)
    return {"maximum_domain_violation": domain, "maximum_row_violation": row_error,
            "numerically_valid": max(domain, row_error) <= 1e-7,
            "fractional_variables": sum(1e-7 < value < 1 - 1e-7 for value in values)}


def integral_candidate(rows, values, directory, standalone_path):
    integers = [int(round(value)) for value in values]
    if any(abs(value - rounded) > 1e-7 or rounded not in (0, 1)
           for value, rounded in zip(values, integers, strict=True)):
        return {"candidate_extracted": False, "cover_found": False,
                "verifier_outcome": "not applicable: fractional LP solution"}
    for indices, coefficients, lower, upper in rows:
        value = sum(coefficient * integers[index]
                    for index, coefficient in zip(indices, coefficients, strict=True))
        if (lower is not None and value < lower) or (upper is not None and value > upper):
            return {"candidate_extracted": False, "cover_found": False,
                    "verifier_outcome": "near-integer vector fails exact raw model rows"}
    blocks = list(combinations(range(1, 17), 5))
    candidate = [block for block, selected in zip(blocks, integers, strict=True) if selected]
    path = directory / "candidate.txt"
    write_blocks(path, candidate)
    package = verify_cover(candidate)
    completed = subprocess.run([sys.executable, str(standalone_path), str(path),
                                "--expected-blocks", "64"], capture_output=True, text=True)
    standalone = json.loads(completed.stdout)
    (directory / "standalone.stdout.txt").write_text(completed.stdout)
    (directory / "standalone.stderr.txt").write_text(completed.stderr)
    write_json(directory / "package-verifier.json", package)
    valid = (len(candidate) == 64 and package["valid"] and standalone["valid"]
             and completed.returncode == 0
             and package["canonical_sha256"] == standalone["canonical_sha256"])
    return {"candidate_extracted": True, "cover_found": valid,
            "verifier_outcome": "both passed" if valid else "candidate rejected",
            "package": package, "standalone": standalone,
            "standalone_returncode": completed.returncode}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    manifest = json.loads((args.input / "manifest.json").read_text())
    audit = json.loads(args.audit.read_text())
    assert audit["input_manifest_sha256"] == sha(args.input / "manifest.json")
    assert len(audit["cases"]) == len(manifest["cases"]) == 38
    audited = {row["id"]: row for row in audit["cases"]}
    assert len(audited) == 38 and all(row["passed"] for row in audited.values())
    args.output.mkdir(parents=True)
    shutil.copytree(args.input, args.output / "input")
    shutil.copyfile(args.audit, args.output / "model-audit.json")
    sources = {}
    for path in (Path(__file__), args.audit.with_name("check_models.py"),
                 ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        shutil.copyfile(path, args.output / path.name)
        sources[path.name] = sha(path)
    metadata = {"sources": sources, "input_manifest_sha256": sha(args.input / "manifest.json"),
                "model_audit_sha256": sha(args.audit), "solver_version": ortools.__version__,
                "backend": "GLOP", "threads": 1, "processes": 1,
                "seconds_per_model_total": 15, "random_seed": "GLOP default; not overridden",
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                           cwd=ROOT, text=True).strip(),
                "scope": "Complete38-case sole-degree19 model inventory only. Numerical LP "
                         "feasibility is not a covering witness. Only positive exact unit-box "
                         "contradictions exclude cases; other negative statuses are inconclusive."}
    write_json(args.output / "metadata.json", metadata)
    records = []
    for entry in manifest["cases"]:
        case_id = entry["id"]
        assert audited[case_id]["model_sha256"] == entry["model_sha256"]
        assert audited[case_id]["rows_sha256"] == entry["rows_sha256"]
        model_path = args.output / "input" / f"{case_id}.pbtxt"
        row_path = args.output / "input" / f"{case_id}-rows.json.gz"
        assert sha(model_path) == entry["model_sha256"] and sha(row_path) == entry["rows_sha256"]
        encoded = json.loads(gzip.decompress(row_path.read_bytes()))
        rows, width = encoded["rows"], encoded["width"]
        directory = args.output / case_id
        directory.mkdir()
        started = time.monotonic()
        deadline = started + 15
        feasibility, values, _ = solve(rows, width, deadline)
        result = {"id": case_id, "model_sha256": entry["model_sha256"],
                  "rows_sha256": entry["rows_sha256"], "feasibility_lp": feasibility,
                  "proves_infeasible": False, "cover_found": False,
                  "candidate_extracted": False,
                  "verifier_outcome": "not applicable: no integer LP solution"}
        if values is not None:
            result["primal_metrics"] = primal_metrics(rows, values)
            primal = directory / "primal.json.gz"
            primal.write_bytes(gzip.compress((json.dumps({"id": case_id, "values": values})
                                             + "\n").encode(), mtime=0))
            result["primal_sha256"] = sha(primal)
            if result["primal_metrics"]["numerically_valid"]:
                result.update(integral_candidate(rows, values, directory,
                                                 args.output / "check_cover.py"))
        elif feasibility["status"] == "INFEASIBLE":
            phase, _, dual = solve(rows, width, deadline, phase_one=True)
            result["phase_one_lp"] = phase
            if dual is not None:
                write_json(directory / "phase-one-duals.json", dual)
                attempts = []
                for denominator in (10**6, 10**8, 10**10):
                    certificate = exact_certificate(rows, width, dual, denominator)
                    attempts.append(certificate)
                    if certificate["proves_infeasible"]:
                        result["proves_infeasible"] = True
                        break
                result["certificate_attempts"] = attempts
        result["elapsed_seconds"] = time.monotonic() - started
        write_json(directory / "result.json", result)
        records.append(result)
        (args.output / "results.json.gz").write_bytes(gzip.compress(
            (json.dumps(records) + "\n").encode(), mtime=0))
        print(json.dumps({"id": case_id, "lp_status": feasibility["status"],
                          "excluded": result["proves_infeasible"],
                          "cover_found": result["cover_found"]}), flush=True)
    summary = {"cases": len(records), "exact_exclusions": sum(row["proves_infeasible"]
                                                              for row in records),
               "covers": sum(row["cover_found"] for row in records),
               "numerically_feasible": sum("primal_sha256" in row for row in records),
               "results_sha256": sha(args.output / "results.json.gz"),
               "total_elapsed_seconds": sum(row["elapsed_seconds"] for row in records),
               "raw_archive": str(args.output.relative_to(ROOT))}
    write_json(args.output / "summary.json", summary)
    write_json(Path(__file__).with_name("summary.json"), summary)


if __name__ == "__main__":
    main()
