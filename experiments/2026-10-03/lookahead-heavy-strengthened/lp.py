# Document:    Exact Rational Fixed-Heavy LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3b1e0ece880f7db1c759b2a000b997d578ceaff1e42b3f62e271f07a1ab0a4b1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import hashlib
import json
import time
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/lookahead-heavy-strengthened-lp-v1.0.0"
INF = 9223372036854775807


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def solve(rows, elastic=False):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(30000)
    xs = [solver.NumVar(0, 1, f"x_{i}") for i in range(1200)]
    constraints = []
    for index, (ids, coefs, lower, upper) in enumerate(rows):
        row = solver.Constraint(lower, upper if upper != INF else solver.infinity())
        for var, coef in zip(ids, coefs, strict=True):
            row.SetCoefficient(xs[var], coef)
        if elastic:
            for side, bound, coef in [("lo", lower, 1), ("hi", upper, -1)]:
                if bound != INF:
                    slack = solver.NumVar(0, solver.infinity(), f"{side}_{index}")
                    row.SetCoefficient(slack, coef)
                    solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    before = time.monotonic()
    status = solver.Solve()
    labels = {
        0: "OPTIMAL",
        1: "FEASIBLE",
        2: "INFEASIBLE",
        3: "UNBOUNDED",
        4: "ABNORMAL",
        6: "NOT_SOLVED",
    }
    record = {
        "status": labels.get(status, str(status)),
        "elastic": elastic,
        "seconds": time.monotonic() - before,
        "time_limit_seconds": 30,
        "solver": solver.SolverVersion(),
    }
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return record, None, None
    record["objective"] = solver.Objective().Value()
    return record, [x.solution_value() for x in xs], [c.dual_value() for c in constraints]


def exact_dual(rows, dual, denominator):
    weights = [round(v * denominator) for v in dual]
    totals = [0] * 1200
    rhs = 0
    for i, (ids, coefs, lower, upper) in enumerate(rows):
        weight = weights[i]
        if weight < 0 and upper == INF:
            weights[i] = weight = 0
        rhs += weight * (lower if weight >= 0 else upper)
        for var, coef in zip(ids, coefs, strict=True):
            totals[var] += weight * coef
    box = sum(max(0, value) for value in totals)
    gap = Fraction(rhs - box, denominator)
    return {
        "denominator": denominator,
        "weights": [[i, w] for i, w in enumerate(weights) if w],
        "rhs_numerator": rhs,
        "box_max_numerator": box,
        "gap": [gap.numerator, gap.denominator],
        "proves_infeasible": rhs > box,
    }


def exact_primal(rows, values, denominator_limit):
    xs = [Fraction(v).limit_denominator(denominator_limit) for v in values]
    if any(x < 0 or x > 1 for x in xs):
        return None
    for ids, coefs, lower, upper in rows:
        value = sum((coef * xs[i] for i, coef in zip(ids, coefs, strict=True)), Fraction(0))
        if value < lower or (upper != INF and value > upper):
            return None
    return {
        "values": [[x.numerator, x.denominator] for x in xs],
        "fractional_variables": sum(0 < x < 1 for x in xs),
        "maximum_denominator": max(x.denominator for x in xs),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", type=Path)
    args = parser.parse_args()
    assert not RAW.exists()
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(args.gate.read_text())
    assert gate["passed"] and gate["model_sha256"] == manifest["model_sha256"]
    source = ROOT / manifest["model"]
    assert sha(source) == manifest["model_sha256"]
    assert sha(HERE / "build.py") == manifest["builder_sha256"]
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(source.read_text(), proto)
    rows = [
        (list(c.linear.vars), list(c.linear.coeffs), *c.linear.domain) for c in proto.constraints
    ]
    assert len(rows) == 697 and len(proto.variables) == 1200
    RAW.mkdir(parents=True)
    for name in ["lp.py", "build.py", "manifest.json", "preservation-audit.json"]:
        (RAW / name).write_bytes((HERE / name).read_bytes())
    (RAW / "independent-audit.json").write_bytes(args.gate.read_bytes())
    first, values, dual = solve(rows)
    attempts = [first]
    result = {
        "runner_sha256": sha(Path(__file__)),
        "model_sha256": sha(source),
        "gate_sha256": sha(args.gate),
        "ortools_version": ortools_version,
        "attempts": attempts,
        "exact_status": "UNRESOLVED",
    }
    if values is not None:
        save(RAW / "numerical-primal.json", values)
        result["numerical_fractional_variables"] = sum(1e-7 < v < 1 - 1e-7 for v in values)
        for limit in [100, 10000, 1000000, 1000000000]:
            primal = exact_primal(rows, values, limit)
            if primal:
                save(HERE / "primal.json", primal)
                save(RAW / "primal.json", primal)
                result["exact_status"] = "RATIONAL_FEASIBLE"
                result["primal_sha256"] = sha(HERE / "primal.json")
                result["fractional_variables"] = primal["fractional_variables"]
                break
    elif first["status"] == "INFEASIBLE":
        phase, values, dual = solve(rows, elastic=True)
        attempts.append(phase)
        if dual is not None:
            save(RAW / "numerical-dual.json", dual)
            for denominator in [1000, 1000000, 1000000000]:
                certificate = exact_dual(rows, dual, denominator)
                if certificate["proves_infeasible"]:
                    save(HERE / "dual.json", certificate)
                    save(RAW / "dual.json", certificate)
                    result["exact_status"] = "RATIONAL_INFEASIBLE"
                    result["dual_sha256"] = sha(HERE / "dual.json")
                    result["gap"] = certificate["gap"]
                    break
    result["scope"] = "Only the fixed-heavy regular four-sevenfold family. Numerical "
    result["scope"] += "statuses alone do not prove feasibility or infeasibility."
    save(HERE / "lp-result.json", result)
    save(RAW / "result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
