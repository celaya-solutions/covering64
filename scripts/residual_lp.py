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

import math
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
    # Round down to one common denominator. Independent rational approximations
    # can create enormous denominators when their capacity errors are rescaled.
    denominator = 1000000
    numerators = {t: max(0, math.floor(v.solution_value() * denominator))
                  for t, v in variables.items()}
    numerators = {t: n for t, n in numerators.items() if n}
    loads = [0] * len(universe.blocks)
    for t, numerator in numerators.items():
        for block in universe.containing[t]:
            loads[block] += numerator
    # This integer capacity check covers every possible added block. Rescaling
    # also repairs any small violation inherited from the floating LP result.
    denominator = max(denominator, max(loads))
    weights = {t: Fraction(n, denominator) for t, n in numerators.items()}
    bound = sum(weights.values(), Fraction(0))
    return {"weights": [[t, w.numerator, w.denominator] for t, w in weights.items()],
            "lower_bound": [bound.numerator, bound.denominator], "lp_status": str(status)}
