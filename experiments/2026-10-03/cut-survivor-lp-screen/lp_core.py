# Document:    Exact Arithmetic LP Helpers for the Twelve-Tuple Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3bb41b28f4e637400344be6564a9caba7c5e9b14935a340185dc3f857fbbe4a3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import time
from fractions import Fraction

from ortools.linear_solver import pywraplp

INF = 9223372036854775807


def solve(rows, elastic=False):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(10000)
    assert solver.SetSolverSpecificParametersAsString("random_seed: 2026104")
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
        "time_limit_seconds": 10,
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
