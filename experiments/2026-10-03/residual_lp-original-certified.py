# Document:    Exact residual covering dual certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Use floating LP only to propose rational, exactly checked dual weights."""

from fractions import Fraction

from ortools.linear_solver import pywraplp


def residual_dual(universe, retained_ids):
    """Return a certified lower bound on additions to these retained blocks.

    Nonnegative weights on uncovered triples are feasible if every possible
    additional block has total weight at most one. Their sum then lower-bounds
    the number of additional blocks. Rational arithmetic checks every column;
    floating solver optimality is not trusted as proof.
    """
    retained = list(retained_ids)
    if len(set(retained)) != len(retained) or any(
        type(i) is not int or not 0 <= i < len(universe.blocks) for i in retained
    ):
        raise ValueError("Retained IDs must be distinct valid lexicographic block IDs")
    covered = {t for b in retained for t in universe.coverage[b]}
    missing = sorted(set(range(len(universe.triples))) - covered)
    if not missing:
        return {"weights": [], "lower_bound": [0, 1], "lp_status": "empty"}
    solver = pywraplp.Solver.CreateSolver("GLOP")
    variables = {t: solver.NumVar(0, solver.infinity(), str(t)) for t in missing}
    for coverage in universe.coverage:
        terms = [variables[t] for t in coverage if t in variables]
        if terms:
            solver.Add(sum(terms) <= 1)
    solver.Maximize(sum(variables.values()))
    status = solver.Solve()
    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return {"weights": [], "lower_bound": [0, 1], "lp_status": str(status)}
    weights = {t: max(Fraction(0), Fraction(v.solution_value()).limit_denominator(1000000))
               for t, v in variables.items()}
    weights = {t: w for t, w in weights.items() if w}
    maximum = max(sum((weights.get(t, Fraction(0)) for t in coverage), Fraction(0))
                  for coverage in universe.coverage)
    if maximum > 1:
        weights = {t: w / maximum for t, w in weights.items()}
    for coverage in universe.coverage:
        if sum((weights.get(t, Fraction(0)) for t in coverage), Fraction(0)) > 1:
            raise RuntimeError("Rational dual capacity check failed")
    bound = sum(weights.values(), Fraction(0))
    return {"weights": [[t, w.numerator, w.denominator] for t, w in weights.items()],
            "lower_bound": [bound.numerator, bound.denominator], "lp_status": str(status)}
