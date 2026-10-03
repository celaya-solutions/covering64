# Document:    Four Sevenfold Double Lift Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independent row arithmetic, original-field preservation, and fractional controls."""

import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_double_cuts as lift  # noqa: E402
from four_seven_search import build_model  # noqa: E402


def protobuf(model):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), result)
    return result


@pytest.fixture(scope="module", params=["cycle", "matching"])
def base(request):
    universe, model, xs, _ = build_model(request.param)
    return request.param, universe, model, xs


def test_every_added_row_and_all_original_fields(base):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    before = protobuf(model)
    flags, info = lift.add_double_triple_cuts(universe, model, xs, case)
    after = protobuf(model)
    assert info["new_variables"] == 400 and info["new_rows"] == 677
    eligible = [i for i, t in enumerate(universe.triples)
                if all(len(set(t) & set(g)) <= 1 for g in lift.ANCHORS)]
    fixed = {}
    for tid, t in enumerate(universe.triples):
        if tid in eligible:
            continue
        group = next(g for g in lift.ANCHORS if len(set(t) & set(g)) >= 2)
        fixed[tid] = 7 if tuple(t) == group else 2 if max(group) + 1 in t else 1
    expected = []

    def add(terms, target):
        expected.append((tuple(sorted(terms)), (target, target)))

    for tid in eligible:
        add([(i, 1) for i in universe.containing[tid]] + [(flags[tid].index, -1)], 1)
    for tid, target in fixed.items():
        if target != 7:
            add([(i, 1) for i in universe.containing[tid]], target)
    add([(flag.index, 1) for flag in flags.values()], 44)
    pairs = list(combinations(range(1, 17), 2))
    for pair in pairs:
        tids = [tid for tid in eligible if set(pair).issubset(universe.triples[tid])]
        # Derive the demand from three times the required pair count, subtracting
        # every known fixed contribution and one base incidence per eligible triple.
        target = 3 * lift.pair_targets(case)[pair] - len(tids)
        target -= sum(value for tid, value in fixed.items()
                      if set(pair).issubset(universe.triples[tid]))
        add([(flags[tid].index, 1) for tid in tids], target)
    actual = []
    for row in after.constraints[len(before.constraints):]:
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        actual.append((tuple(sorted(zip(row.linear.vars, row.linear.coeffs))),
                       tuple(row.linear.domain)))
    assert actual == expected
    assert sum(not terms for terms, _ in actual) == 12
    del after.variables[len(before.variables):]
    del after.constraints[len(before.constraints):]
    assert after == before


def test_fractional_extensions_by_independent_pair_recount(base):
    case, universe, _, _ = base
    path = ROOT / f"experiments/2026-10-03/four-seven-lp/{case}-witness.json"
    witness = json.loads(path.read_text())
    values = [Fraction(0)] * 4368
    for i, numerator, denominator in witness["nonzero_weights"]:
        values[i] = Fraction(numerator, denominator)
    extra = lift.fractional_double_values(universe, values)
    assert len(extra) == 400 and sum(extra.values()) == 44
    assert all(0 <= value <= 1 for value in extra.values())
    for pair, expected in lift.double_pair_targets(case).items():
        actual = sum((value for name, value in extra.items()
                      if set(pair).issubset(universe.triples[int(name.rsplit("_", 1)[1])])),
                     Fraction(0))
        assert actual == expected
    values[next(i for i, value in enumerate(values) if value)] += Fraction(1, 1000)
    with pytest.raises(ValueError):
        lift.fractional_double_values(universe, values)


def test_wrong_case_missing_full_coverage_and_duplicate_lift_rejected(base):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    with pytest.raises(ValueError, match="pair target"):
        lift.add_double_triple_cuts(universe, model, xs,
                                    "matching" if case == "cycle" else "cycle")
    with pytest.raises(ValueError, match="order"):
        lift.add_double_triple_cuts(universe, model, [xs[1], xs[0], *xs[2:]], case)
    lift.add_double_triple_cuts(universe, model, xs, case)
    with pytest.raises(ValueError, match="already present"):
        lift.add_double_triple_cuts(universe, model, xs, case)
    model = original.clone()
    for row in model.proto.constraints:
        if row.has_linear() and tuple(row.linear.domain) == (1, 2**63 - 1):
            row.linear.domain[0] = 0
            break
    with pytest.raises(ValueError, match="coverage"):
        lift.add_double_triple_cuts(
            universe, model, [model.get_int_var_from_proto_index(i) for i in range(4368)], case,
        )
