# Document:    Heavy-Link Blossom Cut Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2697abca9aee12514bc063f816a5dc42762dd3a3131e274906cc5d3de2974ae9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import sys
from itertools import combinations
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_blossom_cuts as cuts  # noqa: E402
from four_seven_double_cuts import add_double_triple_cuts  # noqa: E402
from four_seven_search import build_model  # noqa: E402


def protobuf(model):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), result)
    return result


def expected(group):
    anchor = set(range(4 * group + 1, 4 * group + 4))
    outside = sorted(set(range(1, 17)) - anchor)
    hub = 4 * group + 4
    result = {}
    omitted = 0
    for mask in range(1 << 13):
        subset = tuple(outside[index] for index in range(13) if mask & (1 << index))
        degree_sum = sum(2 if point == hub else 1 for point in subset)
        if degree_sum % 2 == 0 or len(subset) > 6:
            continue
        upper = degree_sum // 2
        edges = tuple(combinations(subset, 2))
        if len(edges) <= upper:
            omitted += 1
            continue
        result[subset] = (upper, edges)
    assert omitted == 24 and len(result) == 2024
    return result


def test_complete_canonical_templates_and_all_four_transports():
    base = dict(cuts.templates(0))
    for group in range(4):
        independent = expected(group)
        assert dict(cuts.templates(group)) == {subset: upper
                                              for subset, (upper, _) in independent.items()}
        points = {point: ((point - 1 + 4 * group) % 16) + 1 for point in range(1, 17)}
        transported = {tuple(sorted(points[point] for point in subset)): upper
                       for subset, upper in base.items()}
        assert transported == dict(cuts.templates(group))
        outside = set(range(1, 17)) - set(range(4 * group + 1, 4 * group + 4))
        for subset, (upper, _) in independent.items():
            complement = outside - set(subset)
            assert len(complement) >= 7
            other_upper = (len(complement) + int(4 * group + 4 in complement)) // 2
            assert upper + other_upper == 6
    for invalid in (-1, 4, True, 0.0):
        with pytest.raises(ValueError):
            list(cuts.templates(invalid))


@pytest.fixture(scope="module", params=["cycle", "matching"])
def base(request):
    universe, model, xs, _ = build_model(request.param)
    return request.param, universe, model, xs


@pytest.mark.parametrize("double_lift", [False, True])
def test_exact_rows_and_preservation_of_every_existing_proto_field(base, double_lift):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(index) for index in range(4368)]
    if double_lift:
        add_double_triple_cuts(universe, model, xs, case)
    model.add_hint(xs[0], 0)
    model.minimize(xs[0])
    before = protobuf(model)
    info = cuts.add_blossom_cuts(universe, model, xs, case)
    after = protobuf(model)
    assert info["new_rows"] == 8096 and info["new_variables"] == 0
    ids = {block: index for index, block in enumerate(combinations(range(1, 17), 5))}
    rules = {group: expected(group) for group in range(4)}
    seen = set()
    for row, descriptor in zip(after.constraints[len(before.constraints):], info["rows"],
                               strict=True):
        group, subset = descriptor["group_index"], tuple(descriptor["subset"])
        upper, edges = rules[group][subset]
        anchor = tuple(range(4 * group + 1, 4 * group + 4))
        expected_ids = sorted(ids[tuple(sorted((*anchor, *edge)))] for edge in edges)
        assert (group, subset) not in seen
        seen.add((group, subset))
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert row.name == descriptor["row_name"]
        assert tuple(row.linear.domain) == (-(2**63), upper)
        assert sorted(zip(row.linear.vars, row.linear.coeffs)) == [(i, 1) for i in expected_ids]
        assert descriptor["variable_indices"] == expected_ids
    assert len(seen) == 8096
    del after.constraints[len(before.constraints):]
    assert before == after
    unchanged = protobuf(model)
    with pytest.raises(ValueError, match="already present"):
        cuts.add_blossom_cuts(universe, model, xs, case)
    assert protobuf(model) == unchanged


def test_invalid_scope_and_damaged_degree_rejected_before_mutation(base):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(index) for index in range(4368)]
    before = protobuf(model)
    for wrong_case, wrong_xs in (("matching" if case == "cycle" else "cycle", xs),
                                 (case, [xs[1], xs[0], *xs[2:]])):
        with pytest.raises(ValueError):
            cuts.add_blossom_cuts(universe, model, wrong_xs, wrong_case)
        assert protobuf(model) == before
    partial_universe, partial, partial_xs, _ = build_model(case, max_missing=1)
    before_partial = protobuf(partial)
    with pytest.raises(ValueError, match="coverage"):
        cuts.add_blossom_cuts(partial_universe, partial, partial_xs, case)
    assert protobuf(partial) == before_partial
    for row in model.proto.constraints:
        if row.has_linear() and list(row.linear.domain) == [20, 20]:
            row.linear.domain[0] = 19
            break
    damaged = protobuf(model)
    with pytest.raises(ValueError, match="degree"):
        cuts.add_blossom_cuts(universe, model, xs, case)
    assert protobuf(model) == damaged
