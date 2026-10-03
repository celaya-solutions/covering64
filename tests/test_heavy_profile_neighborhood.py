# Document:    Neighborhood Heavy Profile Regression Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Catch the original error of omitting multiplicity-six heavy triples."""

import importlib.util
from itertools import product
from pathlib import Path

from covering64.core import read_blocks

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "experiments/2026-10-03/heavy-profile-neighborhood/run.py"
SPEC = importlib.util.spec_from_file_location("profile_neighborhood", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_multiplicity_six_is_heavy_and_two_sevens_are_required():
    triples = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12), (13, 14, 15)]
    counts = dict(zip(triples, [7, 7, 6, 6, 6]))
    assert MODULE.forbidden_profile(counts) is not None
    counts[triples[0]] = 6
    assert MODULE.forbidden_profile(counts) is None
    counts[triples[0]] = 7
    counts[triples[4]] = 5
    assert MODULE.forbidden_profile(counts) is None


def test_actual_three_hole_regression_is_forbidden_and_escape_is_eligible():
    rejected = ROOT / "experiments/2026-10-03/heavy-profile-neighborhood/improvement-h3.txt"
    eligible = ROOT / "experiments/2026-10-03/first-family-independent/normalized-escape-h6.txt"
    assert MODULE.profile(read_blocks(rejected))["forbidden_five_disjoint"] is not None
    assert MODULE.profile(read_blocks(eligible))["forbidden_five_disjoint"] is None


def test_conditional_cut_truth_table_and_auxiliary_hints():
    for counts in product((5, 6, 7), repeat=5):
        model = MODULE.lns.cp_model.CpModel()
        variables = [model.new_int_var(0, 64, f"count_{i}") for i in range(5)]
        result = MODULE.add_profile_cut(model, variables, list(counts), "test")
        expected = not (all(c >= 6 for c in counts) and sum(c >= 7 for c in counts) >= 2)
        assert result["hint_satisfies_cut"] == expected
        values = dict(enumerate(counts))
        values.update(zip(model.proto.solution_hint.vars, model.proto.solution_hint.values))
        valid = True
        for constraint in model.proto.constraints:
            active = all(values[e] if e >= 0 else not values[-e - 1]
                         for e in constraint.enforcement_literal)
            if active:
                row = constraint.linear
                total = sum(values[v] * c for v, c in zip(row.vars, row.coeffs))
                valid &= any(row.domain[i] <= total <= row.domain[i + 1]
                             for i in range(0, len(row.domain), 2))
        assert valid == expected
